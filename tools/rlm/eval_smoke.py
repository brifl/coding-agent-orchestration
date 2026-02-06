#!/usr/bin/env python3
"""Smoke harness for RLM reference tasks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RLM smoke evaluation task.")
    parser.add_argument(
        "--task",
        required=True,
        help="Task JSON path (for example: tasks/rlm/repo_comprehension.json)",
    )
    parser.add_argument(
        "--cache",
        default="readwrite",
        choices=("off", "readonly", "readwrite"),
        help="Cache mode for subcalls tasks (default: readwrite)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    task_path = (REPO_ROOT / args.task).resolve() if not Path(args.task).is_absolute() else Path(args.task)
    if not task_path.exists():
        print(f"ERROR: task not found: {task_path}", file=sys.stderr)
        return 1

    validate_cmd = [sys.executable, str(REPO_ROOT / "tools/rlm/validate_task.py"), str(task_path)]
    validate_proc = _run(validate_cmd)
    if validate_proc.returncode != 0:
        print(validate_proc.stdout.strip())
        print(validate_proc.stderr.strip(), file=sys.stderr)
        return validate_proc.returncode

    task_payload = _read_json(task_path)
    task_id = str(task_payload.get("task_id", "")).strip()
    if not task_id:
        print("ERROR: task_id missing from task payload", file=sys.stderr)
        return 1

    mode = str(task_payload.get("mode", "")).strip().lower()
    run_cmd = [
        sys.executable,
        str(REPO_ROOT / "skills/rlm-tools/executor.py"),
        "run",
        "--task",
        str(task_path),
        "--fresh",
    ]
    if mode == "subcalls":
        run_cmd.extend(["--cache", args.cache])

    run_proc = _run(run_cmd)
    if run_proc.returncode != 0:
        print(run_proc.stdout.strip())
        print(run_proc.stderr.strip(), file=sys.stderr)
        return run_proc.returncode

    run_dir = REPO_ROOT / ".vibe/rlm/runs" / task_id
    executor_state_path = run_dir / "executor_state.json"
    runtime_state_path = run_dir / "state.json"
    if not executor_state_path.exists() or not runtime_state_path.exists():
        print("ERROR: missing run state artifacts after executor run", file=sys.stderr)
        return 1

    executor_state = _read_json(executor_state_path)
    runtime_state = _read_json(runtime_state_path)

    final_artifact = Path(str(executor_state.get("final_artifact") or "")).resolve()
    bundle_dir = Path(str(executor_state.get("bundle_dir") or "")).resolve()

    checks = {
        "bundle_dir_exists": bundle_dir.exists(),
        "multi_iteration": int(runtime_state.get("iteration", 0)) >= 2,
        "status_completed": str(executor_state.get("status")) == "COMPLETED",
        "final_artifact_exists": bool(str(executor_state.get("final_artifact") or "")) and final_artifact.exists(),
        "subcalls_used": int(executor_state.get("subcalls_total", 0)) >= 1,
    }
    passed = all(checks.values())

    report = {
        "task": str(task_path.relative_to(REPO_ROOT)),
        "task_id": task_id,
        "mode": mode,
        "run_dir": str(run_dir),
        "checks": checks,
        "passed": passed,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
