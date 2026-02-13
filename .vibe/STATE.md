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
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define what RLM means in this system, when it should be used, and how it differs from standard prompts and RAG.

## Deliverables (current checkpoint)

- `docs/rlm_overview.md` — RLM concepts, lifecycle, and examples
- `docs/rlm_glossary.md` — terminology (root iteration, bundle, subcall, FINAL, etc.)
- Decision table: when to use RLM vs RAG vs standard Vibe loops

## Acceptance (current checkpoint)

- Documentation explains baseline vs subcall mode and human-assisted providers.
- Decision table included and unambiguous.

## Work log (current session)

- 2026-02-07: Consolidation — transitioned pointer from completed Stage 21A (`21A.5/DONE`) to Stage 21 (`21.0/NOT_STARTED`), archived Stage 21A into HISTORY.md, refreshed objective/deliverables/acceptance to 21.0, and pruned work log.
- 2026-02-13: Implementation — verified 21.0 deliverables already exist from prior Stage 21 work: `docs/rlm_overview.md` (71 lines, covers concepts/lifecycle/modes/decision table), `docs/rlm_glossary.md` (52 lines, covers all key terms). All acceptance criteria met. Set status to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- `docs/rlm_overview.md` exists (71 lines): covers RLM concepts, lifecycle, baseline vs subcall mode, human-assisted providers, and decision table (Standard Loop vs RAG vs RLM).
- `docs/rlm_glossary.md` exists (52 lines): covers all key terms (root iteration, bundle, subcall, FINAL, context bundle, manifest, chunk, runtime sandbox, state snapshot, trace, provider policy, budget, cache mode, replay).
- Decision table in `rlm_overview.md` lines 60-64: three-column comparison with selection criteria, core mechanism, state profile, and typical output.
- `cat docs/rlm_overview.md` — OK
- `cat docs/rlm_glossary.md` — OK

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
