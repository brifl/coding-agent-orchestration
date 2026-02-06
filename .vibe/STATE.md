# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 20
- Checkpoint: 20.4
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Ship the complete skill with agent-facing documentation and a one-command workflow.

## Deliverables (current checkpoint)

- Update `SKILL.md` with full usage docs for scanner, indexer, and retriever
- Add `## When to use RAG` policy section in `SKILL.md` (use vs don't-use guidance)
- Add/verify one-shot `retrieve.py pipeline` workflow (`scan -> build -> search`)
- Verify pipeline against `c:\\src\\tartu` as real-world target

## Acceptance (current checkpoint)

- `skillctl install rag-index --global` succeeds
- `retrieve.py pipeline "control plane" --dirs c:\\src\\tartu --max-depth 2` returns relevant results
- `SKILL.md` has complete, accurate usage instructions for all scripts
- When-to-use policy is present and actionable

## Work log (current session)

- 2026-02-06: Review PASS — 20.3 acceptance met (format, diversity, budget, mode fallback) with adversarial probes; auto-advanced to 20.4; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.3 — retrieve.py now emits provenance headings + language fences, enforces max-per-file and max-context-chars, and supports mode fallback (`sem`/`hybrid` -> `lex`); moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.2 acceptance met with adversarial probes; auto-advanced to 20.3; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.
- 2026-02-06: Consolidation — pruned work log from 32 to 10 entries; archived older entries to HISTORY.md.
- 2026-02-06: Process improvement — work log bloat now routes to consolidation (not improvements); split _consolidation_trigger_reason; all 40 tests pass.
- 2026-02-06: Process improvement — added concrete work-log cap (10 entries) to consolidation prompt; added WORK_LOG_CONSOLIDATION_CAP constant and validation warning; all 25 tests pass.
- 2026-02-05: Review PASS — 20.1 acceptance met; auto-advanced to 20.2; status set to NOT_STARTED.
- 2026-02-05: Implemented 20.1 — chunker.py with Python/Markdown/Generic/Fallback strategies; all 5 acceptance criteria pass.

## Workflow state

(none)

## Evidence

(Checkpoint 20.4 — not yet started)

## Active issues

(None)

## Decisions

(No decisions)
