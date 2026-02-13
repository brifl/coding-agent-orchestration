# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 22
- Checkpoint: 22.0
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Add `STAGE_DESIGNED` and `MAINTENANCE_CYCLE_DONE` workflow flags and dispatcher logic to route to design/maintenance before implementation.

## Deliverables (current checkpoint)

- `_get_stage_number()` helper in `tools/agentctl.py`
- `_stage_design_trigger_reason()` trigger function
- `_maintenance_cycle_trigger_reason()` trigger function
- Updated `_recommend_next()` with new trigger checks and extended return type
- New workflow flags in `.vibe/STATE.md`

## Acceptance (current checkpoint)

- `agentctl next` returns `design` when `STAGE_DESIGNED` is unset.
- `agentctl next` returns maintenance prompt when stage%3 triggers and `MAINTENANCE_CYCLE_DONE` is unset.
- `agentctl next` returns `implement` when both flags are set.

## Work log (current session)

- 2026-02-13: Consolidated Stage 21 (DONE at 21.11). Transitioned to Stage 22 (22.0/NOT_STARTED). Added Stage 22 checkpoints to PLAN.md.
- 2026-02-13: 22.0 implementation — added `_get_stage_number()`, `_stage_design_trigger_reason()`, `_maintenance_cycle_trigger_reason()` to agentctl.py. Updated `_recommend_next()` return type to include prompt_id_override. All 3 acceptance criteria verified.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [ ] STAGE_DESIGNED
- [ ] MAINTENANCE_CYCLE_DONE

## Evidence

- `agentctl next` returns `design` when STAGE_DESIGNED unset → confirmed.
- `agentctl next` returns `implement` + `prompt.test_gap_analysis` when stage%3==1 and MAINTENANCE_CYCLE_DONE unset → confirmed.
- `agentctl next` returns `implement` + default prompt when both flags set → confirmed.
- `agentctl validate --strict` → ok: True.

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
