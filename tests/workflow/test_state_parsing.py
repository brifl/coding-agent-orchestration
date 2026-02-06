"""Tests for STATE.md parsing in agentctl."""
from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import (
    _parse_kv_bullets,
    _clean_status,
    _parse_issues,
    _slice_active_issues_section,
    _validate_issue_schema,
)


class TestParseKvBullets:
    """Tests for _parse_kv_bullets function."""

    def test_basic_parsing(self):
        text = """
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
"""
        result = _parse_kv_bullets(text)
        # Keys are normalized to lowercase with underscores
        assert result["stage"] == "1"
        assert result["checkpoint"] == "1.0"
        assert result["status"] == "IN_PROGRESS"

    def test_with_comments(self):
        text = """
- Stage: 2
- Status: DONE  <!-- comment here -->
"""
        result = _parse_kv_bullets(text)
        # Keys are normalized to lowercase
        assert result["stage"] == "2"
        # Comment is included in raw value (cleaned later by _clean_status)
        assert "DONE" in result["status"]

    def test_empty_text(self):
        result = _parse_kv_bullets("")
        assert result == {}

    def test_no_bullets(self):
        text = "Some text without bullets"
        result = _parse_kv_bullets(text)
        assert result == {}


class TestCleanStatus:
    """Tests for _clean_status function."""

    def test_valid_statuses(self):
        assert _clean_status("NOT_STARTED") == "NOT_STARTED"
        assert _clean_status("IN_PROGRESS") == "IN_PROGRESS"
        assert _clean_status("IN_REVIEW") == "IN_REVIEW"
        assert _clean_status("BLOCKED") == "BLOCKED"
        assert _clean_status("DONE") == "DONE"

    def test_case_insensitive(self):
        assert _clean_status("done") == "DONE"
        assert _clean_status("Done") == "DONE"
        assert _clean_status("in_progress") == "IN_PROGRESS"

    def test_with_whitespace(self):
        assert _clean_status("  DONE  ") == "DONE"
        assert _clean_status("\tIN_REVIEW\n") == "IN_REVIEW"

    def test_invalid_status(self):
        # _clean_status doesn't validate - it just uppercases the first token
        assert _clean_status("INVALID") == "INVALID"
        assert _clean_status("") is None
        assert _clean_status(None) is None


class TestSliceActiveIssuesSection:
    """Tests for _slice_active_issues_section function."""

    def test_basic_section(self):
        text = """# STATE

## Current focus

- Stage: 1

## Active issues

- Issue 1
- Issue 2

## Decisions

- Decision 1
"""
        lines = _slice_active_issues_section(text)
        assert "- Issue 1" in lines
        assert "- Issue 2" in lines
        assert "- Decision 1" not in lines

    def test_no_section(self):
        text = """# STATE

## Current focus

- Stage: 1
"""
        lines = _slice_active_issues_section(text)
        assert lines == []

    def test_empty_section(self):
        text = """# STATE

## Active issues

## Decisions
"""
        lines = _slice_active_issues_section(text)
        # Should return empty lines between sections
        assert all(line.strip() == "" for line in lines)


class TestParseIssues:
    """Tests for _parse_issues function."""

    def test_no_issues(self):
        text = """## Active issues

- None.
"""
        issues = _parse_issues(text)
        assert len(issues) == 0

    def test_checkbox_format(self):
        text = """## Active issues

- [ ] ISSUE-001: Test issue
  - Impact: MAJOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Clarify API contract
  - Evidence Needed: Failing test output
  - Notes: Some notes
"""
        issues = _parse_issues(text)
        assert len(issues) == 1
        # Issue has: impact, title, line (not id)
        assert issues[0].impact == "MAJOR"
        assert issues[0].issue_id == "ISSUE-001"
        assert issues[0].status == "OPEN"
        assert issues[0].owner == "agent"
        assert issues[0].unblock_condition == "Clarify API contract"
        assert issues[0].evidence_needed == "Failing test output"
        assert "ISSUE-001" in issues[0].title

    def test_blocker_format(self):
        # The legacy blocker format without ** markers
        text = """## Active issues

- BLOCKER: Something is broken
"""
        issues = _parse_issues(text)
        assert len(issues) == 1
        assert issues[0].impact == "BLOCKER"

    def test_issue_schema_validation(self):
        text = """## Active issues

- [ ] ISSUE-123: Missing fields example
  - Impact: MINOR
  - Owner: agent
"""
        issues = _parse_issues(text)
        messages = _validate_issue_schema(issues)
        assert len(messages) == 1
        assert "ISSUE-123" in messages[0]
        assert "Status" in messages[0]
        assert "Unblock Condition" in messages[0]
        assert "Evidence Needed" in messages[0]
