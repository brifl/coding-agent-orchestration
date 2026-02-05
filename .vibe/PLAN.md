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
  Package the RAG capability as a reusable skill.
* **Deliverables:**
* `.codex/skills/rag-index/SKILL.md` — skill manifest
  * `.codex/skills/rag-index/retrieve.py` — retrieval interface for agents
  * Integration: agents can call retriever to augment prompts
* **Acceptance:**
  * Skill installs via skillctl
  * Retriever returns context snippets suitable for prompt injection
* **Demo commands:**
* `python tools/skillctl.py install rag-index --global`
  * `python .codex/skills/rag-index/retrieve.py "how does auth work" --top-k 5`
* **Evidence:**
  * Retrieved context snippets

---

## Stage 20 — Multi-Directory RAG Skill

Codex often fails here unless you pin down **chunking, indexing, and retrieval contract**.

### 20.0 — Directory scanner (more detail)

**Add deliverables**

* `scanner.py` must output a **stable manifest schema**:

  * `path`, `rel_path`, `sha256` (or content hash), `size`, `mtime`, `language`, `mime`, `ignored_reason?`
* Gitignore handling:

  * Must respect `.gitignore`, `.ignore`, and explicit excludes
  * Must allow `--no-gitignore` override

**Acceptance tests**

* Scanning same tree twice yields identical manifest ordering + same hashes (unless files changed)
* Exclusions are reported (count by reason)

---

### 20.1 — Index builder (more detail)

Treat this as two parallel indexes:

1. **Lexical index** (BM25-ish) for precision and cheap retrieval
2. **Vector index** for semantic recall

**Chunking contract**

* Deterministic chunking:

  * Markdown: split by headings then cap size
  * Code: split by symbols (functions/classes) where possible, else by lines
* Store:

  * `chunk_id`, `doc_id`, `start_line`, `end_line`, `text`, `token_estimate`, `hash`

**Incremental indexing**

* Skip unchanged chunks via `hash`
* Remove chunks for deleted files

**Storage**

* SQLite is usually easiest for portability + incremental updates:

  * tables: `docs`, `chunks`, `lex_terms` (or FTS5), `vectors` (if stored), `meta`

**Acceptance**

* Re-index after a one-line change only updates affected chunks
* Search returns:

  * `score`, `path`, `line range`, `snippet`, `chunk_id`

---

### 20.2 — Retriever and skill packaging (more detail)

**Retriever interface contract (CLI + library)**

* Input: `query`, optional `paths scope`, `top_k`, `mode={lex|sem|hybrid}`
* Output: **prompt-ready** snippets:

  * each snippet: header line with provenance + fenced content
  * enforce max total chars returned (e.g. `--max-context-chars`)

**Hybrid ranking**

* Combine normalized lexical + semantic scores
* Diversity: avoid returning 5 chunks from same file unless asked

**When-to-use guidance (critical for agent behavior)**

* Add a short policy blurb for agents:

  * Use RAG when:

    * question references repo-specific behavior
    * answer requires exact names/paths/config keys
    * agent is unsure and needs grounding
  * Don’t use RAG when:

    * purely generic knowledge
    * user already provided the relevant snippet

**Evidence requirement**

* Include example query showing lexical beats semantic (exact symbol) and vice versa.

---
