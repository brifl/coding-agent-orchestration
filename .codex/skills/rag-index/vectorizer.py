#!/usr/bin/env python3
"""TF-IDF vector utilities for chunk-level semantic retrieval."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from typing import Any


_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_DEFAULT_MAX_VOCAB = 10_000
_DEFAULT_MIN_DF = 2
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def _tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in _TOKEN_RE.findall(text)]


def _serialize_vector(vec: dict[int, float]) -> str:
    payload = {str(idx): round(weight, 8) for idx, weight in vec.items()}
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _deserialize_vector(raw: str) -> dict[int, float]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    vec: dict[int, float] = {}
    for key, value in payload.items():
        try:
            idx = int(key)
            weight = float(value)
        except (TypeError, ValueError):
            continue
        vec[idx] = weight
    return vec


def _build_tfidf_vectors(
    chunks: list[tuple[str, str]],
    *,
    max_vocab: int = _DEFAULT_MAX_VOCAB,
    min_df: int = _DEFAULT_MIN_DF,
) -> tuple[list[str], list[float], dict[str, dict[int, float]]]:
    doc_term_counts: dict[str, Counter[str]] = {}
    df_counts: Counter[str] = Counter()

    for chunk_id, text in chunks:
        tokens = _tokenize(text)
        if not tokens:
            doc_term_counts[chunk_id] = Counter()
            continue
        counts = Counter(tokens)
        doc_term_counts[chunk_id] = counts
        for term in counts:
            df_counts[term] += 1

    doc_count = len(chunks)
    if doc_count == 0:
        return ([], [], {})

    terms = [
        (term, df)
        for term, df in df_counts.items()
        if df >= min_df and term not in _STOP_WORDS
    ]
    terms.sort(key=lambda item: (-item[1], item[0]))
    vocab_terms = [term for term, _ in terms[:max_vocab]]
    vocab_index = {term: idx for idx, term in enumerate(vocab_terms)}

    idf: list[float] = []
    for term in vocab_terms:
        df = df_counts[term]
        idf.append(math.log((doc_count + 1.0) / (df + 1.0)) + 1.0)

    vectors: dict[str, dict[int, float]] = {}
    for chunk_id, counts in doc_term_counts.items():
        vec: dict[int, float] = {}
        norm_sq = 0.0
        for term, count in counts.items():
            idx = vocab_index.get(term)
            if idx is None:
                continue
            tf = 1.0 + math.log(float(count))
            weight = tf * idf[idx]
            vec[idx] = weight
            norm_sq += weight * weight
        if norm_sq > 0.0:
            inv_norm = 1.0 / math.sqrt(norm_sq)
            for idx in list(vec):
                vec[idx] *= inv_norm
        vectors[chunk_id] = vec

    return (vocab_terms, idf, vectors)


def _load_model(conn: sqlite3.Connection) -> tuple[list[str], list[float]]:
    vocab_row = conn.execute(
        "SELECT value FROM meta WHERE key = 'vectorizer_vocab'"
    ).fetchone()
    idf_row = conn.execute(
        "SELECT value FROM meta WHERE key = 'vectorizer_idf'"
    ).fetchone()
    if vocab_row is None or idf_row is None:
        raise ValueError("semantic vectors are not available; run indexer build with --vectors")

    try:
        vocab = json.loads(vocab_row[0])
        idf = json.loads(idf_row[0])
    except json.JSONDecodeError as exc:
        raise ValueError("stored vectorizer metadata is invalid; rebuild with --vectors") from exc

    if not isinstance(vocab, list) or not isinstance(idf, list):
        raise ValueError("stored vectorizer metadata is invalid; rebuild with --vectors")
    if len(vocab) != len(idf):
        raise ValueError("stored vectorizer metadata is inconsistent; rebuild with --vectors")

    vocab_terms = [str(term) for term in vocab]
    idf_values = [float(value) for value in idf]
    return (vocab_terms, idf_values)


def _build_query_vector(query: str, vocab_terms: list[str], idf: list[float]) -> dict[int, float]:
    vocab_index = {term: idx for idx, term in enumerate(vocab_terms)}
    counts = Counter(_tokenize(query))
    vec: dict[int, float] = {}
    norm_sq = 0.0
    for term, count in counts.items():
        idx = vocab_index.get(term)
        if idx is None:
            continue
        tf = 1.0 + math.log(float(count))
        weight = tf * idf[idx]
        vec[idx] = weight
        norm_sq += weight * weight
    if norm_sq > 0.0:
        inv_norm = 1.0 / math.sqrt(norm_sq)
        for idx in list(vec):
            vec[idx] *= inv_norm
    return vec


def _dot(a: dict[int, float], b: dict[int, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(weight * b.get(idx, 0.0) for idx, weight in a.items())


def rebuild_vectors(
    conn: sqlite3.Connection,
    *,
    max_vocab: int = _DEFAULT_MAX_VOCAB,
    min_df: int = _DEFAULT_MIN_DF,
) -> dict[str, int]:
    """Recompute and persist TF-IDF vectors for all indexed chunks."""
    chunks = conn.execute(
        "SELECT chunk_id, chunk_text FROM chunks_fts"
    ).fetchall()
    rows = [(str(chunk_id), str(chunk_text or "")) for chunk_id, chunk_text in chunks]
    vocab, idf, vectors = _build_tfidf_vectors(rows, max_vocab=max_vocab, min_df=min_df)

    conn.execute("DELETE FROM vectors")
    payload = [
        (chunk_id, _serialize_vector(vectors.get(chunk_id, {})))
        for chunk_id, _ in rows
        if vectors.get(chunk_id)
    ]
    if payload:
        conn.executemany(
            "INSERT INTO vectors (chunk_id, vector) VALUES (?, ?)",
            payload,
        )

    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("vectorizer_vocab", json.dumps(vocab, separators=(",", ":"))),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("vectorizer_idf", json.dumps(idf, separators=(",", ":"))),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("vectorizer_chunk_count", str(len(rows))),
    )
    return {
        "vectors_indexed": len(payload),
        "vector_vocab_size": len(vocab),
    }


def clear_vectors(conn: sqlite3.Connection) -> None:
    """Clear vector rows and model metadata."""
    conn.execute("DELETE FROM vectors")
    conn.execute("DELETE FROM meta WHERE key = 'vectorizer_vocab'")
    conn.execute("DELETE FROM meta WHERE key = 'vectorizer_idf'")
    conn.execute("DELETE FROM meta WHERE key = 'vectorizer_chunk_count'")


def semantic_search(
    index_path: str,
    query: str,
    *,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Return semantic (TF-IDF cosine) search results at chunk granularity."""
    if top_k < 1:
        raise ValueError("--top-k must be >= 1")

    conn = sqlite3.connect(index_path)
    try:
        vocab, idf = _load_model(conn)
        query_vec = _build_query_vector(query, vocab, idf)
        if not query_vec:
            return []

        scores: list[tuple[str, float]] = []
        for chunk_id, raw_vector in conn.execute("SELECT chunk_id, vector FROM vectors"):
            vec = _deserialize_vector(str(raw_vector))
            if not vec:
                continue
            score = _dot(query_vec, vec)
            if score > 0.0:
                scores.append((str(chunk_id), score))

        if not scores:
            return []
        scores.sort(key=lambda item: item[1], reverse=True)
        top = scores[:top_k]
        by_chunk = {chunk_id: score for chunk_id, score in top}

        placeholders = ",".join("?" for _ in top)
        rows = conn.execute(
            f"""
            SELECT
                d.path,
                d.rel_path,
                d.root,
                d.language,
                c.chunk_id,
                c.start_line,
                c.end_line,
                snippet(chunks_fts, 1, '>>>', '<<<', '...', 40) AS snippet
            FROM chunks c
            JOIN docs d ON d.doc_id = c.doc_id
            JOIN chunks_fts ON chunks_fts.chunk_id = c.chunk_id
            WHERE c.chunk_id IN ({placeholders})
            """,
            [chunk_id for chunk_id, _ in top],
        ).fetchall()
        by_meta = {
            str(chunk_id): {
                "path": path,
                "rel_path": rel_path,
                "root": root,
                "language": language,
                "chunk_id": chunk_id,
                "start_line": start_line,
                "end_line": end_line,
                "snippet": snippet,
            }
            for path, rel_path, root, language, chunk_id, start_line, end_line, snippet in rows
        }

        results: list[dict[str, Any]] = []
        for chunk_id, score in top:
            meta = by_meta.get(chunk_id)
            if not meta:
                continue
            payload = dict(meta)
            payload["score"] = round(score, 4)
            results.append(payload)
        return results
    finally:
        conn.close()
