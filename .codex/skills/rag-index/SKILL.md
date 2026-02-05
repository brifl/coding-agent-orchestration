---
name: rag-index
description: Experimental RAG indexing utilities (scanner + indexer + retriever).
version: "0.1.0"
---
# rag-index

## Purpose

Prototype utilities for building a repo index used by retrieval-augmented prompts.

## Scripts

- `scanner.py` — recursive directory scanner
- `indexer.py` — build/search SQLite FTS index from a manifest
- `retrieve.py` — format prompt-ready snippets; includes a pipeline mode

## How to use

- Generate a file manifest: `python3 scanner.py <path1> <path2> --output manifest.json`
- Build or update the index: `python3 indexer.py build --manifest manifest.json --output index.db`
- Search the index: `python3 indexer.py search "query" --index index.db --top-k 5`
- Retrieve formatted context: `python3 retrieve.py "query" --index index.db --top-k 5`
- One-shot pipeline (scan -> build -> retrieve): `python3 retrieve.py pipeline "query" --dirs <path1> <path2>`
