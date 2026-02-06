#!/usr/bin/env python3
"""Retrieve prompt-ready snippets from a chunk-level RAG index.

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
import vectorizer


_ALLOWED_MODES = ("lex", "sem", "hybrid")


def _normalize_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in _ALLOWED_MODES:
        raise ValueError(f"invalid mode '{mode}'; expected one of: {', '.join(_ALLOWED_MODES)}")
    return normalized


def _normalize_language_tag(language: Any) -> str:
    if not isinstance(language, str) or not language.strip():
        return "text"
    cleaned = "".join(ch for ch in language.strip().lower() if ch.isalnum() or ch in {"+", "-", "_"})
    return cleaned or "text"


def _path_key(result: dict[str, Any]) -> str:
    rel_path = result.get("rel_path")
    if isinstance(rel_path, str) and rel_path.strip():
        return rel_path.strip()
    path = result.get("path")
    if isinstance(path, str) and path.strip():
        return path.strip()
    return "unknown"


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _line_range(result: dict[str, Any]) -> str:
    start_line = _int_or_none(result.get("start_line"))
    end_line = _int_or_none(result.get("end_line"))
    if start_line is None or end_line is None:
        return "?"
    return f"{start_line}-{end_line}"


def _select_diverse_results(results: list[dict[str, Any]], max_per_file: int) -> list[dict[str, Any]]:
    if max_per_file < 1:
        raise ValueError("--max-per-file must be >= 1")
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for result in results:
        key = _path_key(result)
        seen = counts.get(key, 0)
        if seen >= max_per_file:
            continue
        counts[key] = seen + 1
        selected.append(result)
    return selected


def format_results(
    query: str,
    results: list[dict[str, Any]],
    *,
    max_chars: int,
    max_per_file: int,
) -> str:
    """Format ranked search results into prompt-ready, budgeted context."""
    if max_chars < 1:
        raise ValueError("--max-context-chars must be >= 1")

    filtered = _select_diverse_results(results, max_per_file)
    if not filtered:
        return ""

    header = f'<!-- RAG context for: "{query}" -->'
    if len(header) > max_chars:
        return ""

    blocks: list[str] = [header]
    total = len(header)

    for result in filtered:
        snippet = str(result.get("snippet") or "").strip()
        if not snippet:
            continue
        path = _path_key(result)
        lines = _line_range(result)
        language_tag = _normalize_language_tag(result.get("language"))
        block = f"### {path}:{lines}\n```{language_tag}\n{snippet}\n```"

        projected = total + 2 + len(block)
        if projected > max_chars:
            continue
        blocks.append(block)
        total = projected

    if len(blocks) == 1:
        return ""
    return "\n\n".join(blocks)


def _normalize_score_map(raw_scores: dict[str, float]) -> dict[str, float]:
    if not raw_scores:
        return {}
    minimum = min(raw_scores.values())
    maximum = max(raw_scores.values())
    if maximum == minimum:
        return {chunk_id: 1.0 for chunk_id in raw_scores}
    span = maximum - minimum
    return {
        chunk_id: (score - minimum) / span
        for chunk_id, score in raw_scores.items()
    }


def _hybrid_results(query: str, index_path: str, *, top_k: int, alpha: float = 0.6) -> list[dict[str, Any]]:
    candidate_k = max(top_k * 5, top_k)
    lexical = indexer.search_index(query, index_path, top_k=candidate_k)
    semantic = vectorizer.semantic_search(index_path, query, top_k=candidate_k)

    by_id: dict[str, dict[str, Any]] = {}
    lex_scores: dict[str, float] = {}
    sem_scores: dict[str, float] = {}

    for row in lexical:
        chunk_id = str(row.get("chunk_id", "")).strip()
        if not chunk_id:
            continue
        by_id[chunk_id] = row
        # BM25 is lower-is-better; flip sign so higher-is-better for normalization.
        lex_scores[chunk_id] = -float(row.get("score", 0.0))

    for row in semantic:
        chunk_id = str(row.get("chunk_id", "")).strip()
        if not chunk_id:
            continue
        by_id.setdefault(chunk_id, row)
        sem_scores[chunk_id] = float(row.get("score", 0.0))

    lex_norm = _normalize_score_map(lex_scores)
    sem_norm = _normalize_score_map(sem_scores)

    combined: list[dict[str, Any]] = []
    for chunk_id, row in by_id.items():
        score = alpha * lex_norm.get(chunk_id, 0.0) + (1.0 - alpha) * sem_norm.get(chunk_id, 0.0)
        merged = dict(row)
        merged["score"] = round(score, 4)
        combined.append(merged)

    combined.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    return combined[:top_k]


def _search_by_mode(
    query: str,
    index_path: str,
    *,
    top_k: int,
    mode: str,
) -> list[dict[str, Any]]:
    if mode == "lex":
        return indexer.search_index(query, index_path, top_k=top_k)
    if mode == "sem":
        return vectorizer.semantic_search(index_path, query, top_k=top_k)
    return _hybrid_results(query, index_path, top_k=top_k)


def retrieve(
    query: str,
    index_path: str,
    *,
    top_k: int = 5,
    max_chars: int = 8000,
    max_per_file: int = 3,
    mode: str = "lex",
) -> str:
    """Retrieve formatted snippets for a query from an index."""
    if top_k < 1:
        raise ValueError("--top-k must be >= 1")
    normalized_mode = _normalize_mode(mode)
    results = _search_by_mode(
        query,
        index_path,
        top_k=top_k,
        mode=normalized_mode,
    )
    return format_results(
        query,
        results,
        max_chars=max_chars,
        max_per_file=max_per_file,
    )


def _write_manifest(manifest: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def pipeline(
    query: str,
    dirs: list[str],
    *,
    index_path: str | None = None,
    top_k: int = 5,
    max_chars: int = 8000,
    max_per_file: int = 3,
    mode: str = "lex",
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

    stats = {
        "files_processed": 0,
        "files_skipped": 0,
        "files_removed": 0,
        "chunks_indexed": 0,
        "chunks_skipped": 0,
        "chunks_removed": 0,
        "errors": 0,
    }
    if not manifest:
        return "", stats

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        _write_manifest(manifest, manifest_path)
        if index_path is None:
            index_path = str(Path(tmpdir) / "index.db")
        normalized_mode = _normalize_mode(mode)
        stats = indexer.build_index(
            str(manifest_path),
            index_path,
            build_vectors=normalized_mode in {"sem", "hybrid"},
        )
        formatted = retrieve(
            query,
            index_path,
            top_k=top_k,
            max_chars=max_chars,
            max_per_file=max_per_file,
            mode=normalized_mode,
        )

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
    parser.add_argument(
        "--max-per-file",
        type=int,
        default=3,
        help="Maximum number of snippets per file (default: 3).",
    )
    parser.add_argument(
        "--mode",
        choices=_ALLOWED_MODES,
        default="lex",
        help="Retrieval mode.",
    )

    args = parser.parse_args(argv)
    try:
        formatted = retrieve(
            args.query,
            args.index,
            top_k=args.top_k,
            max_chars=args.max_context_chars,
            max_per_file=args.max_per_file,
            mode=args.mode,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not formatted.strip():
        print("No results found.")
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
        "--max-per-file",
        type=int,
        default=3,
        help="Maximum number of snippets per file (default: 3).",
    )
    parser.add_argument(
        "--mode",
        choices=_ALLOWED_MODES,
        default="lex",
        help="Retrieval mode.",
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
    try:
        formatted, stats = pipeline(
            args.query,
            args.dirs,
            index_path=args.index,
            top_k=args.top_k,
            max_chars=args.max_context_chars,
            max_per_file=args.max_per_file,
            mode=args.mode,
            include=args.include,
            exclude=args.exclude,
            file_types=_normalize_file_types(args.file_types),
            max_depth=args.max_depth,
            respect_gitignore=not args.no_gitignore,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not formatted.strip():
        print("No results found.")
        return 0

    print(formatted)
    print(
        "Index built: "
        f"{stats['chunks_indexed']} chunks indexed, "
        f"{stats['chunks_skipped']} chunks skipped (unchanged), "
        f"{stats['chunks_removed']} chunks removed, "
        f"{stats.get('vectors_indexed', 0)} vectors indexed, "
        f"vocab {stats.get('vector_vocab_size', 0)}, "
        f"{stats['files_processed']} files processed, "
        f"{stats['files_removed']} files removed, "
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
