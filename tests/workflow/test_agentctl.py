"""Tests for agentctl dispatcher logic."""
from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import (
    WORK_LOG_CONSOLIDATION_CAP,
    _parse_plan_checkpoint_ids,
    _get_stage_for_checkpoint,
    _detect_stage_transition,
    _is_checkpoint_marked_done,
    _next_checkpoint_after,
    _extract_checkpoint_section,
    validate,
)


class TestParsePlanCheckpointIds:
    """Tests for _parse_plan_checkpoint_ids function."""

    def test_basic_parsing(self):
        plan = """
### 1.0 — First checkpoint

### 1.1 — Second checkpoint

### 2.0 — Third checkpoint
"""
        ids = _parse_plan_checkpoint_ids(plan)
        assert ids == ["1.0", "1.1", "2.0"]

    def test_with_done_markers(self):
        plan = """
### (DONE) 1.0 — First checkpoint

### 1.1 — Second checkpoint

### (DONE) 2.0 — Third checkpoint
"""
        ids = _parse_plan_checkpoint_ids(plan)
        assert ids == ["1.0", "1.1", "2.0"]

    def test_with_skipped_markers(self):
        plan = """
### 1.0 — First checkpoint

### (SKIPPED) 1.1 — Skipped checkpoint

### 2.0 — Third checkpoint
"""
        ids = _parse_plan_checkpoint_ids(plan)
        assert ids == ["1.0", "1.1", "2.0"]

    def test_empty_plan(self):
        ids = _parse_plan_checkpoint_ids("")
        assert ids == []

    def test_no_checkpoints(self):
        plan = """
## Stage 1

Some description without checkpoints.
"""
        ids = _parse_plan_checkpoint_ids(plan)
        assert ids == []


class TestGetStageForCheckpoint:
    """Tests for _get_stage_for_checkpoint function."""

    def test_basic_stage_lookup(self):
        plan = """
## Stage 1 — First stage

### 1.0 — Checkpoint in stage 1

## Stage 2 — Second stage

### 2.0 — Checkpoint in stage 2
"""
        assert _get_stage_for_checkpoint(plan, "1.0") == "1"
        assert _get_stage_for_checkpoint(plan, "2.0") == "2"

    def test_checkpoint_not_found(self):
        plan = """
## Stage 1

### 1.0 — Some checkpoint
"""
        assert _get_stage_for_checkpoint(plan, "9.9") is None

    def test_with_done_marker(self):
        plan = """
## Stage 1

### (DONE) 1.0 — Done checkpoint
"""
        assert _get_stage_for_checkpoint(plan, "1.0") == "1"

    def test_with_skipped_marker(self):
        plan = """
## Stage 1

### (SKIPPED) 1.0 — Skipped checkpoint
"""
        assert _get_stage_for_checkpoint(plan, "1.0") == "1"


class TestDetectStageTransition:
    """Tests for _detect_stage_transition function."""

    def test_same_stage(self):
        plan = """
## Stage 1

### 1.0 — First

### 1.1 — Second
"""
        is_change, cur, nxt = _detect_stage_transition(plan, "1.0", "1.1")
        assert is_change is False
        assert cur == "1"
        assert nxt == "1"

    def test_stage_change(self):
        plan = """
## Stage 1

### 1.0 — First

## Stage 2

### 2.0 — Second
"""
        is_change, cur, nxt = _detect_stage_transition(plan, "1.0", "2.0")
        assert is_change is True
        assert cur == "1"
        assert nxt == "2"

    def test_checkpoint_not_found(self):
        plan = """
## Stage 1

### 1.0 — First
"""
        is_change, cur, nxt = _detect_stage_transition(plan, "1.0", "9.9")
        # When next checkpoint not found, stage is None
        assert cur == "1"
        assert nxt is None


class TestIsCheckpointMarkedDone:
    """Tests for _is_checkpoint_marked_done function."""

    def test_done_checkpoint(self):
        plan = """
### (DONE) 1.0 — Completed checkpoint
"""
        assert _is_checkpoint_marked_done(plan, "1.0") is True

    def test_skipped_checkpoint(self):
        plan = """
### (SKIPPED) 1.0 — Skipped checkpoint
"""
        assert _is_checkpoint_marked_done(plan, "1.0") is True

    def test_not_done_checkpoint(self):
        plan = """
### 1.0 — Active checkpoint
"""
        assert _is_checkpoint_marked_done(plan, "1.0") is False

    def test_different_checkpoint(self):
        plan = """
### (DONE) 1.0 — Done checkpoint

### 1.1 — Not done checkpoint
"""
        assert _is_checkpoint_marked_done(plan, "1.0") is True
        assert _is_checkpoint_marked_done(plan, "1.1") is False


class TestNextCheckpointAfter:
    """Tests for _next_checkpoint_after function."""

    def test_basic_next(self):
        ids = ["1.0", "1.1", "2.0"]
        assert _next_checkpoint_after(ids, "1.0") == "1.1"
        assert _next_checkpoint_after(ids, "1.1") == "2.0"

    def test_last_checkpoint(self):
        ids = ["1.0", "1.1", "2.0"]
        assert _next_checkpoint_after(ids, "2.0") is None

    def test_not_found_returns_first(self):
        ids = ["1.0", "1.1"]
        assert _next_checkpoint_after(ids, "9.9") == "1.0"

    def test_empty_list(self):
        assert _next_checkpoint_after([], "1.0") is None


class TestExtractCheckpointSection:
    """Tests for _extract_checkpoint_section function."""

    def test_basic_extraction(self):
        plan = """
## Stage 1

### 1.0 — First checkpoint

* **Objective:**
  Test objective.

---

### 1.1 — Second checkpoint
"""
        section = _extract_checkpoint_section(plan, "1.0")
        assert section is not None
        assert "Test objective" in section
        assert "Second checkpoint" not in section

    def test_checkpoint_not_found(self):
        plan = """
### 1.0 — Only checkpoint
"""
        section = _extract_checkpoint_section(plan, "9.9")
        assert section is None

    def test_with_done_marker(self):
        plan = """
### (DONE) 1.0 — Done checkpoint

Content here.

---
"""
        section = _extract_checkpoint_section(plan, "1.0")
        assert section is not None
        assert "Content here" in section


class TestWorkLogValidationWarning:
    """Tests for work log size validation warning."""

    def test_work_log_over_cap_produces_warning(self, tmp_path):
        vibe = tmp_path / ".vibe"
        vibe.mkdir()
        entries = "\n".join(f"- Entry {i}" for i in range(WORK_LOG_CONSOLIDATION_CAP + 5))
        (vibe / "STATE.md").write_text(
            f"# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n"
            f"- Status: NOT_STARTED\n\n## Work log (current session)\n\n{entries}\n\n"
            f"## Active issues\n\n(none)\n",
            encoding="utf-8",
        )
        (vibe / "PLAN.md").write_text(
            "# PLAN\n\n## Stage 1 — Test\n\n### 1.0 — Test checkpoint\n\n"
            "* **Objective:**\n  Test\n* **Deliverables:**\n  Test\n"
            "* **Acceptance:**\n  Test\n* **Demo commands:**\n  * `echo test`\n"
            "* **Evidence:**\n  Test\n",
            encoding="utf-8",
        )
        result = validate(tmp_path, strict=False)
        work_log_warnings = [w for w in result.warnings if "work log" in w]
        assert len(work_log_warnings) == 1
        assert f">{WORK_LOG_CONSOLIDATION_CAP}" in work_log_warnings[0]

    def test_work_log_under_cap_no_warning(self, tmp_path):
        vibe = tmp_path / ".vibe"
        vibe.mkdir()
        entries = "\n".join(f"- Entry {i}" for i in range(WORK_LOG_CONSOLIDATION_CAP - 2))
        (vibe / "STATE.md").write_text(
            f"# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n"
            f"- Status: NOT_STARTED\n\n## Work log (current session)\n\n{entries}\n\n"
            f"## Active issues\n\n(none)\n",
            encoding="utf-8",
        )
        (vibe / "PLAN.md").write_text(
            "# PLAN\n\n## Stage 1 — Test\n\n### 1.0 — Test checkpoint\n\n"
            "* **Objective:**\n  Test\n* **Deliverables:**\n  Test\n"
            "* **Acceptance:**\n  Test\n* **Demo commands:**\n  * `echo test`\n"
            "* **Evidence:**\n  Test\n",
            encoding="utf-8",
        )
        result = validate(tmp_path, strict=False)
        work_log_warnings = [w for w in result.warnings if "work log" in w]
        assert len(work_log_warnings) == 0
