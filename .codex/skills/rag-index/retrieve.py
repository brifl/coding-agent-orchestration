#!/usr/bin/env python3
"""Retrieve prompt-ready snippets from a RAG index.

Supports direct retrieval from an existing index and a one-shot pipeline
that scans directories, builds an index, and searches in one call.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import indexer
import scanner


def format_results(results: list[dict[str, Any]], max_chars: int) -> str:
    """Format search results as prompt-ready snippets.

    Each snippet is formatted as:
    # file: rel_path
    ```
    snippet
    ```
    """
    blocks: list[str] = []
    total = 0

    for result in results:
        rel_path = result.get("rel_path") or result.get("path") or "unknown"
        snippet = result.get("snippet") or ""
        block = f"# file: {rel_path}\n```\n{snippet}\n```"

        separator = "\n\n" if blocks else ""
        projected = total + len(separator) + len(block)
        if projected > max_chars:
            break
        if separator:
            total += len(separator)
        blocks.append(block)
        total += len(block)

    return "\n\n".join(blocks)


def retrieve(
    query: str,
    index_path: str,
    *,
    top_k: int = 5,
    max_chars: int = 8000,
) -> str:
    """Retrieve formatted snippets for a query from an index."""
    results = indexer.search_index(query, index_path, top_k=top_k)
    return format_results(results, max_chars)


def _write_manifest(manifest: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def pipeline(
    query: str,
    dirs: list[str],
    *,
    index_path: str | None = None,
    top_k: int = 5,
    max_chars: int = 8000,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    file_types: list[str] | None = None,
    max_depth: int | None = None,
    respect_gitignore: bool = True,
) -> tuple[str, dict[str, int]]:
    """Run scan -> build -> search in one call.

    Returns the formatted snippets and build stats.
    """
    manifest = scanner.scan_directories(
        dirs,
        include_patterns=include,
        exclude_patterns=exclude,
        file_types=file_types,
        max_depth=max_depth,
        respect_gitignore=respect_gitignore,
    )

    stats = {"indexed": 0, "skipped": 0, "removed": 0, "errors": 0}
    if not manifest:
        return "", stats

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        _write_manifest(manifest, manifest_path)
        if index_path is None:
            index_path = str(Path(tmpdir) / "index.db")
        stats = indexer.build_index(str(manifest_path), index_path)
        formatted = retrieve(query, index_path, top_k=top_k, max_chars=max_chars)

    return formatted, stats


def _normalize_file_types(file_types: list[str] | None) -> list[str] | None:
    if not file_types:
        return None
    return [t if t.startswith(".") else f".{t}" for t in file_types]


def _run_retrieve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve prompt-ready snippets from a RAG index."
    )
    parser.add_argument("query", help="Search query string.")
    parser.add_argument(
        "--index", "-i", required=True,
        help="Path to the SQLite index database.",
    )
    parser.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="Maximum number of results (default: 5).",
    )
    parser.add_argument(
        "--max-context-chars", type=int, default=8000,
        help="Maximum total output characters (default: 8000).",
    )

    args = parser.parse_args(argv)
    results = indexer.search_index(args.query, args.index, top_k=args.top_k)
    if not results:
        print("No results found.")
        return 0

    formatted = format_results(results, args.max_context_chars)
    if not formatted.strip():
        print("No results fit within max-context-chars.")
        return 0

    print(formatted)
    return 0


def _run_pipeline(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="One-shot pipeline: scan directories, build index, and retrieve."
    )
    parser.add_argument("query", help="Search query string.")
    parser.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help="Directories to scan.",
    )
    parser.add_argument(
        "--index", "-i",
        default=None,
        help="Optional path to persist the index database.",
    )
    parser.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="Maximum number of results (default: 5).",
    )
    parser.add_argument(
        "--max-context-chars", type=int, default=8000,
        help="Maximum total output characters (default: 8000).",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="Include only files matching these glob patterns (e.g. '*.py').",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Exclude files matching these glob patterns.",
    )
    parser.add_argument(
        "--file-types",
        nargs="*",
        default=None,
        help="Include only files with these extensions (e.g. .py .md).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum recursion depth (0 = top-level files only).",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore and .ignore files.",
    )

    args = parser.parse_args(argv)
    formatted, stats = pipeline(
        args.query,
        args.dirs,
        index_path=args.index,
        top_k=args.top_k,
        max_chars=args.max_context_chars,
        include=args.include,
        exclude=args.exclude,
        file_types=_normalize_file_types(args.file_types),
        max_depth=args.max_depth,
        respect_gitignore=not args.no_gitignore,
    )

    if not formatted.strip():
        print("No results found.")
        return 0

    print(formatted)
    print(
        "Index built: "
        f"{stats['indexed']} indexed, "
        f"{stats['skipped']} skipped (unchanged), "
        f"{stats['removed']} removed, "
        f"{stats['errors']} errors.",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    if argv and argv[0] == "pipeline":
        return _run_pipeline(argv[1:])
    return _run_retrieve(argv)


if __name__ == "__main__":
    raise SystemExit(main())
