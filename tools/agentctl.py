#!/usr/bin/env python3
"""
agentctl: lightweight control-plane helper for the vibecoding loop.

Commands:
- validate: enforce invariants across .vibe/STATE.md (and optionally .vibe/PLAN.md)
- status: print current stage/checkpoint/status + issue summary
- next: recommend which prompt loop to run next (ids align to prompts/template_prompts.md)

Assumptions:
- Repo authoritative workflow files live under .vibe/
  - .vibe/STATE.md
  - .vibe/PLAN.md
  - .vibe/HISTORY.md (optional)
- Script is stdlib-only and tolerant of minor markdown variation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

_tools_dir = Path(__file__).parent.resolve()
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

import checkpoint_templates
from resource_resolver import find_resource
from stage_ordering import (
    CHECKPOINT_ID_PATTERN,
    STAGE_ID_PATTERN,
    is_valid_stage_id,
    normalize_checkpoint_id,
    normalize_stage_id,
)

ALLOWED_STATUS = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "IN_REVIEW",
    "BLOCKED",
    "DONE",
}

# For prioritization (highest -> lowest)
IMPACT_ORDER = ["BLOCKER", "MAJOR", "MINOR", "QUESTION"]
IMPACTS = tuple(IMPACT_ORDER)
ISSUE_STATUS_VALUES = ("OPEN", "IN_PROGRESS", "BLOCKED", "RESOLVED")
LOOP_RESULT_PROTOCOL_VERSION = 1
LOOP_RESULT_REQUIRED_FIELDS = (
    "loop",
    "result",
    "stage",
    "checkpoint",
    "status",
    "next_role_hint",
)
LOOP_RESULT_LOOPS = {
    "design",
    "implement",
    "review",
    "issues_triage",
    "consolidation",
    "context_capture",
    "improvements",
    "advance",
}
LOOP_REPORT_REQUIRED_FIELDS = (
    "acceptance_matrix",
    "top_findings",
    "state_transition",
    "loop_result",
)
LOOP_REPORT_ITEM_STATUS = ("PASS", "FAIL", "N/A")
EVIDENCE_STRENGTH_VALUES = ("LOW", "MEDIUM", "HIGH")
LOOP_REPORT_MAX_FINDINGS = 5
CONFIDENCE_MIN_REQUIRED = 0.75
REFACTOR_IDEA_TAG_RE = re.compile(r"\[(MAJOR|MODERATE|MINOR)\]", re.IGNORECASE)

Role = Literal[
    "issues_triage",
    "review",
    "implement",
    "design",
    "context_capture",
    "consolidation",
    "improvements",
    "advance",
    "stop",
]


@dataclass(frozen=True)
class Issue:
    impact: str
    title: str
    line: str
    issue_id: str | None = None
    owner: str | None = None
    status: str | None = None
    unblock_condition: str | None = None
    evidence_needed: str | None = None
    checked: bool = False
    impact_specified: bool = False


@dataclass(frozen=True)
class StateInfo:
    stage: str | None
    checkpoint: str | None
    status: str | None
    evidence_path: str | None
    issues: tuple[Issue, ...]


@dataclass(frozen=True)
class PlanCheck:
    found_checkpoint: bool
    has_objective: bool
    has_deliverables: bool
    has_acceptance: bool
    has_demo: bool
    has_evidence: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    state: StateInfo | None
    plan_check: PlanCheck | None


def _parse_plan_checkpoint_ids(plan_text: str) -> list[str]:
    """
    Extract checkpoint ids in order from headings.

    Recognizes headings like:
      ### 1.2 — Title
      ### 12A.1 - Title
      ### (DONE) 1.2 — Title
      ### (SKIPPED) 12B.3 — Title
      ### (SKIP) 5.1 — Title
    """
    ids: list[str] = []
    # capture (DONE), (SKIPPED), or (SKIP) optionally, then capture the checkpoint id X.Y (with optional stage suffix)
    pat = re.compile(
        rf"(?im)^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?(?P<id>{CHECKPOINT_ID_PATTERN})\b"
    )
    for m in pat.finditer(plan_text):
        raw_id = m.group("id")
        try:
            ids.append(normalize_checkpoint_id(raw_id))
        except ValueError:
            ids.append(raw_id)
    return ids


def _parse_stage_headings(plan_text: str) -> list[tuple[str, int, str]]:
    """
    Return (stage_id, line_no, line_text) for each stage heading.

    Tolerates an optional (SKIP) marker before 'Stage':
      ## Stage 14 — Title
      ## (SKIP) Stage 14 — Title
    """
    lines = plan_text.splitlines()
    results: list[tuple[str, int, str]] = []
    stage_pat = re.compile(r"(?im)^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+(?P<stage>\S+)")
    for idx, line in enumerate(lines, start=1):
        m = stage_pat.match(line)
        if m:
            results.append((m.group("stage"), idx, line.rstrip()))
    return results


def _find_stage_bounds(plan_text: str, stage: str) -> tuple[int | None, int | None]:
    lines = plan_text.splitlines(keepends=True)
    stage_pat = re.compile(rf"(?im)^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{re.escape(stage)}\b")
    next_stage_pat = re.compile(rf"(?im)^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{STAGE_ID_PATTERN}\b")
    start_idx = None
    end_idx = None

    for idx, line in enumerate(lines):
        if start_idx is None and stage_pat.match(line):
            start_idx = idx
            continue
        if start_idx is not None and next_stage_pat.match(line):
            end_idx = idx
            break

    if start_idx is None:
        return (None, None)

    if end_idx is None:
        end_idx = len(lines)

    # Convert line indices to character offsets
    start_offset = sum(len(l) for l in lines[:start_idx])
    end_offset = sum(len(l) for l in lines[:end_idx])
    return (start_offset, end_offset)


def _next_checkpoint_id_for_stage(plan_text: str, stage: str) -> str:
    stage_norm = normalize_stage_id(stage) if is_valid_stage_id(stage) else stage
    ids = [
        cid
        for cid in _parse_plan_checkpoint_ids(plan_text)
        if _get_stage_for_checkpoint(plan_text, cid) == stage_norm and cid.startswith(f"{stage_norm}.")
    ]
    if not ids:
        return f"{stage_norm}.0"
    max_minor = max(int(cid.split(".", 1)[1]) for cid in ids)
    return f"{stage_norm}.{max_minor + 1}"


def _get_stage_for_checkpoint(plan_text: str, checkpoint_id: str) -> str | None:
    """
    Find the stage number that contains a given checkpoint.

    Looks for stage headings like:
      ## Stage 2 — Title
      ## Stage 12A - Title

    Returns the stage number as a string, or None if not found.
    """
    lines = plan_text.splitlines()
    current_stage: str | None = None
    stage_pat = re.compile(rf"(?im)^\s*##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+(?P<stage>{STAGE_ID_PATTERN})\b")
    try:
        checkpoint_norm = normalize_checkpoint_id(checkpoint_id)
    except ValueError:
        checkpoint_norm = checkpoint_id
    checkpoint_pat = re.compile(
        rf"(?im)^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?{re.escape(checkpoint_norm)}\b"
    )

    for line in lines:
        stage_match = stage_pat.match(line)
        if stage_match:
            current_stage = normalize_stage_id(stage_match.group("stage"))
        if checkpoint_pat.match(line):
            return current_stage

    return None


def _detect_stage_transition(
    plan_text: str, current_checkpoint: str, next_checkpoint: str
) -> tuple[bool, str | None, str | None]:
    """
    Detect if advancing from current_checkpoint to next_checkpoint crosses a stage boundary.

    Returns: (is_stage_change, current_stage, next_stage)
    """
    current_stage = _get_stage_for_checkpoint(plan_text, current_checkpoint)
    next_stage = _get_stage_for_checkpoint(plan_text, next_checkpoint)

    is_change = current_stage != next_stage and current_stage is not None and next_stage is not None
    return (is_change, current_stage, next_stage)


def _is_checkpoint_marked_done(plan_text: str, checkpoint_id: str) -> bool:
    """Check if a checkpoint is marked as (DONE) or (SKIPPED) in the plan.

    Note: (SKIP) is intentionally NOT matched here — skipped-for-later
    checkpoints are not considered done."""
    pat = re.compile(rf"(?im)^\s*#{{3,6}}\s+\(\s*(?:DONE|SKIPPED)\s*\)\s+{re.escape(checkpoint_id)}\b")
    return bool(pat.search(plan_text))


def _is_checkpoint_skipped(plan_text: str, checkpoint_id: str) -> bool:
    """Check if a checkpoint is marked as (SKIP) in the plan.

    (SKIP) checkpoints are deferred — bypassed during advance but preserved
    during consolidation.  Removing the marker reactivates the checkpoint."""
    pat = re.compile(rf"(?im)^\s*#{{3,6}}\s+\(\s*SKIP\s*\)\s+{re.escape(checkpoint_id)}\b")
    return bool(pat.search(plan_text))


def _next_checkpoint_after(plan_ids: list[str], current_id: str) -> str | None:
    try:
        idx = plan_ids.index(current_id)
    except ValueError:
        return plan_ids[0] if plan_ids else None
    if idx + 1 < len(plan_ids):
        return plan_ids[idx + 1]
    return None


def _resolve_prompt_catalog_path(repo_root: Path) -> Path | None:
    local_path = repo_root / "prompts" / "template_prompts.md"
    if local_path.exists():
        return local_path

    resolved = find_resource("prompt", "template_prompts.md")
    if resolved and resolved.exists():
        return resolved
    return None


def _load_prompt_catalog_index(
    repo_root: Path,
) -> tuple[dict[str, str], Path | None, str | None]:
    catalog_path = _resolve_prompt_catalog_path(repo_root)
    if catalog_path is None:
        return ({}, None, "Prompt catalog not found (expected prompts/template_prompts.md).")
    try:
        from prompt_catalog import load_catalog  # type: ignore

        entries = load_catalog(catalog_path)
        index = {entry.key: entry.title for entry in entries}
        return (index, catalog_path, None)
    except Exception:
        # Fallback for environments where prompt_catalog.py is not importable
        # from the current script location (for example copied skill scripts).
        try:
            raw = _read_text(catalog_path)
        except OSError as exc:
            return ({}, catalog_path, f"Failed to read prompt catalog at {catalog_path}: {exc}")

        index: dict[str, str] = {}
        header_pat = re.compile(r"(?im)^##\s+(?P<id>[a-z0-9_.-]+)\s+[—–-]\s+(?P<title>.+?)\s*$")
        for match in header_pat.finditer(raw):
            prompt_id = match.group("id").strip()
            if prompt_id and prompt_id not in index:
                index[prompt_id] = match.group("title").strip()

        if not index:
            return ({}, catalog_path, f"Failed to parse prompt catalog at {catalog_path}: no prompt headers found.")

    return (index, catalog_path, None)


def _strip_scalar(value: str) -> str:
    cleaned = value.split("#", 1)[0].strip()
    if (
        (cleaned.startswith('"') and cleaned.endswith('"'))
        or (cleaned.startswith("'") and cleaned.endswith("'"))
    ) and len(cleaned) >= 2:
        return cleaned[1:-1].strip()
    return cleaned


def _collect_workflow_prompt_refs(repo_root: Path) -> tuple[list[tuple[str, str]], tuple[str, ...]]:
    workflows_root = repo_root / "workflows"
    if not workflows_root.exists():
        return ([], ())

    refs: list[tuple[str, str]] = []
    warnings: list[str] = []
    yaml_prompt_pat = re.compile(r"^\s*(?:-\s*)?prompt_id\s*:\s*(?P<value>.+?)\s*$")

    for workflow_path in sorted(workflows_root.iterdir()):
        if not workflow_path.is_file():
            continue
        suffix = workflow_path.suffix.lower()
        if suffix not in {".yaml", ".yml", ".json"}:
            continue

        try:
            raw = _read_text(workflow_path)
        except OSError as exc:
            warnings.append(f"{workflow_path}: unreadable workflow file ({exc}).")
            continue

        if suffix == ".json":
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                warnings.append(f"{workflow_path}: invalid JSON workflow ({exc}).")
                continue
            steps = payload.get("steps", [])
            if not isinstance(steps, list):
                warnings.append(f"{workflow_path}: steps must be a list.")
                continue
            for step in steps:
                if not isinstance(step, dict):
                    continue
                prompt_id = step.get("prompt_id")
                if isinstance(prompt_id, str) and prompt_id.strip():
                    refs.append((workflow_path.name, prompt_id.strip()))
            continue

        for line in raw.splitlines():
            match = yaml_prompt_pat.match(line)
            if not match:
                continue
            prompt_id = _strip_scalar(match.group("value"))
            if prompt_id:
                refs.append((workflow_path.name, prompt_id))

    return (refs, tuple(warnings))


def _slice_active_issues_section(text: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(r"(?im)^\s*##\s+Active issues\s*$", line):
            start = idx + 1
            break
    if start is None:
        return []

    out: list[str] = []
    for line in lines[start:]:
        if re.match(r"(?im)^\s*##\s+\S", line):
            break
        out.append(line)
    return out


def _parse_issues_checkbox_format(text: str) -> tuple[Issue, ...]:
    """
    Parse issues only from the '## Active issues' section:

    - [ ] ISSUE-001: Title
      - Impact: QUESTION
      - Notes: ...
    """
    section_lines = _slice_active_issues_section(text)
    if not section_lines:
        return ()

    issues: list[Issue] = []
    issue_head = re.compile(r"^\s*-\s*\[\s*([xX ]?)\s*\]\s*(.+?)\s*$")
    detail_line = re.compile(r"^\s*-\s*(?P<key>[A-Za-z][A-Za-z _-]*)\s*:\s*(?P<val>.+?)\s*$")

    i = 0
    while i < len(section_lines):
        line = section_lines[i].rstrip("\n")
        m = issue_head.match(line)
        if not m:
            i += 1
            continue

        title = m.group(2).strip()
        # Ignore placeholders and explicit "None."
        if "<short" in title.lower() or title.strip().lower() in {"none", "none."}:
            i += 1
            continue

        checked = m.group(1).strip().lower() == "x"
        issue_id: str | None = None
        id_match = re.match(r"(?i)^(ISSUE-[A-Za-z0-9_.-]+)\s*:\s*(.+)$", title)
        if id_match:
            issue_id = id_match.group(1).upper()

        fields: dict[str, str] = {}
        j = i + 1
        while j < len(section_lines):
            nxt = section_lines[j]
            if issue_head.match(nxt):
                break
            if nxt.strip() == "":
                j += 1
                continue
            dm = detail_line.match(nxt)
            if dm:
                key = _normalize_issue_detail_key(dm.group("key"))
                if key and key not in fields:
                    fields[key] = dm.group("val").strip()
            j += 1

        impact_raw = fields.get("impact")
        impact = impact_raw.split()[0].upper() if impact_raw else None
        if impact not in IMPACTS:
            impact = "QUESTION"

        status_raw = fields.get("status")
        status = status_raw.split()[0].upper() if status_raw else None

        issues.append(
            Issue(
                impact=impact,
                title=title,
                line=line,
                issue_id=issue_id,
                owner=fields.get("owner"),
                status=status,
                unblock_condition=fields.get("unblock_condition"),
                evidence_needed=fields.get("evidence_needed"),
                checked=checked,
                impact_specified=impact_raw is not None,
            )
        )
        i = j

    return tuple(issues)


def _normalize_issue_detail_key(raw_key: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_key.strip().lower()).strip("_")
    aliases = {
        "impact": "impact",
        "owner": "owner",
        "status": "status",
        "unblock_condition": "unblock_condition",
        "unblock": "unblock_condition",
        "evidence_needed": "evidence_needed",
        "evidence": "evidence_needed",
        "notes": "notes",
    }
    return aliases.get(normalized)


def _is_placeholder_value(value: str | None) -> bool:
    if value is None:
        return True
    trimmed = value.strip()
    if not trimmed:
        return True
    lowered = trimmed.lower()
    if lowered in {"none", "none.", "tbd", "todo", "unknown", "n/a"}:
        return True
    return "<" in trimmed and ">" in trimmed


def _validate_issue_schema(issues: tuple[Issue, ...]) -> tuple[str, ...]:
    messages: list[str] = []
    for issue in issues:
        if issue.issue_id is None:
            messages.append(
                f"Active issue '{issue.title}' should use 'ISSUE-<id>: <title>' in the issue header."
            )
            continue

        missing: list[str] = []
        if not issue.impact_specified:
            missing.append("Impact")
        if _is_placeholder_value(issue.owner):
            missing.append("Owner")
        if _is_placeholder_value(issue.status):
            missing.append("Status")
        elif issue.status not in ISSUE_STATUS_VALUES:
            messages.append(
                f"Active issue {issue.issue_id} has invalid Status '{issue.status}'. "
                f"Allowed: {', '.join(ISSUE_STATUS_VALUES)}."
            )
        if _is_placeholder_value(issue.unblock_condition):
            missing.append("Unblock Condition")
        if _is_placeholder_value(issue.evidence_needed):
            missing.append("Evidence Needed")

        if missing:
            messages.append(
                f"Active issue {issue.issue_id} missing required field(s): {', '.join(missing)}."
            )

        if issue.checked and issue.status not in {"RESOLVED"}:
            messages.append(
                f"Active issue {issue.issue_id} is checked but Status is not RESOLVED."
            )
        if not issue.checked and issue.status == "RESOLVED":
            messages.append(
                f"Active issue {issue.issue_id} is unresolved checkbox but Status is RESOLVED."
            )

    return tuple(messages)


def _resolve_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (repo_root / path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _state_path(repo_root: Path) -> Path:
    return repo_root / ".vibe" / "STATE.md"


def _loop_result_path(repo_root: Path) -> Path:
    return repo_root / ".vibe" / "LOOP_RESULT.json"


def _state_sha256(repo_root: Path) -> str:
    path = _state_path(repo_root)
    text = _read_text(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_stage_for_compare(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    if is_valid_stage_id(value):
        return normalize_stage_id(value)
    return value


def _normalize_checkpoint_for_compare(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        return normalize_checkpoint_id(value)
    except ValueError:
        return value


def _bootstrap_loop_result_record(repo_root: Path, state: StateInfo) -> None:
    record_path = _loop_result_path(repo_root)
    if record_path.exists():
        return
    record_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol_version": LOOP_RESULT_PROTOCOL_VERSION,
        "loop": "bootstrap",
        "result": "initialized",
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
        "next_role_hint": "implement",
        "state_sha256": _state_sha256(repo_root),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    record_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_loop_result_record(repo_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    path = _loop_result_path(repo_root)
    if not path.exists():
        return (None, None)
    try:
        payload = json.loads(_read_text(path))
    except (json.JSONDecodeError, OSError) as exc:
        return (None, f"Failed to read {path}: {exc}")
    if not isinstance(payload, dict):
        return (None, f"Invalid LOOP_RESULT payload in {path}: expected JSON object.")
    return (payload, None)


def _loop_result_ack_status(repo_root: Path) -> tuple[bool, str]:
    path = _loop_result_path(repo_root)
    if not path.exists():
        return (True, "LOOP_RESULT protocol initialized for this state snapshot.")

    payload, error = _load_loop_result_record(repo_root)
    if error:
        return (False, error)
    if payload is None:
        return (False, f"Missing LOOP_RESULT payload at {path}.")

    recorded_hash = payload.get("state_sha256")
    if not isinstance(recorded_hash, str) or not recorded_hash:
        return (
            False,
            f"{path} is missing required field 'state_sha256'. "
            "Run agentctl loop-result with the latest LOOP_RESULT line.",
        )

    current_hash = _state_sha256(repo_root)
    if recorded_hash != current_hash:
        return (
            False,
            "Unacknowledged STATE.md changes detected. "
            "Run `python3 tools/agentctl.py --repo-root . --format json loop-result --line \"LOOP_RESULT: {...}\"` "
            "after completing the current loop.",
        )

    return (True, "LOOP_RESULT acknowledged for current state.")


def _parse_loop_result_payload(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("LOOP_RESULT:"):
        text = text.split(":", 1)[1].strip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("LOOP_RESULT payload must be a JSON object.")
    return payload


def _coerce_confidence(raw: Any) -> float | None:
    if isinstance(raw, (int, float)):
        value = float(raw)
    elif isinstance(raw, str):
        try:
            value = float(raw.strip())
        except ValueError:
            return None
    else:
        return None
    if value < 0.0 or value > 1.0:
        return None
    return value


def _next_role_hint_values(raw: Any) -> set[str]:
    if not isinstance(raw, str):
        return set()
    return {part.strip() for part in raw.split("|") if part.strip()}


def _validate_loop_report_schema(payload: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    loop_name = str(payload.get("loop", "")).strip()
    report = payload.get("report")
    if not isinstance(report, dict):
        return ("Missing or invalid LOOP_RESULT field 'report' (object required).",)

    for field in LOOP_REPORT_REQUIRED_FIELDS:
        if field not in report:
            errors.append(f"LOOP_RESULT report missing required field '{field}'.")

    acceptance_matrix = report.get("acceptance_matrix")
    if not isinstance(acceptance_matrix, list):
        errors.append("LOOP_RESULT report field 'acceptance_matrix' must be a list.")
        acceptance_matrix = []
    elif loop_name in {"implement", "review", "issues_triage"} and not acceptance_matrix:
        errors.append(f"LOOP_RESULT report field 'acceptance_matrix' must not be empty for {loop_name} loops.")

    top_findings = report.get("top_findings")
    if not isinstance(top_findings, list):
        errors.append("LOOP_RESULT report field 'top_findings' must be a list.")
        top_findings = []
    elif len(top_findings) > LOOP_REPORT_MAX_FINDINGS:
        errors.append(
            f"LOOP_RESULT report field 'top_findings' exceeds max length {LOOP_REPORT_MAX_FINDINGS}."
        )

    finding_order: list[int] = []
    for idx, finding in enumerate(top_findings):
        if not isinstance(finding, dict):
            errors.append(f"top_findings[{idx}] must be an object.")
            continue
        impact = str(finding.get("impact", "")).strip().upper()
        title = finding.get("title")
        evidence = finding.get("evidence")
        action = finding.get("action")
        if impact not in IMPACTS:
            errors.append(
                f"top_findings[{idx}].impact must be one of {', '.join(IMPACTS)}."
            )
        else:
            finding_order.append(IMPACT_ORDER.index(impact))
        if not isinstance(title, str) or not title.strip():
            errors.append(f"top_findings[{idx}].title must be a non-empty string.")
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(f"top_findings[{idx}].evidence must be a non-empty string.")
        if not isinstance(action, str) or not action.strip():
            errors.append(f"top_findings[{idx}].action must be a non-empty string.")

    if finding_order and finding_order != sorted(finding_order):
        errors.append("top_findings must be ordered by impact priority (BLOCKER->QUESTION).")

    has_low_confidence_critical = False
    for idx, item in enumerate(acceptance_matrix):
        if not isinstance(item, dict):
            errors.append(f"acceptance_matrix[{idx}] must be an object.")
            continue
        required_fields = ("item", "status", "evidence", "critical", "confidence", "evidence_strength")
        for field in required_fields:
            if field not in item:
                errors.append(f"acceptance_matrix[{idx}] missing '{field}'.")

        item_name = item.get("item")
        status = str(item.get("status", "")).strip().upper()
        evidence = item.get("evidence")
        critical = item.get("critical")
        confidence = _coerce_confidence(item.get("confidence"))
        evidence_strength = str(item.get("evidence_strength", "")).strip().upper()

        if not isinstance(item_name, str) or not item_name.strip():
            errors.append(f"acceptance_matrix[{idx}].item must be a non-empty string.")
        if status not in LOOP_REPORT_ITEM_STATUS:
            errors.append(
                f"acceptance_matrix[{idx}].status must be one of {', '.join(LOOP_REPORT_ITEM_STATUS)}."
            )
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(f"acceptance_matrix[{idx}].evidence must be a non-empty string.")
        if not isinstance(critical, bool):
            errors.append(f"acceptance_matrix[{idx}].critical must be true or false.")
        if confidence is None:
            errors.append(
                f"acceptance_matrix[{idx}].confidence must be a number between 0.0 and 1.0."
            )
        if evidence_strength not in EVIDENCE_STRENGTH_VALUES:
            errors.append(
                f"acceptance_matrix[{idx}].evidence_strength must be one of {', '.join(EVIDENCE_STRENGTH_VALUES)}."
            )

        if (
            isinstance(critical, bool)
            and critical
            and confidence is not None
            and (
                confidence < CONFIDENCE_MIN_REQUIRED
                or evidence_strength == "LOW"
            )
        ):
            has_low_confidence_critical = True

    state_transition = report.get("state_transition")
    if not isinstance(state_transition, dict):
        errors.append("LOOP_RESULT report field 'state_transition' must be an object.")
    else:
        before = state_transition.get("before")
        after = state_transition.get("after")
        if not isinstance(before, dict):
            errors.append("state_transition.before must be an object.")
        if not isinstance(after, dict):
            errors.append("state_transition.after must be an object.")
        if isinstance(after, dict):
            after_stage = _normalize_stage_for_compare(str(after.get("stage", "")).strip() or None)
            after_checkpoint = _normalize_checkpoint_for_compare(str(after.get("checkpoint", "")).strip() or None)
            after_status = str(after.get("status", "")).strip().upper()
            payload_stage = _normalize_stage_for_compare(str(payload.get("stage", "")).strip() or None)
            payload_checkpoint = _normalize_checkpoint_for_compare(str(payload.get("checkpoint", "")).strip() or None)
            payload_status = str(payload.get("status", "")).strip().upper()
            if after_stage != payload_stage:
                errors.append("state_transition.after.stage must match LOOP_RESULT stage.")
            if after_checkpoint != payload_checkpoint:
                errors.append("state_transition.after.checkpoint must match LOOP_RESULT checkpoint.")
            if after_status != payload_status:
                errors.append("state_transition.after.status must match LOOP_RESULT status.")

    report_loop_result = report.get("loop_result")
    if not isinstance(report_loop_result, dict):
        errors.append("LOOP_RESULT report field 'loop_result' must be an object.")
    else:
        for field in LOOP_RESULT_REQUIRED_FIELDS:
            value = report_loop_result.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"report.loop_result.{field} must be a non-empty string.")
                continue
            top_value = payload.get(field)
            if field == "status":
                if str(top_value).strip().upper() != str(value).strip().upper():
                    errors.append(f"report.loop_result.{field} must mirror LOOP_RESULT {field}.")
            else:
                if str(top_value).strip() != str(value).strip():
                    errors.append(f"report.loop_result.{field} must mirror LOOP_RESULT {field}.")

    if loop_name in {"review", "issues_triage"} and has_low_confidence_critical:
        next_hints = _next_role_hint_values(payload.get("next_role_hint"))
        status = str(payload.get("status", "")).strip().upper()
        if status not in {"IN_PROGRESS", "BLOCKED"}:
            errors.append(
                "Low-confidence critical acceptance items require LOOP_RESULT status IN_PROGRESS or BLOCKED."
            )
        if "issues_triage" not in next_hints:
            errors.append(
                "Low-confidence critical acceptance items require next_role_hint to include 'issues_triage'."
            )

    return tuple(errors)


def _validate_loop_result_payload(payload: dict[str, Any], state: StateInfo) -> tuple[str, ...]:
    errors: list[str] = []
    for field in LOOP_RESULT_REQUIRED_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Missing or invalid LOOP_RESULT field '{field}'.")

    loop_name = str(payload.get("loop", "")).strip()
    if loop_name and loop_name not in LOOP_RESULT_LOOPS:
        errors.append(
            f"Invalid LOOP_RESULT loop '{loop_name}'. Allowed: {', '.join(sorted(LOOP_RESULT_LOOPS))}."
        )

    status = str(payload.get("status", "")).strip().upper()
    if status and status not in ALLOWED_STATUS:
        errors.append(
            f"Invalid LOOP_RESULT status '{status}'. Allowed: {', '.join(sorted(ALLOWED_STATUS))}."
        )

    payload_stage = _normalize_stage_for_compare(str(payload.get("stage", "")).strip() or None)
    payload_checkpoint = _normalize_checkpoint_for_compare(str(payload.get("checkpoint", "")).strip() or None)
    state_stage = _normalize_stage_for_compare(state.stage)
    state_checkpoint = _normalize_checkpoint_for_compare(state.checkpoint)
    state_status = (state.status or "").strip().upper() or None

    if payload_stage != state_stage:
        errors.append(
            f"LOOP_RESULT stage '{payload.get('stage')}' does not match STATE stage '{state.stage}'."
        )
    if payload_checkpoint != state_checkpoint:
        errors.append(
            f"LOOP_RESULT checkpoint '{payload.get('checkpoint')}' does not match STATE checkpoint '{state.checkpoint}'."
        )
    if status and status != state_status:
        errors.append(
            f"LOOP_RESULT status '{payload.get('status')}' does not match STATE status '{state.status}'."
        )

    errors.extend(_validate_loop_report_schema(payload))

    return tuple(errors)


def _parse_context_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        header = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if header:
            current = header.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line.rstrip())
    return sections


def _summarize_context_section(lines: list[str]) -> str | None:
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.strip()
        if not line:
            idx += 1
            continue
        if line.startswith(("-", "*")):
            item = line.lstrip("-* ").strip()
            if not item:
                idx += 1
                continue
            continuation: list[str] = []
            j = idx + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() == "":
                    j += 1
                    continue
                if re.match(r"^\s*[-*]\s+", nxt):
                    break
                if nxt.startswith(("  ", "\t")):
                    continuation.append(nxt.strip())
                    j += 1
                    continue
                break
            if continuation:
                item = f"{item} {' '.join(continuation)}".strip()
            return item
        return line
    return None


def _context_summary(repo_root: Path) -> tuple[dict[str, str], dict[str, list[str]] | None]:
    context_path = repo_root / ".vibe" / "CONTEXT.md"
    if not context_path.exists():
        return ({}, None)

    text = _read_text(context_path)
    sections = _parse_context_sections(text)

    summary: dict[str, str] = {}
    trimmed_sections: dict[str, list[str]] = {}
    for section_name, lines in sections.items():
        trimmed = list(lines)
        while trimmed and not trimmed[0].strip():
            trimmed.pop(0)
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        trimmed_sections[section_name] = trimmed
        snippet = _summarize_context_section(trimmed)
        if snippet:
            summary[section_name] = snippet

    return (summary, trimmed_sections)


def _parse_kv_bullets(text: str) -> dict[str, str]:
    """
    Parse simple "- key: value" lines, case-insensitive keys.
    Intentionally dumb and stable.
    """
    kv: dict[str, str] = {}
    pat = re.compile(r"(?im)^\s*-\s*([a-zA-Z_][a-zA-Z0-9_\- ]*)\s*:\s*(.+?)\s*$")
    for m in pat.finditer(text):
        key = m.group(1).strip().lower().replace(" ", "_")
        val = m.group(2).strip()
        if key not in kv:
            kv[key] = val
    return kv


def _clean_status(raw: str | None) -> str | None:
    if not raw:
        return None
    # Allow inline comments like: "IN_PROGRESS  <!-- ... -->"
    token = raw.strip().split()[0]
    return token.upper()


def _parse_issues_legacy(text: str) -> tuple[Issue, ...]:
    """
    Legacy support for lines like:
    - BLOCKER: title
    - **RISK: title**
    """
    issues: list[Issue] = []
    pat = re.compile(
        rf"^\s*-\s*(?:\*\*)?\s*({'|'.join(IMPACTS)}|RISK)\s*:\s*(.+?)(?:\s*\*\*)?\s*$",
        re.IGNORECASE,
    )
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.lstrip().startswith(">"):
            continue
        m = pat.match(line)
        if not m:
            continue
        sev = m.group(1).upper()
        if sev == "RISK":
            sev = "MAJOR"
        title = m.group(2).strip()
        issues.append(Issue(impact=sev, title=title, line=line.rstrip()))
    return tuple(issues)


def _parse_issues(text: str) -> tuple[Issue, ...]:
    checkbox = _parse_issues_checkbox_format(text)
    legacy = _parse_issues_legacy(text)
    # Prefer checkbox issues if present; otherwise fall back to legacy.
    return checkbox if checkbox else legacy


def load_state(repo_root: Path, state_path: Path | None = None) -> StateInfo:
    state_path = state_path or (repo_root / ".vibe" / "STATE.md")
    text = _read_text(state_path)

    kv = _parse_kv_bullets(text)

    stage = kv.get("stage")
    checkpoint = kv.get("checkpoint")

    # Support either "status:" (preferred) or "state:" (legacy)
    status = _clean_status(kv.get("status") or kv.get("state"))

    # Evidence path is optional; accept "- path:" if present anywhere.
    evidence_path = kv.get("path")

    issues = _parse_issues(text)

    return StateInfo(
        stage=stage,
        checkpoint=checkpoint,
        status=status,
        evidence_path=evidence_path,
        issues=issues,
    )


def _plan_has_stage(plan_text: str, stage: str) -> bool:
    # Matches: "## Stage 0 — Name" or "## (SKIP) Stage 0 - Name" or "## Stage 0"
    pat = re.compile(rf"(?im)^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{re.escape(stage)}\b")
    return bool(pat.search(plan_text))


def _extract_checkpoint_section(plan_text: str, checkpoint_id: str) -> str | None:
    """
    Find a checkpoint heading containing checkpoint_id and return its section text.

    Supports headings like:
      ### 0.0 — Foo
      ### 0.0 - Foo
      ### Checkpoint 0.0: Foo   (legacy)
      #### (DONE) 0.0 — Foo     (tolerant)
    """
    head_pat = re.compile(
        r"(?im)^(#{3,6})\s+.*?\b" + re.escape(checkpoint_id) + r"\b.*?$"
    )
    m = head_pat.search(plan_text)
    if not m:
        return None

    level = len(m.group(1))
    start = m.start()

    next_pat = re.compile(r"(?im)^\s*(#{1,6})\s+")
    for nm in next_pat.finditer(plan_text, m.end()):
        next_level = len(nm.group(1))
        if next_level <= level:
            end = nm.start()
            return plan_text[start:end].rstrip()

    return plan_text[start:].rstrip()


def check_plan_for_checkpoint(repo_root: Path, checkpoint_id: str) -> PlanCheck:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    if not plan_path.exists():
        return PlanCheck(
            found_checkpoint=False,
            has_objective=False,
            has_deliverables=False,
            has_acceptance=False,
            has_demo=False,
            has_evidence=False,
            warnings=(f".vibe/PLAN.md not found at {plan_path}.",),
        )

    plan_text = _read_text(plan_path)
    section = _extract_checkpoint_section(plan_text, checkpoint_id)
    if section is None:
        return PlanCheck(
            found_checkpoint=False,
            has_objective=False,
            has_deliverables=False,
            has_acceptance=False,
            has_demo=False,
            has_evidence=False,
            warnings=(f"Checkpoint {checkpoint_id} not found in .vibe/PLAN.md headings.",),
        )

    def has_heading(name: str) -> bool:
        # Matches various heading styles:
        # - "- Objective:" or "* Objective:" (bullet with colon)
        # - "- **Objective:**" or "* **Objective:**" (bold bullet with colon inside)
        # - "**Objective**" or "**Objective:**" (bold header)
        # - "Objective:" (plain header)
        return bool(
            re.search(
                rf"(?im)^\s*(?:[-*]+\s*)?(?:\*\*)?\s*{re.escape(name)}\s*:?\s*(?:\*\*)?\s*:?\s*$",
                section,
            )
        )

    has_objective = has_heading("Objective")
    has_deliverables = has_heading("Deliverables")
    has_acceptance = has_heading("Acceptance")
    has_evidence = has_heading("Evidence")

    # Demo commands: accept either explicit heading or code-ish lines
    has_demo_heading = bool(re.search(r"(?im)^\s*(?:[-*]+\s*)?Demo commands\b", section))
    has_commandish = bool(re.search(r"(?im)^\s*[-*]\s*`.+`", section)) or ("```" in section)
    has_demo = has_demo_heading and has_commandish or has_commandish

    warnings: list[str] = []
    if not has_objective:
        warnings.append("Checkpoint section missing 'Objective'.")
    if not has_deliverables:
        warnings.append("Checkpoint section missing 'Deliverables'.")
    if not has_acceptance:
        warnings.append("Checkpoint section missing 'Acceptance'.")
    if not has_demo:
        warnings.append("Checkpoint section missing recognizable demo commands.")
    if not has_evidence:
        warnings.append("Checkpoint section missing 'Evidence'.")

    return PlanCheck(
        found_checkpoint=True,
        has_objective=has_objective,
        has_deliverables=has_deliverables,
        has_acceptance=has_acceptance,
        has_demo=has_demo,
        has_evidence=has_evidence,
        warnings=tuple(warnings),
    )


def validate(repo_root: Path, strict: bool) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    state_path = repo_root / ".vibe" / "STATE.md"
    if not state_path.exists():
        return ValidationResult(
            ok=False,
            errors=(f".vibe/STATE.md not found at {state_path}.",),
            warnings=(),
            state=None,
            plan_check=None,
        )

    state = load_state(repo_root)

    if not state.stage:
        errors.append(".vibe/STATE.md: missing '- Stage: <id>' under Current focus.")
    if not state.checkpoint:
        errors.append(".vibe/STATE.md: missing '- Checkpoint: <id>' under Current focus.")
    if not state.status:
        errors.append(
            ".vibe/STATE.md: missing '- Status: NOT_STARTED|IN_PROGRESS|IN_REVIEW|BLOCKED|DONE'."
        )
    elif state.status not in ALLOWED_STATUS:
        allowed = ", ".join(sorted(ALLOWED_STATUS))
        errors.append(f".vibe/STATE.md: invalid status '{state.status}'. Allowed: {allowed}")

    issue_schema_messages = _validate_issue_schema(state.issues)
    for message in issue_schema_messages:
        (errors if strict else warnings).append(f".vibe/STATE.md: {message}")

    # Evidence path is optional; warn if missing
    if not state.evidence_path:
        warnings.append(".vibe/STATE.md: missing evidence '- path: ...' (optional).")
    else:
        resolved = _resolve_path(repo_root, state.evidence_path)
        if state.status in {"IN_REVIEW", "DONE"} and not resolved.exists():
            msg = f"Evidence file not found at {resolved}."
            (errors if strict else warnings).append(msg)

    plan_check: PlanCheck | None = None
    if state.checkpoint:
        plan_path = repo_root / ".vibe" / "PLAN.md"
        plan_text = _read_text(plan_path) if plan_path.exists() else ""
        if plan_text:
            stage_headings = _parse_stage_headings(plan_text)
            seen_stages: dict[str, int] = {}
            for stage_raw, line_no, line_text in stage_headings:
                if not is_valid_stage_id(stage_raw):
                    errors.append(
                        f".vibe/PLAN.md:{line_no}: invalid stage id '{stage_raw}'. "
                        f"Expected <int><optional alpha suffix>. Line: {line_text}"
                    )
                    continue
                stage_norm = normalize_stage_id(stage_raw)
                if stage_norm in seen_stages:
                    prev_line = seen_stages[stage_norm]
                    errors.append(
                        f".vibe/PLAN.md:{line_no}: duplicate stage id '{stage_norm}' "
                        f"(previously at line {prev_line})."
                    )
                else:
                    seen_stages[stage_norm] = line_no

            if state.stage and not _plan_has_stage(plan_text, state.stage):
                errors.append(
                    f".vibe/PLAN.md: missing stage section for Stage {state.stage}."
                )

        # Check for stage drift: STATE.md stage doesn't match checkpoint's actual stage in PLAN.md
        if plan_text and state.stage:
            actual_stage = _get_stage_for_checkpoint(plan_text, state.checkpoint)
            state_stage = state.stage
            if state_stage and is_valid_stage_id(state_stage):
                state_stage = normalize_stage_id(state_stage)
            if actual_stage and state_stage and actual_stage != state_stage:
                msg = (
                    f"Stage drift detected: STATE.md says Stage {state.stage}, "
                    f"but checkpoint {state.checkpoint} is in Stage {actual_stage} in PLAN.md."
                )
                errors.append(msg)

        plan_check = check_plan_for_checkpoint(repo_root, state.checkpoint)
        if not plan_check.found_checkpoint:
            msg = (
                plan_check.warnings[0]
                if plan_check.warnings
                else ".vibe/PLAN.md checkpoint not found."
            )
            (errors if strict else warnings).append(msg)
        else:
            for w in plan_check.warnings:
                (errors if strict else warnings).append(f".vibe/PLAN.md: {w}")

    catalog_index, catalog_path, catalog_error = _load_prompt_catalog_index(repo_root)
    if catalog_error:
        warnings.append(catalog_error)
    else:
        catalog_ids = set(catalog_index.keys())

        for role, metadata in PROMPT_MAP.items():
            prompt_id = metadata["id"]
            if prompt_id == "stop":
                continue
            if prompt_id not in catalog_ids:
                (errors if strict else warnings).append(
                    f"Prompt map for role '{role}' references missing prompt id '{prompt_id}'."
                )

        workflow_refs, workflow_warnings = _collect_workflow_prompt_refs(repo_root)
        for message in workflow_warnings:
            (errors if strict else warnings).append(message)

        for workflow_name, prompt_id in workflow_refs:
            if prompt_id != "stop" and prompt_id not in catalog_ids:
                (errors if strict else warnings).append(
                    f"{workflow_name}: unknown prompt id '{prompt_id}' (not present in template_prompts.md)."
                )
            mapped_role = _role_for_prompt_id(prompt_id)
            if mapped_role is None:
                (errors if strict else warnings).append(
                    f"{workflow_name}: prompt id '{prompt_id}' has no role mapping in PROMPT_ROLE_MAP."
                )

        if catalog_path and not (repo_root / "prompts" / "template_prompts.md").exists():
            warnings.append(
                f"Using non-local prompt catalog at {catalog_path}; "
                "repo-local prompts/template_prompts.md is recommended."
            )

    ok = len(errors) == 0
    return ValidationResult(
        ok=ok,
        errors=tuple(errors),
        warnings=tuple(warnings),
        state=state,
        plan_check=plan_check,
    )


@dataclass(frozen=True)
class Gate:
    name: str
    command: str
    gate_type: str
    required: bool = False
    pass_criteria: dict[str, Any] | None = None


@dataclass(frozen=True)
class GateResult:
    gate: Gate
    passed: bool
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class GateConfig:
    gates: list[Gate]


def load_gate_config(repo_root: Path, checkpoint_id: str | None) -> GateConfig:
    config_path = repo_root / ".vibe" / "config.json"
    if not config_path.exists():
        return GateConfig(gates=[])

    try:
        config_data = json.loads(_read_text(config_path))
        gate_data = config_data.get("quality_gates", {})
    except (json.JSONDecodeError, IOError):
        return GateConfig(gates=[])

    all_gates: list[Gate] = []
    
    # Global gates
    for g in gate_data.get("global", []):
        all_gates.append(
            Gate(
                name=g.get("name", "Unnamed Gate"),
                command=g.get("command", ""),
                gate_type=g.get("type", "custom"),
                required=g.get("required", False),
                pass_criteria=g.get("pass_criteria"),
            )
        )

    # Checkpoint-specific gates
    if checkpoint_id and "checkpoints" in gate_data and checkpoint_id in gate_data["checkpoints"]:
        for g in gate_data["checkpoints"][checkpoint_id]:
            all_gates.append(
                Gate(
                    name=g.get("name", "Unnamed Gate"),
                    command=g.get("command", ""),
                    gate_type=g.get("type", "custom"),
                    required=g.get("required", False),
                    pass_criteria=g.get("pass_criteria"),
                )
            )

    return GateConfig(gates=all_gates)


def run_gates(repo_root: Path, checkpoint_id: str | None) -> list[GateResult]:
    gate_config = load_gate_config(repo_root, checkpoint_id)
    if not gate_config.gates:
        return []

    results: list[GateResult] = []
    for gate in gate_config.gates:
        if not gate.command:
            results.append(GateResult(gate=gate, passed=False, stdout="", stderr="Gate command is empty.", exit_code=-1))
            continue

        try:
            # Using shell=True for simplicity, but be aware of security implications
            # In a real-world scenario, you might want to parse the command and args
            process = subprocess.run(
                gate.command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=repo_root,
                timeout=300,  # 5-minute timeout
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            exit_code = process.returncode

            passed = True
            if gate.pass_criteria:
                if "exit_code" in gate.pass_criteria and exit_code != gate.pass_criteria["exit_code"]:
                    passed = False
                if passed and "stdout_contains" in gate.pass_criteria and gate.pass_criteria["stdout_contains"] not in stdout:
                    passed = False
                if passed and "stderr_contains" in gate.pass_criteria and gate.pass_criteria["stderr_contains"] not in stderr:
                    passed = False
            elif exit_code != 0:
                passed = False

            results.append(GateResult(gate=gate, passed=passed, stdout=stdout, stderr=stderr, exit_code=exit_code))

        except subprocess.TimeoutExpired as e:
            results.append(GateResult(gate=gate, passed=False, stdout="", stderr=f"Timeout: {e}", exit_code=-1))
        except Exception as e:
            results.append(GateResult(gate=gate, passed=False, stdout="", stderr=f"Execution failed: {e}", exit_code=-1))

    return results


def _top_issue_impact(issues: tuple[Issue, ...]) -> str | None:
    if not issues:
        return None
    # choose highest impact by IMPACT_ORDER
    order = {sev: idx for idx, sev in enumerate(IMPACT_ORDER)}
    best = min(issues, key=lambda i: order.get(i.impact, 999))
    return best.impact


def _get_section_lines(sections: dict[str, list[str]], section_name: str) -> list[str]:
    target = section_name.strip().lower()
    for key, lines in sections.items():
        if key.strip().lower() == target:
            return lines
    return []


def _normalize_flag_name(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", raw.strip()).strip("_").upper()


def _parse_workflow_flags(state_text: str) -> dict[str, bool]:
    sections = _parse_context_sections(state_text)
    lines = _get_section_lines(sections, "Workflow state")
    flags: dict[str, bool] = {}

    checkbox_pat = re.compile(r"^\s*-\s*\[\s*([xX ])\s*\]\s*(.+?)\s*$")
    bullet_pat = re.compile(r"^\s*-\s+(.+?)\s*$")

    for raw in lines:
        m = checkbox_pat.match(raw)
        if m:
            flag = _normalize_flag_name(m.group(2))
            if flag:
                flags[flag] = m.group(1).strip().lower() == "x"
            continue
        b = bullet_pat.match(raw)
        if b:
            value = b.group(1).strip()
            if value.lower() in {"none", "none.", "(none)", "(none yet)"}:
                continue
            flag = _normalize_flag_name(value)
            if flag:
                flags[flag] = True

    return flags


def _load_workflow_flags(repo_root: Path) -> dict[str, bool]:
    state_path = repo_root / ".vibe" / "STATE.md"
    if not state_path.exists():
        return {}
    return _parse_workflow_flags(_read_text(state_path))


def _context_capture_trigger_reason(repo_root: Path, workflow_flags: dict[str, bool]) -> str | None:
    if workflow_flags.get("RUN_CONTEXT_CAPTURE"):
        return "Workflow flag RUN_CONTEXT_CAPTURE is set."

    context_path = repo_root / ".vibe" / "CONTEXT.md"
    state_path = repo_root / ".vibe" / "STATE.md"
    plan_path = repo_root / ".vibe" / "PLAN.md"
    history_path = repo_root / ".vibe" / "HISTORY.md"

    if not context_path.exists():
        return "Context snapshot missing (.vibe/CONTEXT.md)."

    context_mtime = context_path.stat().st_mtime
    sources = [p for p in (state_path, plan_path, history_path) if p.exists()]
    if not sources:
        return None

    latest_source_mtime = max(p.stat().st_mtime for p in sources)
    if latest_source_mtime - context_mtime > 24 * 3600:
        return "Context snapshot is stale (>24h older than workflow docs)."

    return None


def _count_nonempty_signal_lines(lines: list[str]) -> int:
    count = 0
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("<!--"):
            continue
        if line.lower() in {"none", "none.", "(none)", "(none yet)", "(none yet)."}:
            continue
        count += 1
    return count


def _process_improvements_trigger_reason(repo_root: Path, workflow_flags: dict[str, bool]) -> str | None:
    if workflow_flags.get("RUN_PROCESS_IMPROVEMENTS"):
        return "Workflow flag RUN_PROCESS_IMPROVEMENTS is set."

    state_path = repo_root / ".vibe" / "STATE.md"
    if not state_path.exists():
        return None

    sections = _parse_context_sections(_read_text(state_path))
    work_log_lines = _get_section_lines(sections, "Work log (current session)")
    evidence_lines = _get_section_lines(sections, "Evidence")

    work_log_entries = sum(1 for line in work_log_lines if re.match(r"^\s*-\s+", line))
    if work_log_entries > 15:
        return f"Work log has {work_log_entries} entries (>15)."

    evidence_signal_lines = _count_nonempty_signal_lines(evidence_lines)
    if evidence_signal_lines > 50:
        return f"Evidence section has {evidence_signal_lines} non-empty lines (>50)."

    return None


def _recommend_next(state: StateInfo, repo_root: Path) -> tuple[Role, str]:
    workflow_flags = _load_workflow_flags(repo_root)

    # 0) Hard stop / hard triage conditions
    if state.status == "BLOCKED":
        return ("issues_triage", "Checkpoint status is BLOCKED.")

    top = _top_issue_impact(state.issues)
    if top == "BLOCKER":
        return ("issues_triage", "BLOCKER issue present.")

    # 1) Review always happens if IN_REVIEW
    if state.status == "IN_REVIEW":
        return ("review", "Checkpoint status is IN_REVIEW.")

    # 2) If DONE, either advance to next checkpoint or stop if plan exhausted
    if state.status == "DONE":
        plan_path = repo_root / ".vibe" / "PLAN.md"
        plan_text = _read_text(plan_path) if plan_path.exists() else ""
        plan_ids = _parse_plan_checkpoint_ids(plan_text)

        if not plan_ids:
            return ("stop", "No checkpoints found in .vibe/PLAN.md (plan exhausted).")

        if not state.checkpoint:
            return ("advance", "Status DONE but no checkpoint set; advance to first checkpoint in plan.")

        nxt = _next_checkpoint_after(plan_ids, state.checkpoint)
        if not nxt:
            return ("stop", "Current checkpoint is last checkpoint in .vibe/PLAN.md (plan exhausted).")

        # If the next one is explicitly marked (DONE) or (SKIP), skip forward
        while nxt and (
            _is_checkpoint_marked_done(plan_text, nxt)
            or _is_checkpoint_skipped(plan_text, nxt)
        ):
            state_ck = nxt
            nxt = _next_checkpoint_after(plan_ids, state_ck)

        if not nxt:
            return ("stop", "All remaining checkpoints are marked (DONE) or (SKIP) in .vibe/PLAN.md (plan exhausted).")

        # Check for stage transition - recommend consolidation before advancing to new stage
        is_stage_change, cur_stage, nxt_stage = _detect_stage_transition(
            plan_text, state.checkpoint, nxt
        )
        if is_stage_change:
            # Check if STATE.md stage matches the plan's current stage
            if state.stage != nxt_stage:
                return (
                    "consolidation",
                    f"Stage transition detected: {cur_stage} → {nxt_stage}. "
                    f"Run consolidation to archive Stage {cur_stage} and update stage pointer before advancing.",
                )

        return ("advance", f"Checkpoint is DONE; next checkpoint is {nxt}.")

    # 3) Normal execution states
    if state.status in {"NOT_STARTED", "IN_PROGRESS"}:
        # If there are non-blocking issues, triage can be recommended (your choice)
        if top in {"MAJOR", "QUESTION"}:
            return ("issues_triage", f"Active issues present (top impact: {top}).")

        # Context capture is a first-class maintenance loop.
        if state.status == "NOT_STARTED":
            context_reason = _context_capture_trigger_reason(repo_root, workflow_flags)
            if context_reason:
                return ("context_capture", context_reason)

            process_reason = _process_improvements_trigger_reason(repo_root, workflow_flags)
            if process_reason:
                return ("improvements", process_reason)

        return ("implement", f"Checkpoint status is {state.status}.")

    # 4) Default
    return ("design", "No recognized status; stage design likely required.")


def _render_output(payload: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    lines: list[str] = []
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            lines.append(f"{k}: {json.dumps(v)}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


PROMPT_MAP: dict[Role, dict[str, str]] = {
    "issues_triage": {
        "id": "prompt.issues_triage",
        "title": "Issues Triage Prompt",
    },
    "review": {
        "id": "prompt.checkpoint_review",
        "title": "Checkpoint Review Prompt",
    },
    "implement": {
        "id": "prompt.checkpoint_implementation",
        "title": "Checkpoint Implementation Prompt",
    },
    "design": {
        "id": "prompt.stage_design",
        "title": "Stage Design Prompt",
    },
    "context_capture": {
        "id": "prompt.context_capture",
        "title": "Context Capture Prompt",
    },
    "consolidation": {
        "id": "prompt.consolidation",
        "title": "Consolidation Prompt (docs sync + archival)",
    },
    "improvements": {
        "id": "prompt.process_improvements",
        "title": "Process Improvements Prompt (system uplift)",
    },
    "advance": {
        "id": "prompt.advance_checkpoint",
        "title": "Advance Checkpoint Prompt",
    },
    "stop": {
        "id": "stop",
        "title": "Stop (no remaining checkpoints)",
    },
}

# Non-dispatcher prompts can still be selected by configured workflows.
# Map them onto an existing role to keep status transitions coherent.
EXTRA_WORKFLOW_PROMPT_ROLES: dict[str, Role] = {
    "prompt.ideation": "design",
    "prompt.feature_breakdown": "design",
    "prompt.architecture": "design",
    "prompt.milestones": "design",
    "prompt.stages_from_milestones": "design",
    "prompt.checkpoints_from_stage": "design",
    "prompt.refactor_scan": "implement",
    "prompt.refactor_execute": "implement",
    "prompt.refactor_verify": "review",
    "prompt.test_gap_analysis": "design",
    "prompt.test_generation": "implement",
    "prompt.test_review": "review",
    "prompt.demo_script": "design",
    "prompt.feedback_intake": "issues_triage",
    "prompt.feedback_triage": "issues_triage",
}

PROMPT_ROLE_MAP: dict[str, Role] = {meta["id"]: role for role, meta in PROMPT_MAP.items()}
PROMPT_ROLE_MAP.update(EXTRA_WORKFLOW_PROMPT_ROLES)


def _role_for_prompt_id(prompt_id: str) -> Role | None:
    return PROMPT_ROLE_MAP.get(prompt_id)


def _extract_refactor_idea_tags(value: Any) -> set[str]:
    if not isinstance(value, str) or not value:
        return set()
    return {match.group(1).upper() for match in REFACTOR_IDEA_TAG_RE.finditer(value)}


def _continuous_refactor_should_stop(repo_root: Path) -> tuple[bool, str | None]:
    payload, error = _load_loop_result_record(repo_root)
    if error or payload is None:
        return (False, None)

    report = payload.get("report")
    if not isinstance(report, dict):
        return (False, None)

    top_findings = report.get("top_findings")
    if not isinstance(top_findings, list) or not top_findings:
        return (False, None)

    observed_tags: set[str] = set()
    for finding in top_findings:
        if not isinstance(finding, dict):
            continue
        for key in ("title", "evidence", "action"):
            observed_tags.update(_extract_refactor_idea_tags(finding.get(key)))

    if not observed_tags:
        return (False, None)

    if observed_tags.intersection({"MAJOR", "MODERATE"}):
        return (False, None)

    if not observed_tags.issubset({"MINOR"}):
        return (False, None)

    return (
        True,
        "Workflow continuous-refactor found only [MINOR] refactor ideas in the latest LOOP_RESULT report; stopping.",
    )


def _load_workflow_selector(repo_root: Path):
    try:
        from workflow_engine import select_next_prompt
        return select_next_prompt
    except Exception:
        repo_tools_dir = (repo_root / "tools").resolve()
        if repo_tools_dir.exists() and str(repo_tools_dir) not in sys.path:
            sys.path.insert(0, str(repo_tools_dir))
        try:
            from workflow_engine import select_next_prompt
            return select_next_prompt
        except Exception as exc:
            raise RuntimeError(f"Failed to load workflow engine: {exc}") from exc


def _resolve_next_prompt_selection(
    state: StateInfo,
    repo_root: Path,
    workflow: str | None,
) -> tuple[Role, str, str, str]:
    base_role, base_reason = _recommend_next(state, repo_root)
    base_prompt_id = PROMPT_MAP[base_role]["id"]
    base_prompt_title = PROMPT_MAP[base_role]["title"]

    if not workflow or base_role == "stop":
        return (base_role, base_prompt_id, base_prompt_title, base_reason)

    if workflow == "continuous-refactor" and base_role == "implement":
        should_stop, stop_reason = _continuous_refactor_should_stop(repo_root)
        if should_stop:
            return (
                "stop",
                "stop",
                "Stop (continuous-refactor threshold reached)",
                stop_reason or "Workflow continuous-refactor threshold reached.",
            )

    catalog_index, _, catalog_error = _load_prompt_catalog_index(repo_root)
    if catalog_error:
        raise RuntimeError(catalog_error)

    select_next_prompt = _load_workflow_selector(repo_root)

    allowed_prompt_ids = {
        prompt_id
        for prompt_id, mapped_role in PROMPT_ROLE_MAP.items()
        if mapped_role == base_role
    }

    def _select_workflow_prompt(allowed: set[str] | None) -> str | None:
        try:
            return select_next_prompt(workflow, allowed_prompt_ids=allowed)
        except TypeError:
            # Backward-compatible fallback for older workflow_engine versions.
            candidate = select_next_prompt(workflow)
            if allowed is None or candidate is None:
                return candidate
            return candidate if candidate in allowed else None

    current_cwd = Path.cwd()
    try:
        os.chdir(repo_root)
        workflow_prompt_id = _select_workflow_prompt(allowed_prompt_ids)
        raw_workflow_prompt_id = _select_workflow_prompt(None)
    finally:
        os.chdir(current_cwd)
    if not workflow_prompt_id:
        if raw_workflow_prompt_id:
            raw_role = _role_for_prompt_id(raw_workflow_prompt_id)
            if raw_role is None:
                raise RuntimeError(
                    f"Workflow {workflow} selected unmapped prompt id '{raw_workflow_prompt_id}'. "
                    "Add it to PROMPT_ROLE_MAP."
                )
            if raw_workflow_prompt_id != "stop" and raw_workflow_prompt_id not in catalog_index:
                raise RuntimeError(
                    f"Workflow {workflow} selected unknown prompt id '{raw_workflow_prompt_id}' "
                    "(not found in template_prompts.md)."
                )
            return (
                base_role,
                base_prompt_id,
                base_prompt_title,
                f"{base_reason} Workflow {workflow} suggested {raw_workflow_prompt_id} "
                f"({raw_role}); using dispatcher role {base_role}.",
            )
        return (
            base_role,
            base_prompt_id,
            base_prompt_title,
            f"{base_reason} Workflow {workflow} had no matching step; using dispatcher role {base_role}.",
        )

    workflow_role = _role_for_prompt_id(workflow_prompt_id)
    if workflow_role is None:
        raise RuntimeError(
            f"Workflow {workflow} selected unmapped prompt id '{workflow_prompt_id}'. "
            "Add it to PROMPT_ROLE_MAP."
        )

    if workflow_prompt_id != "stop" and workflow_prompt_id not in catalog_index:
        raise RuntimeError(
            f"Workflow {workflow} selected unknown prompt id '{workflow_prompt_id}' "
            "(not found in template_prompts.md)."
        )

    if workflow_role != base_role:
        return (
            base_role,
            base_prompt_id,
            base_prompt_title,
            f"{base_reason} Workflow {workflow} produced mismatched role {workflow_role}; "
            f"using dispatcher role {base_role}.",
        )

    workflow_title = catalog_index.get(workflow_prompt_id, base_prompt_title)
    return (
        workflow_role,
        workflow_prompt_id,
        workflow_title,
        f"{base_reason} Workflow {workflow} selected {workflow_prompt_id}.",
    )


def cmd_validate(args: argparse.Namespace) -> int:
    res = validate(Path(args.repo_root), strict=args.strict)

    payload: dict[str, Any] = {
        "ok": res.ok,
        "errors": list(res.errors),
        "warnings": list(res.warnings),
    }
    if res.state:
        payload["state"] = {
            "stage": res.state.stage,
            "checkpoint": res.state.checkpoint,
            "status": res.state.status,
            "evidence_path": res.state.evidence_path,
            "issues": [
                {
                    "id": i.issue_id,
                    "impact": i.impact,
                    "status": i.status,
                    "owner": i.owner,
                    "title": i.title,
                }
                for i in res.state.issues
            ],
        }
    if res.plan_check:
        payload["plan_check"] = {
            "found_checkpoint": res.plan_check.found_checkpoint,
            "has_objective": res.plan_check.has_objective,
            "has_deliverables": res.plan_check.has_deliverables,
            "has_acceptance": res.plan_check.has_acceptance,
            "has_demo": res.plan_check.has_demo,
            "has_evidence": res.plan_check.has_evidence,
        }

    print(_render_output(payload, args.format))
    return 0 if res.ok else 2


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)

    role, reason = _recommend_next(state, repo_root)
    summary, sections = _context_summary(repo_root)
    prompt_catalog_path = _resolve_prompt_catalog_path(repo_root)

    payload: dict[str, Any] = {
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
        "evidence_path": state.evidence_path,
        "issues_count": len(state.issues),
        "issues_top_impact": _top_issue_impact(state.issues),
        "blockers": [i.title for i in state.issues if i.impact == "BLOCKER"],
        "majors": [i.title for i in state.issues if i.impact == "MAJOR"],
        "questions": [i.title for i in state.issues if i.impact == "QUESTION"],
        "recommended_next_role": role,
        "recommended_next_reason": reason,
        "recommended_prompt_id": PROMPT_MAP[role]["id"],
        "recommended_prompt_title": PROMPT_MAP[role]["title"],
        "context_summary": summary,
        "prompt_catalog_path": str(prompt_catalog_path) if prompt_catalog_path else None,
    }
    if args.with_context and sections is not None:
        payload["context_sections"] = sections
    print(_render_output(payload, args.format))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)
    prompt_catalog_path = _resolve_prompt_catalog_path(repo_root)

    _bootstrap_loop_result_record(repo_root, state)
    loop_ok, loop_reason = _loop_result_ack_status(repo_root)
    if not loop_ok:
        payload = {
            "recommended_role": "stop",
            "recommended_prompt_id": "stop",
            "recommended_prompt_title": "Stop (pending LOOP_RESULT acknowledgement)",
            "reason": loop_reason,
            "stage": state.stage,
            "checkpoint": state.checkpoint,
            "status": state.status,
            "prompt_catalog_path": str(prompt_catalog_path) if prompt_catalog_path else None,
            "workflow": args.workflow,
            "requires_loop_result": True,
        }
        print(_render_output(payload, args.format))
        return 0

    if args.run_gates and state.status in {"NOT_STARTED", "IN_PROGRESS"}:
        gate_results = run_gates(repo_root, state.checkpoint)
        failed_required_gates = [r for r in gate_results if not r.passed and r.gate.required]

        if failed_required_gates:
            payload: dict[str, Any] = {
                "recommended_role": "implement",
                "recommended_prompt_id": PROMPT_MAP["implement"]["id"],
                "recommended_prompt_title": PROMPT_MAP["implement"]["title"],
                "reason": "Required quality gates failed.",
                "stage": state.stage,
                "checkpoint": state.checkpoint,
                "status": state.status,
                "prompt_catalog_path": str(prompt_catalog_path) if prompt_catalog_path else None,
                "gate_results": [
                    {
                        "name": r.gate.name,
                        "passed": r.passed,
                        "stdout": r.stdout,
                        "stderr": r.stderr,
                        "exit_code": r.exit_code,
                    }
                    for r in gate_results
                ],
            }
            print(_render_output(payload, args.format))
            return 1

    try:
        role, prompt_id, prompt_title, reason = _resolve_next_prompt_selection(
            state,
            repo_root,
            args.workflow,
        )
    except RuntimeError as exc:
        payload = {
            "recommended_role": "stop",
            "recommended_prompt_id": "stop",
            "recommended_prompt_title": "Stop (workflow unavailable)",
            "reason": str(exc),
            "workflow": args.workflow,
            "stage": state.stage,
            "checkpoint": state.checkpoint,
            "status": state.status,
            "prompt_catalog_path": str(prompt_catalog_path) if prompt_catalog_path else None,
        }
        print(_render_output(payload, args.format))
        return 2

    payload: dict[str, Any] = {
        "recommended_role": role,
        "recommended_prompt_id": prompt_id,
        "recommended_prompt_title": prompt_title,
        "reason": reason,
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
        "prompt_catalog_path": str(prompt_catalog_path) if prompt_catalog_path else None,
    }
    if args.workflow:
        payload["workflow"] = args.workflow
    
    if args.run_gates and state.status in {"NOT_STARTED", "IN_PROGRESS"}:
        gate_results = run_gates(repo_root, state.checkpoint)
        payload["gate_results"] = [
            {
                "name": r.gate.name,
                "passed": r.passed,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "exit_code": r.exit_code,
            }
            for r in gate_results
        ]


    print(_render_output(payload, args.format))
    return 0


def cmd_loop_result(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)
    raw_payload = ""
    sources = 0

    if args.line:
        raw_payload = args.line
        sources += 1
    if args.json_payload:
        raw_payload = args.json_payload
        sources += 1
    if args.stdin:
        raw_payload = sys.stdin.read()
        sources += 1

    if sources != 1:
        print(
            "Provide exactly one LOOP_RESULT source via --line, --json-payload, or --stdin.",
            file=sys.stderr,
        )
        return 2

    try:
        payload = _parse_loop_result_payload(raw_payload)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid LOOP_RESULT payload: {exc}", file=sys.stderr)
        return 2

    validation_errors = _validate_loop_result_payload(payload, state)
    if validation_errors:
        report = {"ok": False, "errors": list(validation_errors)}
        print(_render_output(report, args.format))
        return 2

    normalized = {
        "loop": str(payload["loop"]).strip(),
        "result": str(payload["result"]).strip(),
        "stage": str(payload["stage"]).strip(),
        "checkpoint": str(payload["checkpoint"]).strip(),
        "status": str(payload["status"]).strip().upper(),
        "next_role_hint": str(payload["next_role_hint"]).strip(),
        "report": payload.get("report"),
    }
    normalized["protocol_version"] = LOOP_RESULT_PROTOCOL_VERSION
    normalized["recorded_at"] = datetime.now(timezone.utc).isoformat()
    normalized["state_sha256"] = _state_sha256(repo_root)

    path = _loop_result_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = {"ok": True, "loop_result_path": str(path), "recorded": normalized}
    print(_render_output(output, args.format))
    return 0


def _parse_cli_params(raw: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    idx = 0
    while idx < len(raw):
        token = raw[idx]
        if not token.startswith("--"):
            idx += 1
            continue
        key = token[2:]
        if not key:
            idx += 1
            continue
        if idx + 1 >= len(raw):
            raise ValueError(f"Missing value for --{key}")
        params[key] = raw[idx + 1]
        idx += 2
    return params


def _extract_add_checkpoint_params(raw_args: list[str]) -> list[str]:
    if not raw_args:
        return []
    try:
        idx = raw_args.index("add-checkpoint")
    except ValueError:
        return []

    params: list[str] = []
    skip_next = False
    it = iter(enumerate(raw_args[idx + 1 :], start=idx + 1))
    for _, token in it:
        if skip_next:
            skip_next = False
            continue
        if token == "--template":
            skip_next = True
            continue
        if token.startswith("--template="):
            continue
        params.append(token)
    return params


def cmd_add_checkpoint(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)
    if not state.stage:
        print("STATE.md is missing a Stage; cannot add checkpoint.")
        return 2

    template_path = Path("templates") / "checkpoints" / f"{args.template}.yaml"
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        return 2

    try:
        template = checkpoint_templates._load_yaml(template_path)
        params = _parse_cli_params(args.params)
        values = checkpoint_templates._build_values(template, params)
        lines = checkpoint_templates._render_checkpoint_lines(template, values)
    except Exception as exc:
        print(f"Failed to render template: {exc}")
        return 2

    plan_path = repo_root / ".vibe" / "PLAN.md"
    if not plan_path.exists():
        print(f"PLAN.md not found at {plan_path}")
        return 2
    plan_text = _read_text(plan_path)

    stage = state.stage
    start, end = _find_stage_bounds(plan_text, stage)
    if start is None or end is None:
        stage_block = f"\n## Stage {stage}\n\n**Stage objective:**\nTBD\n\n"
        plan_text = plan_text.rstrip() + stage_block
        start, end = _find_stage_bounds(plan_text, stage)
        if start is None or end is None:
            print(f"Unable to create stage {stage} in PLAN.md.")
            return 2

    new_id = _next_checkpoint_id_for_stage(plan_text, stage)
    title = lines[0].lstrip("# ").strip()
    lines[0] = f"### {new_id} — {title}"

    block = "\n".join(lines).rstrip() + "\n\n---\n"
    insert_at = end
    updated = plan_text[:insert_at].rstrip() + "\n\n" + block + plan_text[insert_at:]
    plan_path.write_text(updated, encoding="utf-8")

    plan_check = check_plan_for_checkpoint(repo_root, new_id)
    if not plan_check.found_checkpoint or plan_check.warnings:
        print(f"Inserted checkpoint {new_id} failed schema checks.")
        return 2

    print(f"Inserted checkpoint {new_id} from template {args.template}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentctl", description="Control-plane helper for vibecoding loops.")
    p.add_argument("--repo-root", default=".", help="Path to repository root (default: .)")
    p.add_argument("--format", choices=("text", "json"), default="text", help="Output format (text|json).")

    sub = p.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("validate", help="Validate .vibe/STATE.md and .vibe/PLAN.md invariants (CI-friendly).")
    pv.add_argument(
        "--strict",
        action="store_true",
        help="Treat PLAN checkpoint template warnings as errors (recommended for CI).",
    )
    pv.set_defaults(fn=cmd_validate)

    ps = sub.add_parser("status", help="Print current state summary.")
    ps.add_argument(
        "--with-context",
        action="store_true",
        help="Include full CONTEXT.md sections when available.",
    )
    ps.set_defaults(fn=cmd_status)

    pn = sub.add_parser("next", help="Recommend the next loop/prompt to run.")
    pn.add_argument(
        "--run-gates",
        action="store_true",
        help="Run quality gates before recommending next action.",
    )
    pn.add_argument(
        "--workflow",
        help="Use configured workflow to select the next prompt.",
    )
    pn.set_defaults(fn=cmd_next)

    plr = sub.add_parser("loop-result", help="Record and validate LOOP_RESULT output against current STATE.md.")
    src = plr.add_mutually_exclusive_group(required=True)
    src.add_argument("--line", help='Raw LOOP_RESULT line (for example: LOOP_RESULT: {"loop":"implement",...}).')
    src.add_argument("--json-payload", help="Raw LOOP_RESULT JSON object string.")
    src.add_argument("--stdin", action="store_true", help="Read LOOP_RESULT payload from stdin.")
    plr.set_defaults(fn=cmd_loop_result)

    pc = sub.add_parser("add-checkpoint", help="Insert a checkpoint from a template into PLAN.md.")
    pc.add_argument("--template", required=True, help="Template name (file stem).")
    pc.add_argument("params", nargs=argparse.REMAINDER, help="Template parameters.")
    pc.set_defaults(fn=cmd_add_checkpoint)

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    raw_args = list(argv) if argv is not None else list(sys.argv[1:])
    args, unknown = parser.parse_known_args(raw_args)
    if args.cmd == "add-checkpoint":
        args.params = _extract_add_checkpoint_params(raw_args or [])
    elif unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
