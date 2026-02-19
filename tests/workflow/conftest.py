"""Pytest fixtures for workflow tests."""
from __future__ import annotations

import sys
import pytest
from pathlib import Path
from typing import Generator

_tools_dir = Path(__file__).resolve().parents[2] / "tools"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))


@pytest.fixture
def temp_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary repo with .vibe directory structure."""
    vibe_dir = tmp_path / ".vibe"
    vibe_dir.mkdir()
    yield tmp_path


@pytest.fixture
def vibe_state(temp_repo: Path) -> Path:
    """Create a basic STATE.md file and return its path."""
    state_path = temp_repo / ".vibe" / "STATE.md"
    state_path.write_text(
        """# STATE

## Current focus

- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Objective (current checkpoint)

Test objective.

## Deliverables (current checkpoint)

- Test deliverable

## Acceptance (current checkpoint)

- [ ] Test acceptance

## Work log (current session)

- 2026-01-28: Test entry

## Evidence

(None yet)

## Active issues

- None.

## Decisions

- None.
""",
        encoding="utf-8",
    )
    return state_path


@pytest.fixture
def vibe_plan(temp_repo: Path) -> Path:
    """Create a basic PLAN.md file and return its path."""
    plan_path = temp_repo / ".vibe" / "PLAN.md"
    plan_path.write_text(
        """# PLAN

## Stage 1 — Test stage

**Stage objective:** Test objective

### 1.0 — Test checkpoint

* **Objective:**
  Test objective.

* **Deliverables:**
  * Test deliverable

* **Acceptance:**
  * Test acceptance

* **Demo commands:**
  * `echo test`

* **Evidence:**
  * Test evidence

---

### 1.1 — Second checkpoint

* **Objective:**
  Second objective.

* **Deliverables:**
  * Second deliverable

* **Acceptance:**
  * Second acceptance

* **Demo commands:**
  * `echo second`

* **Evidence:**
  * Second evidence

---

## Stage 2 — Second stage

**Stage objective:** Second stage objective

### 2.0 — Stage 2 checkpoint

* **Objective:**
  Stage 2 objective.

* **Deliverables:**
  * Stage 2 deliverable

* **Acceptance:**
  * Stage 2 acceptance

* **Demo commands:**
  * `echo stage2`

* **Evidence:**
  * Stage 2 evidence

---
""",
        encoding="utf-8",
    )
    return plan_path


@pytest.fixture
def vibe_history(temp_repo: Path) -> Path:
    """Create a basic HISTORY.md file and return its path."""
    history_path = temp_repo / ".vibe" / "HISTORY.md"
    history_path.write_text(
        """# HISTORY

## Completed stages

(None yet)

## Resolved issues

(None yet)
""",
        encoding="utf-8",
    )
    return history_path


@pytest.fixture
def full_vibe_setup(vibe_state: Path, vibe_plan: Path, vibe_history: Path) -> Path:
    """Set up complete .vibe directory with STATE, PLAN, and HISTORY."""
    return vibe_state.parent.parent  # Return temp_repo path
