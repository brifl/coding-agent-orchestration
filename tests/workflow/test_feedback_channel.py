"""Integration tests for Stage 24: Structured Human Feedback Channel.

Covers checkpoints 24.0-24.3: schema parsing, validation, inject (duplicate guard),
dispatcher routing, ack, idempotency, and backward compat (no FEEDBACK.md).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
import agentctl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_FEEDBACK = """\
# FEEDBACK

- [ ] FEEDBACK-001: Example concern
  - Impact: MAJOR
  - Type: concern
  - Description: Something smells off
  - Expected: It smells fine
  - Proposed action: Investigate

- [ ] FEEDBACK-002: Minor question
  - Impact: QUESTION
  - Type: question
  - Description: Why is this here?
  - Expected: Clear rationale
  - Proposed action: Add comment
"""

PROCESSED_FEEDBACK = """\
# FEEDBACK

- [x] FEEDBACK-001: Example concern  <!-- processed: ISSUE-001 -->
  - Impact: MAJOR
  - Type: concern
  - Description: Something smells off
  - Expected: It smells fine
  - Proposed action: Investigate
"""

STATE_WITH_ISSUES = """\
# STATE

## Current focus

- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS

## Active issues

- ISSUE-001 (MAJOR): Existing issue
  - Notes: pre-existing
  - Unblock Condition: Fix it
  - Evidence Needed: Tests pass
"""


def _make_feedback_file(tmp_path: Path, content: str) -> Path:
    vibe = tmp_path / ".vibe"
    vibe.mkdir(exist_ok=True)
    fb = vibe / "FEEDBACK.md"
    fb.write_text(content, encoding="utf-8")
    return fb


def _make_state_file(tmp_path: Path, content: str) -> Path:
    vibe = tmp_path / ".vibe"
    vibe.mkdir(exist_ok=True)
    st = vibe / "STATE.md"
    st.write_text(content, encoding="utf-8")
    return st


def _make_history_file(tmp_path: Path, content: str = "# HISTORY\n") -> Path:
    vibe = tmp_path / ".vibe"
    vibe.mkdir(exist_ok=True)
    h = vibe / "HISTORY.md"
    h.write_text(content, encoding="utf-8")
    return h


# ---------------------------------------------------------------------------
# 24.0 — Schema parsing
# ---------------------------------------------------------------------------


class TestFeedbackSchemaParsing:
    """Tests for _parse_feedback_file."""

    def test_valid_entries_parsed(self):
        entries, errors = agentctl._parse_feedback_file(VALID_FEEDBACK)
        assert len(entries) == 2
        assert not errors
        assert entries[0].feedback_id == "FEEDBACK-001"
        assert entries[0].impact == "MAJOR"
        assert entries[0].type == "concern"
        assert not entries[0].checked
        assert not entries[0].processed

    def test_checked_flag(self):
        entries, _ = agentctl._parse_feedback_file(PROCESSED_FEEDBACK)
        assert entries[0].checked is True

    def test_processed_flag(self):
        entries, _ = agentctl._parse_feedback_file(PROCESSED_FEEDBACK)
        assert entries[0].processed is True

    def test_missing_required_field_error(self):
        bad = """\
# FEEDBACK

- [ ] FEEDBACK-001: Missing fields
  - Impact: MAJOR
  - Type: concern
"""
        _, errors = agentctl._parse_feedback_file(bad)
        assert any("Description" in e or "Expected" in e or "Proposed action" in e for e in errors)

    def test_invalid_impact_error(self):
        bad = """\
# FEEDBACK

- [ ] FEEDBACK-001: Bad impact
  - Impact: EXTREME
  - Type: concern
  - Description: Something
  - Expected: Fix
  - Proposed action: Do it
"""
        _, errors = agentctl._parse_feedback_file(bad)
        assert any("impact" in e.lower() or "EXTREME" in e for e in errors)

    def test_duplicate_feedback_id_error(self):
        dup = """\
# FEEDBACK

- [ ] FEEDBACK-001: First
  - Impact: MINOR
  - Type: bug
  - Description: A
  - Expected: B
  - Proposed action: C

- [ ] FEEDBACK-001: Duplicate
  - Impact: MINOR
  - Type: bug
  - Description: A
  - Expected: B
  - Proposed action: C
"""
        _, errors = agentctl._parse_feedback_file(dup)
        assert any("duplicate" in e.lower() or "FEEDBACK-001" in e for e in errors)

    def test_empty_file_returns_no_entries(self):
        entries, errors = agentctl._parse_feedback_file("# FEEDBACK\n\n---\n")
        assert entries == ()
        assert not errors


# ---------------------------------------------------------------------------
# 24.0 — Validation command
# ---------------------------------------------------------------------------


class TestFeedbackValidation:
    """Tests for cmd_feedback_validate."""

    def test_valid_feedback_exits_zero(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_validate(args)
        assert rc == 0

    def test_no_feedback_file_exits_zero(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_validate(args)
        assert rc == 0

    def test_invalid_feedback_exits_two(self, tmp_path):
        bad = "# FEEDBACK\n\n- [ ] FEEDBACK-001: Bad\n  - Impact: EXTREME\n  - Type: bug\n  - Description: A\n  - Expected: B\n  - Proposed action: C\n"
        _make_feedback_file(tmp_path, bad)
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_validate(args)
        assert rc == 2


# ---------------------------------------------------------------------------
# 24.1 — Inject
# ---------------------------------------------------------------------------


class TestFeedbackInject:
    """Tests for cmd_feedback_inject."""

    def test_inject_creates_issues_in_state(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        state_content = "# STATE\n\n## Active issues\n\n(None)\n\n## Next section\n"
        _make_state_file(tmp_path, state_content)
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        rc = agentctl.cmd_feedback_inject(args)
        assert rc == 0
        state_text = (tmp_path / ".vibe" / "STATE.md").read_text(encoding="utf-8")
        assert "ISSUE-001" in state_text
        assert "ISSUE-002" in state_text

    def test_inject_marks_entries_processed(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        state_content = "# STATE\n\n## Active issues\n\n(None)\n\n## Next section\n"
        _make_state_file(tmp_path, state_content)
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        agentctl.cmd_feedback_inject(args)
        fb_text = (tmp_path / ".vibe" / "FEEDBACK.md").read_text(encoding="utf-8")
        assert "<!-- processed: ISSUE-001 -->" in fb_text
        assert "<!-- processed: ISSUE-002 -->" in fb_text

    def test_inject_idempotent_no_duplicates(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        state_content = "# STATE\n\n## Active issues\n\n(None)\n\n## Next section\n"
        _make_state_file(tmp_path, state_content)
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        agentctl.cmd_feedback_inject(args)
        # Second inject should find nothing to do
        rc = agentctl.cmd_feedback_inject(args)
        assert rc == 0
        state_text = (tmp_path / ".vibe" / "STATE.md").read_text(encoding="utf-8")
        # Should have exactly one occurrence of ISSUE-001
        assert state_text.count("ISSUE-001") == 1

    def test_inject_does_not_overwrite_existing_issues(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        _make_state_file(tmp_path, STATE_WITH_ISSUES)
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        agentctl.cmd_feedback_inject(args)
        state_text = (tmp_path / ".vibe" / "STATE.md").read_text(encoding="utf-8")
        # Original issue must still be present
        assert "Existing issue" in state_text
        # New issues get next available IDs (ISSUE-002, ISSUE-003)
        assert "ISSUE-002" in state_text

    def test_inject_dry_run_no_file_changes(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        state_content = "# STATE\n\n## Active issues\n\n(None)\n\n## Next section\n"
        _make_state_file(tmp_path, state_content)
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=True)
        agentctl.cmd_feedback_inject(args)
        fb_text = (tmp_path / ".vibe" / "FEEDBACK.md").read_text(encoding="utf-8")
        state_text = (tmp_path / ".vibe" / "STATE.md").read_text(encoding="utf-8")
        assert "processed:" not in fb_text
        assert "ISSUE-001" not in state_text

    def test_inject_no_feedback_file(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        rc = agentctl.cmd_feedback_inject(args)
        assert rc == 0


# ---------------------------------------------------------------------------
# 24.2 — Dispatcher routing
# ---------------------------------------------------------------------------


class TestDispatcherRouting:
    """Tests for _has_unprocessed_feedback and dispatcher feedback gate."""

    def test_no_feedback_file_returns_false(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        has, reason = agentctl._has_unprocessed_feedback(tmp_path)
        assert has is False
        assert reason == ""

    def test_all_processed_returns_false(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        has, reason = agentctl._has_unprocessed_feedback(tmp_path)
        assert has is False

    def test_unprocessed_entry_returns_true_with_reason(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        has, reason = agentctl._has_unprocessed_feedback(tmp_path)
        assert has is True
        assert "Unprocessed human feedback:" in reason
        assert "2 entries" in reason
        assert "Run agentctl feedback inject" in reason

    def test_top_impact_reported(self, tmp_path):
        mixed = """\
# FEEDBACK

- [ ] FEEDBACK-001: Minor thing
  - Impact: MINOR
  - Type: bug
  - Description: Tiny
  - Expected: Fix
  - Proposed action: Tweak

- [ ] FEEDBACK-002: Blocker
  - Impact: BLOCKER
  - Type: concern
  - Description: Stops work
  - Expected: Unblock
  - Proposed action: Fix now
"""
        _make_feedback_file(tmp_path, mixed)
        has, reason = agentctl._has_unprocessed_feedback(tmp_path)
        assert "top impact: BLOCKER" in reason

    def test_decide_role_routes_to_issues_triage_when_feedback(self):
        ctx = agentctl._DecisionContext(
            workflow_flags={
                "STAGE_DESIGNED": True,
                "MAINTENANCE_CYCLE_DONE": True,
                "RETROSPECTIVE_DONE": True,
                "RUN_CONTEXT_CAPTURE": False,
            },
            plan_text="",
            smoke_gate_result=None,
            context_capture_reason=None,
            consolidation_reason=None,
            process_improvements_reason=None,
            unprocessed_feedback_reason="Unprocessed human feedback: 1 entries (top impact: MAJOR). Run agentctl feedback inject.",
        )
        state = agentctl.StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
        role, reason, _ = agentctl._decide_role(state, ctx)
        assert role == "issues_triage"
        assert "Unprocessed human feedback" in reason

    def test_decide_role_normal_when_no_feedback(self):
        ctx = agentctl._DecisionContext(
            workflow_flags={
                "STAGE_DESIGNED": True,
                "MAINTENANCE_CYCLE_DONE": True,
                "RETROSPECTIVE_DONE": True,
                "RUN_CONTEXT_CAPTURE": False,
            },
            plan_text="",
            smoke_gate_result=None,
            context_capture_reason=None,
            consolidation_reason=None,
            process_improvements_reason=None,
            unprocessed_feedback_reason=None,
        )
        state = agentctl.StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
        role, _, _ = agentctl._decide_role(state, ctx)
        assert role == "implement"

    def test_validate_warns_for_unprocessed_feedback(self, tmp_path):
        _make_feedback_file(tmp_path, VALID_FEEDBACK)
        # Need minimal STATE.md and PLAN.md to avoid unrelated errors
        _make_state_file(tmp_path, "# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n- Status: IN_PROGRESS\n\n## Work log (current session)\n\n- 2026-01-01: entry\n\n## Active issues\n\n(None)\n")
        result = agentctl.validate(tmp_path, strict=False)
        fb_warnings = [w for w in result.warnings if "FEEDBACK.md" in w]
        assert fb_warnings, "Expected FEEDBACK.md warning in validate output"


# ---------------------------------------------------------------------------
# 24.3 — Ack
# ---------------------------------------------------------------------------


class TestFeedbackAck:
    """Tests for cmd_feedback_ack."""

    def test_ack_archives_to_history(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        _make_history_file(tmp_path)
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_ack(args)
        assert rc == 0
        history = (tmp_path / ".vibe" / "HISTORY.md").read_text(encoding="utf-8")
        assert "## Feedback archive" in history
        assert "FEEDBACK-001" in history
        assert "ISSUE-001" in history

    def test_ack_removes_processed_from_feedback(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        _make_history_file(tmp_path)
        args = argparse.Namespace(repo_root=str(tmp_path))
        agentctl.cmd_feedback_ack(args)
        fb = (tmp_path / ".vibe" / "FEEDBACK.md").read_text(encoding="utf-8")
        assert "FEEDBACK-001" not in fb

    def test_ack_keeps_unprocessed_entries(self, tmp_path):
        mixed = """\
# FEEDBACK

- [x] FEEDBACK-001: Done  <!-- processed: ISSUE-001 -->
  - Impact: MINOR
  - Type: bug
  - Description: Fixed
  - Expected: Good
  - Proposed action: Nothing

- [ ] FEEDBACK-002: Still open
  - Impact: MAJOR
  - Type: concern
  - Description: Not done
  - Expected: Fix
  - Proposed action: Review
"""
        _make_feedback_file(tmp_path, mixed)
        _make_history_file(tmp_path)
        args = argparse.Namespace(repo_root=str(tmp_path))
        agentctl.cmd_feedback_ack(args)
        fb = (tmp_path / ".vibe" / "FEEDBACK.md").read_text(encoding="utf-8")
        assert "FEEDBACK-001" not in fb
        assert "FEEDBACK-002" in fb

    def test_ack_idempotent(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        _make_history_file(tmp_path)
        args = argparse.Namespace(repo_root=str(tmp_path))
        agentctl.cmd_feedback_ack(args)
        rc = agentctl.cmd_feedback_ack(args)
        assert rc == 0
        # History should not have duplicate entries
        history = (tmp_path / ".vibe" / "HISTORY.md").read_text(encoding="utf-8")
        assert history.count("FEEDBACK-001") == 1

    def test_ack_no_feedback_file(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_ack(args)
        assert rc == 0

    def test_ack_creates_history_section_if_missing(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        # No existing HISTORY.md
        args = argparse.Namespace(repo_root=str(tmp_path))
        agentctl.cmd_feedback_ack(args)
        history = (tmp_path / ".vibe" / "HISTORY.md").read_text(encoding="utf-8")
        assert "## Feedback archive" in history

    def test_ack_archive_format(self, tmp_path):
        _make_feedback_file(tmp_path, PROCESSED_FEEDBACK)
        args = argparse.Namespace(repo_root=str(tmp_path))
        agentctl.cmd_feedback_ack(args)
        history = (tmp_path / ".vibe" / "HISTORY.md").read_text(encoding="utf-8")
        import re
        # Expect: "- 2026-02-19 FEEDBACK-001 -> ISSUE-001: ... (Type: concern, Impact: MAJOR)"
        assert re.search(r"- \d{4}-\d{2}-\d{2} FEEDBACK-001 -> ISSUE-001:", history)
        assert "Type: concern" in history
        assert "Impact: MAJOR" in history


# ---------------------------------------------------------------------------
# Backward compatibility: no FEEDBACK.md
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    """Repos without FEEDBACK.md are entirely unaffected."""

    def test_has_unprocessed_feedback_no_file(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        has, reason = agentctl._has_unprocessed_feedback(tmp_path)
        assert has is False
        assert reason == ""

    def test_validate_no_feedback_warning(self, tmp_path):
        _make_state_file(tmp_path, "# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n- Status: IN_PROGRESS\n\n## Work log (current session)\n\n- 2026-01-01: entry\n\n## Active issues\n\n(None)\n")
        result = agentctl.validate(tmp_path, strict=False)
        fb_warnings = [w for w in result.warnings if "FEEDBACK.md" in w]
        assert not fb_warnings

    def test_inject_no_feedback_file_exits_zero(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        args = argparse.Namespace(repo_root=str(tmp_path), dry_run=False)
        rc = agentctl.cmd_feedback_inject(args)
        assert rc == 0

    def test_ack_no_feedback_file_exits_zero(self, tmp_path):
        (tmp_path / ".vibe").mkdir()
        args = argparse.Namespace(repo_root=str(tmp_path))
        rc = agentctl.cmd_feedback_ack(args)
        assert rc == 0
