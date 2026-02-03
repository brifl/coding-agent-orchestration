# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

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