# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 20
- Checkpoint: 20.5
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Add a stdlib-only semantic search mode using TF-IDF vectors, enabling hybrid retrieval without external dependencies.

## Deliverables (current checkpoint)

- Add `.codex/skills/rag-index/vectorizer.py` for TF-IDF vector building and cosine similarity search
- Add `vectors` storage in index (`chunk_id` keyed sparse vectors)
- Add `indexer.py build --vectors` support to compute/store vectors
- Add semantic and hybrid retrieval modes (`retrieve.py --mode sem|hybrid`)

## Acceptance (current checkpoint)

- `--mode sem` returns results ranked by TF-IDF cosine similarity
- `--mode hybrid` returns ordering that differs from pure `lex`
- Evidence includes one query favoring `lex` (exact symbol) and one favoring `sem` (related concept)

## Work log (current session)

- 2026-02-06: Review PASS — 20.5 acceptance met (sem/hybrid behavior + adversarial probes); no next checkpoint in PLAN, marked current checkpoint DONE.
- 2026-02-06: Implemented 20.5 — added TF-IDF vectorizer + index `--vectors` build path; implemented semantic and hybrid retrieval modes with lex/sem/hybrid comparison evidence; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.4 acceptance met (docs/policy, install, tartu pipeline); auto-advanced to 20.5; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.4 — expanded rag-index SKILL.md usage docs + RAG usage policy; validated `skillctl install` and pipeline query against `/mnt/c/src/tartu`; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.3 acceptance met (format, diversity, budget, mode fallback) with adversarial probes; auto-advanced to 20.4; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.3 — retrieve.py now emits provenance headings + language fences, enforces max-per-file and max-context-chars, and supports mode fallback (`sem`/`hybrid` -> `lex`); moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.2 acceptance met with adversarial probes; auto-advanced to 20.3; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.
- 2026-02-06: Process improvement — work log bloat now routes to consolidation (not improvements); split _consolidation_trigger_reason; all 40 tests pass.

## Workflow state

(none)

## Evidence

- 2026-02-06 implementation + review evidence (checkpoint 20.5):
  - Vector build: `python3 .codex/skills/rag-index/indexer.py build --manifest /tmp/vibe-20-5/manifest.json --output /tmp/vibe-20-5/index.db --vectors` -> `4 vectors indexed, vocab 7`.
  - Lex-favoring query (exact symbol): `retrieve.py "parse_gitignore_file" --mode lex` returns results, while `--mode sem` returns `No results found.` (symbol token pruned by TF-IDF min_df).
  - Sem-favoring query (related/partial concept): `retrieve.py "session unicorn" --mode lex` returns `No results found.`, while `--mode sem` returns session-related results.
  - Hybrid differs from lex: for query `session token`, lex headers were `[a.py, b.py]` while hybrid returned `[a.py, b.py, c.py]` (different ranking/output set).
  - Adversarial probes: sem on non-vector index exits 2 with clean `ERROR:`; hybrid with `--max-per-file 0` exits 2 with clean `ERROR:` (no traceback).
  - Plan exhausted note: checkpoint `20.5` is the last PLAN entry; status set to `DONE`.

## Active issues

(None)

## Decisions

(No decisions)
