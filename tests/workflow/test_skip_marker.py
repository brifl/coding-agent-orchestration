"""Tests for (SKIP) marker behavior."""
from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import (  # type: ignore
    StateInfo,
    _is_checkpoint_marked_done,
    _is_checkpoint_skipped,
    _parse_plan_checkpoint_ids,
    _recommend_next,
)
from prompt_catalog import load_catalog  # type: ignore


def _write_plan(repo_root: Path, text: str) -> None:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_path.write_text(text, encoding="utf-8")


def test_parse_includes_skip_marker() -> None:
    plan = """
## Stage 1 — Demo

### 1.0 — First

### (SKIP) 1.1 — Deferred

### 1.2 — Third
"""
    assert _parse_plan_checkpoint_ids(plan) == ["1.0", "1.1", "1.2"]


def test_is_checkpoint_skipped_flags_only_skip() -> None:
    plan = """
### (SKIP) 1.1 — Deferred

### (DONE) 1.2 — Done
"""
    assert _is_checkpoint_skipped(plan, "1.1") is True
    assert _is_checkpoint_skipped(plan, "1.2") is False
    assert _is_checkpoint_marked_done(plan, "1.1") is False


def test_recommend_next_skips_skip_marker(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### 1.0 — First

### (SKIP) 1.1 — Deferred

### 1.2 — Third
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "advance"
    assert "1.2" in reason


def test_removing_skip_reactivates_checkpoint(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### 1.0 — First

### 1.1 — Active

### 1.2 — Third
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, reason = _recommend_next(state, temp_repo)
    assert role == "advance"
    assert "1.1" in reason


def test_consolidation_prompt_preserves_skip_marker() -> None:
    catalog_path = Path(__file__).parent.parent.parent / "prompts" / "template_prompts.md"
    entries = load_catalog(catalog_path)
    consolidation = next(entry for entry in entries if entry.key == "prompt.consolidation")
    assert "Preserve any stages/checkpoints marked (SKIP)" in consolidation.body
