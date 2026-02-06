#!/usr/bin/env python3
"""Deterministic context bundle builder for RLM tasks."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_task import _build_line_index, validate_task


@dataclass(frozen=True)
class SourceFile:
    abs_path: Path
    rel_path: str


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _read_task(task_path: Path) -> dict[str, Any] | None:
    try:
        raw = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read task file '{task_path}': {exc}", file=sys.stderr)
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"INVALID: {task_path}")
        print(f"{task_path}:{exc.lineno}: invalid JSON ({exc.msg}).")
        return None

    diagnostics = validate_task(payload, _build_line_index(raw))
    if diagnostics:
        print(f"INVALID: {task_path}")
        for diag in diagnostics:
            print(f"{task_path}:{diag.line}: {diag.message} (field: {diag.field})")
        return None

    if not isinstance(payload, dict):
        print(f"INVALID: {task_path}")
        print(f"{task_path}:1: Task document must be an object.")
        return None

    return payload


def _matches(path: str, patterns: list[str] | None) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _resolve_source_files(task: dict[str, Any], repo_root: Path) -> list[SourceFile]:
    result: list[SourceFile] = []
    seen: set[str] = set()

    context_sources = task.get("context_sources")
    assert isinstance(context_sources, list)

    for source in context_sources:
        assert isinstance(source, dict)
        source_type = str(source.get("type"))
        source_path = Path(str(source.get("path"))).expanduser()
        include = source.get("include") if isinstance(source.get("include"), list) else None
        exclude = source.get("exclude") if isinstance(source.get("exclude"), list) else None

        abs_source_path = source_path if source_path.is_absolute() else (repo_root / source_path)

        candidates: list[Path] = []
        if source_type in {"dir", "snapshot"}:
            if not abs_source_path.exists() or not abs_source_path.is_dir():
                raise RuntimeError(f"Context source directory not found: {source_path}")
            candidates = [p for p in abs_source_path.rglob("*") if p.is_file()]
        elif source_type == "file":
            if not abs_source_path.exists() or not abs_source_path.is_file():
                raise RuntimeError(f"Context source file not found: {source_path}")
            candidates = [abs_source_path]
        else:
            raise RuntimeError(f"Unsupported context source type '{source_type}' for path '{source_path}'.")

        for path in sorted(candidates):
            rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
            if not _matches(rel, include):
                continue
            if exclude and any(fnmatch.fnmatch(rel, pattern) for pattern in exclude):
                continue
            if rel in seen:
                continue
            seen.add(rel)
            result.append(SourceFile(abs_path=path, rel_path=rel))

    result.sort(key=lambda item: item.rel_path)
    return result


def _chunk_text_by_lines(text: str, max_chars: int) -> list[tuple[int, int, str]]:
    lines = text.splitlines(keepends=True)
    if not lines:
        return [(1, 1, "")]

    chunks: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(lines, start=1):
        if len(line) <= max_chars:
            chunks.append((line_no, line_no, line))
            continue

        start = 0
        while start < len(line):
            segment = line[start : start + max_chars]
            chunks.append((line_no, line_no, segment))
            start += max_chars

    return chunks


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_bundle(task: dict[str, Any], repo_root: Path, output_root: Path) -> Path:
    task_id = str(task["task_id"])
    bundle = task["bundle"]
    assert isinstance(bundle, dict)
    max_chars = int(bundle["max_chars"])
    chunking_strategy = str(bundle["chunking_strategy"])

    if chunking_strategy != "by_chars":
        raise RuntimeError(
            "Only chunking_strategy='by_chars' is currently supported by context_bundle.py"
        )

    source_files = _resolve_source_files(task, repo_root)
    if not source_files:
        raise RuntimeError("No files resolved from task.context_sources after include/exclude filtering.")

    bundle_dir = output_root / task_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest_sources: list[dict[str, Any]] = []
    chunks_path = bundle_dir / "chunks.jsonl"
    chunk_count = 0
    total_chars = 0

    with chunks_path.open("w", encoding="utf-8") as chunks_file:
        for source in source_files:
            raw_bytes = source.abs_path.read_bytes()
            text = raw_bytes.decode("utf-8", errors="replace")
            file_hash = _sha256_bytes(raw_bytes)
            manifest_sources.append(
                {
                    "path": source.rel_path,
                    "sha256": file_hash,
                    "size_bytes": len(raw_bytes),
                }
            )

            for line_start, line_end, chunk_text in _chunk_text_by_lines(text, max_chars):
                chunk_count += 1
                char_count = len(chunk_text)
                total_chars += char_count
                chunk_payload = {
                    "char_count": char_count,
                    "chunk_id": f"{chunk_count:08d}",
                    "hash": _sha256_text(chunk_text),
                    "range": {
                        "line_end": line_end,
                        "line_start": line_start,
                    },
                    "source": source.rel_path,
                    "text": chunk_text,
                }
                chunks_file.write(json.dumps(chunk_payload, sort_keys=True) + "\n")

    manifest_payload = {
        "chunking_strategy": chunking_strategy,
        "max_chars": max_chars,
        "sources": manifest_sources,
        "task_id": task_id,
    }
    manifest_path = bundle_dir / "manifest.json"
    _write_json(manifest_path, manifest_payload)

    manifest_hash = _sha256_bytes(manifest_path.read_bytes())
    meta_payload = {
        "chunk_count": chunk_count,
        "manifest_sha256": manifest_hash,
        "source_count": len(manifest_sources),
        "task_id": task_id,
        "total_chars": total_chars,
    }
    meta_path = bundle_dir / "bundle.meta.json"
    _write_json(meta_path, meta_payload)

    print(f"BUNDLE_DIR: {bundle_dir}")
    print(f"MANIFEST: {manifest_path}")
    print(f"CHUNKS: {chunks_path}")
    print(f"META: {meta_path}")
    print(f"SOURCE_COUNT: {len(manifest_sources)}")
    print(f"CHUNK_COUNT: {chunk_count}")

    return bundle_dir


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic RLM context bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build a context bundle from a task file.")
    build.add_argument("--task", required=True, help="Path to task JSON file")
    build.add_argument(
        "--output-root",
        default=".vibe/rlm/bundles",
        help="Bundle output root (default: .vibe/rlm/bundles)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command != "build":
        print(f"Unsupported command '{args.command}'.", file=sys.stderr)
        return 2

    repo_root = Path.cwd().resolve()
    task_path = Path(args.task).resolve()
    output_root = Path(args.output_root).resolve()

    task_payload = _read_task(task_path)
    if task_payload is None:
        return 1

    try:
        _build_bundle(task_payload, repo_root, output_root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
