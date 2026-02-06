---
name: rag-index
description: Experimental RAG indexing utilities (scanner + indexer + retriever).
version: "0.1.0"
---
# rag-index

## Purpose

Prototype utilities for building a repo index used by retrieval-augmented prompts.
The workflow is scan -> index -> retrieve, with a one-shot pipeline for ad-hoc use.

## Scripts

- `scanner.py` — recursive directory scanner that emits deterministic JSON manifests
- `indexer.py` — chunk-aware SQLite index builder and lexical search (`build`, `search`)
- `retrieve.py` — prompt-context formatter that consumes chunk-level search results (`retrieve`, `pipeline`)

## How to use

1. Generate a manifest (scanner):
   - `python3 scanner.py <path1> <path2> --output manifest.json`
   - Common options:
     - `--file-types .py .md`
     - `--max-depth 2`
     - `--exclude "*.venv*" "*.git*"`
     - `--stats` to print exclusion counts
2. Build/update an index (indexer):
   - `python3 indexer.py build --manifest manifest.json --output index.db`
   - Incremental behavior:
     - unchanged files are skipped
     - changed files update only changed chunks
     - removed files/chunks are deleted
3. Search the index (indexer):
   - `python3 indexer.py search "query" --index index.db --top-k 5`
   - Returns chunk-level records (`path`, `rel_path`, `start_line`, `end_line`, `chunk_id`, `snippet`)
4. Retrieve prompt-ready context (retrieve):
   - `python3 retrieve.py "query" --index index.db --top-k 5`
   - Useful options:
     - `--max-context-chars 8000` hard output budget
     - `--max-per-file 3` diversity cap
     - `--mode lex|sem|hybrid` (`sem`/`hybrid` currently warn and fall back to `lex`)
5. One-shot pipeline (retrieve):
   - `python3 retrieve.py pipeline "query" --dirs <path1> <path2>`
   - Optional:
     - `--index /tmp/rag.db` to persist index
     - `--max-depth 2`
     - `--file-types .py .md`
   - This runs scan -> build -> retrieve in one command.

## When to use RAG

Use RAG when:
- the question depends on repository-specific behavior or contracts
- the answer needs exact symbols, paths, config keys, or line ranges
- the agent is uncertain and needs grounded evidence from code/docs

Do not use RAG when:
- the question is purely generic knowledge
- the user already provided the exact snippet needed
- the target file is already fully in active context and retrieval adds no value
