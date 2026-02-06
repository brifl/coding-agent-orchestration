# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 19A — Multi-Directory RAG Skill

**Stage objective:**
Create a reusable skill that scans directories, builds a searchable index, and supports retrieval-augmented prompting.

### 19A.0 — Directory scanner

* **Objective:**
  Build a scanner that indexes multiple directories.
* **Deliverables:**
  * `.codex/skills/rag-index/scanner.py` — recursive directory scanner
  * Configurable: include/exclude patterns, file types, depth
  * Output: file manifest with metadata (path, size, mtime, type)
* **Acceptance:**
  * Scans multiple directories in one pass
  * Respects gitignore and custom exclusions
* **Demo commands:**
  * `python .codex/skills/rag-index/scanner.py /path/to/code --output manifest.json`
* **Evidence:**
  * Manifest output for sample directory
---

### 19A.1 — Index builder

* **Objective:**
  Build a searchable index from scanned files.
* **Deliverables:**
  * `.codex/skills/rag-index/indexer.py` — builds embeddings/keyword index
  * Supports: full-text search, semantic search (with embeddings)
  * Storage: local SQLite or JSON for portability
* **Acceptance:**
  * Index is persistent and incremental (only re-index changed files)
  * Search returns ranked results
* **Demo commands:**
  * `python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db`
  * `python .codex/skills/rag-index/indexer.py search "authentication" --index index.db`
* **Evidence:**
  * Search results for sample query
---

### 19A.2 — RAG retriever and skill packaging

* **Objective:**
  Close out the Stage 19A prototype with a working end-to-end pipeline: scan → index → retrieve.
* **Deliverables:**
  * `.codex/skills/rag-index/retrieve.py` — retrieval CLI and library interface
  * Update `.codex/skills/rag-index/SKILL.md` — add indexer + retriever to manifest
* **Design:**
  * `retrieve.py` wraps the indexer's `search_index()` and formats results as prompt-ready snippets
  * Output format: one snippet per result, each with a provenance header (`# file: rel_path`) + fenced content block
  * `--top-k` (default 5) and `--max-context-chars` (default 8000) to budget context window usage
  * Library API: `retrieve(query, index_path, top_k, max_chars) -> str` returns formatted prompt context
  * CLI: `python retrieve.py "query" --index index.db --top-k 5`
  * Also supports a one-shot `retrieve.py pipeline "query" --dirs dir1 dir2` that runs scan → build → search in one call
* **Acceptance:**
  * `python tools/skillctl.py install rag-index --global` succeeds (manifest validates)
  * `retrieve.py` returns formatted snippets with provenance headers
  * `retrieve.py pipeline` produces results from raw directories without pre-built index
* **Demo commands:**
  * `python tools/skillctl.py install rag-index --global`
  * `python .codex/skills/rag-index/retrieve.py "scan directories" --index index.db --top-k 3`
  * `python .codex/skills/rag-index/retrieve.py pipeline "scan directories" --dirs .codex/skills/rag-index`
* **Evidence:**
  * Formatted context snippets showing provenance headers
  * skillctl install output

---

## Stage 20 — RAG Pipeline Hardening

**Stage objective:**
Upgrade the Stage 19A prototype into a production-quality RAG pipeline with chunk-level indexing, stable contracts, and hybrid retrieval.

**Why this matters:**
The 19A prototype indexes whole files into FTS5. This works for small codebases but breaks down because: (1) search returns entire files as context, wasting token budget; (2) no line-level provenance for agents to cite; (3) no semantic fallback when exact keywords don't appear. Stage 20 fixes all three by introducing **chunking** as the core abstraction.

**Key design constraint:** Zero required external dependencies. The entire pipeline runs on Python stdlib + SQLite. Semantic search uses a TF-IDF baseline (stdlib-only); external embedding APIs are optional and pluggable.

**Architecture after Stage 20:**

```
scanner.py  →  manifest.json  →  chunker.py  →  indexer.py  →  index.db  →  retrieve.py  →  prompt context
  (files)       (file list)       (chunks)      (FTS + vec)    (SQLite)     (formatted)     (to agent)
```

---

### 20.0 — Scanner hardening

* **Objective:**
  Harden the manifest schema for determinism, add content hashing, and report exclusion stats.
* **Deliverables:**
  * Upgrade `scanner.py` manifest entries to include:
    * `content_hash` — SHA-256 of file content (enables change detection without re-reading)
    * `language` — inferred from extension (e.g., `.py` → `python`, `.md` → `markdown`). Use a built-in mapping dict; unknown → `null`
  * Stable manifest ordering: entries sorted by `(root, rel_path)` lexicographically
  * `--stats` flag: print exclusion summary to stderr (e.g., `Excluded: 12 by gitignore, 3 by --exclude, 5 by --file-types`)
* **Design notes:**
  * Language map is a simple `dict[str, str]` covering ~20 common extensions. Not exhaustive; `null` is fine for unknowns.
  * `content_hash` is computed during scan since we `stat()` each file anyway. Cost: one SHA-256 per file (fast for typical repo sizes).
  * Backward-compatible: existing manifest consumers ignore extra fields. `content_hash` replaces the redundant re-hashing in `indexer.py`.
* **Acceptance:**
  * Scanning same tree twice yields byte-identical manifest JSON (determinism)
  * `content_hash` present on every entry; verified by re-hashing file content
  * `--stats` prints exclusion breakdown by reason
* **Demo commands:**
  * `python .codex/skills/rag-index/scanner.py . --max-depth 1 --output manifest.json --stats`
  * `python -c "import json; m=json.load(open('manifest.json')); print(m[0].keys())"` (shows new fields)
  * `python .codex/skills/rag-index/scanner.py . --max-depth 1 --output m2.json && diff manifest.json m2.json` (determinism)
* **Evidence:**
  * Manifest entry showing all fields including `content_hash` and `language`
  * Determinism diff (empty)
  * Stats output

---

### 20.1 — Chunking engine

* **Objective:**
  Build a deterministic chunking library that splits files into indexed units suitable for precise retrieval.
* **Deliverables:**
  * `.codex/skills/rag-index/chunker.py` — chunking engine with strategy dispatch
  * Strategies:
    * **Python** (`language == "python"`): Parse with `ast` module. Each top-level function/class/assignment block becomes a chunk. Nested definitions stay with their parent. If a function exceeds `max_chunk_tokens`, split by method for classes or by logical sections for long functions.
    * **Markdown** (`language == "markdown"`): Split by heading hierarchy (# → ## → ###). Each section becomes a chunk. Cap at `max_chunk_tokens`; if exceeded, split at paragraph boundaries.
    * **Generic code** (all other languages): Split at blank-line-separated blocks. Merge small adjacent blocks to avoid tiny chunks. Cap at `max_chunk_tokens`.
    * **Fallback**: Fixed-size line windows with configurable overlap (default: 100 lines, 20 line overlap).
  * Chunk schema (returned as dicts):
    * `chunk_id`: `"{content_hash}:{start_line}-{end_line}"` (stable, deterministic)
    * `doc_path`: source file path
    * `start_line`: 1-indexed inclusive
    * `end_line`: 1-indexed inclusive
    * `text`: chunk content
    * `token_estimate`: `len(text) // 4` (conservative heuristic, no tokenizer dependency)
    * `hash`: SHA-256 of `text` (for incremental skip)
    * `language`: inherited from manifest
  * Library API: `chunk_file(path, language, max_chunk_tokens=500) -> list[dict]`
  * CLI: `python chunker.py <file> [--language python] [--max-tokens 500]` (prints JSON)
* **Design notes:**
  * `max_chunk_tokens=500` default balances retrieval precision vs. context. At `~4 chars/token`, this is ~2000 chars — enough for a typical function.
  * Python AST strategy falls back to generic-code if `ast.parse()` fails (syntax errors, Python 2, etc.).
  * Chunk IDs are content-addressed: same file content → same chunk IDs. This is critical for incremental indexing in 20.2.
  * No external dependencies. `ast` is stdlib; markdown parsing is regex/line-based.
* **Acceptance:**
  * Chunking the same file twice produces identical output (determinism)
  * A Python file with 3 functions produces 3+ chunks (one per function + possible module docstring)
  * A Markdown file with 4 headings produces 4 chunks
  * No chunk exceeds `max_chunk_tokens * 5` characters (hard cap with forced split)
  * Chunks have non-overlapping, contiguous line ranges that cover the entire file
* **Demo commands:**
  * `python .codex/skills/rag-index/chunker.py .codex/skills/rag-index/scanner.py --language python`
  * `python .codex/skills/rag-index/chunker.py README.md --language markdown`
  * `python -c "import json; chunks=json.loads(open('/dev/stdin').read()); print(f'{len(chunks)} chunks, lines {chunks[0][\"start_line\"]}-{chunks[-1][\"end_line\"]}')"` (piped from above)
* **Evidence:**
  * Chunk listing for scanner.py showing function-level splits
  * Chunk listing for a markdown file showing heading-level splits

---

### 20.2 — Chunk-aware index builder

* **Objective:**
  Upgrade the indexer to work at chunk granularity with chunk-level incremental updates.
* **Deliverables:**
  * Upgrade `indexer.py` schema (bump `_SCHEMA_VERSION` to 2):
    * New `chunks` table: `chunk_id TEXT PK, doc_id INT FK, start_line INT, end_line INT, token_estimate INT, chunk_hash TEXT`
    * FTS5 now indexes chunk text (not whole-file text): `chunks_fts(chunk_id, chunk_text)`
    * Keep `docs` table for file-level metadata
  * Upgrade `build` subcommand:
    * For each manifest file: read → chunk (via `chunker.py`) → index chunks
    * Incremental at chunk level: compare `chunk_hash` to skip unchanged chunks
    * Remove chunks for files no longer in manifest
    * Remove stale chunks when a file changes (old chunks deleted, new chunks inserted)
  * Upgrade `search` subcommand:
    * Returns: `score`, `path`, `rel_path`, `start_line`, `end_line`, `snippet`, `chunk_id`
    * Snippet is extracted from chunk text (not whole file)
  * Migration: if existing v1 DB detected, drop and rebuild (print warning)
* **Design notes:**
  * The indexer imports `chunker.chunk_file()` as a library call — no subprocess overhead.
  * FTS5 `snippet()` now works on chunk-sized text, producing much more relevant snippets than whole-file matching.
  * `chunk_hash` is computed by the chunker, not re-computed by the indexer. The indexer trusts it.
  * Two-phase build: (1) process manifest, compute chunks, diff against DB; (2) batch insert/delete in a single transaction.
* **Acceptance:**
  * Changing one line in a file only re-indexes affected chunks (verify via stats output)
  * Deleting a file removes all its chunks
  * Search results include `start_line` and `end_line` (not just file path)
  * Re-indexing unchanged files reports 0 indexed
* **Demo commands:**
  * `python .codex/skills/rag-index/scanner.py . --max-depth 1 --file-types .py --output manifest.json`
  * `python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db`
  * `python .codex/skills/rag-index/indexer.py search "parse gitignore" --index index.db --top-k 3`
  * `python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db` (re-run, expect 0 indexed)
* **Evidence:**
  * Build stats showing chunk counts
  * Search result with line range
  * Incremental re-build showing 0 indexed

---

### 20.3 — Retriever upgrade with prompt formatting and diversity

* **Objective:**
  Upgrade retrieve.py to produce high-quality, budget-aware, diverse context for agent prompts.
* **Deliverables:**
  * Upgrade `retrieve.py` to consume chunk-level search results
  * **Prompt-ready output format:**
    ```
    <!-- RAG context for: "{query}" -->

    \### .codex/skills/rag-index/scanner.py:20-31
    ```python
    def _parse_gitignore(gitignore_path: Path) -> list[str]:
        ...
    ```

    \### .codex/skills/rag-index/scanner.py:74-95

    ```python
    def scan_directories(...):
        ...
    ```
    ```
    Each snippet: heading with `rel_path:start-end`, fenced code block with language tag.
  * `--max-context-chars` (default 8000): total character budget. Stop adding snippets once budget exceeded.
  * `--max-per-file` (default 3): diversity cap — at most N chunks from the same file.
  * `--mode {lex}` (only lexical for now; `sem` and `hybrid` are stubs that warn and fall back to `lex`)
  * Library API: `retrieve(query, index_path, ...) -> str` returns the formatted block above
* **Design notes:**
  * The prompt format uses markdown headings + fenced code so agents and LLMs can parse provenance trivially.
  * Language tag on fenced blocks comes from the `language` field in docs table (populated by scanner's language detection from 20.0).
  * Diversity: after BM25 ranking, greedily select top results while respecting per-file cap. This prevents one large file from dominating all results.
  * `--max-context-chars` is a hard stop, not a target. Better to return 3 great snippets than 10 mediocre ones.
* **Acceptance:**
  * Output includes provenance headers with file path + line range
  * Output uses fenced code blocks with correct language tags
  * With `--max-per-file 2`, no file appears more than twice in results
  * Total output respects `--max-context-chars` budget
* **Demo commands:**
  * `python .codex/skills/rag-index/retrieve.py "parse gitignore" --index index.db --top-k 5 --max-per-file 2`
  * `python .codex/skills/rag-index/retrieve.py "parse gitignore" --index index.db --max-context-chars 2000`
* **Evidence:**
  * Formatted prompt context block showing provenance headers + fenced code
  * Diversity enforcement (max-per-file)

---

### 20.4 — Agent integration and usage policy

* **Objective:**
  Ship the complete skill with agent-facing documentation and a one-command workflow.
* **Deliverables:**
  * Update `SKILL.md` with full usage docs for all three tools (scanner, indexer, retriever)
  * Add `## When to use RAG` policy section in SKILL.md:
    * **Use RAG when:** question references repo-specific behavior; answer requires exact names/paths/config; agent is unsure and needs grounding
    * **Don't use RAG when:** purely generic knowledge; user already provided the relevant snippet; question is about a file already in context
  * `retrieve.py pipeline` one-shot command: scan → build → search in one invocation
    * `python retrieve.py pipeline "query" --dirs dir1 dir2 [--index /tmp/rag.db]`
    * Useful for ad-hoc queries without pre-built index
  * Verify full pipeline against `c:\src\tartu` as a real-world test target
* **Acceptance:**
  * `skillctl install rag-index --global` succeeds
  * `retrieve.py pipeline "control plane" --dirs c:\src\tartu --max-depth 2` returns relevant results from the tartu codebase
  * SKILL.md has complete, accurate usage instructions for all scripts
  * When-to-use policy is present and actionable
* **Demo commands:**
  * `python tools/skillctl.py install rag-index --global`
  * `python .codex/skills/rag-index/retrieve.py pipeline "how does the engine work" --dirs c:\src\tartu --top-k 5`
* **Evidence:**
  * Full pipeline output against tartu repo
  * skillctl install output
  * SKILL.md screenshot or excerpt

---

### 20.5 — TF-IDF semantic search (stretch)

> **Note:** This checkpoint is optional. Ship it if 20.0–20.4 land cleanly; skip or defer if time-boxed.

* **Objective:**
  Add a stdlib-only semantic search mode using TF-IDF vectors, enabling hybrid retrieval without external dependencies.
* **Deliverables:**
  * `.codex/skills/rag-index/vectorizer.py` — TF-IDF vector builder and cosine similarity search
  * New `vectors` table in index.db: `chunk_id TEXT PK, vector BLOB` (numpy-free: store as JSON list of floats or packed struct)
  * `indexer.py build --vectors` flag to compute and store TF-IDF vectors during indexing
  * `retrieve.py --mode sem` uses vector search; `--mode hybrid` combines BM25 + TF-IDF scores
* **Design notes:**
  * TF-IDF is simple but effective for code search: exact symbol names and identifiers get high weight.
  * Vocabulary: top 10K terms by document frequency. Prune rare terms (< 2 docs) and stop words.
  * Vectors stored as sparse dicts `{term_idx: weight}` serialized as JSON. Cosine similarity on sparse vectors is fast enough for <100K chunks.
  * Hybrid scoring: `score = alpha * norm_bm25 + (1-alpha) * norm_tfidf` with `alpha=0.6` default.
  * Normalize: BM25 scores to [0,1] via min-max over result set; TF-IDF cosine is already [0,1].
  * Pluggable: if someone wants real embeddings later, they replace `vectorizer.py` with an API-backed version. Same interface.
* **Acceptance:**
  * `--mode sem` returns results ranked by TF-IDF cosine similarity
  * `--mode hybrid` returns results that differ from pure `lex` ordering (proving combination works)
  * Evidence: one query where `lex` finds the right result and `sem` doesn't (exact symbol name), and one where `sem` finds it and `lex` doesn't (synonym/related concept)
* **Demo commands:**
  * `python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db --vectors`
  * `python .codex/skills/rag-index/retrieve.py "authentication" --index index.db --mode lex --top-k 3`
  * `python .codex/skills/rag-index/retrieve.py "authentication" --index index.db --mode sem --top-k 3`
  * `python .codex/skills/rag-index/retrieve.py "authentication" --index index.db --mode hybrid --top-k 3`
* **Evidence:**
  * Side-by-side comparison of lex vs sem vs hybrid for the same query

---
