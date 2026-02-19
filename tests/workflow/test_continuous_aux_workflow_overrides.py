"""Regression tests for continuous-test-generation/documentation workflow overrides."""
from __future__ import annotations

import json
from pathlib import Path

from agentctl import Issue, StateInfo, _resolve_next_prompt_selection, build_parser  # type: ignore


def _write_state(repo_root: Path, body: str) -> None:
    state_path = repo_root / ".vibe" / "STATE.md"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(body, encoding="utf-8")


def _write_plan(repo_root: Path, body: str) -> None:
    plan_path = repo_root / ".vibe" / "PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(body, encoding="utf-8")


def _write_prompt_catalog(repo_root: Path, body: str) -> None:
    prompts_dir = repo_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "template_prompts.md").write_text(body, encoding="utf-8")


def _write_workflow(repo_root: Path, name: str, body: str) -> None:
    workflows_dir = repo_root / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / f"{name}.yaml").write_text(body, encoding="utf-8")


def _write_loop_result(repo_root: Path, findings: list[dict[str, str]]) -> None:
    path = repo_root / ".vibe" / "LOOP_RESULT.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "loop": "implement",
        "report": {
            "top_findings": findings,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_json_command(capsys, argv: list[str]) -> tuple[int, dict[str, object]]:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.fn(args))
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def _seed_continuous_test_generation_workflow(repo_root: Path) -> None:
    _write_prompt_catalog(
        repo_root,
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
        repo_root,
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


def _seed_continuous_documentation_workflow(repo_root: Path) -> None:
    _write_prompt_catalog(
        repo_root,
        """## prompt.docs_gap_analysis - Docs Gap Analysis
```md
gap
```

## prompt.docs_gap_fix - Docs Gap Fix
```md
fix
```

## prompt.docs_refactor_analysis - Docs Refactor Analysis
```md
analyze
```

## prompt.docs_refactor_fix - Docs Refactor Fix
```md
refactor-fix
```
""",
    )
    _write_workflow(
        repo_root,
        "continuous-documentation",
        """name: continuous-documentation
description: docs
triggers:
  - type: manual
steps:
  - prompt_id: prompt.docs_gap_analysis
  - prompt_id: prompt.docs_gap_fix
  - prompt_id: prompt.docs_refactor_analysis
  - prompt_id: prompt.docs_refactor_fix
""",
    )


def _major_issue() -> Issue:
    return Issue(
        impact="MAJOR",
        title="Needs cleanup",
        line="- [ ] ISSUE-020: Needs cleanup",
        issue_id="ISSUE-020",
        owner="agent",
        status="OPEN",
        checked=False,
        impact_specified=True,
    )


def _blocker_issue() -> Issue:
    return Issue(
        impact="BLOCKER",
        title="Blocked",
        line="- [ ] ISSUE-021: Blocked",
        issue_id="ISSUE-021",
        owner="agent",
        status="OPEN",
        checked=False,
        impact_specified=True,
    )


def test_continuous_test_generation_ignores_plan_exhaustion_stop(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: DONE
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _seed_continuous_test_generation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-test-generation")

    assert role in {"implement", "review"}
    assert prompt_id in {"prompt.test_gap_analysis", "prompt.test_generation", "prompt.test_review"}
    assert "strict cycle" in reason


def test_continuous_test_generation_ignores_non_blocking_issue_routing(temp_repo: Path) -> None:
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
    _seed_continuous_test_generation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(_major_issue(),))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-test-generation")

    assert role in {"implement", "review"}
    assert prompt_id in {"prompt.test_gap_analysis", "prompt.test_generation", "prompt.test_review"}
    assert "strict cycle" in reason


def test_continuous_test_generation_routes_blocker_to_triage(temp_repo: Path) -> None:
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
    _seed_continuous_test_generation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(_blocker_issue(),))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-test-generation")

    assert role == "issues_triage"
    assert prompt_id == "prompt.issues_triage"
    assert "BLOCKER issue present" in reason


def test_cmd_next_continuous_test_generation_recommended_roles_not_plan_coupled(temp_repo: Path, capsys) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: DONE
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _seed_continuous_test_generation_workflow(temp_repo)

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--workflow", "continuous-test-generation"],
    )

    assert exit_code == 0
    assert payload["recommended_prompt_id"] in {
        "prompt.test_gap_analysis",
        "prompt.test_generation",
        "prompt.test_review",
    }
    recommended_roles = payload["recommended_roles"]  # type: ignore[index]
    assert len(recommended_roles) == 1
    assert recommended_roles[0]["checkpoint"] == "1.0"
    assert recommended_roles[0]["prompt_id"] == payload["recommended_prompt_id"]


def test_continuous_documentation_ignores_plan_exhaustion_stop(temp_repo: Path) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: DONE
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _seed_continuous_documentation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-documentation")

    assert role == "implement"
    assert prompt_id in {
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    }
    assert "strict cycle" in reason


def test_continuous_documentation_ignores_non_blocking_issue_routing(temp_repo: Path) -> None:
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
    _seed_continuous_documentation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(_major_issue(),))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-documentation")

    assert role == "implement"
    assert prompt_id in {
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    }
    assert "strict cycle" in reason


def test_continuous_documentation_routes_blocker_to_triage(temp_repo: Path) -> None:
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
    _seed_continuous_documentation_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(_blocker_issue(),))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-documentation")

    assert role == "issues_triage"
    assert prompt_id == "prompt.issues_triage"
    assert "BLOCKER issue present" in reason


def test_continuous_documentation_stops_when_only_minor_findings(temp_repo: Path) -> None:
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
    _seed_continuous_documentation_workflow(temp_repo)
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Tighten section headings",
                "evidence": "No major gaps remain",
                "action": "Optional cleanup only",
            }
        ],
    )

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-documentation")

    assert role == "stop"
    assert prompt_id == "stop"
    assert "threshold reached" in title
    assert "only [MINOR]" in reason


def test_cmd_next_continuous_documentation_recommended_roles_not_plan_coupled(temp_repo: Path, capsys) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: DONE
""",
    )
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _seed_continuous_documentation_workflow(temp_repo)

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--workflow", "continuous-documentation"],
    )

    assert exit_code == 0
    assert payload["recommended_prompt_id"] in {
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    }
    recommended_roles = payload["recommended_roles"]  # type: ignore[index]
    assert len(recommended_roles) == 1
    assert recommended_roles[0]["checkpoint"] == "1.0"
    assert recommended_roles[0]["prompt_id"] == payload["recommended_prompt_id"]
