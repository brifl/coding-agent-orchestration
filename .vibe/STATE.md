# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.4
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Implement bounded iteration with constant-size metadata and explicit stop semantics.

## Deliverables (current checkpoint)

- `skills/rlm-tools/executor.py` with `run`, `step`, `resume`
- Run directory: `.vibe/rlm/runs/<task_id>/` with `state.json`, `trace.jsonl`, final artifacts

## Acceptance (current checkpoint)

- Baseline mode completes multi-iteration runs and stops only on `FINAL()` or limits.

## Work log (current session)

- 2026-02-07: Consolidation — transitioned pointer from completed Stage 21A (`21A.5/DONE`) to Stage 21 (`21.0/NOT_STARTED`), archived Stage 21A into HISTORY.md, refreshed objective/deliverables/acceptance to 21.0, and pruned work log.
- 2026-02-13: Implementation — verified 21.0 deliverables already exist from prior Stage 21 work. All acceptance criteria met. Reviewed and PASSED. Auto-advanced to 21.1.
- 2026-02-13: 21.1 — deliverables pre-exist, validation demo OK. Reviewed PASS, auto-advanced to 21.2.
- 2026-02-13: 21.2 — context_bundle.py pre-exists, determinism verified. PASS, advanced to 21.3.
- 2026-02-13: 21.3 — runtime.py pre-exists. Selftest passes (stdout capture, resume, finalize rejection). PASS, advanced to 21.4.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

(None yet — checkpoint 21.4 not started.)

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
