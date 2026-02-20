"""Regression tests for continuous-refactor workflow override behavior."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from agentctl import StateInfo, _resolve_next_prompt_selection, build_parser  # type: ignore


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


def _seed_continuous_refactor_workflow(repo_root: Path) -> None:
    _write_prompt_catalog(
        repo_root,
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
        repo_root,
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


def _seed_workflow_engine(repo_root: Path) -> None:
    tools_dir = repo_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parents[2] / "tools" / "workflow_engine.py"
    shutil.copyfile(src, tools_dir / "workflow_engine.py")


def _run_json_command(capsys, argv: list[str]) -> tuple[int, dict[str, object]]:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.fn(args))
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def test_continuous_refactor_ignores_plan_exhaustion_stop(temp_repo: Path) -> None:
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
    _seed_continuous_refactor_workflow(temp_repo)

    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")

    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"
    assert "strict cycle" in reason


def test_continuous_refactor_ignores_non_blocking_issue_routing(temp_repo: Path) -> None:
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
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )
    _seed_continuous_refactor_workflow(temp_repo)

    major_issue = Issue(
        impact="MAJOR",
        title="Needs cleanup",
        line="- [ ] ISSUE-010: Needs cleanup",
        issue_id="ISSUE-010",
        owner="agent",
        status="OPEN",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(major_issue,))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")

    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"
    assert "strict cycle" in reason


def test_continuous_refactor_routes_blocker_to_triage(temp_repo: Path) -> None:
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
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo
### 1.0 — First
""",
    )

    blocker = Issue(
        impact="BLOCKER",
        title="Crashes on startup",
        line="- [ ] ISSUE-011: Crashes on startup",
        issue_id="ISSUE-011",
        owner="agent",
        status="OPEN",
        checked=False,
        impact_specified=True,
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=(blocker,))
    role, prompt_id, _title, reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")

    assert role == "issues_triage"
    assert prompt_id == "prompt.issues_triage"
    assert "BLOCKER issue present" in reason


def test_cmd_next_continuous_refactor_recommended_roles_not_plan_coupled(temp_repo: Path, capsys) -> None:
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
    _seed_continuous_refactor_workflow(temp_repo)

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--workflow", "continuous-refactor"],
    )

    assert exit_code == 0
    assert payload["recommended_prompt_id"] in {
        "prompt.refactor_scan",
        "prompt.refactor_execute",
        "prompt.refactor_verify",
    }
    recommended_roles = payload["recommended_roles"]  # type: ignore[index]
    assert len(recommended_roles) == 1
    assert recommended_roles[0]["checkpoint"] == "1.0"
    assert recommended_roles[0]["prompt_id"] == payload["recommended_prompt_id"]


def test_skill_packaged_cmd_next_continuous_refactor_uses_strict_cycle(temp_repo: Path) -> None:
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
    _seed_continuous_refactor_workflow(temp_repo)
    _seed_workflow_engine(temp_repo)

    skill_agentctl = Path(__file__).resolve().parents[2] / ".codex" / "skills" / "vibe-loop" / "scripts" / "agentctl.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(skill_agentctl),
            "--repo-root",
            str(temp_repo),
            "--format",
            "json",
            "next",
            "--workflow",
            "continuous-refactor",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["recommended_prompt_id"] in {
        "prompt.refactor_scan",
        "prompt.refactor_execute",
        "prompt.refactor_verify",
    }
    assert payload["recommended_role"] in {"implement", "review"}
    assert "strict cycle" in payload["reason"]
