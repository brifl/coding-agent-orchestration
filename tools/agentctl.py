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
ISSUE_STATUS_VALUES = ("OPEN", "IN_PROGRESS", "BLOCKED", "RESOLVED", "DECISION_REQUIRED")
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
    "retrospective",
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
IDEA_IMPACT_TAG_RE = re.compile(r"\[(MAJOR|MODERATE|MINOR)\]", re.IGNORECASE)
WORK_LOG_CONSOLIDATION_CAP = 10

Role = Literal[
    "issues_triage",
    "review",
    "implement",
    "design",
    "context_capture",
    "consolidation",
    "improvements",
    "advance",
    "retrospective",
    "stop",
]


_FEEDBACK_IMPACTS = ("QUESTION", "MINOR", "MAJOR", "BLOCKER")
_FEEDBACK_TYPES = ("bug", "feature", "concern", "question")


@dataclass(frozen=True)
class FeedbackEntry:
    feedback_id: str
    impact: str
    type: str
    description: str
    expected: str
    proposed_action: str
    checked: bool
    processed: bool
    line_number: int


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
class MinorIdea:
    idea_id: int
    impact: str
    title: str
    evidence: str
    action: str


@dataclass(frozen=True)
class ContinuousMinorStopContext:
    workflow: str
    reason: str
    ideas: tuple[MinorIdea, ...]
    ideas_digest: str


@dataclass(frozen=True)
class PlanCheck:
    found_checkpoint: bool
    has_objective: bool
    has_deliverables: bool
    has_acceptance: bool
    has_demo: bool
    has_evidence: bool
    warnings: tuple[str, ...]
    complexity_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    state: StateInfo | None
    plan_check: PlanCheck | None


def _iter_visible_markdown_lines(
    text: str,
    *,
    keepends: bool = False,
) -> Iterable[tuple[int, str, bool]]:
    """Yield (line_no, line, is_visible) while hiding fenced-code block content.

    Headings inside fenced code blocks are treated as invisible for parser logic.
    """
    lines = text.splitlines(keepends=keepends)
    in_fence = False
    fence_char = ""
    fence_len = 0
    fence_pat = re.compile(r"^\s*(`{3,}|~{3,})")

    for line_no, line in enumerate(lines, start=1):
        m = fence_pat.match(line)
        if m:
            token = m.group(1)
            char = token[0]
            length = len(token)
            if not in_fence:
                in_fence = True
                fence_char = char
                fence_len = length
            elif char == fence_char and length >= fence_len:
                in_fence = False
            yield (line_no, line, False)
            continue

        yield (line_no, line, not in_fence)


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
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?(?P<id>{CHECKPOINT_ID_PATTERN})\b"
    )
    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if not is_visible:
            continue
        m = pat.match(line)
        if not m:
            continue
        raw_id = m.group("id")
        try:
            ids.append(normalize_checkpoint_id(raw_id))
        except ValueError:
            ids.append(raw_id)
    return ids


def _parse_checkpoint_dependencies(plan_text: str) -> tuple[dict[str, list[str]], list[str]]:
    """Parse optional `depends_on: [X.Y, ...]` annotations from PLAN.md checkpoint headers.

    The `depends_on:` line must appear immediately after (or within 3 lines of) the
    `### N.M — Title` heading, before any `* **` checkpoint metadata. Parsing is
    whitespace-tolerant.

    Returns (deps_map, parse_errors) where:
      - deps_map maps normalized checkpoint_id -> list of normalized dep IDs
      - parse_errors is a list of diagnostic strings for malformed annotations
    Checkpoints without `depends_on:` have an empty dep list.
    """
    deps_map: dict[str, list[str]] = {}
    parse_errors: list[str] = []

    checkpoint_pat = re.compile(
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?(?P<id>{CHECKPOINT_ID_PATTERN})\b"
    )
    depends_pat = re.compile(r"^\s*depends_on:\s*(?P<rest>.*)$", re.IGNORECASE)
    list_pat = re.compile(r"^\[(?P<inner>[^\]]*)\]$")

    lines = plan_text.splitlines()
    i = 0
    while i < len(lines):
        m = checkpoint_pat.match(lines[i])
        if m:
            raw_id = m.group("id")
            try:
                cp_id = normalize_checkpoint_id(raw_id)
            except ValueError:
                cp_id = raw_id
            deps_map.setdefault(cp_id, [])
            # Scan next few lines for depends_on: annotation
            scan_limit = min(i + 4, len(lines))
            for j in range(i + 1, scan_limit):
                dm = depends_pat.match(lines[j])
                if not dm:
                    # Stop scanning at next heading or metadata line
                    if re.match(r"^\s*#+", lines[j]) or re.match(r"^\s*\*\s+\*\*", lines[j]):
                        break
                    continue
                rest = dm.group("rest").strip()
                lm = list_pat.match(rest)
                if not lm:
                    parse_errors.append(
                        f"Line {j + 1}: malformed depends_on value for {cp_id!r}: {rest!r} (expected [X.Y, ...])"
                    )
                    break
                raw_deps = [s.strip() for s in lm.group("inner").split(",") if s.strip()]
                normalized_deps: list[str] = []
                for raw_dep in raw_deps:
                    try:
                        normalized_deps.append(normalize_checkpoint_id(raw_dep))
                    except ValueError:
                        parse_errors.append(
                            f"Line {j + 1}: invalid dep ID {raw_dep!r} in {cp_id!r} depends_on"
                        )
                deps_map[cp_id] = normalized_deps
                break
        i += 1

    return deps_map, parse_errors


def _validate_checkpoint_dag(
    checkpoint_ids: list[str],
    deps: dict[str, list[str]],
) -> list[str]:
    """Validate the checkpoint dependency graph for cycles, dangling refs, and self-deps.

    Returns a list of error strings. Empty list means the DAG is valid.
    Uses DFS with grey/black coloring for cycle detection.
    """
    errors: list[str] = []
    id_set = set(checkpoint_ids)

    # Self-dependency check and dangling reference check
    for cp_id, dep_list in deps.items():
        for dep in dep_list:
            if dep == cp_id:
                errors.append(f"Self-dependency: {cp_id!r} depends on itself.")
            elif dep not in id_set:
                errors.append(f"Dangling dependency: {cp_id!r} depends on {dep!r}, which does not exist.")

    # Cycle detection via DFS (grey/black coloring)
    # grey = currently in DFS stack; black = fully explored
    color: dict[str, str] = {}

    def dfs(node: str, path: list[str]) -> None:
        color[node] = "grey"
        for dep in deps.get(node, []):
            if dep not in id_set:
                continue  # already reported as dangling
            if color.get(dep) == "grey":
                # Found a cycle — find where it starts
                cycle_start = path.index(dep) if dep in path else 0
                cycle_path = path[cycle_start:] + [dep]
                errors.append("Cycle: " + " -> ".join(cycle_path))
            elif color.get(dep) != "black":
                dfs(dep, path + [dep])
        color[node] = "black"

    for cp_id in checkpoint_ids:
        if color.get(cp_id) != "black":
            dfs(cp_id, [cp_id])

    return errors


def _get_satisfied_deps(plan_text: str, checkpoint_id: str) -> bool:
    """Return True iff all dependencies of checkpoint_id are (DONE) or (SKIP) in plan_text.

    If the checkpoint has no dependencies, returns True (vacuously satisfied).
    """
    deps_map, _ = _parse_checkpoint_dependencies(plan_text)
    deps = deps_map.get(checkpoint_id, [])
    for dep in deps:
        if not (_is_checkpoint_marked_done(plan_text, dep) or _is_checkpoint_skipped(plan_text, dep)):
            return False
    return True


def _get_unmet_deps(plan_text: str, checkpoint_id: str) -> list[str]:
    """Return the list of unsatisfied dependency IDs for checkpoint_id."""
    deps_map, _ = _parse_checkpoint_dependencies(plan_text)
    deps = deps_map.get(checkpoint_id, [])
    return [
        dep for dep in deps
        if not (_is_checkpoint_marked_done(plan_text, dep) or _is_checkpoint_skipped(plan_text, dep))
    ]


def _check_checkpoint_minor_ordering(checkpoint_ids: list[str]) -> list[str]:
    """Warn when minor IDs within a stage are not in non-decreasing numeric order."""
    warnings: list[str] = []
    # Group minor numbers by stage in document order.
    from collections import defaultdict as _defaultdict
    stage_minors: dict[str, list[tuple[int, str]]] = _defaultdict(list)
    for cid in checkpoint_ids:
        if "." not in cid:
            continue
        stage_part, minor_part = cid.rsplit(".", 1)
        try:
            minor_int = int(minor_part)
        except ValueError:
            continue
        stage_minors[stage_part].append((minor_int, cid))
    for stage, entries in stage_minors.items():
        for i in range(1, len(entries)):
            prev_minor, prev_cid = entries[i - 1]
            curr_minor, curr_cid = entries[i]
            if curr_minor < prev_minor:
                warnings.append(
                    f"Checkpoint minor IDs out of order in Stage {stage}: "
                    f"{prev_cid} followed by {curr_cid}."
                )
    return warnings


def _parse_stage_headings(plan_text: str) -> list[tuple[str, int, str]]:
    """
    Return (stage_id, line_no, line_text) for each stage heading.

    Tolerates an optional (SKIP) marker before 'Stage':
      ## Stage 14 — Title
      ## (SKIP) Stage 14 — Title
    """
    results: list[tuple[str, int, str]] = []
    stage_pat = re.compile(r"^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+(?P<stage>\S+)")
    for idx, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if not is_visible:
            continue
        m = stage_pat.match(line)
        if m:
            results.append((m.group("stage"), idx, line.rstrip()))
    return results


def _find_stage_bounds(plan_text: str, stage: str) -> tuple[int | None, int | None]:
    lines = plan_text.splitlines(keepends=True)
    indexed_lines = list(_iter_visible_markdown_lines(plan_text, keepends=True))
    stage_pat = re.compile(rf"^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{re.escape(stage)}\b")
    next_stage_pat = re.compile(rf"^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{STAGE_ID_PATTERN}\b")
    start_idx = None
    end_idx = None

    for idx, (_, line, is_visible) in enumerate(indexed_lines):
        if not is_visible:
            continue
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
    current_stage: str | None = None
    stage_pat = re.compile(rf"^\s*##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+(?P<stage>{STAGE_ID_PATTERN})\b")
    try:
        checkpoint_norm = normalize_checkpoint_id(checkpoint_id)
    except ValueError:
        checkpoint_norm = checkpoint_id
    checkpoint_pat = re.compile(
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?{re.escape(checkpoint_norm)}\b"
    )

    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if not is_visible:
            continue
        stage_match = stage_pat.match(line)
        if stage_match:
            current_stage = normalize_stage_id(stage_match.group("stage"))
        if checkpoint_pat.match(line):
            return current_stage

    return None


def _get_stage_number(stage_id: str) -> int | None:
    """Extract the numeric prefix from a stage ID for modular arithmetic.

    Examples: "21" -> 21, "21A" -> 21, "22" -> 22, "5B" -> 5.
    Returns None if the stage ID does not start with digits.
    """
    if not stage_id:
        return None
    m = re.match(r"(\d+)", stage_id)
    return int(m.group(1)) if m else None


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
    pat = re.compile(rf"^\s*#{{3,6}}\s+\(\s*(?:DONE|SKIPPED)\s*\)\s+{re.escape(checkpoint_id)}\b")
    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if is_visible and pat.match(line):
            return True
    return False


def _is_checkpoint_skipped(plan_text: str, checkpoint_id: str) -> bool:
    """Check if a checkpoint is marked as (SKIP) in the plan.

    (SKIP) checkpoints are deferred — bypassed during advance but preserved
    during consolidation.  Removing the marker reactivates the checkpoint."""
    pat = re.compile(rf"^\s*#{{3,6}}\s+\(\s*SKIP\s*\)\s+{re.escape(checkpoint_id)}\b")
    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if is_visible and pat.match(line):
            return True
    return False


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
    fallback_reason: str | None = None
    try:
        from prompt_catalog import load_catalog  # type: ignore

        entries = load_catalog(catalog_path)
        index = {entry.key: entry.title for entry in entries}
        return (index, catalog_path, None)
    except Exception as exc:
        # Fallback for environments where prompt_catalog.py is not importable
        # from the current script location (for example copied skill scripts).
        fallback_reason = f"{type(exc).__name__}: {exc}"
        try:
            raw = _read_text(catalog_path)
        except OSError as exc:
            detail = f"Failed to read prompt catalog at {catalog_path}: {exc}"
            if fallback_reason:
                detail += f" (fallback after {fallback_reason})"
            return ({}, catalog_path, detail)

        index: dict[str, str] = {}
        header_pat = re.compile(r"(?im)^##\s+(?P<id>[a-z0-9_.-]+)\s+[—–-]\s+(?P<title>.+?)\s*$")
        for match in header_pat.finditer(raw):
            prompt_id = match.group("id").strip()
            if prompt_id and prompt_id not in index:
                index[prompt_id] = match.group("title").strip()

        if not index:
            detail = f"Failed to parse prompt catalog at {catalog_path}: no prompt headers found."
            if fallback_reason:
                detail += f" (fallback after {fallback_reason})"
            return ({}, catalog_path, detail)

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


def _parse_feedback_file(text: str) -> tuple[tuple[FeedbackEntry, ...], list[str]]:
    """Parse .vibe/FEEDBACK.md and return (entries, errors).

    Each entry has the form:
        - [ ] FEEDBACK-001: <title>
          - Impact: QUESTION|MINOR|MAJOR|BLOCKER
          - Type: bug|feature|concern|question
          - Description: <text>
          - Expected: <text>
          - Proposed action: <optional>

    errors is a list of "line N: <message>" strings (empty on success).
    """
    lines = text.splitlines()
    entries: list[FeedbackEntry] = []
    errors: list[str] = []
    seen_ids: dict[str, int] = {}

    entry_head = re.compile(r"^\s*-\s*\[\s*([xX ]?)\s*\]\s*(.+?)\s*$")
    detail_re = re.compile(r"^\s*-\s*(?P<key>[A-Za-z][A-Za-z _-]*)\s*:\s*(?P<val>.+?)\s*$")
    feedback_id_re = re.compile(r"^(FEEDBACK-\d+):\s*(.+)$", re.IGNORECASE)

    i = 0
    while i < len(lines):
        raw = lines[i]
        m = entry_head.match(raw)
        if not m:
            i += 1
            continue

        entry_line = i + 1  # 1-indexed
        title_full = m.group(2).strip()
        id_m = feedback_id_re.match(title_full)
        if not id_m:
            i += 1
            continue  # not a FEEDBACK-NNN entry; skip

        feedback_id = id_m.group(1).upper()
        checked = m.group(1).strip().lower() == "x"
        processed = "<!-- processed:" in raw

        # Duplicate ID check
        if feedback_id in seen_ids:
            errors.append(f"line {entry_line}: duplicate FEEDBACK-ID {feedback_id} (first seen at line {seen_ids[feedback_id]})")
        else:
            seen_ids[feedback_id] = entry_line

        # Collect detail lines
        fields: dict[str, str] = {}
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if entry_head.match(nxt):
                break
            dm = detail_re.match(nxt)
            if dm:
                key = dm.group("key").strip().lower().replace(" ", "_")
                val = dm.group("val").strip()
                if key not in fields:
                    fields[key] = val
            j += 1

        # Validate required fields
        impact_raw = fields.get("impact", "")
        impact = impact_raw.upper() if impact_raw else ""
        if not impact:
            errors.append(f"line {entry_line}: {feedback_id} missing required field 'Impact'")
        elif impact not in _FEEDBACK_IMPACTS:
            errors.append(f"line {entry_line}: {feedback_id} invalid Impact '{impact}' (must be one of {', '.join(_FEEDBACK_IMPACTS)})")

        type_raw = fields.get("type", "")
        fb_type = type_raw.lower() if type_raw else ""
        if not fb_type:
            errors.append(f"line {entry_line}: {feedback_id} missing required field 'Type'")
        elif fb_type not in _FEEDBACK_TYPES:
            errors.append(f"line {entry_line}: {feedback_id} invalid Type '{fb_type}' (must be one of {', '.join(_FEEDBACK_TYPES)})")

        description = fields.get("description", "")
        if not description:
            errors.append(f"line {entry_line}: {feedback_id} missing required field 'Description'")

        expected = fields.get("expected", "")
        if not expected:
            errors.append(f"line {entry_line}: {feedback_id} missing required field 'Expected'")

        entries.append(FeedbackEntry(
            feedback_id=feedback_id,
            impact=impact or "QUESTION",
            type=fb_type or "",
            description=description,
            expected=expected,
            proposed_action=fields.get("proposed_action", ""),
            checked=checked,
            processed=processed,
            line_number=entry_line,
        ))
        i = j

    return tuple(entries), errors


def _next_issue_id(state_text: str) -> int:
    """Return the next available ISSUE number by scanning STATE.md Active issues."""
    existing = re.findall(r"ISSUE-(\d+)", state_text, re.IGNORECASE)
    if not existing:
        return 1
    return max(int(n) for n in existing) + 1


def _feedback_entry_to_issue_block(entry: "FeedbackEntry", issue_id: str) -> str:
    """Format a FeedbackEntry as an Issue block for STATE.md."""
    notes = f"{entry.type.capitalize()}: {entry.description}" if entry.description else entry.type
    lines = [
        f"- [ ] {issue_id}: {entry.feedback_id} - {entry.type}",
        f"  - Impact: {entry.impact}",
        f"  - Status: OPEN",
        f"  - Owner: agent",
        f"  - Unblock Condition: {entry.expected or 'See description'}",
        f"  - Evidence Needed: (to be determined during triage)",
        f"  - Notes: {notes}",
    ]
    if entry.proposed_action:
        lines.append(f"  - Proposed action: {entry.proposed_action}")
    return "\n".join(lines)


def _inject_into_state_md(state_text: str, issue_blocks: list[str]) -> str:
    """Append issue blocks into the ## Active issues section of STATE.md."""
    lines = state_text.splitlines(keepends=True)
    insert_idx: int | None = None
    in_section = False
    for i, line in enumerate(lines):
        if re.match(r"(?im)^\s*##\s+Active issues\s*$", line):
            in_section = True
            continue
        if in_section:
            if re.match(r"(?im)^\s*##\s+\S", line):
                insert_idx = i
                break
    if insert_idx is None and in_section:
        insert_idx = len(lines)

    if insert_idx is None:
        new_section = "\n## Active issues\n\n" + "\n\n".join(issue_blocks) + "\n"
        return state_text + new_section

    # Remove trailing placeholder "(None)" if present
    j = insert_idx - 1
    while j >= 0 and lines[j].strip().lower() in {"", "(none)", "(none.)"}:
        j -= 1
    insert_idx = j + 1

    new_block = "\n" + "\n\n".join(issue_blocks) + "\n"
    lines.insert(insert_idx, new_block)
    return "".join(lines)


def _mark_feedback_processed(feedback_text: str, feedback_id: str, issue_id: str) -> str:
    """Mark a FEEDBACK entry as [x] and add <!-- processed: ISSUE-NNN --> comment."""
    lines = feedback_text.splitlines(keepends=True)
    entry_re = re.compile(
        r"^(\s*-\s*\[)\s*[ ]?\s*(\]\s*" + re.escape(feedback_id) + r"\b.*?)(\s*)$"
    )
    result = []
    for line in lines:
        stripped = line.rstrip("\n\r")
        m = entry_re.match(stripped)
        if m and "<!-- processed:" not in stripped:
            new_line = re.sub(r"\[\s*[ ]?\s*\]", "[x]", stripped) + f"  <!-- processed: {issue_id} -->"
            result.append(new_line + "\n")
        else:
            result.append(line)
    return "".join(result)


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
        if issue.checked and issue.status == "RESOLVED":
            messages.append(
                f"Active issue {issue.issue_id} is resolved; "
                "move it to HISTORY.md to keep Active issues clean."
            )
        if issue.checked and issue.status == "DECISION_REQUIRED":
            messages.append(
                f"Active issue {issue.issue_id} is checked but Status is DECISION_REQUIRED; "
                "set Status to RESOLVED or IN_PROGRESS once the decision is made."
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


def _continuous_approval_path(repo_root: Path) -> Path:
    return repo_root / ".vibe" / "CONTINUOUS_APPROVALS.json"


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


def _write_stop_loop_result(
    repo_root: Path,
    state: StateInfo,
    reason: str,
    *,
    report: dict[str, Any] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    """Persist a stop sentinel to LOOP_RESULT.json when the dispatcher halts."""
    path = _loop_result_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol_version": LOOP_RESULT_PROTOCOL_VERSION,
        "loop": "stop",
        "result": "stop",
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
        "next_role_hint": "stop",
        "reason": reason,
        "state_sha256": _state_sha256(repo_root),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if report is not None:
        payload["report"] = report
    if isinstance(extra_fields, dict):
        for key, value in extra_fields.items():
            if isinstance(key, str) and key and key not in payload:
                payload[key] = value
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _validate_acceptance_matrix_items(
    report: dict[str, Any], loop_name: str
) -> tuple[list[str], bool]:
    """Validate acceptance_matrix entries. Returns (errors, has_low_confidence_critical)."""
    errors: list[str] = []
    has_low_confidence_critical = False

    acceptance_matrix = report.get("acceptance_matrix")
    if not isinstance(acceptance_matrix, list):
        errors.append("LOOP_RESULT report field 'acceptance_matrix' must be a list.")
        return errors, False
    if loop_name in {"implement", "review", "issues_triage"} and not acceptance_matrix:
        errors.append(
            f"LOOP_RESULT report field 'acceptance_matrix' must not be empty for {loop_name} loops."
        )

    for idx, item in enumerate(acceptance_matrix):
        if not isinstance(item, dict):
            errors.append(f"acceptance_matrix[{idx}] must be an object.")
            continue
        for field in ("item", "status", "evidence", "critical", "confidence", "evidence_strength"):
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
            and (confidence < CONFIDENCE_MIN_REQUIRED or evidence_strength == "LOW")
        ):
            has_low_confidence_critical = True

    return errors, has_low_confidence_critical


def _validate_top_findings(report: dict[str, Any]) -> list[str]:
    """Validate top_findings list and each finding's required fields and ordering."""
    errors: list[str] = []

    top_findings = report.get("top_findings")
    if not isinstance(top_findings, list):
        errors.append("LOOP_RESULT report field 'top_findings' must be a list.")
        return errors
    if len(top_findings) > LOOP_REPORT_MAX_FINDINGS:
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
            errors.append(f"top_findings[{idx}].impact must be one of {', '.join(IMPACTS)}.")
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

    return errors


def _validate_state_transition(
    report: dict[str, Any], payload: dict[str, Any]
) -> list[str]:
    """Validate state_transition and assert after-state matches top-level LOOP_RESULT fields."""
    errors: list[str] = []

    state_transition = report.get("state_transition")
    if not isinstance(state_transition, dict):
        errors.append("LOOP_RESULT report field 'state_transition' must be an object.")
        return errors

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

    return errors


def _validate_report_loop_result_mirror(
    report: dict[str, Any], payload: dict[str, Any]
) -> list[str]:
    """Validate that report.loop_result mirrors the top-level LOOP_RESULT required fields."""
    errors: list[str] = []

    report_loop_result = report.get("loop_result")
    if not isinstance(report_loop_result, dict):
        errors.append("LOOP_RESULT report field 'loop_result' must be an object.")
        return errors

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

    return errors


def _validate_loop_report_schema(payload: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    loop_name = str(payload.get("loop", "")).strip()
    report = payload.get("report")
    if not isinstance(report, dict):
        return ("Missing or invalid LOOP_RESULT field 'report' (object required).",)

    for field in LOOP_REPORT_REQUIRED_FIELDS:
        if field not in report:
            errors.append(f"LOOP_RESULT report missing required field '{field}'.")

    am_errors, has_low_confidence_critical = _validate_acceptance_matrix_items(report, loop_name)
    errors.extend(am_errors)
    errors.extend(_validate_top_findings(report))
    errors.extend(_validate_state_transition(report, payload))
    errors.extend(_validate_report_loop_result_mirror(report, payload))

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
    pat = re.compile(rf"^##\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+{re.escape(stage)}\b")
    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if is_visible and pat.match(line):
            return True
    return False


def _extract_checkpoint_section(plan_text: str, checkpoint_id: str) -> str | None:
    """
    Find a checkpoint heading containing checkpoint_id and return its section text.

    Supports headings like:
      ### 0.0 — Foo
      ### 0.0 - Foo
      ### Checkpoint 0.0: Foo   (legacy)
      #### (DONE) 0.0 — Foo     (tolerant)
    """
    indexed_lines = list(_iter_visible_markdown_lines(plan_text, keepends=True))
    head_pat = re.compile(
        r"^\s*(#{3,6})\s+.*?\b" + re.escape(checkpoint_id) + r"\b.*?$"
    )

    start_idx: int | None = None
    level: int | None = None
    for idx, (_, line, is_visible) in enumerate(indexed_lines):
        if not is_visible:
            continue
        m = head_pat.match(line)
        if m:
            start_idx = idx
            level = len(m.group(1))
            break

    if start_idx is None or level is None:
        return None

    next_pat = re.compile(r"^\s*(#{1,6})\s+")
    end_idx = len(indexed_lines)
    for idx in range(start_idx + 1, len(indexed_lines)):
        _, line, is_visible = indexed_lines[idx]
        if not is_visible:
            continue
        nm = next_pat.match(line)
        if nm and len(nm.group(1)) <= level:
            end_idx = idx
            break

    return "".join(line for _, line, _ in indexed_lines[start_idx:end_idx]).rstrip()


# Checkpoint complexity budget: warn when a checkpoint is likely too large for one loop.
COMPLEXITY_BUDGET: dict[str, int] = {
    "Deliverables": 5,
    "Acceptance": 6,
    "Demo commands": 4,
}

_CHECKPOINT_FIELD_NAMES = ("Objective", "Deliverables", "Acceptance", "Demo commands", "Evidence")
_CHECKPOINT_FIELD_HEADING_RE = re.compile(
    r"(?im)^\s*(?:[-*]+\s*)?(?:\*\*)?\s*(?:"
    + "|".join(re.escape(f) for f in _CHECKPOINT_FIELD_NAMES)
    + r")\s*:?\s*(?:\*\*)?\s*:?\s*$"
)


def _count_items_in_subsection(section: str, heading_name: str) -> int:
    """Count bullet items under a named heading within a checkpoint section."""
    target_re = re.compile(
        rf"(?im)^\s*(?:[-*]+\s*)?(?:\*\*)?\s*{re.escape(heading_name)}\s*:?\s*(?:\*\*)?\s*:?\s*$"
    )
    m = target_re.search(section)
    if not m:
        return 0
    lines = section[m.end():].splitlines()
    count = 0
    for line in lines:
        if _CHECKPOINT_FIELD_HEADING_RE.match(line):
            break
        if re.match(r"^\s*(?:---+|#{3,})\s*$", line):
            break
        if re.match(r"^\s*[-*]\s+\S", line):
            count += 1
    return count


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

    complexity_warnings: list[str] = []
    for field_name, budget in COMPLEXITY_BUDGET.items():
        count = _count_items_in_subsection(section, field_name)
        if count > budget:
            complexity_warnings.append(
                f"Checkpoint {checkpoint_id} '{field_name}' has {count} items "
                f"(budget: {budget}); consider splitting this checkpoint."
            )

    return PlanCheck(
        found_checkpoint=True,
        has_objective=has_objective,
        has_deliverables=has_deliverables,
        has_acceptance=has_acceptance,
        has_demo=has_demo,
        has_evidence=has_evidence,
        warnings=tuple(warnings),
        complexity_warnings=tuple(complexity_warnings),
    )


def _validate_state_section(
    repo_root: Path,
    state: StateInfo,
    state_path: Path,
    strict: bool,
) -> tuple[list[str], list[str]]:
    """Validate STATE.md fields, issue schema, work log size, and evidence path."""
    errors: list[str] = []
    warnings: list[str] = []

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

    for message in _validate_issue_schema(state.issues):
        (errors if strict else warnings).append(f".vibe/STATE.md: {message}")

    state_text = _read_text(state_path)
    sections = _parse_context_sections(state_text)
    work_log_lines = _get_section_lines(sections, "Work log (current session)")
    work_log_entries = sum(1 for line in work_log_lines if re.match(r"^\s*-\s+", line))
    if work_log_entries > WORK_LOG_CONSOLIDATION_CAP:
        warnings.append(
            f".vibe/STATE.md: work log has {work_log_entries} entries "
            f"(>{WORK_LOG_CONSOLIDATION_CAP}); consider running consolidation to prune."
        )

    if not state.evidence_path:
        warnings.append(".vibe/STATE.md: missing evidence '- path: ...' (optional).")
    else:
        resolved = _resolve_path(repo_root, state.evidence_path)
        if state.status in {"IN_REVIEW", "DONE"} and not resolved.exists():
            msg = f"Evidence file not found at {resolved}."
            (errors if strict else warnings).append(msg)

    return errors, warnings


def _validate_plan_section(
    repo_root: Path,
    state: StateInfo,
    strict: bool,
    strict_complexity: bool,
) -> tuple[list[str], list[str], PlanCheck | None]:
    """Validate PLAN.md stage headings, checkpoint ordering, stage drift, and plan check."""
    errors: list[str] = []
    warnings: list[str] = []
    plan_check: PlanCheck | None = None

    if not state.checkpoint:
        return errors, warnings, plan_check

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
            errors.append(f".vibe/PLAN.md: missing stage section for Stage {state.stage}.")

        for w in _check_checkpoint_minor_ordering(_parse_plan_checkpoint_ids(plan_text)):
            warnings.append(f".vibe/PLAN.md: {w}")

    if plan_text and state.stage:
        actual_stage = _get_stage_for_checkpoint(plan_text, state.checkpoint)
        state_stage = state.stage
        if state_stage and is_valid_stage_id(state_stage):
            state_stage = normalize_stage_id(state_stage)
        if actual_stage and state_stage and actual_stage != state_stage:
            errors.append(
                f"Stage drift detected: STATE.md says Stage {state.stage}, "
                f"but checkpoint {state.checkpoint} is in Stage {actual_stage} in PLAN.md."
            )

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
        for w in plan_check.complexity_warnings:
            (errors if strict_complexity else warnings).append(f".vibe/PLAN.md: {w}")

    return errors, warnings, plan_check


def _validate_catalog_section(
    repo_root: Path,
    strict: bool,
) -> tuple[list[str], list[str]]:
    """Validate prompt catalog and workflow prompt references."""
    errors: list[str] = []
    warnings: list[str] = []

    catalog_index, catalog_path, catalog_error = _load_prompt_catalog_index(repo_root)
    if catalog_error:
        warnings.append(catalog_error)
        return errors, warnings

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

    return errors, warnings


def validate(repo_root: Path, strict: bool, strict_complexity: bool = False) -> ValidationResult:
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

    state_errors, state_warnings = _validate_state_section(repo_root, state, state_path, strict)
    plan_errors, plan_warnings, plan_check = _validate_plan_section(
        repo_root, state, strict, strict_complexity
    )
    catalog_errors, catalog_warnings = _validate_catalog_section(repo_root, strict)

    # Feedback gate warning
    has_feedback, feedback_reason = _has_unprocessed_feedback(repo_root)
    feedback_warnings = [f".vibe/FEEDBACK.md: {feedback_reason}"] if has_feedback else []

    # DAG validation
    plan_path = repo_root / ".vibe" / "PLAN.md"
    dag_errors: list[str] = []
    dag_warnings: list[str] = []
    if plan_path.exists():
        plan_text = _read_text(plan_path)
        cp_ids = _parse_plan_checkpoint_ids(plan_text)
        deps_map, dep_parse_errors = _parse_checkpoint_dependencies(plan_text)
        dag_diags = _validate_checkpoint_dag(cp_ids, deps_map) + dep_parse_errors
        if dag_diags:
            if strict:
                dag_errors = [f"PLAN.md DAG: {d}" for d in dag_diags]
            else:
                dag_warnings = [f"PLAN.md DAG: {d}" for d in dag_diags]

    all_errors = state_errors + plan_errors + catalog_errors + dag_errors
    all_warnings = state_warnings + plan_warnings + catalog_warnings + feedback_warnings + dag_warnings
    return ValidationResult(
        ok=len(all_errors) == 0,
        errors=tuple(all_errors),
        warnings=tuple(all_warnings),
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


def _consolidation_trigger_reason(repo_root: Path) -> str | None:
    """Check if work log bloat warrants a consolidation loop."""
    state_path = repo_root / ".vibe" / "STATE.md"
    if not state_path.exists():
        return None

    sections = _parse_context_sections(_read_text(state_path))
    work_log_lines = _get_section_lines(sections, "Work log (current session)")
    work_log_entries = sum(1 for line in work_log_lines if re.match(r"^\s*-\s+", line))
    if work_log_entries > WORK_LOG_CONSOLIDATION_CAP:
        return f"Work log has {work_log_entries} entries (>{WORK_LOG_CONSOLIDATION_CAP}); consolidation needed to prune."

    return None


def _process_improvements_trigger_reason(
    repo_root: Path,
    workflow_flags: dict[str, bool],
    current_checkpoint: str | None = None,
) -> str | None:
    if workflow_flags.get("RUN_PROCESS_IMPROVEMENTS"):
        return "Workflow flag RUN_PROCESS_IMPROVEMENTS is set."

    # If improvements already ran this cycle, suppress the auto-trigger
    if workflow_flags.get("PROCESS_IMPROVEMENTS_DONE"):
        return None

    # Retrospective trigger: every 5 stages
    if current_checkpoint:
        stage_num = _get_stage_number(current_checkpoint.split(".")[0] if "." in current_checkpoint else current_checkpoint)
        if stage_num is not None and stage_num > 0 and stage_num % 5 == 0:
            return f"Stage {stage_num} retrospective: stage number is divisible by 5."

    state_path = repo_root / ".vibe" / "STATE.md"
    if not state_path.exists():
        return None

    sections = _parse_context_sections(_read_text(state_path))
    evidence_lines = _get_section_lines(sections, "Evidence")

    evidence_signal_lines = _count_nonempty_signal_lines(evidence_lines)
    if evidence_signal_lines > 50:
        return f"Evidence section has {evidence_signal_lines} non-empty lines (>50)."

    return None


def _stage_design_trigger_reason(workflow_flags: dict[str, bool]) -> str | None:
    """Check if stage design should run before implementation.

    Stage design runs once per stage when STAGE_DESIGNED flag is not set.
    The flag is cleared on stage transitions (by consolidation) and set
    by the stage design loop.
    """
    if workflow_flags.get("STAGE_DESIGNED"):
        return None
    # Only trigger if the flag key exists in workflow state (backward-compat:
    # repos without the flag won't get unexpected design loops).
    if "STAGE_DESIGNED" not in workflow_flags:
        return None
    return "New stage entered without design; STAGE_DESIGNED flag not set."


def _retrospective_trigger_reason(workflow_flags: dict[str, bool]) -> str | None:
    """Check if a stage retrospective should run after a stage transition.

    Retrospective runs once per stage when RETROSPECTIVE_DONE flag is not set.
    Consolidation clears the flag; the retrospective loop sets it.
    Backward-compat: repos without the flag in workflow state won't get unexpected loops.
    """
    if workflow_flags.get("RETROSPECTIVE_DONE"):
        return None
    if "RETROSPECTIVE_DONE" not in workflow_flags:
        return None
    return "Stage transition completed without retrospective; RETROSPECTIVE_DONE flag not set."


_MAINTENANCE_CYCLE_TYPES = {0: "refactor", 1: "test", 2: "docs"}
_MAINTENANCE_PROMPT_MAP = {
    "refactor": "prompt.refactor_scan",
    "test": "prompt.test_gap_analysis",
    "docs": "prompt.docs_gap_analysis",
}


def _maintenance_cycle_trigger_reason(
    workflow_flags: dict[str, bool],
    stage_id: str | None,
) -> tuple[str | None, str | None]:
    """Check if a periodic maintenance cycle should run.

    Returns (reason, prompt_id) or (None, None).

    Cycle type is determined by stage_number % 3:
      0 → refactor, 1 → test backfill, 2 → documentation.
    """
    if workflow_flags.get("MAINTENANCE_CYCLE_DONE"):
        return (None, None)
    if "MAINTENANCE_CYCLE_DONE" not in workflow_flags:
        return (None, None)
    if not stage_id:
        return (None, None)

    stage_num = _get_stage_number(stage_id)
    if stage_num is None:
        return (None, None)

    cycle_type = _MAINTENANCE_CYCLE_TYPES.get(stage_num % 3, "refactor")
    prompt_id = _MAINTENANCE_PROMPT_MAP[cycle_type]
    return (
        f"Stage {stage_num} maintenance cycle: {cycle_type} (stage % 3 == {stage_num % 3}).",
        prompt_id,
    )


def _extract_demo_commands(plan_text: str, checkpoint_id: str) -> list[str]:
    """Extract demo commands for a specific checkpoint from PLAN.md.

    Looks for a checkpoint heading (### X.Y — ...) followed by a
    ``* **Demo commands:**`` section with backtick-wrapped commands.
    """
    # Find the checkpoint heading
    heading_pat = re.compile(
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?"
        + re.escape(checkpoint_id) + r"\b"
    )
    lines = plan_text.splitlines()
    start_idx: int | None = None
    for idx, line in enumerate(lines):
        if heading_pat.match(line):
            start_idx = idx
            break
    if start_idx is None:
        return []

    # Find the next checkpoint heading (end boundary)
    next_heading_pat = re.compile(
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?{CHECKPOINT_ID_PATTERN}\b"
    )
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        if next_heading_pat.match(lines[idx]):
            end_idx = idx
            break

    # Find "Demo commands:" within this section
    section = lines[start_idx:end_idx]
    in_demo = False
    commands: list[str] = []
    for line in section:
        stripped = line.strip()
        if stripped.startswith("* **Demo commands:**") or stripped.startswith("- **Demo commands:**"):
            in_demo = True
            continue
        if in_demo:
            # Stop at next bold field or blank line
            if stripped.startswith("* **") or stripped.startswith("- **") or stripped == "---":
                break
            # Extract backtick-wrapped command
            m = re.match(r"^\s*[\*\-]\s+`(.+)`\s*$", stripped)
            if m:
                commands.append(m.group(1))
    return commands


def _run_smoke_test_gate(
    repo_root: Path,
    state: "StateInfo",
    plan_text: str,
    timeout: int = 30,
) -> tuple[bool, str | None]:
    """Run demo commands for the current checkpoint as a smoke test.

    Returns (passed, failure_reason).  If no demo commands are defined,
    returns (True, None).
    """
    if not state.checkpoint:
        return (True, None)

    commands = _extract_demo_commands(plan_text, state.checkpoint)
    if not commands:
        return (True, None)

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                stderr_snippet = (result.stderr or "").strip()[:200]
                return (
                    False,
                    f"Demo command failed (rc={result.returncode}): {cmd}"
                    + (f"\n{stderr_snippet}" if stderr_snippet else ""),
                )
        except subprocess.TimeoutExpired:
            return (False, f"Demo command timed out after {timeout}s: {cmd}")
        except OSError as exc:
            return (False, f"Demo command could not run: {cmd} ({exc})")

    return (True, None)


def _has_unprocessed_feedback(repo_root: Path) -> tuple[bool, str]:
    """Return (has_feedback, reason_string) for unprocessed FEEDBACK.md entries."""
    feedback_path = repo_root / ".vibe" / "FEEDBACK.md"
    if not feedback_path.exists():
        return False, ""
    text = feedback_path.read_text(encoding="utf-8")
    entries, _ = _parse_feedback_file(text)
    unprocessed = [e for e in entries if not e.processed]
    if not unprocessed:
        return False, ""
    top_impact = max(
        (e.impact for e in unprocessed),
        key=lambda imp: _FEEDBACK_IMPACTS.index(imp) if imp in _FEEDBACK_IMPACTS else len(_FEEDBACK_IMPACTS),
        default="QUESTION",
    )
    reason = (
        f"Unprocessed human feedback: {len(unprocessed)} entries "
        f"(top impact: {top_impact}). Run agentctl feedback inject."
    )
    return True, reason


@dataclass(frozen=True)
class _DecisionContext:
    """Pre-loaded IO context for the pure role-decision function."""
    workflow_flags: dict[str, bool]
    plan_text: str
    smoke_gate_result: tuple[bool, str] | None  # Set only when state is IN_REVIEW
    context_capture_reason: str | None
    consolidation_reason: str | None
    process_improvements_reason: str | None
    unprocessed_feedback_reason: str | None


def _gather_decision_context(state: StateInfo, repo_root: Path) -> _DecisionContext:
    """Perform all IO needed for role selection and bundle into a context object."""
    workflow_flags = _load_workflow_flags(repo_root)
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_text = _read_text(plan_path) if plan_path.exists() else ""
    smoke_gate_result = (
        _run_smoke_test_gate(repo_root, state, plan_text)
        if state.status == "IN_REVIEW"
        else None
    )
    return _DecisionContext(
        workflow_flags=workflow_flags,
        plan_text=plan_text,
        smoke_gate_result=smoke_gate_result,
        context_capture_reason=_context_capture_trigger_reason(repo_root, workflow_flags),
        consolidation_reason=_consolidation_trigger_reason(repo_root),
        process_improvements_reason=_process_improvements_trigger_reason(
            repo_root, workflow_flags, state.checkpoint
        ),
        unprocessed_feedback_reason=_has_unprocessed_feedback(repo_root)[1] or None,
    )


def _decide_role(state: StateInfo, ctx: _DecisionContext) -> tuple[Role, str, str | None]:
    """Pure role-selection logic. No IO — all context is pre-loaded in ctx.

    Returns (role, reason, prompt_id_override).
    prompt_id_override is non-None only for maintenance cycles that need
    a specific prompt different from the role's default.
    """
    # 0) Hard stop / hard triage conditions
    if state.status == "BLOCKED":
        return ("issues_triage", "Checkpoint status is BLOCKED.", None)

    top = _top_issue_impact(state.issues)
    if top == "BLOCKER":
        blocker_issues = [i for i in state.issues if i.impact == "BLOCKER"]
        all_human_owned = all(
            i.owner and i.owner.lower() == "human" for i in blocker_issues
        )
        if all_human_owned:
            titles = "; ".join(i.issue_id or i.title for i in blocker_issues)
            return (
                "stop",
                f"All BLOCKER issues are owner: human — agent cannot proceed unilaterally. "
                f"Resolve: {titles}",
                None,
            )
        return ("issues_triage", "BLOCKER issue present.", None)

    # 0a) Human approval gate — stop and surface DECISION_REQUIRED issues for human review
    decision_issues = [i for i in state.issues if i.status == "DECISION_REQUIRED"]
    if decision_issues:
        titles = "; ".join(i.issue_id or i.title for i in decision_issues)
        return (
            "stop",
            f"Human decision required before proceeding. "
            f"Resolve DECISION_REQUIRED issue(s): {titles}",
            None,
        )

    # 0b) Unprocessed human feedback gate
    if ctx.unprocessed_feedback_reason:
        return ("issues_triage", ctx.unprocessed_feedback_reason, None)

    # 1) Review if IN_REVIEW — smoke gate result pre-loaded
    if state.status == "IN_REVIEW":
        if ctx.smoke_gate_result is not None:
            passed, failure_reason = ctx.smoke_gate_result
            if not passed:
                return ("issues_triage", f"Smoke test gate failed: {failure_reason}", None)
        return ("review", "Checkpoint status is IN_REVIEW.", None)

    # 2) If DONE, either advance to next checkpoint or stop if plan exhausted
    if state.status == "DONE":
        plan_ids = _parse_plan_checkpoint_ids(ctx.plan_text)

        if not plan_ids:
            return ("stop", "No checkpoints found in .vibe/PLAN.md (plan exhausted).", None)

        if not state.checkpoint:
            return ("advance", "Status DONE but no checkpoint set; advance to first checkpoint in plan.", None)

        nxt = _next_checkpoint_after(plan_ids, state.checkpoint)
        if not nxt:
            return ("stop", "Current checkpoint is last checkpoint in .vibe/PLAN.md (plan exhausted).", None)

        # If the next one is explicitly marked (DONE) or (SKIP), skip forward
        while nxt and (
            _is_checkpoint_marked_done(ctx.plan_text, nxt)
            or _is_checkpoint_skipped(ctx.plan_text, nxt)
        ):
            state_ck = nxt
            nxt = _next_checkpoint_after(plan_ids, state_ck)

        if not nxt:
            return ("stop", "All remaining checkpoints are marked (DONE) or (SKIP) in .vibe/PLAN.md (plan exhausted).", None)

        # Also skip dep-blocked checkpoints (deps not yet DONE/SKIP)
        dep_blocked: dict[str, list[str]] = {}
        while nxt and not _get_satisfied_deps(ctx.plan_text, nxt):
            unmet = _get_unmet_deps(ctx.plan_text, nxt)
            dep_blocked[nxt] = unmet
            state_ck = nxt
            nxt = _next_checkpoint_after(plan_ids, state_ck)
            # Re-skip any DONE/SKIP checkpoints encountered while scanning
            while nxt and (
                _is_checkpoint_marked_done(ctx.plan_text, nxt)
                or _is_checkpoint_skipped(ctx.plan_text, nxt)
            ):
                state_ck = nxt
                nxt = _next_checkpoint_after(plan_ids, state_ck)

        if not nxt and dep_blocked:
            unmet_details = "; ".join(
                f"{cp}: waiting on {deps}" for cp, deps in dep_blocked.items()
            )
            return (
                "stop",
                f"All remaining checkpoints are dep-blocked. Unmet deps: {unmet_details}",
                None,
            )

        # Check for stage transition - recommend consolidation before advancing to new stage
        is_stage_change, cur_stage, nxt_stage = _detect_stage_transition(
            ctx.plan_text, state.checkpoint, nxt
        )
        if is_stage_change:
            # Check if STATE.md stage matches the plan's current stage
            if state.stage != nxt_stage:
                return (
                    "consolidation",
                    f"Stage transition detected: {cur_stage} → {nxt_stage}. "
                    f"Run consolidation to archive Stage {cur_stage} and update stage pointer before advancing.",
                    None,
                )

        return ("advance", f"Checkpoint is DONE; next checkpoint is {nxt}.", None)

    # 3) Normal execution states
    if state.status in {"NOT_STARTED", "IN_PROGRESS"}:
        # If there are non-blocking issues, triage can be recommended (your choice)
        if top in {"MAJOR", "QUESTION"}:
            return ("issues_triage", f"Active issues present (top impact: {top}).", None)

        # Maintenance loops fire before implementation when NOT_STARTED.
        if state.status == "NOT_STARTED":
            # Retrospective — runs once per stage after a transition, before design
            retro_reason = _retrospective_trigger_reason(ctx.workflow_flags)
            if retro_reason:
                return ("retrospective", retro_reason, None)

            # Stage design check — runs once per stage after retrospective
            stage_design_reason = _stage_design_trigger_reason(ctx.workflow_flags)
            if stage_design_reason:
                return ("design", stage_design_reason, None)

            # Maintenance cycle — refactor/test/docs based on stage%3
            maint_reason, maint_prompt = _maintenance_cycle_trigger_reason(
                ctx.workflow_flags, state.stage,
            )
            if maint_reason and maint_prompt:
                return ("implement", maint_reason, maint_prompt)

            if ctx.context_capture_reason:
                return ("context_capture", ctx.context_capture_reason, None)

            if ctx.consolidation_reason:
                return ("consolidation", ctx.consolidation_reason, None)

            if ctx.process_improvements_reason:
                return ("improvements", ctx.process_improvements_reason, None)

        return ("implement", f"Checkpoint status is {state.status}.", None)

    # 4) Default
    return ("design", "No recognized status; stage design likely required.", None)


def _recommend_next(state: StateInfo, repo_root: Path) -> tuple[Role, str, str | None]:
    """Shell: gather IO context, then delegate to pure _decide_role."""
    ctx = _gather_decision_context(state, repo_root)
    return _decide_role(state, ctx)


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
    "retrospective": {
        "id": "prompt.retrospective",
        "title": "Stage Retrospective Prompt",
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
    "prompt.test_gap_analysis": "implement",
    "prompt.test_generation": "implement",
    "prompt.test_review": "review",
    "prompt.docs_gap_analysis": "implement",
    "prompt.docs_gap_fix": "implement",
    "prompt.docs_refactor_analysis": "implement",
    "prompt.docs_refactor_fix": "implement",
    "prompt.demo_script": "design",
    "prompt.feedback_intake": "issues_triage",
    "prompt.feedback_triage": "issues_triage",
}

PROMPT_ROLE_MAP: dict[str, Role] = {meta["id"]: role for role, meta in PROMPT_MAP.items()}
PROMPT_ROLE_MAP.update(EXTRA_WORKFLOW_PROMPT_ROLES)

CONTINUOUS_OVERRIDE_WORKFLOWS = frozenset(
    {
        "continuous-refactor",
        "continuous-test-generation",
        "continuous-documentation",
    }
)

CONTINUOUS_OVERRIDE_REASON_PREFIX: dict[str, str] = {
    "continuous-refactor": "Continuous-refactor override active (plan state ignored).",
    "continuous-test-generation": "Continuous-test-generation override active (plan state ignored).",
    "continuous-documentation": "Continuous-documentation override active (plan state ignored).",
}

CONTINUOUS_WORKFLOW_ALLOWED_PROMPTS: dict[str, set[str]] = {
    "continuous-refactor": {
        "prompt.refactor_scan",
        "prompt.refactor_execute",
        "prompt.refactor_verify",
    },
    "continuous-test-generation": {
        "prompt.test_gap_analysis",
        "prompt.test_generation",
        "prompt.test_review",
    },
    "continuous-documentation": {
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    },
}

CONTINUOUS_THRESHOLD_STOP_REASONS: dict[str, str] = {
    "continuous-refactor": "Workflow continuous-refactor found only [MINOR] refactor ideas in the latest LOOP_RESULT report; stopping.",
    "continuous-test-generation": "Workflow continuous-test-generation found only [MINOR] test gaps in the latest gap analysis report; stopping.",
    "continuous-documentation": "Workflow continuous-documentation found only [MINOR] documentation findings in the latest LOOP_RESULT report; stopping.",
}

CONTINUOUS_APPROVAL_EXECUTE_PROMPTS: dict[str, set[str]] = {
    "continuous-refactor": {"prompt.refactor_execute"},
    "continuous-test-generation": {"prompt.test_generation"},
    "continuous-documentation": {"prompt.docs_gap_fix", "prompt.docs_refactor_fix"},
}


def _role_for_prompt_id(prompt_id: str) -> Role | None:
    return PROMPT_ROLE_MAP.get(prompt_id)

def _extract_idea_impact_tags(value: Any) -> set[str]:
    if not isinstance(value, str) or not value:
        return set()
    return {match.group(1).upper() for match in IDEA_IMPACT_TAG_RE.finditer(value)}


def _top_findings_from_loop_result(payload: dict[str, Any]) -> list[dict[str, Any]]:
    report = payload.get("report")
    if not isinstance(report, dict):
        return []
    top_findings = report.get("top_findings")
    if not isinstance(top_findings, list):
        return []
    return [finding for finding in top_findings if isinstance(finding, dict)]


def _idea_impact_tags_from_loop_result(payload: dict[str, Any]) -> set[str]:
    observed_tags: set[str] = set()
    for finding in _top_findings_from_loop_result(payload):
        for key in ("title", "evidence", "action"):
            observed_tags.update(_extract_idea_impact_tags(finding.get(key)))
    return observed_tags


def _minor_ideas_from_loop_result(payload: dict[str, Any]) -> tuple[MinorIdea, ...]:
    ideas: list[MinorIdea] = []
    for idx, finding in enumerate(_top_findings_from_loop_result(payload), start=1):
        ideas.append(
            MinorIdea(
                idea_id=idx,
                impact=str(finding.get("impact", "MINOR")).strip().upper() or "MINOR",
                title=str(finding.get("title", "")).strip(),
                evidence=str(finding.get("evidence", "")).strip(),
                action=str(finding.get("action", "")).strip(),
            )
        )
    return tuple(ideas)


def _minor_idea_digest(ideas: tuple[MinorIdea, ...]) -> str:
    serial = [
        {
            "impact": idea.impact,
            "title": idea.title,
            "evidence": idea.evidence,
            "action": idea.action,
        }
        for idea in ideas
    ]
    blob = json.dumps(serial, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _minor_ideas_to_payload(
    ideas: tuple[MinorIdea, ...],
    *,
    selected_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    selected = selected_ids or set()
    return [
        {
            "id": idea.idea_id,
            "impact": idea.impact,
            "title": idea.title,
            "evidence": idea.evidence,
            "action": idea.action,
            "selected": idea.idea_id in selected,
        }
        for idea in ideas
    ]


def _continuous_stop_gate_applies(workflow: str, prompt_id: str | None) -> bool:
    if workflow == "continuous-refactor":
        return prompt_id in CONTINUOUS_APPROVAL_EXECUTE_PROMPTS.get(workflow, set())
    return True


def _continuous_workflow_minor_stop_context(
    repo_root: Path,
    workflow: str,
) -> ContinuousMinorStopContext | None:
    if workflow not in CONTINUOUS_THRESHOLD_STOP_REASONS:
        return None

    payload, error = _load_loop_result_record(repo_root)
    if error or payload is None:
        return None

    observed_tags = _idea_impact_tags_from_loop_result(payload)
    if not observed_tags:
        return None
    if observed_tags.intersection({"MAJOR", "MODERATE"}):
        return None
    if not observed_tags.issubset({"MINOR"}):
        return None

    if workflow == "continuous-test-generation":
        loop_name = str(payload.get("loop", "")).strip().lower()
        if loop_name and loop_name not in {"design", "implement", "stop"}:
            return None

    ideas = _minor_ideas_from_loop_result(payload)
    if not ideas:
        return None

    return ContinuousMinorStopContext(
        workflow=workflow,
        reason=CONTINUOUS_THRESHOLD_STOP_REASONS[workflow],
        ideas=ideas,
        ideas_digest=_minor_idea_digest(ideas),
    )


def _load_continuous_approvals(repo_root: Path) -> dict[str, Any]:
    path = _continuous_approval_path(repo_root)
    if not path.exists():
        return {"approvals": {}}
    try:
        raw = json.loads(_read_text(path))
    except (json.JSONDecodeError, OSError):
        return {"approvals": {}}
    if not isinstance(raw, dict):
        return {"approvals": {}}
    approvals = raw.get("approvals")
    if not isinstance(approvals, dict):
        raw["approvals"] = {}
    return raw


def _save_continuous_approvals(repo_root: Path, payload: dict[str, Any]) -> None:
    path = _continuous_approval_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_approved_ids(raw: Any, max_id: int) -> list[int]:
    if not isinstance(raw, list):
        return []
    cleaned: list[int] = []
    for item in raw:
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            value = item
        elif isinstance(item, str) and item.strip().isdigit():
            value = int(item.strip())
        else:
            continue
        if 1 <= value <= max_id and value not in cleaned:
            cleaned.append(value)
    return cleaned


def _lookup_matching_continuous_approval(
    repo_root: Path,
    workflow: str,
    context: ContinuousMinorStopContext,
) -> list[int]:
    payload = _load_continuous_approvals(repo_root)
    approvals_raw = payload.get("approvals")
    approvals = approvals_raw if isinstance(approvals_raw, dict) else {}
    entry = approvals.get(workflow)
    if not isinstance(entry, dict):
        return []

    expected_state_hash = _state_sha256(repo_root)
    if str(entry.get("state_sha256", "")).strip() != expected_state_hash:
        approvals.pop(workflow, None)
        payload["approvals"] = approvals
        _save_continuous_approvals(repo_root, payload)
        return []

    if str(entry.get("ideas_digest", "")).strip() != context.ideas_digest:
        approvals.pop(workflow, None)
        payload["approvals"] = approvals
        _save_continuous_approvals(repo_root, payload)
        return []

    approved_ids = _normalize_approved_ids(entry.get("approved_ids"), len(context.ideas))
    if not approved_ids:
        approvals.pop(workflow, None)
        payload["approvals"] = approvals
        _save_continuous_approvals(repo_root, payload)
        return []
    return approved_ids


def _store_continuous_approval(
    repo_root: Path,
    workflow: str,
    context: ContinuousMinorStopContext,
    approved_ids: list[int],
) -> None:
    payload = _load_continuous_approvals(repo_root)
    approvals_raw = payload.get("approvals")
    approvals = approvals_raw if isinstance(approvals_raw, dict) else {}
    approvals[workflow] = {
        "approved_ids": approved_ids,
        "ideas_digest": context.ideas_digest,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "state_sha256": _state_sha256(repo_root),
    }
    payload["approvals"] = approvals
    _save_continuous_approvals(repo_root, payload)


def _clear_continuous_approval(repo_root: Path, workflow: str) -> None:
    payload = _load_continuous_approvals(repo_root)
    approvals_raw = payload.get("approvals")
    approvals = approvals_raw if isinstance(approvals_raw, dict) else {}
    if workflow not in approvals:
        return
    approvals.pop(workflow, None)
    payload["approvals"] = approvals
    _save_continuous_approvals(repo_root, payload)


def _parse_approval_ids_arg(raw: str) -> list[int]:
    tokens = [token for token in re.split(r"[,\s]+", raw.strip()) if token]
    if not tokens:
        raise ValueError("No idea IDs provided.")
    approved_ids: list[int] = []
    for token in tokens:
        if not token.isdigit():
            raise ValueError(f"Invalid idea id '{token}'; use positive integers.")
        value = int(token)
        if value < 1:
            raise ValueError(f"Invalid idea id '{token}'; use positive integers.")
        if value not in approved_ids:
            approved_ids.append(value)
    return approved_ids


def _continuous_refactor_should_stop(repo_root: Path) -> tuple[bool, str | None]:
    context = _continuous_workflow_minor_stop_context(repo_root, "continuous-refactor")
    if context is None:
        return (False, None)
    return (True, context.reason)


def _continuous_test_generation_should_stop(repo_root: Path) -> tuple[bool, str | None]:
    context = _continuous_workflow_minor_stop_context(repo_root, "continuous-test-generation")
    if context is None:
        return (False, None)
    return (True, context.reason)


def _continuous_documentation_should_stop(repo_root: Path) -> tuple[bool, str | None]:
    context = _continuous_workflow_minor_stop_context(repo_root, "continuous-documentation")
    if context is None:
        return (False, None)
    return (True, context.reason)


def _continuous_workflow_should_stop(repo_root: Path, workflow: str) -> tuple[bool, str | None]:
    context = _continuous_workflow_minor_stop_context(repo_root, workflow)
    if context is None:
        return (False, None)
    return (True, context.reason)


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


def _continuous_workflow_blocking_decision(state: StateInfo) -> tuple[Role, str] | None:
    """Return blocking override for continuous workflows, if any.

    Continuous workflow mode intentionally ignores normal checkpoint-plan state routing
    and only yields to blocking states/issues.
    """
    if state.status == "BLOCKED":
        return ("issues_triage", "Checkpoint status is BLOCKED.")

    blocker_issues = [i for i in state.issues if i.impact == "BLOCKER"]
    if blocker_issues:
        all_human_owned = all(i.owner and i.owner.lower() == "human" for i in blocker_issues)
        if all_human_owned:
            titles = "; ".join(i.issue_id or i.title for i in blocker_issues)
            return (
                "stop",
                f"All BLOCKER issues are owner: human — agent cannot proceed unilaterally. "
                f"Resolve: {titles}",
            )
        return ("issues_triage", "BLOCKER issue present.")

    decision_issues = [i for i in state.issues if i.status == "DECISION_REQUIRED"]
    if decision_issues:
        titles = "; ".join(i.issue_id or i.title for i in decision_issues)
        return (
            "stop",
            f"Human decision required before proceeding. "
            f"Resolve DECISION_REQUIRED issue(s): {titles}",
        )

    return None


def _resolve_next_prompt_selection(
    state: StateInfo,
    repo_root: Path,
    workflow: str | None,
) -> tuple[Role, str, str, str]:
    base_role, base_reason, prompt_override = _recommend_next(state, repo_root)
    base_prompt_id = prompt_override or PROMPT_MAP[base_role]["id"]
    base_prompt_title = PROMPT_MAP[base_role]["title"]

    if not workflow:
        return (base_role, base_prompt_id, base_prompt_title, base_reason)

    if workflow in CONTINUOUS_OVERRIDE_WORKFLOWS:
        blocking_decision = _continuous_workflow_blocking_decision(state)
        if blocking_decision is not None:
            role, reason = blocking_decision
            return (role, PROMPT_MAP[role]["id"], PROMPT_MAP[role]["title"], reason)
    elif base_role == "stop":
        return (base_role, base_prompt_id, base_prompt_title, base_reason)

    strict_cycle_workflow = workflow in {
        "continuous-refactor",
        "continuous-test-generation",
        "continuous-documentation",
        "refactor-cycle",
    }
    strict_cycle_allowed = base_role in {"implement", "review"} or workflow in CONTINUOUS_OVERRIDE_WORKFLOWS
    reason_prefix = base_reason
    if workflow in CONTINUOUS_OVERRIDE_REASON_PREFIX:
        reason_prefix = CONTINUOUS_OVERRIDE_REASON_PREFIX[workflow]

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
        if strict_cycle_workflow:
            workflow_prompt_id = _select_workflow_prompt(None)
            raw_workflow_prompt_id = workflow_prompt_id
        else:
            workflow_prompt_id = _select_workflow_prompt(allowed_prompt_ids)
            raw_workflow_prompt_id = _select_workflow_prompt(None)
    finally:
        os.chdir(current_cwd)

    if workflow in CONTINUOUS_WORKFLOW_ALLOWED_PROMPTS:
        allowed_prompts = CONTINUOUS_WORKFLOW_ALLOWED_PROMPTS[workflow]
        if workflow_prompt_id and workflow_prompt_id not in allowed_prompts:
            allowed_list = ", ".join(sorted(allowed_prompts))
            raise RuntimeError(
                f"Workflow {workflow} selected unsupported prompt id '{workflow_prompt_id}'. "
                f"{workflow} only supports {allowed_list}."
            )

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

    workflow_title = catalog_index.get(workflow_prompt_id, base_prompt_title)

    if workflow in CONTINUOUS_WORKFLOW_ALLOWED_PROMPTS:
        stop_context = _continuous_workflow_minor_stop_context(repo_root, workflow)
        if stop_context is not None and _continuous_stop_gate_applies(workflow, workflow_prompt_id):
            approved_ids = _lookup_matching_continuous_approval(repo_root, workflow, stop_context)
            if not approved_ids:
                return (
                    "stop",
                    "stop",
                    f"Stop ({workflow} threshold reached)",
                    stop_context.reason,
                )
            approved_label = ",".join(str(value) for value in approved_ids)
            return (
                workflow_role,
                workflow_prompt_id,
                workflow_title,
                f"{reason_prefix} Workflow {workflow} selected {workflow_prompt_id} (strict cycle, approved minor ideas: {approved_label}).",
            )

    if strict_cycle_workflow:
        if not strict_cycle_allowed:
            return (
                base_role,
                base_prompt_id,
                base_prompt_title,
                f"{reason_prefix} Workflow {workflow} selected {workflow_prompt_id}, "
                f"but dispatcher priority role is {base_role}; using dispatcher role {base_role}.",
            )
        return (
            workflow_role,
            workflow_prompt_id,
            workflow_title,
            f"{reason_prefix} Workflow {workflow} selected {workflow_prompt_id} (strict cycle).",
        )

    if workflow_role != base_role:
        return (
            base_role,
            base_prompt_id,
            base_prompt_title,
            f"{base_reason} Workflow {workflow} produced mismatched role {workflow_role}; "
            f"using dispatcher role {base_role}.",
        )

    return (
        workflow_role,
        workflow_prompt_id,
        workflow_title,
        f"{base_reason} Workflow {workflow} selected {workflow_prompt_id}.",
    )


def cmd_validate(args: argparse.Namespace) -> int:
    res = validate(Path(args.repo_root), strict=args.strict, strict_complexity=args.strict_complexity)

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
            "complexity_warnings": list(res.plan_check.complexity_warnings),
        }

    print(_render_output(payload, args.format))
    return 0 if res.ok else 2


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)

    role, reason, prompt_override = _recommend_next(state, repo_root)
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
        "recommended_prompt_id": prompt_override or PROMPT_MAP[role]["id"],
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

    workflow_name = str(args.workflow or "").strip()
    continuous_stop_context: ContinuousMinorStopContext | None = None
    approved_ids_applied: list[int] = []
    if workflow_name in CONTINUOUS_OVERRIDE_WORKFLOWS:
        continuous_stop_context = _continuous_workflow_minor_stop_context(repo_root, workflow_name)
        if (
            role != "stop"
            and continuous_stop_context is not None
            and _continuous_stop_gate_applies(workflow_name, prompt_id)
        ):
            approved_ids_applied = _lookup_matching_continuous_approval(
                repo_root,
                workflow_name,
                continuous_stop_context,
            )

    stop_has_minor_ideas = (
        role == "stop"
        and continuous_stop_context is not None
        and reason == continuous_stop_context.reason
    )

    if role == "stop":
        if stop_has_minor_ideas and continuous_stop_context is not None:
            report = {
                "top_findings": [
                    {
                        "impact": idea.impact,
                        "title": idea.title,
                        "evidence": idea.evidence,
                        "action": idea.action,
                    }
                    for idea in continuous_stop_context.ideas
                ]
            }
            _write_stop_loop_result(
                repo_root,
                state,
                reason,
                report=report,
                extra_fields={
                    "ideas_digest": continuous_stop_context.ideas_digest,
                    "workflow": workflow_name,
                },
            )
        else:
            _write_stop_loop_result(repo_root, state, reason)

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

    if stop_has_minor_ideas and continuous_stop_context is not None:
        payload["approval_required"] = True
        payload["minor_ideas"] = _minor_ideas_to_payload(continuous_stop_context.ideas)
        payload["minor_ideas_digest"] = continuous_stop_context.ideas_digest
        payload["approval_command"] = (
            "python3 tools/agentctl.py --repo-root . --format json "
            f"workflow-approve --workflow {workflow_name} --ids 1"
        )

    if approved_ids_applied and continuous_stop_context is not None:
        selected = set(approved_ids_applied)
        payload["approval_applied"] = True
        payload["approved_minor_idea_ids"] = approved_ids_applied
        payload["approved_minor_ideas"] = _minor_ideas_to_payload(
            continuous_stop_context.ideas,
            selected_ids=selected,
        )
        _clear_continuous_approval(repo_root, workflow_name)

    # Parallel dispatch: add recommended_roles list (always present; N=1 is backward compat)
    if args.workflow in CONTINUOUS_OVERRIDE_WORKFLOWS:
        if role == "stop":
            payload["recommended_roles"] = []
        else:
            payload["recommended_roles"] = [
                {
                    "checkpoint": state.checkpoint,
                    "role": role,
                    "prompt_id": prompt_id,
                    "reason": reason,
                }
            ]
    else:
        parallel_n = getattr(args, "parallel", 1) or 1
        plan_path = repo_root / ".vibe" / "PLAN.md"
        plan_text = _read_text(plan_path) if plan_path.exists() else ""
        ready_cps = _get_ready_checkpoints(plan_text, state)[:parallel_n]
        implement_prompt = PROMPT_MAP.get("implement", {})
        recommended_roles = [
            {
                "checkpoint": cp_id,
                "role": "implement",
                "prompt_id": implement_prompt.get("id", "prompt.checkpoint_implementation"),
                "reason": f"Checkpoint {cp_id} is ready (deps satisfied).",
            }
            for cp_id in ready_cps
        ]
        payload["recommended_roles"] = recommended_roles

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


def cmd_workflow_approve(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    workflow = str(args.workflow).strip()

    if workflow not in CONTINUOUS_OVERRIDE_WORKFLOWS:
        payload = {
            "ok": False,
            "error": (
                f"Unsupported workflow '{workflow}'. "
                f"Expected one of: {', '.join(sorted(CONTINUOUS_OVERRIDE_WORKFLOWS))}."
            ),
        }
        print(_render_output(payload, args.format))
        return 2

    stop_context = _continuous_workflow_minor_stop_context(repo_root, workflow)
    if stop_context is None:
        payload = {
            "ok": False,
            "error": (
                f"No pending [MINOR]-only findings available for workflow '{workflow}'. "
                "Run the workflow until it halts on a minor-only threshold first."
            ),
        }
        print(_render_output(payload, args.format))
        return 2

    try:
        approved_ids = _parse_approval_ids_arg(args.ids)
    except ValueError as exc:
        payload = {"ok": False, "error": str(exc)}
        print(_render_output(payload, args.format))
        return 2

    max_id = len(stop_context.ideas)
    invalid = [value for value in approved_ids if value > max_id]
    if invalid:
        payload = {
            "ok": False,
            "error": (
                f"Approved ids out of range: {invalid}. "
                f"Valid idea ids are 1..{max_id}."
            ),
            "minor_ideas": _minor_ideas_to_payload(stop_context.ideas),
        }
        print(_render_output(payload, args.format))
        return 2

    _store_continuous_approval(repo_root, workflow, stop_context, approved_ids)
    selected = set(approved_ids)
    payload = {
        "ok": True,
        "workflow": workflow,
        "approved_minor_idea_ids": approved_ids,
        "approved_minor_ideas": _minor_ideas_to_payload(
            stop_context.ideas,
            selected_ids=selected,
        ),
        "minor_ideas_digest": stop_context.ideas_digest,
        "next_step": (
            "Run agentctl next with the same --workflow to continue "
            "using the approved minor ideas."
        ),
    }
    print(_render_output(payload, args.format))
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


def cmd_plan(args: argparse.Namespace) -> int:
    """Handle `agentctl plan` — resolve config, validate, and run (or dry-run) the plan pipeline."""
    from plan_pipeline import PipelineConfigError, resolve_config

    repo_root = Path(args.repo_root)
    try:
        config = resolve_config(
            repo_root,
            problem_statement=getattr(args, "problem_statement", None),
            provider=getattr(args, "provider", None),
            dry_run=getattr(args, "dry_run", False),
            output_path=getattr(args, "output", None),
            overwrite=getattr(args, "overwrite", False),
        )
    except PipelineConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if config.dry_run:
        print(f"(dry run \u2014 no files written)")
        print(f"  problem_statement : {config.problem_statement}")
        print(f"  provider          : {config.provider if config.provider else '(not set)'}")
        print(f"  output_path       : {config.output_path}")
        return 0

    # Full pipeline execution (checkpoints 23.2–23.3)
    from plan_pipeline import render_plan_md, run_plan_pipeline

    resume_run_id = getattr(args, "resume_run_id", None)
    try:
        result = run_plan_pipeline(
            config,
            repo_root,
            resume_run_id=resume_run_id,
        )
    except Exception as exc:
        print(f"ERROR: Pipeline failed: {exc}", file=sys.stderr)
        return 1

    plan_text, warnings = render_plan_md(result)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    n_stages = len(result.stages)
    n_checkpoints = len(result.checkpoints)
    n_warnings = len(warnings)
    summary = (
        f"Generated {n_stages} stage{'s' if n_stages != 1 else ''}, "
        f"{n_checkpoints} checkpoint{'s' if n_checkpoints != 1 else ''}."
        + (f" {n_warnings} complexity warning{'s' if n_warnings != 1 else ''}." if n_warnings else "")
    )
    print(summary)

    out_path = Path(config.output_path)
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(plan_text, encoding="utf-8")
    print(f"Written to {out_path}")
    return 0


def cmd_feedback_validate(args: argparse.Namespace) -> int:
    """Validate .vibe/FEEDBACK.md schema and print diagnostics."""
    repo_root = Path(args.repo_root).resolve()
    feedback_path = repo_root / ".vibe" / "FEEDBACK.md"

    if not feedback_path.exists():
        print("(no FEEDBACK.md found - nothing to validate)")
        return 0

    text = feedback_path.read_text(encoding="utf-8")
    entries, errors = _parse_feedback_file(text)

    if errors:
        for err in errors:
            print(err)
        return 2

    unprocessed = sum(1 for e in entries if not e.checked)
    print(f"Feedback file OK ({len(entries)} entries, {unprocessed} unprocessed)")
    return 0


def cmd_feedback_inject(args: argparse.Namespace) -> int:
    """Inject unprocessed FEEDBACK.md entries as Issues into STATE.md."""
    repo_root = Path(args.repo_root).resolve()
    feedback_path = repo_root / ".vibe" / "FEEDBACK.md"
    state_path = repo_root / ".vibe" / "STATE.md"
    dry_run: bool = getattr(args, "dry_run", False)

    if not feedback_path.exists():
        print("(no FEEDBACK.md found - nothing to inject)")
        return 0

    feedback_text = feedback_path.read_text(encoding="utf-8")
    entries, errors = _parse_feedback_file(feedback_text)
    if errors:
        print("FEEDBACK.md has validation errors. Run 'agentctl feedback validate' to see details.")
        for err in errors:
            print(f"  {err}")
        return 2

    to_inject = [e for e in entries if not e.processed]
    if not to_inject:
        print("Nothing to inject (all entries already processed).")
        return 0

    state_text = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    next_id = _next_issue_id(state_text)

    assignments: list[tuple["FeedbackEntry", str]] = []
    for entry in to_inject:
        issue_id = f"ISSUE-{next_id:03d}"
        assignments.append((entry, issue_id))
        next_id += 1

    if dry_run:
        print(f"(dry run) Would inject {len(assignments)} feedback entries:")
        for entry, issue_id in assignments:
            print(f"  {entry.feedback_id} -> {issue_id} (Impact: {entry.impact})")
        return 0

    # Build issue blocks and inject
    issue_blocks = [_feedback_entry_to_issue_block(entry, iid) for entry, iid in assignments]
    new_state = _inject_into_state_md(state_text, issue_blocks)
    state_path.write_text(new_state, encoding="utf-8")

    # Mark feedback entries as processed
    new_feedback = feedback_text
    for entry, issue_id in assignments:
        new_feedback = _mark_feedback_processed(new_feedback, entry.feedback_id, issue_id)
    feedback_path.write_text(new_feedback, encoding="utf-8")

    print(f"Injected {len(assignments)} feedback entries as Issues:")
    for entry, issue_id in assignments:
        print(f"  {entry.feedback_id} -> {issue_id} (Impact: {entry.impact})")
    return 0


def cmd_feedback_ack(args: argparse.Namespace) -> int:
    """Archive processed FEEDBACK.md entries to HISTORY.md and clear them."""
    repo_root = Path(args.repo_root).resolve()
    feedback_path = repo_root / ".vibe" / "FEEDBACK.md"
    history_path = repo_root / ".vibe" / "HISTORY.md"

    if not feedback_path.exists():
        print("(no FEEDBACK.md found - nothing to archive)")
        return 0

    feedback_text = feedback_path.read_text(encoding="utf-8")
    entries, errors = _parse_feedback_file(feedback_text)
    if errors:
        print("FEEDBACK.md has validation errors. Run 'agentctl feedback validate' to see details.")
        for err in errors:
            print(f"  {err}")
        return 2

    to_archive = [e for e in entries if e.processed]
    if not to_archive:
        print("Nothing to archive.")
        return 0

    today = __import__("datetime").date.today().isoformat()

    # Build archive lines
    archive_lines: list[str] = []
    for entry in to_archive:
        # Extract ISSUE-ID from FEEDBACK.md line (look for <!-- processed: ISSUE-NNN -->)
        issue_id = _extract_issue_id_for_feedback(feedback_text, entry.feedback_id)
        arrow = "->"
        line = (
            f"- {today} {entry.feedback_id} {arrow} {issue_id}: "
            f"{entry.description} (Type: {entry.type}, Impact: {entry.impact})"
        )
        archive_lines.append(line)

    # Append to HISTORY.md under ## Feedback archive section
    history_text = history_path.read_text(encoding="utf-8") if history_path.exists() else ""
    history_text = _append_to_feedback_archive(history_text, archive_lines)
    history_path.write_text(history_text, encoding="utf-8")

    # Remove archived entries from FEEDBACK.md (keep unprocessed ones)
    new_feedback = _remove_processed_entries(feedback_text)
    feedback_path.write_text(new_feedback, encoding="utf-8")

    print(f"Archived {len(to_archive)} feedback entries to HISTORY.md.")
    return 0


def _extract_issue_id_for_feedback(feedback_text: str, feedback_id: str) -> str:
    """Extract ISSUE-ID from the processed comment for a given FEEDBACK-ID line."""
    import re
    pattern = re.compile(
        r"- \[x\] " + re.escape(feedback_id) + r".*?<!--\s*processed:\s*(ISSUE-\d+)\s*-->",
        re.MULTILINE,
    )
    m = pattern.search(feedback_text)
    return m.group(1) if m else "ISSUE-???"


def _append_to_feedback_archive(history_text: str, archive_lines: list[str]) -> str:
    """Append archive lines to '## Feedback archive' section in HISTORY.md text."""
    section_header = "## Feedback archive"
    block = "\n".join(archive_lines)
    if section_header in history_text:
        # Insert after the section header line
        parts = history_text.split(section_header, 1)
        return parts[0] + section_header + "\n\n" + block + "\n" + parts[1].lstrip("\n")
    else:
        # Create section at end
        sep = "\n\n" if history_text.rstrip() else ""
        return history_text.rstrip() + sep + "\n## Feedback archive\n\n" + block + "\n"


def _remove_processed_entries(feedback_text: str) -> str:
    """Remove processed (checked + processed comment) entries from FEEDBACK.md text."""
    import re
    # Match a feedback entry block: starts with "- [x] FEEDBACK-NNN:" and the processed comment,
    # followed by indented continuation lines.
    pattern = re.compile(
        r"- \[x\] FEEDBACK-\d+:.*?<!-- processed:.*?-->\n(?:  [^\n]*\n)*",
        re.MULTILINE,
    )
    return pattern.sub("", feedback_text)


def _parse_checkpoint_titles(plan_text: str) -> dict[str, str]:
    """Extract title strings from checkpoint headings in PLAN.md.

    Returns dict mapping normalized checkpoint_id -> title text (after the em-dash/hyphen separator).
    Checkpoints with no title separator map to empty string.
    """
    titles: dict[str, str] = {}
    pat = re.compile(
        rf"^\s*#{{3,6}}\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?(?P<id>{CHECKPOINT_ID_PATTERN})"
        r"(?:\s*[\u2014\-]+\s*(?P<title>.+?))?\s*$"
    )
    for _, line, is_visible in _iter_visible_markdown_lines(plan_text):
        if not is_visible:
            continue
        m = pat.match(line)
        if not m:
            continue
        raw_id = m.group("id")
        try:
            cp_id = normalize_checkpoint_id(raw_id)
        except ValueError:
            cp_id = raw_id
        raw_title = m.group("title")
        titles[cp_id] = raw_title.strip() if raw_title else ""
    return titles


def _compute_dag_node_status(plan_text: str, checkpoint_id: str) -> str:
    """Compute DAG node status: DONE | SKIP | READY | DEP_BLOCKED."""
    if _is_checkpoint_marked_done(plan_text, checkpoint_id):
        return "DONE"
    if _is_checkpoint_skipped(plan_text, checkpoint_id):
        return "SKIP"
    if _get_unmet_deps(plan_text, checkpoint_id):
        return "DEP_BLOCKED"
    return "READY"


def _get_ready_checkpoints(plan_text: str, state: "StateInfo") -> list[str]:
    """Return all dep-satisfied, not-yet-done checkpoints in document order.

    A checkpoint is 'ready' iff it is not DONE, not SKIP, and all its deps are satisfied.
    The state parameter is accepted for interface consistency and future use.
    """
    cp_ids = _parse_plan_checkpoint_ids(plan_text)
    return [cp_id for cp_id in cp_ids if _compute_dag_node_status(plan_text, cp_id) == "READY"]


def cmd_dag(args: argparse.Namespace) -> int:
    """Render the checkpoint dependency graph as JSON or ASCII tree."""
    repo_root = Path(args.repo_root)
    plan_path = repo_root / ".vibe" / "PLAN.md"
    dag_format = getattr(args, "dag_format", "ascii")

    if not plan_path.exists():
        if dag_format == "json":
            print(json.dumps({"nodes": [], "edges": [], "error": "PLAN.md not found"}, indent=2))
        else:
            print("No .vibe/PLAN.md found.")
        return 1

    plan_text = _read_text(plan_path)
    cp_ids = _parse_plan_checkpoint_ids(plan_text)
    titles = _parse_checkpoint_titles(plan_text)
    deps_map, _ = _parse_checkpoint_dependencies(plan_text)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    for cp_id in cp_ids:
        status = _compute_dag_node_status(plan_text, cp_id)
        title = titles.get(cp_id, "")
        node_deps = deps_map.get(cp_id, [])
        nodes.append({"id": cp_id, "title": title, "status": status, "deps": node_deps})
        for dep in node_deps:
            edges.append({"from": dep, "to": cp_id})

    if dag_format == "json":
        print(json.dumps({"nodes": nodes, "edges": edges}, indent=2))
        return 0

    # ASCII output
    _STATUS_ICONS = {"DONE": "[+]", "SKIP": "[-]", "READY": "[>]", "DEP_BLOCKED": "[!]"}
    for node in nodes:
        status = node["status"]
        cp_id = node["id"]
        title = node["title"]
        icon = _STATUS_ICONS.get(status, "[?]")
        sep = " -- " if title else ""
        label = f"{icon} {cp_id}{sep}{title}"
        if status == "READY":
            label += " (ready)"
        elif status == "DEP_BLOCKED":
            unmet = _get_unmet_deps(plan_text, cp_id)
            label += f" (blocked: {', '.join(unmet)})"
        print(label)

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
    pv.add_argument(
        "--strict-complexity",
        dest="strict_complexity",
        action="store_true",
        help="Treat checkpoint complexity budget violations as errors (fail if a checkpoint exceeds item limits).",
    )
    pv.set_defaults(fn=cmd_validate, strict_complexity=False)

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
    pn.add_argument(
        "--parallel",
        type=int,
        default=None,
        metavar="N",
        help="Return up to N simultaneously-runnable (dep-satisfied) checkpoints (N>=1). "
             "Adds recommended_roles list to output; N=1 is identical to default behavior.",
    )
    pn.set_defaults(fn=cmd_next)

    plr = sub.add_parser("loop-result", help="Record and validate LOOP_RESULT output against current STATE.md.")
    src = plr.add_mutually_exclusive_group(required=True)
    src.add_argument("--line", help='Raw LOOP_RESULT line (for example: LOOP_RESULT: {"loop":"implement",...}).')
    src.add_argument("--json-payload", help="Raw LOOP_RESULT JSON object string.")
    src.add_argument("--stdin", action="store_true", help="Read LOOP_RESULT payload from stdin.")
    plr.set_defaults(fn=cmd_loop_result)

    pwa = sub.add_parser(
        "workflow-approve",
        help="Approve numbered minor findings for a continuous workflow threshold stop.",
    )
    pwa.add_argument(
        "--workflow",
        required=True,
        choices=tuple(sorted(CONTINUOUS_OVERRIDE_WORKFLOWS)),
        help="Target continuous workflow name.",
    )
    pwa.add_argument(
        "--ids",
        required=True,
        help="Comma/space-separated idea ids (for example: 1,3,5).",
    )
    pwa.set_defaults(fn=cmd_workflow_approve)

    pc = sub.add_parser("add-checkpoint", help="Insert a checkpoint from a template into PLAN.md.")
    pc.add_argument("--template", required=True, help="Template name (file stem).")
    pc.add_argument("params", nargs=argparse.REMAINDER, help="Template parameters.")
    pc.set_defaults(fn=cmd_add_checkpoint)

    pp = sub.add_parser("plan", help="Generate a PLAN.md from a problem statement using the plan pipeline.")
    pp.add_argument(
        "--problem-statement",
        dest="problem_statement",
        help="High-level description of what to build (required unless set in config).",
    )
    pp.add_argument(
        "--provider",
        help="LLM provider to use (e.g. anthropic, openai). Overrides config file.",
    )
    pp.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Validate config and print resolved settings without writing any files.",
    )
    pp.add_argument(
        "--output",
        default=None,
        help="Path to write the generated PLAN.md (default: .vibe/PLAN.md).",
    )
    pp.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    pp.add_argument(
        "--resume",
        dest="resume_run_id",
        default=None,
        metavar="RUN_ID",
        help="Resume a previous pipeline run by run ID, reusing completed step outputs.",
    )
    pp.set_defaults(fn=cmd_plan)

    pfb = sub.add_parser("feedback", help="Manage .vibe/FEEDBACK.md entries.")
    pfb_sub = pfb.add_subparsers(dest="feedback_cmd", required=True)

    pfb_v = pfb_sub.add_parser("validate", help="Validate FEEDBACK.md schema and print diagnostics.")
    pfb_v.set_defaults(fn=cmd_feedback_validate)

    pfb_i = pfb_sub.add_parser("inject", help="Inject unprocessed FEEDBACK.md entries as Issues into STATE.md.")
    pfb_i.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Print what would be injected without modifying files.",
    )
    pfb_i.set_defaults(fn=cmd_feedback_inject)

    pfb_a = pfb_sub.add_parser("ack", help="Archive processed FEEDBACK.md entries to HISTORY.md.")
    pfb_a.set_defaults(fn=cmd_feedback_ack)

    pdag = sub.add_parser("dag", help="Render the checkpoint dependency graph.")
    pdag.add_argument(
        "--format",
        dest="dag_format",
        choices=("json", "ascii"),
        default="ascii",
        help="Output format: json (structured) or ascii (default, human-readable tree).",
    )
    pdag.set_defaults(fn=cmd_dag)

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
