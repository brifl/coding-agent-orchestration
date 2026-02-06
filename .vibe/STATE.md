# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define what RLM means in this system, when it should be used, and how it differs from standard prompts and RAG.

## Deliverables (current checkpoint)

- Add `docs/rlm_overview.md` (RLM concepts, lifecycle, examples)
- Add `docs/rlm_glossary.md` (terminology: root iteration, bundle, subcall, FINAL, etc.)
- Add a decision table for when to use RLM vs RAG vs standard Vibe loops

## Acceptance (current checkpoint)

- Documentation clearly explains baseline vs subcall mode and human-assisted providers

## Work log (current session)

- 2026-02-06: Consolidation — archived Stage 19A and Stage 20, pruned PLAN to Stage 21+, transitioned state pointer to 21.0/NOT_STARTED, set RUN_CONTEXT_CAPTURE.
- 2026-02-06: Implemented 20.5 — added TF-IDF vectorizer + index `--vectors` build path; implemented semantic and hybrid retrieval modes with lex/sem/hybrid comparison evidence; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.4 acceptance met (docs/policy, install, tartu pipeline); auto-advanced to 20.5; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.4 — expanded rag-index SKILL.md usage docs + RAG usage policy; validated `skillctl install` and pipeline query against `/mnt/c/src/tartu`; moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.3 acceptance met (format, diversity, budget, mode fallback) with adversarial probes; auto-advanced to 20.4; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.3 — retrieve.py now emits provenance headings + language fences, enforces max-per-file and max-context-chars, and supports mode fallback (`sem`/`hybrid` -> `lex`); moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.2 acceptance met with adversarial probes; auto-advanced to 20.3; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

(Checkpoint 21.0 — not yet started)

## Active issues

(None)

## Decisions

(No decisions)
