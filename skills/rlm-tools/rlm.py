#!/usr/bin/env python3
"""RLM skill entrypoints wrapper."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_python_script(relative_path: str, args: list[str]) -> int:
    script_path = REPO_ROOT / relative_path
    cmd = [sys.executable, str(script_path), *args]
    proc = subprocess.run(cmd)
    return int(proc.returncode)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rlm", description="RLM skill entrypoints")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_cmd = subparsers.add_parser("validate", help="Validate a task schema")
    validate_cmd.add_argument("task", help="Task JSON path")

    bundle_cmd = subparsers.add_parser("bundle", help="Build context bundle for a task")
    bundle_cmd.add_argument("--task", required=True, help="Task JSON path")
    bundle_cmd.add_argument(
        "--output-root",
        default=".vibe/rlm/bundles",
        help="Bundle output root (default: .vibe/rlm/bundles)",
    )

    run_cmd = subparsers.add_parser("run", help="Run executor until stop")
    run_cmd.add_argument("--task", required=True, help="Task JSON path")
    run_cmd.add_argument("--run-dir", help="Override run directory")
    run_cmd.add_argument("--fresh", action="store_true", help="Reset run directory first")
    run_cmd.add_argument("--cache", choices=("off", "readonly", "readwrite"), help="Cache mode")

    step_cmd = subparsers.add_parser("step", help="Run one executor step")
    step_cmd.add_argument("--run-dir", required=True, help="Run directory")
    step_cmd.add_argument("--cache", choices=("off", "readonly", "readwrite"), help="Cache mode")

    resume_cmd = subparsers.add_parser("resume", help="Resume executor until stop")
    resume_cmd.add_argument("--run-dir", required=True, help="Run directory")
    resume_cmd.add_argument("--cache", choices=("off", "readonly", "readwrite"), help="Cache mode")

    providers_cmd = subparsers.add_parser("providers", help="Run provider health checks")
    providers_cmd.add_argument(
        "--provider",
        default="all",
        help="Provider selection (all|openai|anthropic|google|triton)",
    )
    providers_cmd.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repository root for provider config resolution",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _run_python_script("tools/rlm/validate_task.py", [args.task])

    if args.command == "bundle":
        return _run_python_script(
            "tools/rlm/context_bundle.py",
            ["build", "--task", args.task, "--output-root", args.output_root],
        )

    if args.command == "run":
        cmd_args = ["run", "--task", args.task]
        if args.run_dir:
            cmd_args.extend(["--run-dir", args.run_dir])
        if args.fresh:
            cmd_args.append("--fresh")
        if args.cache:
            cmd_args.extend(["--cache", args.cache])
        return _run_python_script("skills/rlm-tools/executor.py", cmd_args)

    if args.command == "step":
        cmd_args = ["step", "--run-dir", args.run_dir]
        if args.cache:
            cmd_args.extend(["--cache", args.cache])
        return _run_python_script("skills/rlm-tools/executor.py", cmd_args)

    if args.command == "resume":
        cmd_args = ["resume", "--run-dir", args.run_dir]
        if args.cache:
            cmd_args.extend(["--cache", args.cache])
        return _run_python_script("skills/rlm-tools/executor.py", cmd_args)

    if args.command == "providers":
        cmd_args = ["--provider", args.provider, "--repo-root", args.repo_root]
        return _run_python_script("tools/rlm/provider_check.py", cmd_args)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
