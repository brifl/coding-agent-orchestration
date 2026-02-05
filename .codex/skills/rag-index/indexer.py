#!/usr/bin/env python3
"""Index builder for multi-directory RAG indexing.

Reads a file manifest (from scanner.py), indexes file contents into a
SQLite database with FTS5 for full-text search, and supports incremental
re-indexing by tracking content hashes.

Supports:
- Full-text search via SQLite FTS5 with BM25 ranking
- Semantic search stub (requires external embeddings library)
- Incremental indexing: only re-indexes files whose content has changed
- Persistent storage in a single SQLite file
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


_SCHEMA_VERSION = 1


def _init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS docs (
            doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            path        TEXT UNIQUE NOT NULL,
            rel_path    TEXT NOT NULL,
            root        TEXT NOT NULL,
            size        INTEGER,
            mtime       REAL,
            mime_type   TEXT,
            content_hash TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            rel_path,
            content_text,
            tokenize='porter unicode61'
        );
    """)
    # Store schema version
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("schema_version", str(_SCHEMA_VERSION)),
    )
    conn.commit()


def _hash_content(text: str) -> str:
    """Return SHA-256 hex digest of text content."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _read_file_text(path: str) -> str | None:
    """Read file as text, returning None if binary or unreadable."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None


def build_index(
    manifest_path: str,
    output_path: str,
) -> dict[str, int]:
    """Build or update an index from a manifest file.

    Args:
        manifest_path: Path to the JSON manifest from scanner.py.
        output_path: Path to the SQLite database file.

    Returns:
        Stats dict with counts of indexed, skipped, removed, and errored files.
    """
    manifest: list[dict[str, Any]] = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode=WAL")
    _init_db(conn)

    stats = {"indexed": 0, "skipped": 0, "removed": 0, "errors": 0}

    # Track which paths are in the current manifest
    manifest_paths: set[str] = set()

    for entry in manifest:
        file_path = entry["path"]
        manifest_paths.add(file_path)

        # Read file content
        content = _read_file_text(file_path)
        if content is None:
            stats["errors"] += 1
            continue

        content_hash = _hash_content(content)

        # Check if already indexed with same hash (incremental)
        row = conn.execute(
            "SELECT doc_id, content_hash FROM docs WHERE path = ?",
            (file_path,),
        ).fetchone()

        if row is not None:
            existing_id, existing_hash = row
            if existing_hash == content_hash:
                stats["skipped"] += 1
                continue
            # Content changed — remove old FTS entry, update doc
            conn.execute(
                "DELETE FROM docs_fts WHERE rowid = ?",
                (existing_id,),
            )
            conn.execute(
                "UPDATE docs SET rel_path=?, root=?, size=?, mtime=?, "
                "mime_type=?, content_hash=? WHERE doc_id=?",
                (
                    entry.get("rel_path", ""),
                    entry.get("root", ""),
                    entry.get("size"),
                    entry.get("mtime"),
                    entry.get("type", ""),
                    content_hash,
                    existing_id,
                ),
            )
            doc_id = existing_id
        else:
            # New file
            cur = conn.execute(
                "INSERT INTO docs (path, rel_path, root, size, mtime, mime_type, content_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    file_path,
                    entry.get("rel_path", ""),
                    entry.get("root", ""),
                    entry.get("size"),
                    entry.get("mtime"),
                    entry.get("type", ""),
                    content_hash,
                ),
            )
            doc_id = cur.lastrowid

        # Insert into FTS index
        conn.execute(
            "INSERT INTO docs_fts(rowid, rel_path, content_text) VALUES (?, ?, ?)",
            (doc_id, entry.get("rel_path", ""), content),
        )
        stats["indexed"] += 1

    # Remove docs no longer in the manifest
    existing = conn.execute("SELECT doc_id, path, rel_path FROM docs").fetchall()
    for doc_id, path, rel_path in existing:
        if path not in manifest_paths:
            conn.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
            conn.execute("DELETE FROM docs WHERE doc_id = ?", (doc_id,))
            stats["removed"] += 1

    conn.commit()
    conn.close()
    return stats


def search_index(
    query: str,
    index_path: str,
    *,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Search the index and return ranked results.

    Args:
        query: The search query string.
        index_path: Path to the SQLite database.
        top_k: Maximum number of results to return.

    Returns:
        List of result dicts with path, rel_path, rank score, and snippet.
    """
    conn = sqlite3.connect(index_path)

    results: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT
            d.path,
            d.rel_path,
            d.root,
            d.mime_type,
            bm25(docs_fts, 1.0, 5.0) AS score,
            snippet(docs_fts, 1, '>>>', '<<<', '...', 40) AS snippet
        FROM docs_fts
        JOIN docs d ON d.doc_id = docs_fts.rowid
        WHERE docs_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (query, top_k),
    ).fetchall()

    for path, rel_path, root, mime_type, score, snippet in rows:
        results.append({
            "path": path,
            "rel_path": rel_path,
            "root": root,
            "type": mime_type,
            "score": round(score, 4),
            "snippet": snippet,
        })

    conn.close()
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build and search a file index for RAG."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # build subcommand
    build_p = sub.add_parser("build", help="Build or update the index from a manifest.")
    build_p.add_argument(
        "--manifest", "-m", required=True,
        help="Path to the JSON manifest from scanner.py.",
    )
    build_p.add_argument(
        "--output", "-o", required=True,
        help="Path to the SQLite index database.",
    )

    # search subcommand
    search_p = sub.add_parser("search", help="Search the index.")
    search_p.add_argument("query", help="Search query string.")
    search_p.add_argument(
        "--index", "-i", required=True,
        help="Path to the SQLite index database.",
    )
    search_p.add_argument(
        "--top-k", "-k", type=int, default=10,
        help="Maximum number of results (default: 10).",
    )

    args = parser.parse_args(argv)

    if args.command == "build":
        stats = build_index(args.manifest, args.output)
        print(
            f"Index built: {stats['indexed']} indexed, "
            f"{stats['skipped']} skipped (unchanged), "
            f"{stats['removed']} removed, "
            f"{stats['errors']} errors."
        )

    elif args.command == "search":
        results = search_index(args.query, args.index, top_k=args.top_k)
        if not results:
            print("No results found.")
        else:
            print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
