#!/usr/bin/env python3
"""Persistent RLM runtime with deterministic stdout capture and resumable state."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

RUNTIME_VERSION = 1
TRUNCATION_MARKER = "\n...[truncated]\n"

SAFE_BUILTINS: dict[str, Any] = {
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "reversed": reversed,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


class RuntimeErrorState(RuntimeError):
    """Runtime state was invalid or ambiguous for resume."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _truncate_stdout(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False

    keep = max_chars - len(TRUNCATION_MARKER)
    if keep <= 0:
        return TRUNCATION_MARKER[:max_chars], True
    return text[:keep] + TRUNCATION_MARKER, True


class RLMRuntime:
    def __init__(self, bundle_dir: Path, run_dir: Path, max_stdout_chars: int = 4000) -> None:
        if max_stdout_chars < 1:
            raise ValueError("max_stdout_chars must be >= 1")

        self.bundle_dir = bundle_dir.resolve()
        self.run_dir = run_dir.resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.run_dir / "state.json"
        self.max_stdout_chars = int(max_stdout_chars)

        self.chunks = self._load_chunks(self.bundle_dir)
        self.chunks_by_id = {str(chunk["chunk_id"]): chunk for chunk in self.chunks}
        self.context = {
            "bundle_dir": str(self.bundle_dir),
            "chunk_count": len(self.chunks),
            "sources": sorted({str(chunk.get("source", "")) for chunk in self.chunks}),
        }
        self.bundle_fingerprint = self._bundle_fingerprint(self.bundle_dir)

        self.iteration = 0
        self.finalized = False
        self.final_payload: Any = None
        self.events: list[dict[str, Any]] = []
        self.memory: dict[str, Any] = {}

        if self.state_path.exists():
            self._load_state()
        else:
            self._save_state()

    @staticmethod
    def _load_chunks(bundle_dir: Path) -> list[dict[str, Any]]:
        chunks_path = bundle_dir / "chunks.jsonl"
        if not chunks_path.exists():
            raise RuntimeErrorState(f"Missing bundle chunks file: {chunks_path}")
        chunks = _load_jsonl(chunks_path)
        for idx, chunk in enumerate(chunks, start=1):
            if "chunk_id" not in chunk:
                chunk["chunk_id"] = f"{idx:08d}"
        return chunks

    @staticmethod
    def _bundle_fingerprint(bundle_dir: Path) -> str:
        manifest_path = bundle_dir / "manifest.json"
        chunks_path = bundle_dir / "chunks.jsonl"
        if not manifest_path.exists() or not chunks_path.exists():
            raise RuntimeErrorState(
                f"Bundle fingerprint requires manifest/chunks files in {bundle_dir}"
            )
        data = manifest_path.read_bytes() + b"\n--\n" + chunks_path.read_bytes()
        return _sha256_bytes(data)

    def _state_payload(self) -> dict[str, Any]:
        return {
            "bundle_dir": str(self.bundle_dir),
            "bundle_fingerprint": self.bundle_fingerprint,
            "events": self.events,
            "final_payload": self.final_payload,
            "finalized": self.finalized,
            "iteration": self.iteration,
            "max_stdout_chars": self.max_stdout_chars,
            "memory": self.memory,
            "runtime_version": RUNTIME_VERSION,
        }

    def _save_state(self) -> None:
        payload = self._state_payload()
        self.state_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _load_state(self) -> None:
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeErrorState(f"State file is not an object: {self.state_path}")

        persisted_fingerprint = str(payload.get("bundle_fingerprint", "")).strip()
        if persisted_fingerprint != self.bundle_fingerprint:
            raise RuntimeErrorState(
                "State bundle fingerprint does not match current bundle contents; "
                "resume would be ambiguous."
            )

        persisted_max_stdout = payload.get("max_stdout_chars")
        if persisted_max_stdout != self.max_stdout_chars:
            raise RuntimeErrorState(
                "State max_stdout_chars does not match requested runtime settings; "
                "resume would be ambiguous."
            )

        iteration = payload.get("iteration")
        finalized = payload.get("finalized")
        final_payload = payload.get("final_payload")
        events = payload.get("events")
        memory = payload.get("memory")

        if not isinstance(iteration, int) or iteration < 0:
            raise RuntimeErrorState("State field 'iteration' must be an integer >= 0.")
        if not isinstance(finalized, bool):
            raise RuntimeErrorState("State field 'finalized' must be true or false.")
        if events is None:
            events = []
        if memory is None:
            memory = {}
        if not isinstance(events, list):
            raise RuntimeErrorState("State field 'events' must be a list.")
        if not isinstance(memory, dict):
            raise RuntimeErrorState("State field 'memory' must be an object.")

        self.iteration = iteration
        self.finalized = finalized
        self.final_payload = final_payload
        self.events = events
        self.memory = memory

    def list_chunks(self, source: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for chunk in self.chunks:
            chunk_source = str(chunk.get("source", ""))
            if source is not None and chunk_source != source:
                continue
            rows.append(
                {
                    "char_count": chunk.get("char_count"),
                    "chunk_id": str(chunk.get("chunk_id")),
                    "range": chunk.get("range"),
                    "source": chunk_source,
                }
            )
            if len(rows) >= max(0, int(limit)):
                break
        return rows

    def get_chunk(self, chunk_id: str) -> str:
        key = str(chunk_id)
        chunk = self.chunks_by_id.get(key)
        if chunk is None:
            raise KeyError(f"Unknown chunk_id '{chunk_id}'")
        return str(chunk.get("text", ""))

    def peek(self, chunk_id: str, max_chars: int = 200) -> str:
        max_chars = max(1, int(max_chars))
        return self.get_chunk(chunk_id)[:max_chars]

    def grep(self, pattern: str, source: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        regex = re.compile(pattern)
        rows: list[dict[str, Any]] = []
        for chunk in self.chunks:
            chunk_source = str(chunk.get("source", ""))
            if source is not None and chunk_source != source:
                continue

            text = str(chunk.get("text", ""))
            for line_no, line in enumerate(text.splitlines(), start=1):
                if not regex.search(line):
                    continue
                rows.append(
                    {
                        "chunk_id": str(chunk.get("chunk_id")),
                        "line_no": line_no,
                        "line_text": line,
                        "source": chunk_source,
                    }
                )
                if len(rows) >= max(0, int(limit)):
                    return rows
        return rows

    def FINAL(self, value: Any) -> Any:
        self.finalized = True
        self.final_payload = value
        return value

    def step(self, code: str) -> dict[str, Any]:
        if self.finalized:
            raise RuntimeErrorState("Runtime already finalized; additional steps are not allowed.")

        code = str(code)
        stdout_buffer = io.StringIO()
        error: str | None = None

        env: dict[str, Any] = {
            "FINAL": self.FINAL,
            "context": self.context,
            "get_chunk": self.get_chunk,
            "grep": self.grep,
            "list_chunks": self.list_chunks,
            "memory": self.memory,
            "peek": self.peek,
        }

        try:
            with contextlib.redirect_stdout(stdout_buffer):
                exec(code, {"__builtins__": SAFE_BUILTINS}, env)
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"

        raw_stdout = stdout_buffer.getvalue()
        stdout_text, truncated = _truncate_stdout(raw_stdout, self.max_stdout_chars)
        self.iteration += 1

        event = {
            "code_sha256": _sha256_text(code),
            "error": error,
            "finalized": self.finalized,
            "iteration": self.iteration,
            "stdout_chars": len(raw_stdout),
            "stdout_sha256": _sha256_text(raw_stdout),
            "stdout_truncated": truncated,
        }
        self.events.append(event)
        self._save_state()

        return {
            "error": error,
            "final_payload": self.final_payload,
            "finalized": self.finalized,
            "iteration": self.iteration,
            "stdout": stdout_text,
            "stdout_truncated": truncated,
        }


def _load_state_for_display(run_dir: Path) -> dict[str, Any]:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        raise RuntimeErrorState(f"Missing state file: {state_path}")
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeErrorState(f"State file is not an object: {state_path}")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RLM runtime sandbox.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    step_cmd = subparsers.add_parser("step", help="Execute one runtime step.")
    step_cmd.add_argument("--bundle-dir", required=True, help="Bundle directory path")
    step_cmd.add_argument("--run-dir", required=True, help="Run directory path")
    step_cmd.add_argument("--code", help="Inline Python code to execute")
    step_cmd.add_argument("--code-file", help="File containing Python code to execute")
    step_cmd.add_argument(
        "--max-stdout-chars",
        type=int,
        default=4000,
        help="Maximum stdout characters persisted/returned per step",
    )

    state_cmd = subparsers.add_parser("show-state", help="Print runtime state.json.")
    state_cmd.add_argument("--run-dir", required=True, help="Run directory path")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        if args.command == "show-state":
            payload = _load_state_for_display(Path(args.run_dir).resolve())
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        if args.command != "step":
            print(f"Unsupported command '{args.command}'.", file=sys.stderr)
            return 2

        if bool(args.code) == bool(args.code_file):
            print("ERROR: provide exactly one of --code or --code-file.", file=sys.stderr)
            return 2

        if args.code_file:
            code = Path(args.code_file).read_text(encoding="utf-8")
        else:
            code = str(args.code)

        runtime = RLMRuntime(
            bundle_dir=Path(args.bundle_dir).resolve(),
            run_dir=Path(args.run_dir).resolve(),
            max_stdout_chars=args.max_stdout_chars,
        )
        result = runtime.step(code)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("error") is None else 1

    except RuntimeErrorState as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
