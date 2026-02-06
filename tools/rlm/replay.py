#!/usr/bin/env python3
"""Summarize and compare RLM run traces for replay verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _resolve_trace_path(run_dir: Path, executor_state: dict[str, Any]) -> Path:
    trace_raw = str(executor_state.get("trace_path", "")).strip()
    if not trace_raw:
        return run_dir / "trace.jsonl"

    trace_path = Path(trace_raw).expanduser()
    if not trace_path.is_absolute():
        return (run_dir / trace_path).resolve()
    return trace_path


def _run_summary(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    state_path = run_dir / "executor_state.json"
    if not state_path.exists():
        raise RuntimeError(f"Missing executor state: {state_path}")

    executor_state = _load_json(state_path)
    trace_path = _resolve_trace_path(run_dir, executor_state)
    if not trace_path.exists():
        raise RuntimeError(f"Missing trace file: {trace_path}")

    events = _load_jsonl(trace_path)
    response_hashes = [
        str(event.get("response_hash", ""))
        for event in events
        if event.get("event") == "subcall" and str(event.get("response_hash", "")).strip()
    ]

    final_artifact_raw = str(executor_state.get("final_artifact") or "").strip()
    final_artifact = Path(final_artifact_raw).resolve() if final_artifact_raw else None
    final_sha256 = None
    if final_artifact is not None and final_artifact.exists():
        final_sha256 = _sha256_file(final_artifact)

    return {
        "run_dir": str(run_dir),
        "mode": executor_state.get("mode"),
        "status": executor_state.get("status"),
        "stop_reason": executor_state.get("stop_reason"),
        "trace_path": str(trace_path),
        "response_hashes": response_hashes,
        "response_hash_count": len(response_hashes),
        "final_artifact": str(final_artifact) if final_artifact else None,
        "final_artifact_sha256": final_sha256,
    }


def cmd_summary(args: argparse.Namespace) -> int:
    payload = _run_summary(Path(args.run_dir))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    first = _run_summary(Path(args.run_a))
    second = _run_summary(Path(args.run_b))

    comparisons = {
        "response_hashes_match": first["response_hashes"] == second["response_hashes"],
        "final_artifact_sha256_match": first["final_artifact_sha256"] == second["final_artifact_sha256"],
    }
    all_match = all(comparisons.values())

    payload = {
        "match": all_match,
        "comparisons": comparisons,
        "run_a": first,
        "run_b": second,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all_match else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay and compare RLM run traces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_cmd = subparsers.add_parser("summary", help="Summarize one run directory.")
    summary_cmd.add_argument("--run-dir", required=True, help="Run directory")
    summary_cmd.set_defaults(func=cmd_summary)

    compare_cmd = subparsers.add_parser("compare", help="Compare two run directories.")
    compare_cmd.add_argument("--run-a", required=True, help="First run directory")
    compare_cmd.add_argument("--run-b", required=True, help="Second run directory")
    compare_cmd.set_defaults(func=cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
