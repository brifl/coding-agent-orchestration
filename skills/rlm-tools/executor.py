#!/usr/bin/env python3
"""Baseline RLM executor with bounded iteration and resumable state."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_RLM_DIR = REPO_ROOT / "tools" / "rlm"
if str(TOOLS_RLM_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_RLM_DIR))

from context_bundle import _build_bundle, _read_task  # type: ignore
from runtime import RLMRuntime, RuntimeErrorState  # type: ignore

EXECUTOR_STATE_FILE = "executor_state.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (repo_root / path)


def _validate_baseline_program(task: dict[str, Any]) -> list[str]:
    program = task.get("baseline_program")
    if not isinstance(program, list) or not program:
        raise RuntimeError(
            "Task must define a non-empty 'baseline_program' list for baseline executor mode."
        )
    normalized: list[str] = []
    for idx, item in enumerate(program):
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(f"baseline_program[{idx}] must be a non-empty string.")
        normalized.append(item)
    return normalized


def _load_task(task_path: Path) -> dict[str, Any]:
    task = _read_task(task_path)
    if task is None:
        raise RuntimeError("Task validation failed.")
    if str(task.get("mode")) != "baseline":
        raise RuntimeError("Checkpoint 21.4 executor supports only mode='baseline'.")
    _validate_baseline_program(task)
    return task


def _bundle_dir_for_task(task: dict[str, Any], repo_root: Path) -> Path:
    output_root = repo_root / ".vibe" / "rlm" / "bundles"
    _build_bundle(task, repo_root, output_root)
    task_id = str(task.get("task_id"))
    return output_root / task_id


def _default_run_dir(task: dict[str, Any], repo_root: Path) -> Path:
    task_id = str(task.get("task_id"))
    return repo_root / ".vibe" / "rlm" / "runs" / task_id


def _state_path(run_dir: Path) -> Path:
    return run_dir / EXECUTOR_STATE_FILE


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_executor_state(run_dir: Path) -> dict[str, Any]:
    path = _state_path(run_dir)
    if not path.exists():
        raise RuntimeError(f"Missing executor state file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Executor state must be an object: {path}")
    return payload


def _save_executor_state(run_dir: Path, state: dict[str, Any]) -> None:
    _write_json(_state_path(run_dir), state)


def _append_trace(trace_path: Path, payload: dict[str, Any]) -> None:
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _finalize_artifacts(task: dict[str, Any], final_payload: Any, repo_root: Path) -> str:
    outputs = task.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Task outputs must be an object.")

    final_path_raw = outputs.get("final_path")
    if not isinstance(final_path_raw, str) or not final_path_raw.strip():
        raise RuntimeError("Task outputs.final_path must be a non-empty string.")

    final_path = _resolve_path(final_path_raw, repo_root)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(final_payload, (dict, list)):
        text = json.dumps(final_payload, indent=2, sort_keys=True)
    else:
        text = str(final_payload)
    final_path.write_text(text + "\n", encoding="utf-8")

    return str(final_path)


def _init_executor_state(
    task: dict[str, Any],
    task_path: Path,
    bundle_dir: Path,
    run_dir: Path,
    trace_path: Path,
) -> dict[str, Any]:
    limits = task.get("limits")
    assert isinstance(limits, dict)

    state = {
        "bundle_dir": str(bundle_dir),
        "cursor": 0,
        "final_artifact": None,
        "max_root_iters": int(limits["max_root_iters"]),
        "max_stdout_chars": int(limits["max_stdout_chars"]),
        "status": "RUNNING",
        "stop_reason": None,
        "task_id": str(task["task_id"]),
        "task_path": str(task_path),
        "task_sha256": _sha256_file(task_path),
        "trace_path": str(trace_path),
    }
    return state


def _validate_resume_state(state: dict[str, Any], run_dir: Path, repo_root: Path) -> tuple[dict[str, Any], Path, Path]:
    task_path = Path(str(state.get("task_path", ""))).resolve()
    if not task_path.exists():
        raise RuntimeError(f"Task path in executor state no longer exists: {task_path}")

    recorded_sha = str(state.get("task_sha256", "")).strip()
    current_sha = _sha256_file(task_path)
    if recorded_sha != current_sha:
        raise RuntimeError(
            "Task content changed since executor state was created; resume would be ambiguous."
        )

    task = _load_task(task_path)
    bundle_dir = Path(str(state.get("bundle_dir", ""))).resolve()
    if not bundle_dir.exists():
        bundle_dir = _bundle_dir_for_task(task, repo_root)

    trace_path = Path(str(state.get("trace_path", run_dir / "trace.jsonl"))).resolve()
    return task, bundle_dir, trace_path


def _record_step(
    runtime_result: dict[str, Any],
    code: str,
    cursor: int,
    trace_path: Path,
) -> None:
    payload = {
        "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "error": runtime_result.get("error"),
        "event": "iteration",
        "finalized": bool(runtime_result.get("finalized")),
        "iteration": int(runtime_result.get("iteration", 0)),
        "program_index": cursor,
        "recorded_at": _utc_now(),
        "stdout_chars": len(str(runtime_result.get("stdout", ""))),
        "stdout_truncated": bool(runtime_result.get("stdout_truncated")),
    }
    _append_trace(trace_path, payload)


def _record_stop(state: dict[str, Any], runtime: RLMRuntime, trace_path: Path) -> None:
    payload = {
        "event": "stop",
        "finalized": runtime.finalized,
        "iteration": runtime.iteration,
        "recorded_at": _utc_now(),
        "status": state.get("status"),
        "stop_reason": state.get("stop_reason"),
    }
    _append_trace(trace_path, payload)


def _step_once(
    task: dict[str, Any],
    state: dict[str, Any],
    runtime: RLMRuntime,
    trace_path: Path,
    repo_root: Path,
) -> bool:
    if state.get("status") != "RUNNING":
        return False

    max_root_iters = int(state.get("max_root_iters", 0))
    if runtime.iteration >= max_root_iters:
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "MAX_ROOT_ITERS"
        _record_stop(state, runtime, trace_path)
        return False

    program = _validate_baseline_program(task)
    cursor = int(state.get("cursor", 0))
    if cursor >= len(program):
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "PROGRAM_EXHAUSTED"
        _record_stop(state, runtime, trace_path)
        return False

    code = program[cursor]
    result = runtime.step(code)
    _record_step(result, code, cursor, trace_path)

    state["cursor"] = cursor + 1

    if result.get("error"):
        state["status"] = "BLOCKED"
        state["stop_reason"] = "STEP_ERROR"
        _record_stop(state, runtime, trace_path)
        return False

    if bool(result.get("finalized")):
        state["status"] = "COMPLETED"
        state["stop_reason"] = "FINAL"
        state["final_artifact"] = _finalize_artifacts(task, result.get("final_payload"), repo_root)
        _record_stop(state, runtime, trace_path)
        return False

    if runtime.iteration >= max_root_iters:
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "MAX_ROOT_ITERS"
        _record_stop(state, runtime, trace_path)
        return False

    return True


def _summary(run_dir: Path, state: dict[str, Any], runtime: RLMRuntime) -> dict[str, Any]:
    return {
        "cursor": state.get("cursor"),
        "final_artifact": state.get("final_artifact"),
        "iteration": runtime.iteration,
        "run_dir": str(run_dir),
        "status": state.get("status"),
        "stop_reason": state.get("stop_reason"),
        "trace_path": state.get("trace_path"),
    }


def cmd_run(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    task_path = _resolve_path(args.task, repo_root).resolve()
    task = _load_task(task_path)

    run_dir = _resolve_path(args.run_dir, repo_root).resolve() if args.run_dir else _default_run_dir(task, repo_root)
    if args.fresh and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = _bundle_dir_for_task(task, repo_root)
    trace_path = _resolve_path(str(task["trace"]["trace_path"]), repo_root)

    state = _init_executor_state(task, task_path, bundle_dir, run_dir, trace_path)
    _save_executor_state(run_dir, state)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    while _step_once(task, state, runtime, trace_path, repo_root):
        _save_executor_state(run_dir, state)

    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"COMPLETED", "LIMIT_REACHED"} else 1


def cmd_step(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    run_dir = _resolve_path(args.run_dir, repo_root).resolve()
    state = _load_executor_state(run_dir)
    task, bundle_dir, trace_path = _validate_resume_state(state, run_dir, repo_root)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    _step_once(task, state, runtime, trace_path, repo_root)
    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"RUNNING", "COMPLETED", "LIMIT_REACHED"} else 1


def cmd_resume(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    run_dir = _resolve_path(args.run_dir, repo_root).resolve()
    state = _load_executor_state(run_dir)
    task, bundle_dir, trace_path = _validate_resume_state(state, run_dir, repo_root)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    while _step_once(task, state, runtime, trace_path, repo_root):
        _save_executor_state(run_dir, state)

    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"COMPLETED", "LIMIT_REACHED"} else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RLM baseline executor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Create a run and execute until stop.")
    run_cmd.add_argument("--task", required=True, help="Task JSON path")
    run_cmd.add_argument("--run-dir", help="Override run directory")
    run_cmd.add_argument("--fresh", action="store_true", help="Delete existing run directory before start")
    run_cmd.set_defaults(func=cmd_run)

    step_cmd = subparsers.add_parser("step", help="Execute one iteration for an existing run.")
    step_cmd.add_argument("--run-dir", required=True, help="Existing run directory")
    step_cmd.set_defaults(func=cmd_step)

    resume_cmd = subparsers.add_parser("resume", help="Resume an existing run until stop.")
    resume_cmd.add_argument("--run-dir", required=True, help="Existing run directory")
    resume_cmd.set_defaults(func=cmd_resume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except (RuntimeError, RuntimeErrorState) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
