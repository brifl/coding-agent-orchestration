#!/usr/bin/env python3
"""Index builder for multi-directory RAG indexing (schema v2).

Reads a file manifest (from scanner.py), chunks files (via chunker.py),
and indexes chunk text into a SQLite database with FTS5 for full-text search.

Schema v2 changes from v1:
- New ``chunks`` table for chunk-level storage
- FTS5 (``chunks_fts``) indexes chunk text instead of whole-file text
- ``docs`` table gains ``language`` column
- Incremental updates at chunk granularity via ``chunk_hash``

Supports:
- Full-text search via SQLite FTS5 with BM25 ranking at chunk granularity
- Incremental indexing: only re-indexes chunks whose content has changed
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

# Import chunker as a library call (same skill directory)
_skill_dir = Path(__file__).parent.resolve()
if str(_skill_dir) not in sys.path:
    sys.path.insert(0, str(_skill_dir))

from chunker import chunk_file  # noqa: E402


_SCHEMA_VERSION = 2


def _init_db(conn: sqlite3.Connection) -> None:
    """Create v2 tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS docs (
            doc_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            path         TEXT UNIQUE NOT NULL,
            rel_path     TEXT NOT NULL,
            root         TEXT NOT NULL,
            size         INTEGER,
            mtime        REAL,
            mime_type    TEXT,
            language     TEXT,
            content_hash TEXT
        );

        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id       TEXT PRIMARY KEY,
            doc_id         INTEGER NOT NULL REFERENCES docs(doc_id),
            start_line     INTEGER NOT NULL,
            end_line       INTEGER NOT NULL,
            token_estimate INTEGER,
            chunk_hash     TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            chunk_id,
            chunk_text,
            tokenize='porter unicode61'
        );
    """)
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("schema_version", str(_SCHEMA_VERSION)),
    )
    conn.commit()


def _check_migration(conn: sqlite3.Connection, db_path: str) -> bool:
    """Check if existing DB is v1 and needs migration.

    Returns True if migration was performed (DB was dropped and recreated).
    """
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
    except sqlite3.OperationalError:
        # No meta table — fresh DB
        return False

    if row is None:
        return False

    version = int(row[0])
    if version >= _SCHEMA_VERSION:
        return False

    # v1 detected — drop everything and rebuild
    print(
        f"WARNING: Existing index at {db_path} uses schema v{version}. "
        f"Dropping and rebuilding for v{_SCHEMA_VERSION}.",
        file=sys.stderr,
    )
    # Drop all tables (FTS virtual tables must be dropped explicitly)
    for table in ("docs_fts", "chunks_fts", "chunks", "docs", "meta"):
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return True


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

    Two-phase build:
    1. Process manifest files, compute chunks, diff against DB
    2. Batch insert/delete in a single transaction

    Returns stats dict with chunk-level counts.
    """
    manifest: list[dict[str, Any]] = json.loads(
        Path(manifest_path).read_text(encoding="utf-8")
    )

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode=WAL")

    _check_migration(conn, output_path)
    _init_db(conn)

    stats = {
        "files_processed": 0,
        "files_skipped": 0,
        "files_removed": 0,
        "chunks_indexed": 0,
        "chunks_skipped": 0,
        "chunks_removed": 0,
        "errors": 0,
    }

    manifest_paths: set[str] = set()

    for entry in manifest:
        file_path = entry["path"]
        manifest_paths.add(file_path)

        # Read file content
        content = _read_file_text(file_path)
        if content is None:
            stats["errors"] += 1
            continue

        content_hash = entry.get("content_hash") or _hash_content(content)
        language = entry.get("language")

        # Check if doc already indexed with same content_hash
        row = conn.execute(
            "SELECT doc_id, content_hash FROM docs WHERE path = ?",
            (file_path,),
        ).fetchone()

        if row is not None:
            existing_id, existing_hash = row
            if existing_hash == content_hash:
                # File unchanged — all chunks still valid
                stats["files_skipped"] += 1
                continue

            # File changed — remove old chunks and FTS entries
            old_chunks = conn.execute(
                "SELECT chunk_id FROM chunks WHERE doc_id = ?",
                (existing_id,),
            ).fetchall()
            for (old_cid,) in old_chunks:
                conn.execute(
                    "DELETE FROM chunks_fts WHERE chunk_id = ?",
                    (old_cid,),
                )
                stats["chunks_removed"] += 1
            conn.execute(
                "DELETE FROM chunks WHERE doc_id = ?",
                (existing_id,),
            )

            # Update doc metadata
            conn.execute(
                "UPDATE docs SET rel_path=?, root=?, size=?, mtime=?, "
                "mime_type=?, language=?, content_hash=? WHERE doc_id=?",
                (
                    entry.get("rel_path", ""),
                    entry.get("root", ""),
                    entry.get("size"),
                    entry.get("mtime"),
                    entry.get("type", ""),
                    language,
                    content_hash,
                    existing_id,
                ),
            )
            doc_id = existing_id
        else:
            # New file
            cur = conn.execute(
                "INSERT INTO docs (path, rel_path, root, size, mtime, mime_type, language, content_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    file_path,
                    entry.get("rel_path", ""),
                    entry.get("root", ""),
                    entry.get("size"),
                    entry.get("mtime"),
                    entry.get("type", ""),
                    language,
                    content_hash,
                ),
            )
            doc_id = cur.lastrowid

        # Chunk the file
        file_chunks = chunk_file(file_path, language=language)

        # Insert chunks and FTS entries
        for chunk in file_chunks:
            chunk_id = chunk["chunk_id"]
            chunk_hash = chunk["hash"]

            # Check if this exact chunk already exists (shouldn't for changed files,
            # but handles edge cases)
            existing_chunk = conn.execute(
                "SELECT chunk_hash FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()

            if existing_chunk is not None:
                if existing_chunk[0] == chunk_hash:
                    stats["chunks_skipped"] += 1
                    continue
                # Chunk content changed — remove old FTS entry
                conn.execute(
                    "DELETE FROM chunks_fts WHERE chunk_id = ?",
                    (chunk_id,),
                )
                conn.execute(
                    "DELETE FROM chunks WHERE chunk_id = ?",
                    (chunk_id,),
                )

            conn.execute(
                "INSERT INTO chunks (chunk_id, doc_id, start_line, end_line, "
                "token_estimate, chunk_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    chunk_id,
                    doc_id,
                    chunk["start_line"],
                    chunk["end_line"],
                    chunk["token_estimate"],
                    chunk_hash,
                ),
            )
            conn.execute(
                "INSERT INTO chunks_fts(chunk_id, chunk_text) VALUES (?, ?)",
                (chunk_id, chunk["text"]),
            )
            stats["chunks_indexed"] += 1

        stats["files_processed"] += 1

    # Remove docs (and their chunks) no longer in the manifest
    existing = conn.execute("SELECT doc_id, path FROM docs").fetchall()
    for doc_id, path in existing:
        if path not in manifest_paths:
            old_chunks = conn.execute(
                "SELECT chunk_id FROM chunks WHERE doc_id = ?",
                (doc_id,),
            ).fetchall()
            for (old_cid,) in old_chunks:
                conn.execute(
                    "DELETE FROM chunks_fts WHERE chunk_id = ?",
                    (old_cid,),
                )
                stats["chunks_removed"] += 1
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM docs WHERE doc_id = ?", (doc_id,))
            stats["files_removed"] += 1

    conn.commit()
    conn.close()
    return stats


def search_index(
    query: str,
    index_path: str,
    *,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Search the index at chunk granularity and return ranked results.

    Returns list of result dicts with path, rel_path, start_line, end_line,
    snippet, chunk_id, and score.
    """
    conn = sqlite3.connect(index_path)

    results: list[dict[str, Any]] = []
    rows = conn.execute(
        """
        SELECT
            d.path,
            d.rel_path,
            d.root,
            d.language,
            c.chunk_id,
            c.start_line,
            c.end_line,
            bm25(chunks_fts, 1.0, 5.0) AS score,
            snippet(chunks_fts, 1, '>>>', '<<<', '...', 40) AS snippet
        FROM chunks_fts
        JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
        JOIN docs d ON d.doc_id = c.doc_id
        WHERE chunks_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (query, top_k),
    ).fetchall()

    for path, rel_path, root, language, chunk_id, start_line, end_line, score, snippet in rows:
        results.append({
            "path": path,
            "rel_path": rel_path,
            "root": root,
            "language": language,
            "chunk_id": chunk_id,
            "start_line": start_line,
            "end_line": end_line,
            "score": round(score, 4),
            "snippet": snippet,
        })

    conn.close()
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build and search a chunk-level file index for RAG."
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
            f"Index built: {stats['files_processed']} files processed, "
            f"{stats['files_skipped']} files skipped (unchanged), "
            f"{stats['files_removed']} files removed, "
            f"{stats['chunks_indexed']} chunks indexed, "
            f"{stats['chunks_skipped']} chunks skipped, "
            f"{stats['chunks_removed']} chunks removed, "
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
