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
    prompt_path = repo_root / ".codex" / "skills" / "vibe-prompts" / "resources" / "template_prompts.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(body, encoding="utf-8")


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


# ── Improvement 1: Human-owned BLOCKERs route to stop ─────────────────────


def test_all_human_owned_blockers_route_to_stop(temp_repo: Path) -> None:
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    issue = Issue(
        impact="BLOCKER",
        title="Need prod credentials from human",
        line="- [ ] ISSUE-300: Need prod credentials from human",
        issue_id="ISSUE-300",
        owner="human",
        status="BLOCKED",
        unblock_condition="Human provides credentials",
        evidence_needed="Credentials supplied",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "stop"
    assert "human" in reason.lower()
    assert "ISSUE-300" in reason


def test_agent_owned_blocker_routes_to_issues_triage(temp_repo: Path) -> None:
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    issue = Issue(
        impact="BLOCKER",
        title="Test suite crashes on import",
        line="- [ ] ISSUE-301: Test suite crashes on import",
        issue_id="ISSUE-301",
        owner="agent",
        status="OPEN",
        unblock_condition="Fix the import error",
        evidence_needed="Tests pass",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "issues_triage"


def test_major_issue_in_progress_routes_to_implement(temp_repo: Path) -> None:
    """MAJOR issues already in progress should not pin dispatcher to triage."""
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    issue = Issue(
        impact="MAJOR",
        title="Harden contract validation",
        line="- [ ] ISSUE-400: Harden contract validation",
        issue_id="ISSUE-400",
        owner="agent",
        status="IN_PROGRESS",
        unblock_condition="Implement and test strict checks",
        evidence_needed="Targeted tests pass",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "implement", reason


def test_major_issue_open_routes_to_issues_triage(temp_repo: Path) -> None:
    """MAJOR issues still OPEN should route to triage first."""
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    issue = Issue(
        impact="MAJOR",
        title="Contract ambiguity needs triage",
        line="- [ ] ISSUE-401: Contract ambiguity needs triage",
        issue_id="ISSUE-401",
        owner="agent",
        status="OPEN",
        unblock_condition="Clarify scope and evidence",
        evidence_needed="Updated STATE issue notes",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(issue,))
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "issues_triage"
    assert "MAJOR" in reason


def test_mixed_blocker_ownership_routes_to_issues_triage(temp_repo: Path) -> None:
    """If any BLOCKER is agent-owned, triage (not stop) so agent can work on it."""
    from agentctl import Issue  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )
    human_issue = Issue(
        impact="BLOCKER",
        title="Need human approval",
        line="- [ ] ISSUE-302: Need human approval",
        issue_id="ISSUE-302",
        owner="human",
        status="BLOCKED",
        unblock_condition="Human approves",
        evidence_needed="Approval in STATE.md",
        checked=False,
        impact_specified=True,
    )
    agent_issue = Issue(
        impact="BLOCKER",
        title="Agent must fix build",
        line="- [ ] ISSUE-303: Agent must fix build",
        issue_id="ISSUE-303",
        owner="agent",
        status="OPEN",
        unblock_condition="Build passes",
        evidence_needed="CI green",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(
        stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None,
        issues=(human_issue, agent_issue),
    )
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "issues_triage"


# ── Improvement 3: Stop decisions recorded in LOOP_RESULT.json ────────────


def test_stop_route_writes_loop_result_json(temp_repo: Path) -> None:
    from agentctl import _write_stop_loop_result  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: NOT_STARTED
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    _write_stop_loop_result(temp_repo, state, "plan exhausted")
    path = temp_repo / ".vibe" / "LOOP_RESULT.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["loop"] == "stop"
    assert data["result"] == "stop"
    assert data["reason"] == "plan exhausted"
    assert data["next_role_hint"] == "stop"
    assert data["stage"] == "1"
    assert data["checkpoint"] == "1.0"


def test_stop_loop_result_overwrites_existing(temp_repo: Path) -> None:
    from agentctl import _write_stop_loop_result  # type: ignore

    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 2
- Checkpoint: 2.1
- Status: DONE
""",
    )
    path = temp_repo / ".vibe" / "LOOP_RESULT.json"
    path.write_text('{"loop": "implement", "result": "old"}', encoding="utf-8")
    state = StateInfo(stage="2", checkpoint="2.1", status="DONE", evidence_path=None, issues=())
    _write_stop_loop_result(temp_repo, state, "last checkpoint reached")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["loop"] == "stop"
    assert data["reason"] == "last checkpoint reached"


# ── Stage 22 E2E: _extract_demo_commands ─────────────────────────────────────


def test_extract_demo_commands_checkpoint_not_found() -> None:
    from agentctl import _extract_demo_commands  # type: ignore

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `echo first`\n"
    result = _extract_demo_commands(plan_text, "2.0")
    assert result == []


def test_extract_demo_commands_single_command() -> None:
    from agentctl import _extract_demo_commands  # type: ignore

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `echo hello`\n"
    result = _extract_demo_commands(plan_text, "1.0")
    assert result == ["echo hello"]


def test_extract_demo_commands_multiple_commands() -> None:
    from agentctl import _extract_demo_commands  # type: ignore

    plan_text = (
        "### 1.0 — First\n\n* **Demo commands:**\n  * `echo one`\n  * `echo two`\n"
        "\n### 1.1 — Second\n"
    )
    result = _extract_demo_commands(plan_text, "1.0")
    assert result == ["echo one", "echo two"]


def test_extract_demo_commands_stops_at_next_checkpoint() -> None:
    from agentctl import _extract_demo_commands  # type: ignore

    plan_text = (
        "### 1.0 — First\n\n* **Demo commands:**\n  * `echo first`\n\n"
        "### 1.1 — Second\n\n* **Demo commands:**\n  * `echo second`\n"
    )
    assert _extract_demo_commands(plan_text, "1.0") == ["echo first"]
    assert _extract_demo_commands(plan_text, "1.1") == ["echo second"]


# ── Stage 22 E2E: _run_smoke_test_gate ───────────────────────────────────────


def test_smoke_gate_no_checkpoint(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `echo ok`\n"
    state = StateInfo(stage="1", checkpoint=None, status="NOT_STARTED", evidence_path=None, issues=())
    passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text)
    assert passed is True
    assert reason is None


def test_smoke_gate_no_demo_commands(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore

    plan_text = "### 1.0 — First\n\n* **Objective:**\n  No commands.\n"
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text)
    assert passed is True
    assert reason is None


def test_smoke_gate_success(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore
    from unittest.mock import MagicMock, patch

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `echo ok`\n"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    with patch("agentctl.subprocess.run", return_value=mock_result):
        passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text)
    assert passed is True
    assert reason is None


def test_smoke_gate_nonzero_exit(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore
    from unittest.mock import MagicMock, patch

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `bad-command`\n"
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "command not found"
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    with patch("agentctl.subprocess.run", return_value=mock_result):
        passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text)
    assert passed is False
    assert reason is not None
    assert "rc=1" in reason
    assert "bad-command" in reason


def test_smoke_gate_timeout(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore
    from unittest.mock import patch
    import subprocess as _subprocess

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `sleep 999`\n"
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    with patch(
        "agentctl.subprocess.run",
        side_effect=_subprocess.TimeoutExpired("sleep 999", 5),
    ):
        passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text, timeout=5)
    assert passed is False
    assert reason is not None
    assert "timed out" in reason
    assert "sleep 999" in reason


def test_smoke_gate_oserror(temp_repo: Path) -> None:
    from agentctl import _run_smoke_test_gate  # type: ignore
    from unittest.mock import patch

    plan_text = "### 1.0 — First\n\n* **Demo commands:**\n  * `nonexistent-binary`\n"
    state = StateInfo(stage="1", checkpoint="1.0", status="NOT_STARTED", evidence_path=None, issues=())
    with patch("agentctl.subprocess.run", side_effect=OSError("No such file")):
        passed, reason = _run_smoke_test_gate(temp_repo, state, plan_text)
    assert passed is False
    assert reason is not None
    assert "could not run" in reason


# ── Stage 22 E2E: _maintenance_cycle_trigger_reason ──────────────────────────


def test_maintenance_cycle_flag_absent_returns_none() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({}, "3")
    assert reason is None
    assert prompt is None


def test_maintenance_cycle_flag_done_returns_none() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({"MAINTENANCE_CYCLE_DONE": True}, "3")
    assert reason is None
    assert prompt is None


def test_maintenance_cycle_no_stage_returns_none() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({"MAINTENANCE_CYCLE_DONE": False}, None)
    assert reason is None
    assert prompt is None


def test_maintenance_cycle_stage_mod_0_refactor() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({"MAINTENANCE_CYCLE_DONE": False}, "3")  # 3 % 3 == 0
    assert reason is not None
    assert "refactor" in reason
    assert prompt == "prompt.refactor_scan"


def test_maintenance_cycle_stage_mod_1_test() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({"MAINTENANCE_CYCLE_DONE": False}, "22")  # 22 % 3 == 1
    assert reason is not None
    assert "test" in reason
    assert prompt == "prompt.test_gap_analysis"


def test_maintenance_cycle_stage_mod_2_docs() -> None:
    from agentctl import _maintenance_cycle_trigger_reason  # type: ignore

    reason, prompt = _maintenance_cycle_trigger_reason({"MAINTENANCE_CYCLE_DONE": False}, "5")  # 5 % 3 == 2
    assert reason is not None
    assert "docs" in reason
    assert prompt == "prompt.docs_gap_analysis"


# ── Stage 22 E2E: Flag lifecycle integration ──────────────────────────────────


def _write_state_flags(repo_root: Path, flags: dict[str, bool], *, stage: str = "3") -> None:
    """Write STATE.md (and stub CONTEXT.md) with given workflow flags for flag lifecycle tests."""
    flag_lines = "\n".join(
        f"- [{'x' if v else ' '}] {k}" for k, v in flags.items()
    )
    _write_state(
        repo_root,
        f"""# STATE

## Current focus
- Stage: {stage}
- Checkpoint: {stage}.0
- Status: NOT_STARTED

## Workflow state
{flag_lines}

## Work log (current session)
- 2026-01-01: entry
""",
    )
    # Ensure CONTEXT.md exists so the context-capture fallback doesn't interfere.
    context_path = repo_root / ".vibe" / "CONTEXT.md"
    if not context_path.exists():
        context_path.write_text("# Context\n", encoding="utf-8")


def test_flag_lifecycle_retro_unset_triggers_retrospective(temp_repo: Path) -> None:
    """RETROSPECTIVE_DONE unset → retrospective loop selected."""
    _write_state_flags(
        temp_repo,
        {
            "RUN_CONTEXT_CAPTURE": False,
            "RETROSPECTIVE_DONE": False,
            "STAGE_DESIGNED": False,
            "MAINTENANCE_CYCLE_DONE": False,
        },
    )
    state = StateInfo(stage="3", checkpoint="3.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "retrospective"
    assert "RETROSPECTIVE_DONE" in reason


def test_flag_lifecycle_retro_done_design_unset_triggers_design(temp_repo: Path) -> None:
    """RETROSPECTIVE_DONE set, STAGE_DESIGNED unset → design loop selected."""
    _write_state_flags(
        temp_repo,
        {
            "RUN_CONTEXT_CAPTURE": False,
            "RETROSPECTIVE_DONE": True,
            "STAGE_DESIGNED": False,
            "MAINTENANCE_CYCLE_DONE": False,
        },
    )
    state = StateInfo(stage="3", checkpoint="3.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "design"
    assert "STAGE_DESIGNED" in reason


def test_flag_lifecycle_design_done_maint_unset_triggers_maintenance(temp_repo: Path) -> None:
    """RETROSPECTIVE_DONE + STAGE_DESIGNED set, MAINTENANCE_CYCLE_DONE unset → implement (maintenance)."""
    _write_state_flags(
        temp_repo,
        {
            "RUN_CONTEXT_CAPTURE": False,
            "RETROSPECTIVE_DONE": True,
            "STAGE_DESIGNED": True,
            "MAINTENANCE_CYCLE_DONE": False,
        },
        stage="3",  # 3 % 3 == 0 → refactor
    )
    state = StateInfo(stage="3", checkpoint="3.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, prompt = _recommend_next(state, temp_repo)
    assert role == "implement"
    assert prompt == "prompt.refactor_scan"


def test_flag_lifecycle_all_flags_set_triggers_implement(temp_repo: Path) -> None:
    """All maintenance flags set → normal implement route."""
    _write_state_flags(
        temp_repo,
        {
            "RUN_CONTEXT_CAPTURE": False,
            "RETROSPECTIVE_DONE": True,
            "STAGE_DESIGNED": True,
            "MAINTENANCE_CYCLE_DONE": True,
        },
    )
    _write_plan(
        temp_repo,
        "# PLAN\n\n## Stage 3 — Demo\n\n### 3.0 — First\n",
    )
    state = StateInfo(stage="3", checkpoint="3.0", status="NOT_STARTED", evidence_path=None, issues=())
    role, reason, _ = _recommend_next(state, temp_repo)
    assert role == "implement"
