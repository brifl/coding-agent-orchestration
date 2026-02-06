#!/usr/bin/env python3
"""Validate and summarize .vibe/STATE.md and .vibe/PLAN.md."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ALLOWED_STATUS = {"NOT_STARTED", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE"}
ALLOWED_ISSUE_IMPACT = {"QUESTION", "MINOR", "MAJOR", "BLOCKER"}
ALLOWED_ISSUE_STATUS = {"OPEN", "IN_PROGRESS", "BLOCKED", "RESOLVED"}

REQUIRED_STATE_SECTIONS = (
    "Current focus",
    "Objective (current checkpoint)",
    "Deliverables (current checkpoint)",
    "Acceptance (current checkpoint)",
    "Work log (current session)",
    "Evidence",
    "Active issues",
    "Decisions",
)

REQUIRED_CHECKPOINT_FIELDS = (
    "Objective",
    "Deliverables",
    "Acceptance",
    "Demo commands",
    "Evidence",
)

_STAGE_RE = re.compile(r"^\d+[A-Za-z]*$")
_CHECKPOINT_RE = re.compile(r"^(\d+[A-Za-z]*)\.(\d+)$")


@dataclass(frozen=True)
class Issue:
    issue_id: str
    title: str
    impact: str | None
    status: str | None
    owner: str | None
    unblock_condition: str | None
    evidence_needed: str | None


@dataclass(frozen=True)
class StateSummary:
    path: str
    stage: str | None
    checkpoint: str | None
    status: str | None
    sections: list[str]
    issues: list[Issue]


@dataclass(frozen=True)
class CheckpointSummary:
    checkpoint_id: str
    title: str
    stage: str | None
    line: int
    fields_present: list[str]


@dataclass(frozen=True)
class StageSummary:
    stage_id: str
    title: str
    line: int
    checkpoint_ids: list[str]


@dataclass(frozen=True)
class PlanSummary:
    path: str
    stages: list[StageSummary]
    checkpoints: list[CheckpointSummary]


@dataclass(frozen=True)
class TroubleshootResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    state: StateSummary | None
    plan: PlanSummary | None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _section_map(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _normalize_issue_key(raw_key: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", raw_key.strip().lower()).strip("_")
    aliases = {
        "impact": "impact",
        "status": "status",
        "owner": "owner",
        "unblock_condition": "unblock_condition",
        "unblock": "unblock_condition",
        "evidence_needed": "evidence_needed",
        "evidence": "evidence_needed",
    }
    return aliases.get(normalized)


def _parse_issues(active_issue_lines: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    issue_head = re.compile(r"^\s*-\s*\[\s*([xX ]?)\s*\]\s*(.+?)\s*$")
    detail_line = re.compile(r"^\s*-\s*(?P<key>[A-Za-z][A-Za-z _-]*)\s*:\s*(?P<val>.+?)\s*$")

    idx = 0
    while idx < len(active_issue_lines):
        line = active_issue_lines[idx]
        head_match = issue_head.match(line)
        if not head_match:
            idx += 1
            continue

        head_text = head_match.group(2).strip()
        parsed_head = re.match(r"(?i)^(ISSUE-[A-Za-z0-9_.-]+)\s*:\s*(.+)$", head_text)
        if not parsed_head:
            idx += 1
            continue

        issue_id = parsed_head.group(1).upper()
        title = parsed_head.group(2).strip()

        fields: dict[str, str] = {}
        scan = idx + 1
        while scan < len(active_issue_lines):
            candidate = active_issue_lines[scan]
            if issue_head.match(candidate):
                break
            detail_match = detail_line.match(candidate)
            if detail_match:
                key = _normalize_issue_key(detail_match.group("key"))
                if key and key not in fields:
                    fields[key] = detail_match.group("val").strip()
            scan += 1

        issues.append(
            Issue(
                issue_id=issue_id,
                title=title,
                impact=fields.get("impact"),
                status=fields.get("status"),
                owner=fields.get("owner"),
                unblock_condition=fields.get("unblock_condition"),
                evidence_needed=fields.get("evidence_needed"),
            )
        )
        idx = scan

    return issues


def _parse_state(path: Path) -> StateSummary:
    text = _read_text(path)
    sections = _section_map(text)
    focus_lines = sections.get("Current focus", [])
    kv: dict[str, str] = {}
    for line in focus_lines:
        match = re.match(r"^\s*-\s*([^:]+):\s*(.+?)\s*$", line)
        if not match:
            continue
        key = re.sub(r"[^a-z0-9]+", "_", match.group(1).strip().lower()).strip("_")
        value = match.group(2).split("<!--", 1)[0].strip()
        kv[key] = value

    active_issue_lines = sections.get("Active issues", [])
    issues = _parse_issues(active_issue_lines)

    return StateSummary(
        path=str(path),
        stage=kv.get("stage"),
        checkpoint=kv.get("checkpoint"),
        status=kv.get("status", "").split()[0].upper() if kv.get("status") else None,
        sections=list(sections.keys()),
        issues=issues,
    )


def _extract_checkpoint_sections(plan_text: str) -> list[tuple[str, str, int, int, str | None]]:
    lines = plan_text.splitlines()
    sections: list[tuple[str, str, int, int, str | None]] = []
    current_stage: str | None = None
    stage_re = re.compile(r"^(#{2,6})\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+([0-9A-Za-z]+)\s*[—–-]?\s*(.*)$")
    cp_re = re.compile(
        r"^(#{3,6})\s+(?:\(\s*(?:DONE|SKIPPED|SKIP)\s*\)\s+)?([0-9A-Za-z]+\.\d+)\s*[—–-]?\s*(.*)$"
    )

    checkpoint_entries: list[tuple[int, int, str, str, str | None]] = []

    for idx, raw in enumerate(lines, start=1):
        stage_match = stage_re.match(raw)
        if stage_match:
            current_stage = stage_match.group(2)
            continue

        cp_match = cp_re.match(raw)
        if cp_match:
            level = len(cp_match.group(1))
            cp_id = cp_match.group(2)
            title = cp_match.group(3).strip()
            checkpoint_entries.append((idx, level, cp_id, title, current_stage))

    for start_line, level, cp_id, title, stage_id in checkpoint_entries:
        end_line = len(lines)
        for candidate_idx in range(start_line, len(lines)):
            raw = lines[candidate_idx]
            heading = re.match(r"^(#{1,6})\s+", raw)
            if heading and len(heading.group(1)) <= level:
                end_line = candidate_idx
                break
        sections.append((cp_id, title, start_line, end_line, stage_id))

    return sections


def _find_fields(section_text: str) -> list[str]:
    found: list[str] = []
    for field in REQUIRED_CHECKPOINT_FIELDS:
        pattern = re.compile(
            rf"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?\s*{re.escape(field)}\s*:?(?:\*\*)?\s*$"
        )
        if pattern.search(section_text):
            found.append(field)
    return found


def _parse_plan(path: Path) -> PlanSummary:
    text = _read_text(path)
    lines = text.splitlines()

    stages: list[StageSummary] = []
    stage_re = re.compile(r"^(#{2,6})\s+(?:\(\s*SKIP\s*\)\s+)?Stage\s+([0-9A-Za-z]+)\s*[—–-]?\s*(.*)$")
    for idx, raw in enumerate(lines, start=1):
        match = stage_re.match(raw)
        if not match:
            continue
        stage_id = match.group(2)
        stage_title = match.group(3).strip()
        stages.append(StageSummary(stage_id=stage_id, title=stage_title, line=idx, checkpoint_ids=[]))

    checkpoint_sections = _extract_checkpoint_sections(text)
    checkpoints: list[CheckpointSummary] = []

    for cp_id, cp_title, start, end, stage_id in checkpoint_sections:
        section_text = "\n".join(lines[start - 1 : end])
        fields = _find_fields(section_text)
        checkpoints.append(
            CheckpointSummary(
                checkpoint_id=cp_id,
                title=cp_title,
                stage=stage_id,
                line=start,
                fields_present=fields,
            )
        )

    stage_index = {stage.stage_id: stage for stage in stages}
    for checkpoint in checkpoints:
        if checkpoint.stage and checkpoint.stage in stage_index:
            stage = stage_index[checkpoint.stage]
            stage.checkpoint_ids.append(checkpoint.checkpoint_id)

    return PlanSummary(path=str(path), stages=stages, checkpoints=checkpoints)


def _validate_state_format(state: StateSummary, errors: list[str], warnings: list[str]) -> None:
    section_set = set(state.sections)
    for required in REQUIRED_STATE_SECTIONS:
        if required not in section_set:
            errors.append(f"STATE missing required section: '{required}'.")

    if not state.stage:
        errors.append("STATE missing '- Stage: <id>' under 'Current focus'.")
    elif not _STAGE_RE.match(state.stage):
        errors.append(f"STATE Stage has invalid format: '{state.stage}'.")

    if not state.checkpoint:
        errors.append("STATE missing '- Checkpoint: <id>' under 'Current focus'.")
    else:
        checkpoint_match = _CHECKPOINT_RE.match(state.checkpoint)
        if checkpoint_match is None:
            errors.append(f"STATE Checkpoint has invalid format: '{state.checkpoint}'.")
        elif state.stage and checkpoint_match.group(1).upper() != state.stage.upper():
            errors.append(
                "STATE Current focus is inconsistent: "
                f"Stage '{state.stage}' does not match Checkpoint '{state.checkpoint}'."
            )

    if not state.status:
        errors.append(
            "STATE missing '- Status: NOT_STARTED|IN_PROGRESS|IN_REVIEW|BLOCKED|DONE' under 'Current focus'."
        )
    elif state.status not in ALLOWED_STATUS:
        allowed = ", ".join(sorted(ALLOWED_STATUS))
        errors.append(f"STATE Status '{state.status}' is invalid. Allowed: {allowed}.")

    for issue in state.issues:
        if issue.impact is None:
            errors.append(f"{issue.issue_id}: missing required issue field 'Impact'.")
        elif issue.impact.upper() not in ALLOWED_ISSUE_IMPACT:
            allowed_impact = ", ".join(sorted(ALLOWED_ISSUE_IMPACT))
            errors.append(
                f"{issue.issue_id}: Impact '{issue.impact}' is invalid. Allowed: {allowed_impact}."
            )

        if issue.status is None:
            errors.append(f"{issue.issue_id}: missing required issue field 'Status'.")
        elif issue.status.upper() not in ALLOWED_ISSUE_STATUS:
            allowed_issue_status = ", ".join(sorted(ALLOWED_ISSUE_STATUS))
            errors.append(
                f"{issue.issue_id}: Status '{issue.status}' is invalid. Allowed: {allowed_issue_status}."
            )

        if not issue.owner:
            errors.append(f"{issue.issue_id}: missing required issue field 'Owner'.")
        if not issue.unblock_condition:
            errors.append(f"{issue.issue_id}: missing required issue field 'Unblock Condition'.")
        if not issue.evidence_needed:
            errors.append(f"{issue.issue_id}: missing required issue field 'Evidence Needed'.")

    if "Active issues" in section_set and not state.issues:
        warnings.append(
            "STATE has no structured ISSUE entries in 'Active issues' (expected '- [ ] ISSUE-<id>: ...')."
        )


def _validate_plan_format(plan: PlanSummary, errors: list[str], _warnings: list[str]) -> None:
    if not plan.stages:
        errors.append("PLAN has no stage headings. Expected '## Stage <id> - <name>'.")

    stage_ids_seen: set[str] = set()
    for stage in plan.stages:
        normalized = stage.stage_id.upper()
        if not _STAGE_RE.match(stage.stage_id):
            errors.append(
                f"PLAN line {stage.line}: Stage id '{stage.stage_id}' is invalid."
            )
        if normalized in stage_ids_seen:
            errors.append(
                f"PLAN line {stage.line}: duplicate Stage id '{stage.stage_id}'."
            )
        stage_ids_seen.add(normalized)

    if not plan.checkpoints:
        errors.append("PLAN has no checkpoint headings. Expected '### <stage>.<n> - <name>'.")

    checkpoint_ids_seen: set[str] = set()
    for checkpoint in plan.checkpoints:
        cp_match = _CHECKPOINT_RE.match(checkpoint.checkpoint_id)
        if cp_match is None:
            errors.append(
                f"PLAN line {checkpoint.line}: checkpoint id '{checkpoint.checkpoint_id}' is invalid."
            )
            continue

        cp_stage = cp_match.group(1)
        if checkpoint.stage and cp_stage.upper() != checkpoint.stage.upper():
            errors.append(
                f"PLAN line {checkpoint.line}: checkpoint '{checkpoint.checkpoint_id}' sits under Stage '{checkpoint.stage}'."
            )

        normalized_cp = checkpoint.checkpoint_id.upper()
        if normalized_cp in checkpoint_ids_seen:
            errors.append(
                f"PLAN line {checkpoint.line}: duplicate checkpoint id '{checkpoint.checkpoint_id}'."
            )
        checkpoint_ids_seen.add(normalized_cp)

        missing_fields = [field for field in REQUIRED_CHECKPOINT_FIELDS if field not in checkpoint.fields_present]
        if missing_fields:
            joined = ", ".join(missing_fields)
            errors.append(
                f"PLAN line {checkpoint.line}: checkpoint '{checkpoint.checkpoint_id}' missing field(s): {joined}."
            )


def _validate_cross_file(state: StateSummary, plan: PlanSummary, errors: list[str]) -> None:
    if state.stage is None or state.checkpoint is None:
        return

    stage_ids = {stage.stage_id.upper() for stage in plan.stages}
    checkpoint_ids = {checkpoint.checkpoint_id.upper(): checkpoint for checkpoint in plan.checkpoints}

    if state.stage.upper() not in stage_ids:
        errors.append(f"STATE Stage '{state.stage}' is not present in PLAN.")

    state_checkpoint_key = state.checkpoint.upper()
    if state_checkpoint_key not in checkpoint_ids:
        errors.append(f"STATE Checkpoint '{state.checkpoint}' is not present in PLAN.")
        return

    plan_checkpoint = checkpoint_ids[state_checkpoint_key]
    cp_match = _CHECKPOINT_RE.match(state.checkpoint)
    if cp_match and cp_match.group(1).upper() != state.stage.upper():
        errors.append(
            f"STATE says Stage '{state.stage}', but Checkpoint '{state.checkpoint}' belongs to Stage '{cp_match.group(1)}'."
        )

    if plan_checkpoint.stage and plan_checkpoint.stage.upper() != state.stage.upper():
        errors.append(
            f"PLAN places Checkpoint '{state.checkpoint}' under Stage '{plan_checkpoint.stage}', "
            f"but STATE says Stage '{state.stage}'."
        )


def run_troubleshoot(vibe_dir: Path) -> TroubleshootResult:
    errors: list[str] = []
    warnings: list[str] = []

    state_path = vibe_dir / "STATE.md"
    plan_path = vibe_dir / "PLAN.md"

    state_summary: StateSummary | None = None
    plan_summary: PlanSummary | None = None

    if not state_path.exists():
        errors.append(f"Missing required file: {state_path}")
    else:
        state_summary = _parse_state(state_path)
        _validate_state_format(state_summary, errors, warnings)

    if not plan_path.exists():
        errors.append(f"Missing required file: {plan_path}")
    else:
        plan_summary = _parse_plan(plan_path)
        _validate_plan_format(plan_summary, errors, warnings)

    if state_summary is not None and plan_summary is not None:
        _validate_cross_file(state_summary, plan_summary, errors)

    return TroubleshootResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        state=state_summary,
        plan=plan_summary,
    )


def _render_text(result: TroubleshootResult) -> str:
    lines: list[str] = []
    lines.append("Vibe Troubleshoot Report")
    lines.append("=======================")

    if result.state:
        lines.append("")
        lines.append("STATE")
        lines.append(f"- Path: {result.state.path}")
        lines.append(f"- Stage: {result.state.stage or '(missing)'}")
        lines.append(f"- Checkpoint: {result.state.checkpoint or '(missing)'}")
        lines.append(f"- Status: {result.state.status or '(missing)'}")
        lines.append(f"- Sections detected: {', '.join(result.state.sections) if result.state.sections else '(none)'}")
        issue_ids = ", ".join(issue.issue_id for issue in result.state.issues)
        lines.append(f"- Structured issues: {issue_ids if issue_ids else '(none)'}")

    if result.plan:
        lines.append("")
        lines.append("PLAN")
        lines.append(f"- Path: {result.plan.path}")
        lines.append(f"- Stage count: {len(result.plan.stages)}")
        lines.append(f"- Checkpoint count: {len(result.plan.checkpoints)}")
        if result.plan.stages:
            lines.append("- Stages:")
            for stage in result.plan.stages:
                if stage.checkpoint_ids:
                    checkpoints = ", ".join(stage.checkpoint_ids)
                else:
                    checkpoints = "(none)"
                title = f" - {stage.title}" if stage.title else ""
                lines.append(f"  - {stage.stage_id}{title}: {checkpoints}")

    lines.append("")
    if result.ok:
        lines.append("Validation: PASS")
    else:
        lines.append("Validation: FAIL")

    lines.append(f"Errors: {len(result.errors)}")
    for error in result.errors:
        lines.append(f"- ERROR: {error}")

    lines.append(f"Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        lines.append(f"- WARN: {warning}")

    return "\n".join(lines)


def _to_json_payload(result: TroubleshootResult) -> dict[str, object]:
    return {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "state": asdict(result.state) if result.state else None,
        "plan": asdict(result.plan) if result.plan else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and summarize .vibe STATE/PLAN files.")
    parser.add_argument(
        "--vibe-dir",
        default=".vibe",
        help="Directory containing STATE.md and PLAN.md (default: .vibe)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args(argv)

    result = run_troubleshoot(Path(args.vibe_dir).resolve())

    if args.json:
        print(json.dumps(_to_json_payload(result), indent=2, sort_keys=True))
    else:
        print(_render_text(result))

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
