# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Build deterministic context bundles that can exceed model context size.

## Deliverables (current checkpoint)

- Add `tools/rlm/context_bundle.py`
- Add bundle output at `.vibe/rlm/bundles/<task_id>/`:
  - `manifest.json` (ordered files, hashes, sizes)
  - `chunks.jsonl` (chunk metadata + text)
  - `bundle.meta.json`

## Acceptance (current checkpoint)

- Same inputs produce identical manifests and chunk hashes.
- One-line edit only affects related chunks.

## Work log (current session)

- 2026-02-06: Review PASS — 21.1 acceptance met with demo + adversarial probes (semantic invalid schema and malformed JSON); auto-advanced to 21.2 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.1 — added `docs/rlm_task_schema.md`, `tools/rlm/validate_task.py`, and example tasks under `tasks/rlm/`; validated pass path on `tasks/rlm/example.json` and fail-fast diagnostics on malformed input; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.0 acceptance met (`rlm_overview` + `rlm_glossary` + decision table) with adversarial probes for required sections/terms; auto-advanced to 21.1 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.0 — added `docs/rlm_overview.md` and `docs/rlm_glossary.md`, including decision table (`RLM vs RAG vs standard loops`) and baseline/subcall + human-assisted provider explanations; moved status to IN_REVIEW.
- 2026-02-06: Consolidation — archived Stage 19A and Stage 20, pruned PLAN to Stage 21+, transitioned state pointer to 21.0/NOT_STARTED, set RUN_CONTEXT_CAPTURE.
- 2026-02-06: Implemented 20.5 — added TF-IDF vectorizer + index `--vectors` build path; implemented semantic and hybrid retrieval modes with lex/sem/hybrid comparison evidence; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.4 acceptance met (docs/policy, install, tartu pipeline); auto-advanced to 20.5; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.4 — expanded rag-index SKILL.md usage docs + RAG usage policy; validated `skillctl install` and pipeline query against `/mnt/c/src/tartu`; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.3 acceptance met (format, diversity, budget, mode fallback) with adversarial probes; auto-advanced to 20.4; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.3 — retrieve.py now emits provenance headings + language fences, enforces max-per-file and max-context-chars, and supports mode fallback (`sem`/`hybrid` -> `lex`); moved to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

(Checkpoint 21.2 — not yet started)

## Active issues

(None)

## Decisions

(No decisions)
