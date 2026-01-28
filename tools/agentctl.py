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
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

ALLOWED_STATUS = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "IN_REVIEW",
    "BLOCKED",
    "DONE",
}

# For prioritization (highest -> lowest)
SEVERITY_ORDER = ["BLOCKER", "MAJOR", "MINOR", "QUESTION"]
SEVERITIES = tuple(SEVERITY_ORDER)

Role = Literal[
    "issues_triage",
    "review",
    "implement",
    "design",
    "consolidation",
    "improvements",
    "advance",
]


@dataclass(frozen=True)
class Issue:
    severity: str
    title: str
    line: str


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
      ### 1.2 - Title
      ### (DONE) 1.2 — Title
    """
    ids: list[str] = []
    # capture (DONE) optionally, then capture the numeric id X.Y
    pat = re.compile(r"(?im)^\s*#{3,6}\s+(?:\(\s*DONE\s*\)\s+)?(?P<id>\d+\.\d+)\b")
    for m in pat.finditer(plan_text):
        ids.append(m.group("id"))
    return ids


def _is_checkpoint_marked_done(plan_text: str, checkpoint_id: str) -> bool:
    pat = re.compile(rf"(?im)^\s*#{3,6}\s+\(\s*DONE\s*\)\s+{re.escape(checkpoint_id)}\b")
    return bool(pat.search(plan_text))


def _next_checkpoint_after(plan_ids: list[str], current_id: str) -> str | None:
    try:
        idx = plan_ids.index(current_id)
    except ValueError:
        return plan_ids[0] if plan_ids else None
    if idx + 1 < len(plan_ids):
        return plan_ids[idx + 1]
    return None


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
      - Severity: QUESTION
      - Notes: ...
    """
    section_lines = _slice_active_issues_section(text)
    if not section_lines:
        return ()

    issues: list[Issue] = []
    issue_head = re.compile(r"^\s*-\s*\[\s*([xX ]?)\s*\]\s*(.+?)\s*$")
    severity_line = re.compile(r"(?im)^\s*-\s*Severity\s*:\s*(.+?)\s*$")

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

        sev: str | None = None
        j = i + 1
        while j < len(section_lines):
            nxt = section_lines[j]
            if issue_head.match(nxt):
                break
            if nxt.strip() == "":
                break
            sm = severity_line.match(nxt)
            if sm and sev is None:
                sev = sm.group(1).strip().split()[0].upper()
            j += 1

        if sev not in SEVERITIES:
            sev = "QUESTION"

        issues.append(Issue(severity=sev, title=title, line=line))
        i = j

    return tuple(issues)


def _resolve_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (repo_root / path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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
        rf"^\s*-\s*(?:\*\*)?\s*({'|'.join(SEVERITIES)}|RISK)\s*:\s*(.+?)(?:\s*\*\*)?\s*$",
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
        issues.append(Issue(severity=sev, title=title, line=line.rstrip()))
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
    # Matches: "## Stage 0 — Name" or "## Stage 0 - Name" or "## Stage 0"
    pat = re.compile(rf"(?im)^##\s+Stage\s+{re.escape(stage)}\b")
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
        # Matches either "- Objective:" bullet style or "Objective" header style.
        return bool(
            re.search(
                rf"(?im)^\s*(?:-+\s*)?(?:\*\*)?\s*{re.escape(name)}\s*(?:\*\*)?\s*(?::)?\s*$",
                section,
            )
        )

    has_objective = has_heading("Objective")
    has_deliverables = has_heading("Deliverables")
    has_acceptance = has_heading("Acceptance")
    has_evidence = has_heading("Evidence")

    # Demo commands: accept either explicit heading or code-ish lines
    has_demo_heading = bool(re.search(r"(?im)^\s*(?:-+\s*)?Demo commands\b", section))
    has_commandish = bool(re.search(r"(?im)^\s*-\s*`.+`", section)) or ("```" in section)
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
        if state.stage and plan_text and not _plan_has_stage(plan_text, state.stage):
            warnings.append(f".vibe/PLAN.md: missing stage section for Stage {state.stage}.")

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

    ok = len(errors) == 0
    return ValidationResult(
        ok=ok,
        errors=tuple(errors),
        warnings=tuple(warnings),
        state=state,
        plan_check=plan_check,
    )


def _top_issue_severity(issues: tuple[Issue, ...]) -> str | None:
    if not issues:
        return None
    # choose highest severity by SEVERITY_ORDER
    order = {sev: idx for idx, sev in enumerate(SEVERITY_ORDER)}
    best = min(issues, key=lambda i: order.get(i.severity, 999))
    return best.severity


def _recommend_next(state: StateInfo, repo_root: Path) -> tuple[Role, str]:
    # 0) Hard stop / hard triage conditions
    if state.status == "BLOCKED":
        return ("issues_triage", "Checkpoint status is BLOCKED.")

    top = _top_issue_severity(state.issues)
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

        # If the next one is explicitly marked (DONE), skip forward until you find not-DONE
        while nxt and _is_checkpoint_marked_done(plan_text, nxt):
            state_ck = nxt
            nxt = _next_checkpoint_after(plan_ids, state_ck)

        if not nxt:
            return ("stop", "All remaining checkpoints are marked (DONE) in .vibe/PLAN.md (plan exhausted).")

        return ("advance", f"Checkpoint is DONE; next checkpoint is {nxt}.")

    # 3) Normal execution states
    if state.status in {"NOT_STARTED", "IN_PROGRESS"}:
        # If there are non-blocking issues, triage can be recommended (your choice)
        if top in {"MAJOR", "QUESTION"}:
            return ("issues_triage", f"Active issues present (top severity: {top}).")
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
            "issues": [{"severity": i.severity, "title": i.title} for i in res.state.issues],
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

    payload: dict[str, Any] = {
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
        "evidence_path": state.evidence_path,
        "issues_count": len(state.issues),
        "issues_top_severity": _top_issue_severity(state.issues),
        "blockers": [i.title for i in state.issues if i.severity == "BLOCKER"],
        "majors": [i.title for i in state.issues if i.severity == "MAJOR"],
        "questions": [i.title for i in state.issues if i.severity == "QUESTION"],
        "recommended_next_role": role,
        "recommended_next_reason": reason,
        "recommended_prompt_id": PROMPT_MAP[role]["id"],
        "recommended_prompt_title": PROMPT_MAP[role]["title"],
    }
    print(_render_output(payload, args.format))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    state = load_state(repo_root)

    role, reason = _recommend_next(state, repo_root)

    payload: dict[str, Any] = {
        "recommended_role": role,
        "recommended_prompt_id": PROMPT_MAP[role]["id"],
        "recommended_prompt_title": PROMPT_MAP[role]["title"],
        "reason": reason,
        "stage": state.stage,
        "checkpoint": state.checkpoint,
        "status": state.status,
    }
    print(_render_output(payload, args.format))
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
    ps.set_defaults(fn=cmd_status)

    pn = sub.add_parser("next", help="Recommend the next loop/prompt to run.")
    pn.set_defaults(fn=cmd_next)

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
