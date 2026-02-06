"""Tests for .vibe/troubleshoot.py."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_troubleshoot_module():
    script_path = Path(__file__).resolve().parents[2] / ".vibe" / "troubleshoot.py"
    spec = importlib.util.spec_from_file_location("vibe_troubleshoot", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_troubleshoot_passes_for_valid_state_and_plan(temp_repo: Path) -> None:
    _write(
        temp_repo / ".vibe" / "STATE.md",
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS

## Objective (current checkpoint)
- Keep docs aligned.

## Deliverables (current checkpoint)
- .vibe/troubleshoot.py

## Acceptance (current checkpoint)
- [ ] Validator reports PASS.

## Work log (current session)
- 2026-02-06: Started.

## Evidence
- path: logs/demo.txt

## Active issues
- [ ] ISSUE-101: Clarify migration note
  - Impact: QUESTION
  - Status: OPEN
  - Owner: human
  - Unblock Condition: Clarify whether migration is required.
  - Evidence Needed: Decision note in STATE.md.
  - Notes: Pending review.

## Decisions
- 2026-02-06: Keep script stdlib-only.
""",
    )
    _write(
        temp_repo / ".vibe" / "PLAN.md",
        """# PLAN

## Stage 1 - Docs

### 1.0 - Add validator
- Objective:
  - Add a validator script.
- Deliverables:
  - .vibe/troubleshoot.py
- Acceptance:
  - [ ] Script validates STATE.md and PLAN.md.
- Demo commands:
  - `python3 .vibe/troubleshoot.py`
- Evidence:
  - Troubleshooter output in STATE.md.
""",
    )

    troubleshoot = _load_troubleshoot_module()
    result = troubleshoot.run_troubleshoot(temp_repo / ".vibe")

    assert result.ok is True
    assert result.errors == []
    assert result.state is not None
    assert result.state.stage == "1"
    assert result.state.checkpoint == "1.0"
    assert result.plan is not None
    assert len(result.plan.stages) == 1
    assert len(result.plan.checkpoints) == 1


def test_troubleshoot_reports_state_plan_mismatch(temp_repo: Path) -> None:
    _write(
        temp_repo / ".vibe" / "STATE.md",
        """# STATE

## Current focus
- Stage: 2
- Checkpoint: 2.0
- Status: NOT_STARTED

## Objective (current checkpoint)
- Placeholder.

## Deliverables (current checkpoint)
- Placeholder.

## Acceptance (current checkpoint)
- Placeholder.

## Work log (current session)
- 2026-02-06: Placeholder.

## Evidence
- Placeholder.

## Active issues
- [ ] ISSUE-201: Placeholder
  - Impact: MINOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Placeholder.
  - Evidence Needed: Placeholder.
  - Notes: Placeholder.

## Decisions
- 2026-02-06: Placeholder.
""",
    )
    _write(
        temp_repo / ".vibe" / "PLAN.md",
        """# PLAN

## Stage 1 - Build

### 1.0 - Bootstrap
- Objective:
  - Placeholder.
- Deliverables:
  - Placeholder.
- Acceptance:
  - [ ] Placeholder.
- Demo commands:
  - `echo demo`
- Evidence:
  - Placeholder.
""",
    )

    troubleshoot = _load_troubleshoot_module()
    result = troubleshoot.run_troubleshoot(temp_repo / ".vibe")

    assert result.ok is False
    assert any("STATE Stage '2' is not present in PLAN." in err for err in result.errors)
    assert any("STATE Checkpoint '2.0' is not present in PLAN." in err for err in result.errors)
