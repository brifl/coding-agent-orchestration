"""Tests for agentctl next-role routing extensions."""
from __future__ import annotations

import os
import json
import sys
import time
from pathlib import Path

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import WORK_LOG_CONSOLIDATION_CAP, StateInfo, _recommend_next, _resolve_next_prompt_selection  # type: ignore


def _write_state(repo_root: Path, body: str) -> None:
    state_path = repo_root / ".vibe" / "STATE.md"
    state_path.write_text(body, encoding="utf-8")


def _write_plan(repo_root: Path, body: str) -> None:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_path.write_text(body, encoding="utf-8")


def _write_prompt_catalog(repo_root: Path, body: str) -> None:
    prompts_dir = repo_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "template_prompts.md").write_text(body, encoding="utf-8")


def _write_workflow(repo_root: Path, name: str, body: str) -> None:
    workflows_dir = repo_root / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / f"{name}.yaml").write_text(body, encoding="utf-8")


def _write_loop_result(repo_root: Path, findings: list[dict[str, str]], *, loop: str = "implement") -> None:
    payload = {
        "loop": loop,
        "result": "ready_for_review",
        "stage": "1",
        "checkpoint": "1.0",
        "status": "IN_PROGRESS",
        "next_role_hint": "review|issues_triage",
        "report": {
            "acceptance_matrix": [
                {
                    "item": "scan completed",
                    "status": "PASS",
                    "evidence": "scan output",
                    "critical": True,
                    "confidence": 0.95,
                    "evidence_strength": "HIGH",
                }
            ],
            "top_findings": findings,
            "state_transition": {
                "before": {"stage": "1", "checkpoint": "1.0", "status": "IN_PROGRESS"},
                "after": {"stage": "1", "checkpoint": "1.0", "status": "IN_PROGRESS"},
            },
            "loop_result": {
                "loop": loop,
                "result": "ready_for_review",
                "stage": "1",
                "checkpoint": "1.0",
                "status": "IN_PROGRESS",
                "next_role_hint": "review|issues_triage",
            },
        },
    }
    path = repo_root / ".vibe" / "LOOP_RESULT.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


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
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "context_capture"
    assert "RUN_CONTEXT_CAPTURE" in reason


def test_work_log_bloat_routes_to_consolidation(temp_repo: Path) -> None:
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
    # Avoid automatic context-capture recommendation so we can test consolidation routing.
    context_path = temp_repo / ".vibe" / "CONTEXT.md"
    context_path.write_text("# CONTEXT\n", encoding="utf-8")

    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "consolidation"
    assert "consolidation needed" in reason


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
    role, reason, _ = _recommend_next(state, temp_repo)
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
    role, reason, _ = _recommend_next(state, temp_repo)
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
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "context_capture"
    assert "stale" in reason.lower()


def test_workflow_overlay_preserves_dispatcher_role(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_REVIEW
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.stage_design - Stage Design
```md
stage
```

## prompt.checkpoint_review - Checkpoint Review
```md
review
```
""",
    )
    _write_workflow(
        temp_repo,
        "standard",
        """name: standard
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.stage_design
""",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_REVIEW", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "standard")
    assert role == "review"
    assert prompt_id == "prompt.checkpoint_review"
    assert "using dispatcher role review" in reason


def test_workflow_overlay_chooses_first_step_matching_dispatcher_role(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.stage_design - Stage Design
```md
design
```

## prompt.checkpoint_implementation - Checkpoint Implementation
```md
implement
```
""",
    )
    _write_workflow(
        temp_repo,
        "standard",
        """name: standard
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.stage_design
  - prompt_id: prompt.checkpoint_implementation
""",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "standard")
    assert role == "implement"
    assert prompt_id == "prompt.checkpoint_implementation"
    assert "selected prompt.checkpoint_implementation" in reason


def test_workflow_overlay_rejects_unknown_prompt_ids(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.checkpoint_implementation - Checkpoint Implementation
```md
impl
```
""",
    )
    _write_workflow(
        temp_repo,
        "broken",
        """name: broken
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_checkpoint
""",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    try:
        _resolve_next_prompt_selection(state, temp_repo, "broken")
    except RuntimeError as exc:
        assert "unmapped prompt id 'prompt.refactor_checkpoint'" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for unknown workflow prompt id")


def test_continuous_refactor_stops_when_only_minor_ideas(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.refactor_scan - Refactor Scan
```md
scan
```

## prompt.refactor_execute - Refactor Execute
```md
execute
```

## prompt.refactor_verify - Refactor Verify
```md
verify
```
""",
    )
    _write_workflow(
        temp_repo,
        "continuous-refactor",
        """name: continuous-refactor
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_scan
  - prompt_id: prompt.refactor_execute
  - prompt_id: prompt.refactor_verify
""",
    )
    # Prime strict cycle to "execute" step so stop-gate is evaluated after scan output.
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, _reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"

    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Rename helper for readability",
                "evidence": "Low-risk cleanup",
                "action": "Schedule later",
            }
        ],
    )

    role, prompt_id, title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    assert role == "stop"
    assert prompt_id == "stop"
    assert "threshold reached" in title
    assert "only [MINOR]" in reason


def test_continuous_refactor_continues_with_moderate_idea(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.refactor_scan - Refactor Scan
```md
scan
```

## prompt.refactor_execute - Refactor Execute
```md
execute
```

## prompt.refactor_verify - Refactor Verify
```md
verify
```
""",
    )
    _write_workflow(
        temp_repo,
        "continuous-refactor",
        """name: continuous-refactor
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_scan
  - prompt_id: prompt.refactor_execute
  - prompt_id: prompt.refactor_verify
""",
    )
    # First step in strict cycle is scan.
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, _reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"

    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MODERATE] Extract module boundary",
                "evidence": "Improves maintainability across callsites",
                "action": "Execute next",
            }
        ],
    )

    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    assert role == "implement"
    assert prompt_id == "prompt.refactor_execute"
    assert "selected prompt.refactor_execute" in reason


def test_continuous_refactor_strict_cycle_sequences_prompts(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.refactor_scan - Refactor Scan
```md
scan
```

## prompt.refactor_execute - Refactor Execute
```md
execute
```

## prompt.refactor_verify - Refactor Verify
```md
verify
```
""",
    )
    _write_workflow(
        temp_repo,
        "continuous-refactor",
        """name: continuous-refactor
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_scan
  - prompt_id: prompt.refactor_execute
  - prompt_id: prompt.refactor_verify
""",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())

    role_1, prompt_1, _title_1, _reason_1 = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    role_2, prompt_2, _title_2, _reason_2 = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    role_3, prompt_3, _title_3, _reason_3 = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")

    assert (role_1, prompt_1) == ("implement", "prompt.refactor_scan")
    assert (role_2, prompt_2) == ("implement", "prompt.refactor_execute")
    assert (role_3, prompt_3) == ("review", "prompt.refactor_verify")


def test_refactor_cycle_keeps_running_with_minor_only_ideas(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.refactor_scan - Refactor Scan
```md
scan
```

## prompt.checkpoint_implementation - Checkpoint Implementation
```md
impl
```
""",
    )
    _write_workflow(
        temp_repo,
        "refactor-cycle",
        """name: refactor-cycle
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_scan
    every: 3
  - prompt_id: prompt.checkpoint_implementation
""",
    )
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Rename helper for readability",
                "evidence": "Low-risk cleanup",
                "action": "Do later",
            }
        ],
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "refactor-cycle")
    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"
    assert "selected prompt.refactor_scan" in reason


def test_continuous_test_generation_stops_when_only_minor_gaps(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.test_gap_analysis - Test Gap Analysis
```md
gap
```

## prompt.test_generation - Test Generation
```md
gen
```

## prompt.test_review - Test Review
```md
review
```
""",
    )
    _write_workflow(
        temp_repo,
        "continuous-test-generation",
        """name: continuous-test-generation
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.test_gap_analysis
    every: 3
  - prompt_id: prompt.test_generation
  - prompt_id: prompt.test_review
""",
    )
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Add edge-path assertion",
                "evidence": "Low-risk gap",
                "action": "Schedule later",
            }
        ],
        loop="design",
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-test-generation")
    assert role == "stop"
    assert prompt_id == "stop"
    assert "threshold reached" in title
    assert "only [MINOR]" in reason


def test_continuous_test_generation_continues_with_moderate_gap(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.1
- Status: IN_PROGRESS
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
### 1.1 — Second
""",
    )
    _write_prompt_catalog(
        temp_repo,
        """## prompt.test_gap_analysis - Test Gap Analysis
```md
gap
```

## prompt.test_generation - Test Generation
```md
gen
```

## prompt.test_review - Test Review
```md
review
```
""",
    )
    _write_workflow(
        temp_repo,
        "continuous-test-generation",
        """name: continuous-test-generation
description: test
triggers:
  - type: manual
steps:
  - prompt_id: prompt.test_gap_analysis
    every: 3
  - prompt_id: prompt.test_generation
  - prompt_id: prompt.test_review
""",
    )
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MODERATE] Add failing-path integration test",
                "evidence": "Covers real regression risk",
                "action": "Implement now",
            }
        ],
        loop="design",
    )

    state = StateInfo(stage="1", checkpoint="1.1", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-test-generation")
    assert role == "implement"
    assert prompt_id == "prompt.test_generation"
    assert "selected prompt.test_generation" in reason


class TestWorkLogConsolidationRouting:
    """Work log bloat should route to consolidation, not improvements."""

    def test_work_log_over_cap_routes_to_consolidation(self, tmp_path):
        vibe = tmp_path / ".vibe"
        vibe.mkdir()
        entries = "\n".join(f"- Entry {i}" for i in range(WORK_LOG_CONSOLIDATION_CAP + 5))
        _write_state(
            tmp_path,
            f"# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n"
            f"- Status: NOT_STARTED\n\n## Work log (current session)\n\n{entries}\n\n"
            f"## Active issues\n\n(none)\n",
        )
        _write_plan(
            tmp_path,
            "# PLAN\n\n## Stage 1 — Test\n\n### 1.0 — Test\n\n"
            "* **Objective:**\n  T\n* **Deliverables:**\n  T\n"
            "* **Acceptance:**\n  T\n* **Demo commands:**\n  * `echo t`\n"
            "* **Evidence:**\n  T\n",
        )
        # Prevent context_capture from firing first
        (vibe / "CONTEXT.md").write_text("# CONTEXT\n", encoding="utf-8")
        state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
        role, reason, _ = _recommend_next(state, tmp_path)
        assert role == "consolidation", f"Expected consolidation, got {role}: {reason}"
        assert "consolidation needed" in reason

    def test_work_log_under_cap_routes_to_implement(self, tmp_path):
        vibe = tmp_path / ".vibe"
        vibe.mkdir()
        entries = "\n".join(f"- Entry {i}" for i in range(WORK_LOG_CONSOLIDATION_CAP - 2))
        _write_state(
            tmp_path,
            f"# STATE\n\n## Current focus\n\n- Stage: 1\n- Checkpoint: 1.0\n"
            f"- Status: NOT_STARTED\n\n## Work log (current session)\n\n{entries}\n\n"
            f"## Active issues\n\n(none)\n",
        )
        _write_plan(
            tmp_path,
            "# PLAN\n\n## Stage 1 — Test\n\n### 1.0 — Test\n\n"
            "* **Objective:**\n  T\n* **Deliverables:**\n  T\n"
            "* **Acceptance:**\n  T\n* **Demo commands:**\n  * `echo t`\n"
            "* **Evidence:**\n  T\n",
        )
        # Prevent context_capture from firing first
        (vibe / "CONTEXT.md").write_text("# CONTEXT\n", encoding="utf-8")
        state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
        role, reason, _ = _recommend_next(state, tmp_path)
        assert role == "implement", f"Expected implement, got {role}: {reason}"


# ── Improvement 3: DECISION_REQUIRED human approval gate ──────────────────


def test_decision_required_issue_routes_to_stop(temp_repo: Path) -> None:
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Workflow state
- [x] STAGE_DESIGNED
""",
    )
    issue = Issue(
        impact="MAJOR",
        title="Should we support multi-tenant namespacing?",
        line="- [ ] ISSUE-007: Should we support multi-tenant namespacing?",
        issue_id="ISSUE-007",
        owner="human",
        status="DECISION_REQUIRED",
        unblock_condition="Human selects approach A or B",
        evidence_needed="Explicit decision in STATE.md",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "stop"
    assert "DECISION_REQUIRED" in reason
    assert "ISSUE-007" in reason


def test_decision_required_takes_precedence_over_implement(temp_repo: Path) -> None:
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS

## Workflow state
- [x] STAGE_DESIGNED
""",
    )
    issue = Issue(
        impact="MINOR",
        title="Which logging format?",
        line="- [ ] ISSUE-008: Which logging format?",
        issue_id="ISSUE-008",
        owner="human",
        status="DECISION_REQUIRED",
        unblock_condition="Human picks format",
        evidence_needed="Decision recorded",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "stop"
    assert "DECISION_REQUIRED" in reason


def test_no_decision_required_does_not_stop(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Workflow state
- [x] STAGE_DESIGNED
""",
    )
    # Prevent context_capture trigger
    (temp_repo / ".vibe" / "CONTEXT.md").write_text("# CONTEXT\n", encoding="utf-8")
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role != "stop"


# ── Improvement 4: Retrospective trigger ──────────────────────────────────


def test_retrospective_flag_routes_to_retrospective(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 2
- Checkpoint: 2.0
- Status: NOT_STARTED

## Workflow state
- [ ] RETROSPECTIVE_DONE
- [ ] STAGE_DESIGNED
""",
    )
    state = StateInfo(stage="2", checkpoint="2.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "retrospective"
    assert "RETROSPECTIVE_DONE" in reason


def test_retrospective_done_flag_skips_retrospective(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 2
- Checkpoint: 2.0
- Status: NOT_STARTED

## Workflow state
- [x] RETROSPECTIVE_DONE
- [ ] STAGE_DESIGNED
""",
    )
    state = StateInfo(stage="2", checkpoint="2.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "design"  # advances to stage_design since STAGE_DESIGNED is not set


def test_retrospective_fires_before_stage_design(temp_repo: Path) -> None:
    """Retrospective should run first so lessons can inform stage design."""
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 2
- Checkpoint: 2.0
- Status: NOT_STARTED

## Workflow state
- [ ] RETROSPECTIVE_DONE
- [ ] STAGE_DESIGNED
""",
    )
    state = StateInfo(stage="2", checkpoint="2.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "retrospective"


def test_retrospective_absent_flag_does_not_trigger(temp_repo: Path) -> None:
    """Repos without RETROSPECTIVE_DONE in workflow state are not affected (backward compat)."""
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED

## Workflow state
- [x] STAGE_DESIGNED
""",
    )
    # Prevent context_capture trigger
    (temp_repo / ".vibe" / "CONTEXT.md").write_text("# CONTEXT\n", encoding="utf-8")
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "implement"  # no retrospective trigger; STAGE_DESIGNED already set
