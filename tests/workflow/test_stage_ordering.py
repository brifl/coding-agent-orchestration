"""Tests for stage ordering and agentctl selection."""
from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import _recommend_next, load_state  # type: ignore
from stage_ordering import parse_checkpoint_id, parse_stage_id, stage_sort_key  # type: ignore


def _write_state(repo_root: Path, *, stage: str, checkpoint: str, status: str, issues: str = "- None.") -> None:
    state_path = repo_root / ".vibe" / "STATE.md"
    state_path.write_text(
        """# STATE

## Current focus

- Stage: {stage}
- Checkpoint: {checkpoint}
- Status: {status}

## Active issues

{issues}
""".format(stage=stage, checkpoint=checkpoint, status=status, issues=issues),
        encoding="utf-8",
    )


def _write_plan(repo_root: Path, text: str) -> None:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_path.write_text(text, encoding="utf-8")


def test_stage_sort_key_orders_suffixes() -> None:
    stages = ["12B", "12", "13", "12A", "2", "2B", "2A"]
    assert sorted(stages, key=stage_sort_key) == ["2", "2A", "2B", "12", "12A", "12B", "13"]


def test_parse_stage_and_checkpoint_ids() -> None:
    assert parse_stage_id("12")[0] == 12
    assert parse_stage_id("12a")[1] == "A"
    assert parse_checkpoint_id("12A.3") == ("12A", 3)


def test_agentctl_next_prefers_inserted_stage(tmp_path: Path) -> None:
    (tmp_path / ".vibe").mkdir()
    _write_state(tmp_path, stage="12", checkpoint="12.2", status="DONE")
    _write_plan(
        tmp_path,
        """# PLAN

## Stage 12 — Twelve

### 12.2 — Done checkpoint

---

## Stage 12A — Inserted

### 12A.0 — Inserted checkpoint

---

## Stage 13 — Thirteen

### 13.0 — Next checkpoint
""",
    )

    state = load_state(tmp_path)
    role, reason = _recommend_next(state, tmp_path)
    assert role == "consolidation"
    assert "12A" in reason


def test_blocker_issue_overrides_ordering(tmp_path: Path) -> None:
    (tmp_path / ".vibe").mkdir()
    _write_state(
        tmp_path,
        stage="12A",
        checkpoint="12A.0",
        status="NOT_STARTED",
        issues="""- [ ] ISSUE-999: Blocked
  - Impact: BLOCKER
""",
    )
    _write_plan(
        tmp_path,
        """# PLAN

## Stage 12A — Inserted

### 12A.0 — Inserted checkpoint
""",
    )

    state = load_state(tmp_path)
    role, _ = _recommend_next(state, tmp_path)
    assert role == "issues_triage"
