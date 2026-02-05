---
name: rag-index
description: Experimental RAG indexing utilities (scanner + indexer).
version: "0.1.0"
---
# rag-index

## Purpose

Prototype utilities for building a repo index used by retrieval-augmented prompts.

## Scripts

- `scanner.py` — recursive directory scanner

## How to use

- Generate a file manifest:
  - Run: `python3 scanner.py <path1> <path2> --output manifest.json`
