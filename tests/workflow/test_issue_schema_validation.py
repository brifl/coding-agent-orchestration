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
  - Impact: MINOR
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
  - Impact: MAJOR
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
  - Impact: QUESTION
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Need reproduction steps.
  - Evidence Needed: Command output showing failure.
  - Notes: Optional notes field.
""",
    )
    result = validate(temp_repo, strict=True)
    assert result.ok is True


# ── Improvement 3: DECISION_REQUIRED issue status ─────────────────────────


def test_decision_required_status_is_valid(temp_repo: Path) -> None:
    _write_plan(temp_repo)
    _write_state(
        temp_repo,
        """
- [ ] ISSUE-200: Architecture direction needed
  - Impact: MAJOR
  - Status: DECISION_REQUIRED
  - Owner: human
  - Unblock Condition: Human selects approach A or B.
  - Evidence Needed: Decision recorded in STATE.md Decisions section.
""",
    )
    result = validate(temp_repo, strict=True)
    assert result.ok is True, f"Unexpected errors: {result.errors}"
    assert not any("invalid Status" in e for e in result.errors)


def test_decision_required_checked_is_invalid(temp_repo: Path) -> None:
    _write_plan(temp_repo)
    _write_state(
        temp_repo,
        """
- [x] ISSUE-201: Architecture direction needed
  - Impact: MAJOR
  - Status: DECISION_REQUIRED
  - Owner: human
  - Unblock Condition: Human selects approach A or B.
  - Evidence Needed: Decision recorded in STATE.md Decisions section.
""",
    )
    result = validate(temp_repo, strict=True)
    assert any("DECISION_REQUIRED" in e for e in result.errors)


def test_decision_required_in_loop_result_loops() -> None:
    from agentctl import LOOP_RESULT_LOOPS  # type: ignore
    assert "retrospective" in LOOP_RESULT_LOOPS


# ── Improvement 5: Checkpoint complexity budget ───────────────────────────


def _write_plan_with_many_items(repo_root: Path, deliverables: int, acceptance: int, demo: int) -> None:
    deliverable_lines = "\n".join(f"  * Deliverable {i}" for i in range(1, deliverables + 1))
    acceptance_lines = "\n".join(f"  * Acceptance {i}" for i in range(1, acceptance + 1))
    demo_lines = "\n".join(f"  * `echo demo{i}`" for i in range(1, demo + 1))
    (repo_root / ".vibe" / "PLAN.md").write_text(
        f"""# PLAN

## Stage 1 — Demo stage

### 1.0 — Large checkpoint

* **Objective:**
  Test many items.

* **Deliverables:**
{deliverable_lines}

* **Acceptance:**
{acceptance_lines}

* **Demo commands:**
{demo_lines}

* **Evidence:**
  * Output of demo commands.
""",
        encoding="utf-8",
    )


def _write_basic_state(repo_root: Path) -> None:
    (repo_root / ".vibe" / "STATE.md").write_text(
        """# STATE

## Current focus

- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED
""",
        encoding="utf-8",
    )


def test_complexity_within_budget_produces_no_complexity_warnings(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=3, acceptance=4, demo=2)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False)
    assert result.plan_check is not None
    assert result.plan_check.complexity_warnings == ()


def test_too_many_deliverables_produces_complexity_warning(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=6, acceptance=4, demo=2)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False)
    assert result.plan_check is not None
    assert any("Deliverables" in w for w in result.plan_check.complexity_warnings)
    # In non-strict-complexity mode it should be a warning, not an error
    assert not any("Deliverables" in e for e in result.errors)
    assert any("Deliverables" in w for w in result.warnings)


def test_too_many_acceptance_produces_complexity_warning(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=3, acceptance=7, demo=2)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False)
    assert result.plan_check is not None
    assert any("Acceptance" in w for w in result.plan_check.complexity_warnings)


def test_too_many_demo_commands_produces_complexity_warning(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=3, acceptance=4, demo=5)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False)
    assert result.plan_check is not None
    assert any("Demo commands" in w for w in result.plan_check.complexity_warnings)


def test_strict_complexity_promotes_to_error(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=6, acceptance=4, demo=2)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False, strict_complexity=True)
    assert result.ok is False
    assert any("Deliverables" in e for e in result.errors)


def test_strict_complexity_passes_within_budget(temp_repo: Path) -> None:
    _write_plan_with_many_items(temp_repo, deliverables=5, acceptance=6, demo=4)
    _write_basic_state(temp_repo)
    result = validate(temp_repo, strict=False, strict_complexity=True)
    assert result.ok is True
    assert result.plan_check is not None
    assert result.plan_check.complexity_warnings == ()
