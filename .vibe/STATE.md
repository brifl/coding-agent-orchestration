# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define a strict invocation format for RLM runs and validate it before execution.

## Deliverables (current checkpoint)

- `docs/rlm_task_schema.md`
- `tools/rlm/validate_task.py`
- Example tasks in `tasks/rlm/`

## Acceptance (current checkpoint)

- Invalid tasks fail fast with file/line diagnostics.

## Work log (current session)

- 2026-02-07: Consolidation — transitioned pointer from completed Stage 21A (`21A.5/DONE`) to Stage 21 (`21.0/NOT_STARTED`), archived Stage 21A into HISTORY.md, refreshed objective/deliverables/acceptance to 21.0, and pruned work log.
- 2026-02-13: Implementation — verified 21.0 deliverables already exist from prior Stage 21 work. All acceptance criteria met. Reviewed and PASSED. Auto-advanced to 21.1.
- 2026-02-13: Implementation 21.1 — verified deliverables pre-exist: `docs/rlm_task_schema.md`, `tools/rlm/validate_task.py`, `tasks/rlm/` examples. Demo: valid task passes, malformed task fails with file/line diagnostics. Set IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- `docs/rlm_task_schema.md` exists (79 lines): documents all required fields, field details, and usage.
- `tools/rlm/validate_task.py` exists: validates tasks against schema.
- `tasks/rlm/example.json` — VALID (passes validation).
- `tasks/rlm/malformed_missing_query.json` — INVALID with 3 diagnostics including file/line info.
- Demo: `python3 tools/rlm/validate_task.py tasks/rlm/example.json` -> `VALID`
- Demo: `python3 tools/rlm/validate_task.py tasks/rlm/malformed_missing_query.json` -> `INVALID` with diagnostics.

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
