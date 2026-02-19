"""Tests for continuous-workflow minor-idea approval flow."""
from __future__ import annotations

import hashlib
import json
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


def _write_loop_result(repo_root: Path, findings: list[dict[str, str]]) -> None:
    state_text = (repo_root / ".vibe" / "STATE.md").read_text(encoding="utf-8")
    state_hash = hashlib.sha256(state_text.encode("utf-8")).hexdigest()
    payload = {
        "loop": "implement",
        "result": "ready_for_review",
        "stage": "1",
        "checkpoint": "1.0",
        "status": "IN_PROGRESS",
        "next_role_hint": "review|issues_triage",
        "report": {
            "top_findings": findings,
        },
        "state_sha256": state_hash,
    }
    path = repo_root / ".vibe" / "LOOP_RESULT.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _run_json_command(capsys, argv: list[str]) -> tuple[int, dict[str, object]]:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.fn(args))
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def _seed_common_repo(temp_repo: Path) -> StateInfo:
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

    state = StateInfo(stage="1", checkpoint="1.0", status="IN_PROGRESS", evidence_path=None, issues=())
    role, prompt_id, _title, _reason = _resolve_next_prompt_selection(state, temp_repo, "continuous-refactor")
    assert role == "implement"
    assert prompt_id == "prompt.refactor_scan"
    return state


def test_cmd_next_threshold_stop_emits_numbered_minor_ideas(temp_repo: Path, capsys) -> None:
    _seed_common_repo(temp_repo)
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Rename helper for readability",
                "evidence": "Low-risk cleanup",
                "action": "Defer unless approved",
            }
        ],
    )

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--workflow", "continuous-refactor"],
    )

    assert exit_code == 0
    assert payload["recommended_role"] == "stop"
    assert payload["approval_required"] is True
    assert "workflow-approve" in str(payload.get("approval_command", ""))
    ideas = payload["minor_ideas"]  # type: ignore[index]
    assert len(ideas) == 1
    assert ideas[0]["id"] == 1
    assert "Rename helper" in ideas[0]["title"]


def test_workflow_approve_allows_next_execute_once(temp_repo: Path, capsys) -> None:
    _seed_common_repo(temp_repo)
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Rename helper for readability",
                "evidence": "Low-risk cleanup",
                "action": "Defer unless approved",
            }
        ],
    )

    approve_code, approve_payload = _run_json_command(
        capsys,
        [
            "--repo-root",
            str(temp_repo),
            "--format",
            "json",
            "workflow-approve",
            "--workflow",
            "continuous-refactor",
            "--ids",
            "1",
        ],
    )
    assert approve_code == 0
    assert approve_payload["ok"] is True
    assert approve_payload["approved_minor_idea_ids"] == [1]

    next_code, next_payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--workflow", "continuous-refactor"],
    )
    assert next_code == 0
    assert next_payload["recommended_role"] == "implement"
    assert next_payload["recommended_prompt_id"] == "prompt.refactor_execute"
    assert next_payload["approval_applied"] is True
    assert next_payload["approved_minor_idea_ids"] == [1]

    approval_path = temp_repo / ".vibe" / "CONTINUOUS_APPROVALS.json"
    approvals = json.loads(approval_path.read_text(encoding="utf-8"))
    assert approvals["approvals"].get("continuous-refactor") is None


def test_workflow_approve_rejects_out_of_range_ids(temp_repo: Path, capsys) -> None:
    _seed_common_repo(temp_repo)
    _write_loop_result(
        temp_repo,
        [
            {
                "impact": "MINOR",
                "title": "[MINOR] Rename helper for readability",
                "evidence": "Low-risk cleanup",
                "action": "Defer unless approved",
            }
        ],
    )

    exit_code, payload = _run_json_command(
        capsys,
        [
            "--repo-root",
            str(temp_repo),
            "--format",
            "json",
            "workflow-approve",
            "--workflow",
            "continuous-refactor",
            "--ids",
            "3",
        ],
    )

    assert exit_code == 2
    assert payload["ok"] is False
    assert "out of range" in str(payload["error"])
