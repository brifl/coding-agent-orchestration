#!/usr/bin/env python3
"""Deterministic chunking engine for RAG indexing.

Splits files into indexed units suitable for precise retrieval.
Supports language-specific strategies: Python (AST), Markdown (headings),
generic code (blank-line blocks), and a fixed-size fallback.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_chunk(
    doc_path: str,
    lines: list[str],
    start_line: int,
    end_line: int,
    content_hash: str,
    language: str | None,
) -> dict[str, Any]:
    """Build a chunk dict from a range of lines."""
    text = "\n".join(lines)
    return {
        "chunk_id": f"{content_hash}:{start_line}-{end_line}",
        "doc_path": doc_path,
        "start_line": start_line,
        "end_line": end_line,
        "text": text,
        "token_estimate": len(text) // 4,
        "hash": _sha256(text),
        "language": language,
    }


def _force_split(
    doc_path: str,
    lines: list[str],
    start_line: int,
    content_hash: str,
    language: str | None,
    max_chars: int,
) -> list[dict[str, Any]]:
    """Force-split a block that exceeds the hard cap into smaller chunks."""
    chunks: list[dict[str, Any]] = []
    buf: list[str] = []
    buf_start = start_line
    buf_chars = 0

    for i, line in enumerate(lines):
        line_chars = len(line) + 1  # +1 for newline join
        if buf and buf_chars + line_chars > max_chars:
            chunks.append(_make_chunk(
                doc_path, buf, buf_start, buf_start + len(buf) - 1,
                content_hash, language,
            ))
            buf = []
            buf_start = start_line + i
            buf_chars = 0
        buf.append(line)
        buf_chars += line_chars

    if buf:
        chunks.append(_make_chunk(
            doc_path, buf, buf_start, buf_start + len(buf) - 1,
            content_hash, language,
        ))
    return chunks


# ---------------------------------------------------------------------------
# Python AST strategy
# ---------------------------------------------------------------------------

def _ast_node_lines(node: ast.AST) -> tuple[int, int]:
    """Get the line range of an AST node (1-indexed, inclusive)."""
    return node.lineno, node.end_lineno or node.lineno


def _is_import(node: ast.AST) -> bool:
    """Check if a node is an import statement."""
    return isinstance(node, (ast.Import, ast.ImportFrom))


def _group_top_level_nodes(body: list[ast.stmt]) -> list[list[ast.stmt]]:
    """Group consecutive import statements into single groups.

    Each function/class/assignment is its own group.
    Consecutive imports merge into one group.
    """
    groups: list[list[ast.stmt]] = []
    for node in body:
        if _is_import(node) and groups and all(_is_import(n) for n in groups[-1]):
            groups[-1].append(node)
        else:
            groups.append([node])
    return groups


def _chunk_python(
    doc_path: str,
    all_lines: list[str],
    content_hash: str,
    language: str | None,
    max_chunk_tokens: int,
) -> list[dict[str, Any]]:
    """Chunk Python using AST: each top-level function/class/assignment becomes a chunk.

    Consecutive import statements are grouped into a single chunk.
    """
    source = "\n".join(all_lines)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_generic(doc_path, all_lines, content_hash, language, max_chunk_tokens)

    if not tree.body:
        return [_make_chunk(doc_path, all_lines, 1, len(all_lines), content_hash, language)]

    max_chars = max_chunk_tokens * 5
    chunks: list[dict[str, Any]] = []
    covered_end = 0  # track last covered line (0 = none yet)

    groups = _group_top_level_nodes(tree.body)

    for group in groups:
        first_start, _ = _ast_node_lines(group[0])
        _, last_end = _ast_node_lines(group[-1])

        # Capture any gap lines before this group (comments, blank lines, docstrings, etc.)
        if covered_end + 1 < first_start:
            gap_lines = all_lines[covered_end:first_start - 1]
            node_lines = gap_lines + all_lines[first_start - 1:last_end]
            chunk_start = covered_end + 1
        else:
            node_lines = all_lines[first_start - 1:last_end]
            chunk_start = first_start

        text = "\n".join(node_lines)
        node = group[0] if len(group) == 1 else None
        if len(text) > max_chars:
            # For classes, try splitting by method
            if node and isinstance(node, ast.ClassDef) and node.body:
                sub_chunks = _split_class_methods(
                    doc_path, all_lines, node, chunk_start, content_hash, language, max_chars,
                )
                chunks.extend(sub_chunks)
            else:
                chunks.extend(_force_split(
                    doc_path, node_lines, chunk_start, content_hash, language, max_chars,
                ))
        else:
            chunks.append(_make_chunk(
                doc_path, node_lines, chunk_start, chunk_start + len(node_lines) - 1,
                content_hash, language,
            ))

        covered_end = last_end

    # Trailing lines after last AST node
    if covered_end < len(all_lines):
        trailing = all_lines[covered_end:]
        if trailing and any(l.strip() for l in trailing):
            chunks.append(_make_chunk(
                doc_path, trailing, covered_end + 1, len(all_lines),
                content_hash, language,
            ))
        elif chunks:
            # Append blank trailing lines to last chunk
            last = chunks[-1]
            last["text"] += "\n" + "\n".join(trailing)
            last["end_line"] = len(all_lines)
            last["token_estimate"] = len(last["text"]) // 4
            last["hash"] = _sha256(last["text"])
            last["chunk_id"] = f"{content_hash}:{last['start_line']}-{last['end_line']}"

    return chunks


def _split_class_methods(
    doc_path: str,
    all_lines: list[str],
    class_node: ast.ClassDef,
    chunk_start: int,
    content_hash: str,
    language: str | None,
    max_chars: int,
) -> list[dict[str, Any]]:
    """Split a large class into per-method chunks."""
    chunks: list[dict[str, Any]] = []
    class_start, class_end = _ast_node_lines(class_node)

    # Class header: from chunk_start to first body node
    first_body = class_node.body[0]
    first_body_start = first_body.lineno
    header_lines = all_lines[chunk_start - 1:first_body_start - 1]
    if header_lines:
        chunks.append(_make_chunk(
            doc_path, header_lines, chunk_start, chunk_start + len(header_lines) - 1,
            content_hash, language,
        ))

    # Each body statement as a chunk
    prev_end = first_body_start - 1
    for stmt in class_node.body:
        s, e = _ast_node_lines(stmt)
        stmt_lines = all_lines[s - 1:e]
        text = "\n".join(stmt_lines)
        if len(text) > max_chars:
            chunks.extend(_force_split(doc_path, stmt_lines, s, content_hash, language, max_chars))
        else:
            chunks.append(_make_chunk(doc_path, stmt_lines, s, e, content_hash, language))
        prev_end = e

    return chunks


# ---------------------------------------------------------------------------
# Markdown strategy
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+")


def _chunk_markdown(
    doc_path: str,
    all_lines: list[str],
    content_hash: str,
    language: str | None,
    max_chunk_tokens: int,
) -> list[dict[str, Any]]:
    """Chunk Markdown by heading hierarchy."""
    max_chars = max_chunk_tokens * 5
    sections: list[tuple[int, int]] = []  # (start_line_0idx, end_line_0idx_exclusive)
    current_start = 0

    for i, line in enumerate(all_lines):
        if i > 0 and _HEADING_RE.match(line):
            sections.append((current_start, i))
            current_start = i

    sections.append((current_start, len(all_lines)))

    chunks: list[dict[str, Any]] = []
    for s0, e0 in sections:
        sec_lines = all_lines[s0:e0]
        if not sec_lines or not any(l.strip() for l in sec_lines):
            continue
        text = "\n".join(sec_lines)
        if len(text) > max_chars:
            chunks.extend(_force_split(
                doc_path, sec_lines, s0 + 1, content_hash, language, max_chars,
            ))
        else:
            chunks.append(_make_chunk(
                doc_path, sec_lines, s0 + 1, e0, content_hash, language,
            ))

    return chunks


# ---------------------------------------------------------------------------
# Generic code strategy
# ---------------------------------------------------------------------------

def _chunk_generic(
    doc_path: str,
    all_lines: list[str],
    content_hash: str,
    language: str | None,
    max_chunk_tokens: int,
) -> list[dict[str, Any]]:
    """Chunk by blank-line-separated blocks, merging small adjacent blocks."""
    max_chars = max_chunk_tokens * 5
    min_chars = max_chunk_tokens  # minimum target before merging

    # Split into blocks at blank lines
    blocks: list[tuple[int, list[str]]] = []  # (start_0idx, lines)
    current_block: list[str] = []
    block_start = 0

    for i, line in enumerate(all_lines):
        if line.strip() == "" and current_block:
            current_block.append(line)
            # Check if next line is also blank or end of file
            if i + 1 >= len(all_lines) or all_lines[i + 1].strip() != "":
                blocks.append((block_start, current_block))
                current_block = []
                block_start = i + 1
            continue
        if not current_block:
            block_start = i
        current_block.append(line)

    if current_block:
        blocks.append((block_start, current_block))

    if not blocks:
        return [_make_chunk(doc_path, all_lines, 1, len(all_lines), content_hash, language)]

    # Merge small adjacent blocks
    merged: list[tuple[int, list[str]]] = [blocks[0]]
    for start_0, blk_lines in blocks[1:]:
        prev_start, prev_lines = merged[-1]
        combined_text = "\n".join(prev_lines) + "\n" + "\n".join(blk_lines)
        if len(combined_text) < min_chars:
            merged[-1] = (prev_start, prev_lines + blk_lines)
        else:
            merged.append((start_0, blk_lines))

    chunks: list[dict[str, Any]] = []
    for start_0, blk_lines in merged:
        text = "\n".join(blk_lines)
        start_1 = start_0 + 1
        end_1 = start_0 + len(blk_lines)
        if len(text) > max_chars:
            chunks.extend(_force_split(
                doc_path, blk_lines, start_1, content_hash, language, max_chars,
            ))
        else:
            chunks.append(_make_chunk(
                doc_path, blk_lines, start_1, end_1, content_hash, language,
            ))

    return chunks


# ---------------------------------------------------------------------------
# Fallback strategy (fixed-size windows)
# ---------------------------------------------------------------------------

def _chunk_fallback(
    doc_path: str,
    all_lines: list[str],
    content_hash: str,
    language: str | None,
    window: int = 100,
    overlap: int = 20,
) -> list[dict[str, Any]]:
    """Fixed-size line windows with overlap."""
    if len(all_lines) <= window:
        return [_make_chunk(doc_path, all_lines, 1, len(all_lines), content_hash, language)]

    chunks: list[dict[str, Any]] = []
    step = max(1, window - overlap)
    i = 0
    while i < len(all_lines):
        end = min(i + window, len(all_lines))
        chunk_lines = all_lines[i:end]
        chunks.append(_make_chunk(
            doc_path, chunk_lines, i + 1, end, content_hash, language,
        ))
        if end >= len(all_lines):
            break
        i += step

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_file(
    path: str | Path,
    language: str | None = None,
    max_chunk_tokens: int = 500,
) -> list[dict[str, Any]]:
    """Chunk a file using the appropriate strategy.

    Args:
        path: Path to the file to chunk.
        language: Language identifier (e.g. "python", "markdown").
                  If None, uses fallback strategy.
        max_chunk_tokens: Target max tokens per chunk (~4 chars/token).

    Returns:
        List of chunk dicts with deterministic ordering and IDs.
    """
    p = Path(path)
    content = p.read_text(encoding="utf-8", errors="replace")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    all_lines = content.splitlines()
    doc_path = str(p)

    if not all_lines:
        return [_make_chunk(doc_path, [""], 1, 1, content_hash, language)]

    if language == "python":
        chunks = _chunk_python(doc_path, all_lines, content_hash, language, max_chunk_tokens)
    elif language == "markdown":
        chunks = _chunk_markdown(doc_path, all_lines, content_hash, language, max_chunk_tokens)
    elif language is not None:
        chunks = _chunk_generic(doc_path, all_lines, content_hash, language, max_chunk_tokens)
    else:
        chunks = _chunk_fallback(doc_path, all_lines, content_hash, language)

    # Ensure contiguous, non-overlapping coverage
    chunks = _ensure_contiguous(chunks, doc_path, all_lines, content_hash, language)

    return chunks


def _ensure_contiguous(
    chunks: list[dict[str, Any]],
    doc_path: str,
    all_lines: list[str],
    content_hash: str,
    language: str | None,
) -> list[dict[str, Any]]:
    """Fill any gaps to guarantee contiguous coverage of all lines."""
    if not chunks:
        return [_make_chunk(doc_path, all_lines, 1, len(all_lines), content_hash, language)]

    # Sort by start_line
    chunks.sort(key=lambda c: c["start_line"])

    result: list[dict[str, Any]] = []
    expected_start = 1

    for chunk in chunks:
        if chunk["start_line"] > expected_start:
            # Fill gap
            gap_lines = all_lines[expected_start - 1:chunk["start_line"] - 1]
            result.append(_make_chunk(
                doc_path, gap_lines, expected_start, chunk["start_line"] - 1,
                content_hash, language,
            ))
        result.append(chunk)
        expected_start = chunk["end_line"] + 1

    # Fill trailing gap
    if expected_start <= len(all_lines):
        trailing = all_lines[expected_start - 1:]
        result.append(_make_chunk(
            doc_path, trailing, expected_start, len(all_lines),
            content_hash, language,
        ))

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Chunk a file for RAG indexing."
    )
    parser.add_argument("file", help="Path to the file to chunk.")
    parser.add_argument(
        "--language",
        default=None,
        help="Language identifier (e.g. python, markdown). Auto-detects if omitted.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Target max tokens per chunk (default: 500).",
    )

    args = parser.parse_args(argv)

    # Auto-detect language from extension if not specified
    language = args.language
    if language is None:
        from scanner import _EXTENSION_TO_LANGUAGE
        ext = Path(args.file).suffix.lower()
        language = _EXTENSION_TO_LANGUAGE.get(ext)

    chunks = chunk_file(args.file, language=language, max_chunk_tokens=args.max_tokens)
    print(json.dumps(chunks, indent=2))


if __name__ == "__main__":
    main()
