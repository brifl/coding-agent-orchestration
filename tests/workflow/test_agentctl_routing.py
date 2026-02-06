"""Tests for agentctl next-role routing extensions."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import StateInfo, _recommend_next  # type: ignore


def _write_state(repo_root: Path, body: str) -> None:
    state_path = repo_root / ".vibe" / "STATE.md"
    state_path.write_text(body, encoding="utf-8")


def _write_plan(repo_root: Path, body: str) -> None:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_path.write_text(body, encoding="utf-8")


def test_context_capture_flag_routes_to_context_capture(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Workflow state
- [x] RUN_CONTEXT_CAPTURE
""",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "context_capture"
    assert "RUN_CONTEXT_CAPTURE" in reason


def test_work_log_bloat_routes_to_improvements(temp_repo: Path) -> None:
    work_log = "\n".join(f"- 2026-02-06: entry {idx}" for idx in range(1, 17))
    _write_state(
        temp_repo,
        f"""# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Workflow state
- [ ] RUN_CONTEXT_CAPTURE
- [ ] RUN_PROCESS_IMPROVEMENTS

## Work log (current session)
{work_log}

## Evidence
(None yet)
""",
    )
    # Avoid automatic context-capture recommendation so we can test improvements routing.
    context_path = temp_repo / ".vibe" / "CONTEXT.md"
    context_path.write_text("# CONTEXT\n", encoding="utf-8")

    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "improvements"
    assert "Work log has 16 entries" in reason


def test_done_stage_transition_routes_to_consolidation(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First

## Stage 2 — Demo
### 2.0 — Second
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "consolidation"
    assert "Stage transition detected" in reason


def test_done_same_stage_routes_to_advance(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
### 1.1 — Second
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "advance"
    assert "1.1" in reason


def test_stale_context_routes_to_context_capture(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )

    context_path = temp_repo / ".vibe" / "CONTEXT.md"
    context_path.write_text("# CONTEXT\n", encoding="utf-8")

    # Make context old relative to state/plan to force stale detection.
    stale_time = time.time() - (26 * 3600)
    os.utime(context_path, (stale_time, stale_time))

    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "context_capture"
    assert "stale" in reason.lower()
