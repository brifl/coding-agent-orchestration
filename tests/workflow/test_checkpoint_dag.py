"""Stage 25 tests for checkpoint dependency graph behavior."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add tools directory to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import (  # type: ignore
    StateInfo,
    _parse_checkpoint_dependencies,
    _recommend_next,
    _validate_checkpoint_dag,
    build_parser,
    validate,
)


def _write_state(repo_root: Path, *, stage: str, checkpoint: str, status: str) -> None:
    vibe_dir = repo_root / ".vibe"
    vibe_dir.mkdir(parents=True, exist_ok=True)
    (vibe_dir / "STATE.md").write_text(
        f"""# STATE

## Current focus
- Stage: {stage}
- Checkpoint: {checkpoint}
- Status: {status}

## Active issues

(None)
""",
        encoding="utf-8",
    )


def _write_plan(repo_root: Path, body: str) -> None:
    vibe_dir = repo_root / ".vibe"
    vibe_dir.mkdir(parents=True, exist_ok=True)
    (vibe_dir / "PLAN.md").write_text(body, encoding="utf-8")


def _run_json_command(capsys, argv: list[str]) -> tuple[int, dict[str, object]]:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.fn(args))
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def _run_text_command(capsys, argv: list[str]) -> tuple[int, str]:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = int(args.fn(args))
    text = capsys.readouterr().out
    return exit_code, text


def test_parse_checkpoint_dependencies_supports_optional_annotations() -> None:
    plan = """# PLAN

## Stage 1 — Demo

### 1.0 — Bootstrap

### 1.1 — Build parser
  depends_on: [1.0]

### 1.2 — Validate graph
  depends_on: [1.0, 1.1]
"""
    deps, parse_errors = _parse_checkpoint_dependencies(plan)

    assert parse_errors == []
    assert deps["1.0"] == []
    assert deps["1.1"] == ["1.0"]
    assert deps["1.2"] == ["1.0", "1.1"]


def test_parse_checkpoint_dependencies_reports_malformed_value() -> None:
    plan = """# PLAN

## Stage 1 — Demo

### 1.0 — Bootstrap
  depends_on: 1.9
"""
    deps, parse_errors = _parse_checkpoint_dependencies(plan)

    assert deps["1.0"] == []
    assert len(parse_errors) == 1
    assert "malformed depends_on value" in parse_errors[0]


def test_validate_checkpoint_dag_reports_cycle_dangling_and_self() -> None:
    checkpoint_ids = ["1.0", "1.1", "1.2"]
    deps = {
        "1.0": ["1.0"],     # self-dependency
        "1.1": ["9.9"],     # dangling dependency
        "1.2": ["1.2"],     # self-dependency (also cycle)
    }
    errors = _validate_checkpoint_dag(checkpoint_ids, deps)

    assert any("Self-dependency: '1.0'" in err for err in errors)
    assert any("Dangling dependency: '1.1' depends on '9.9'" in err for err in errors)
    assert any("Self-dependency: '1.2'" in err for err in errors)


def test_validate_strict_surfaces_cycle_errors(temp_repo: Path) -> None:
    _write_state(temp_repo, stage="1", checkpoint="1.0", status="NOT_STARTED")
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### 1.0 — One
  depends_on: [1.1]

* **Objective:**
  Obj.
* **Deliverables:**
  * Deliv.
* **Acceptance:**
  * Acc.
* **Demo commands:**
  * `echo ok`
* **Evidence:**
  * Ev.

### 1.1 — Two
  depends_on: [1.0]

* **Objective:**
  Obj.
* **Deliverables:**
  * Deliv.
* **Acceptance:**
  * Acc.
* **Demo commands:**
  * `echo ok`
* **Evidence:**
  * Ev.
""",
    )

    result = validate(temp_repo, strict=True)

    assert result.ok is False
    assert any("Cycle:" in message for message in result.errors)


def test_done_dispatch_skips_dep_blocked_checkpoint(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Complete

### 1.1 — Waiting
  depends_on: [1.3]

### 1.2 — Ready
  depends_on: [1.0]

### 1.3 — Future dependency
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())

    role, reason, _ = _recommend_next(state, temp_repo)

    assert role == "advance"
    assert "1.2" in reason


def test_done_dispatch_stops_when_all_remaining_are_dep_blocked(temp_repo: Path) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Complete

### 1.1 — Blocked A
  depends_on: [1.2]

### 1.2 — Blocked B
  depends_on: [1.1]
""",
    )
    state = StateInfo(stage="1", checkpoint="1.0", status="DONE", evidence_path=None, issues=())

    role, reason, _ = _recommend_next(state, temp_repo)

    assert role == "stop"
    assert "dep-blocked" in reason
    assert "1.1" in reason and "1.2" in reason


def test_cmd_dag_json_renders_nodes_edges_and_status(temp_repo: Path, capsys) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Foundation

### (SKIP) 1.1 — Deferred

### 1.2 — Ready leaf
  depends_on: [1.0]

### 1.3 — Blocked node
  depends_on: [1.2, 1.4]

### 1.4 — Another ready leaf
  depends_on: [1.0]
""",
    )

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "dag", "--format", "json"],
    )

    assert exit_code == 0

    nodes = {node["id"]: node for node in payload["nodes"]}  # type: ignore[index]
    assert nodes["1.0"]["status"] == "DONE"
    assert nodes["1.1"]["status"] == "SKIP"
    assert nodes["1.2"]["status"] == "READY"
    assert nodes["1.3"]["status"] == "DEP_BLOCKED"
    assert nodes["1.4"]["status"] == "READY"

    edges = {(edge["from"], edge["to"]) for edge in payload["edges"]}  # type: ignore[index]
    assert ("1.0", "1.2") in edges
    assert ("1.2", "1.3") in edges
    assert ("1.4", "1.3") in edges


def test_cmd_dag_ascii_renders_ready_and_blocked_annotations(temp_repo: Path, capsys) -> None:
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Foundation

### 1.1 — Ready
  depends_on: [1.0]

### 1.2 — Blocked
  depends_on: [1.1]
""",
    )

    exit_code, output = _run_text_command(
        capsys,
        ["--repo-root", str(temp_repo), "dag", "--format", "ascii"],
    )

    assert exit_code == 0
    assert "[+] 1.0 -- Foundation" in output
    assert "[>] 1.1 -- Ready (ready)" in output
    assert "[!] 1.2 -- Blocked (blocked:" in output


def test_cmd_next_parallel_two_returns_two_ready_checkpoints(temp_repo: Path, capsys) -> None:
    _write_state(temp_repo, stage="1", checkpoint="1.0", status="DONE")
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Foundation

### 1.1 — Ready A
  depends_on: [1.0]

### 1.2 — Ready B
  depends_on: [1.0]

### 1.3 — Blocked C
  depends_on: [1.1, 1.2]
""",
    )

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--parallel", "2"],
    )

    assert exit_code == 0
    recommended_roles = payload["recommended_roles"]  # type: ignore[index]
    checkpoints = [item["checkpoint"] for item in recommended_roles]
    assert checkpoints == ["1.1", "1.2"]


def test_cmd_next_parallel_two_returns_one_when_only_one_ready(temp_repo: Path, capsys) -> None:
    _write_state(temp_repo, stage="1", checkpoint="1.0", status="DONE")
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Foundation

### 1.1 — Ready A
  depends_on: [1.0]

### (DONE) 1.2 — Already complete
  depends_on: [1.0]

### 1.3 — Blocked C
  depends_on: [1.1, 1.2]
""",
    )

    exit_code, payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--parallel", "2"],
    )

    assert exit_code == 0
    recommended_roles = payload["recommended_roles"]  # type: ignore[index]
    assert len(recommended_roles) == 1
    assert recommended_roles[0]["checkpoint"] == "1.1"


def test_cmd_next_parallel_one_matches_default_shape(temp_repo: Path, capsys) -> None:
    _write_state(temp_repo, stage="1", checkpoint="1.0", status="DONE")
    _write_plan(
        temp_repo,
        """# PLAN

## Stage 1 — Demo

### (DONE) 1.0 — Foundation

### 1.1 — Ready A
  depends_on: [1.0]

### 1.2 — Blocked B
  depends_on: [1.1]
""",
    )

    exit_default, default_payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next"],
    )
    exit_parallel, parallel_payload = _run_json_command(
        capsys,
        ["--repo-root", str(temp_repo), "--format", "json", "next", "--parallel", "1"],
    )

    assert exit_default == 0
    assert exit_parallel == 0
    assert default_payload["recommended_role"] == parallel_payload["recommended_role"]
    assert default_payload["recommended_prompt_id"] == parallel_payload["recommended_prompt_id"]
    assert len(default_payload["recommended_roles"]) == 1
    assert len(parallel_payload["recommended_roles"]) == 1
    assert default_payload["recommended_roles"][0]["checkpoint"] == "1.1"
    assert parallel_payload["recommended_roles"][0]["checkpoint"] == "1.1"
