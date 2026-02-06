"""Tests for strict active-issue schema validation."""
from __future__ import annotations

import sys
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import validate  # type: ignore


def _write_plan(repo_root: Path) -> None:
    (repo_root / ".vibe" / "PLAN.md").write_text(
        """# PLAN

## Stage 1 — Demo stage

### 1.0 — Demo checkpoint

* **Objective:**
  Demo objective.

* **Deliverables:**
  * Demo deliverable.

* **Acceptance:**
  * Demo acceptance.

* **Demo commands:**
  * `echo demo`

* **Evidence:**
  * Demo evidence.
""",
        encoding="utf-8",
    )


def _write_state(repo_root: Path, issues_block: str) -> None:
    (repo_root / ".vibe" / "STATE.md").write_text(
        f"""# STATE

## Current focus

- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Active issues
{issues_block}
""",
        encoding="utf-8",
    )


def test_validate_non_strict_warns_for_missing_issue_fields(temp_repo: Path) -> None:
    _write_plan(temp_repo)
    _write_state(
        temp_repo,
        """
- [ ] ISSUE-101: Missing fields
  - Severity: MINOR
  - Owner: agent
""",
    )
    result = validate(temp_repo, strict=False)
    assert result.ok is True
    assert any("ISSUE-101" in warning and "missing required field" in warning for warning in result.warnings)


def test_validate_strict_errors_for_missing_issue_fields(temp_repo: Path) -> None:
    _write_plan(temp_repo)
    _write_state(
        temp_repo,
        """
- [ ] ISSUE-102: Missing fields
  - Severity: MAJOR
  - Owner: agent
""",
    )
    result = validate(temp_repo, strict=True)
    assert result.ok is False
    assert any("ISSUE-102" in error and "missing required field" in error for error in result.errors)


def test_validate_strict_passes_with_complete_issue_schema(temp_repo: Path) -> None:
    _write_plan(temp_repo)
    _write_state(
        temp_repo,
        """
- [ ] ISSUE-103: Fully specified issue
  - Severity: QUESTION
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Need reproduction steps.
  - Evidence Needed: Command output showing failure.
  - Notes: Optional notes field.
""",
    )
    result = validate(temp_repo, strict=True)
    assert result.ok is True
