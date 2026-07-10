# STATE

## Current focus

- Stage: 34
- Checkpoint: 34.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Make dispatcher status and next-step selection pure queries, with verification executed only when explicitly requested.

## Deliverables (current checkpoint)

- Remove implicit PLAN demo-command execution from routing
- Run each explicitly requested gate at most once
- Keep proportional verification in review guidance rather than dispatcher side effects
- Add subprocess-spy and gate invocation-count regression coverage

## Acceptance (current checkpoint)

- `status` and normal `next` perform no subprocess work.
- Dispatcher owns no PLAN smoke timeout or implicit demo execution.
- `next --run-gates` executes every configured gate once.
- Long legitimate demos do not alter role selection merely because they exceed 30 seconds.

## Current truth

- Stage 33 is archived: consumers now execute and reinstall one provenance-visible managed runtime without local framework patches.
- Current `IN_REVIEW` routing executes PLAN demo commands through `_smoke_test_gate` and imposes a 30-second timeout.
- The Stage 33 reviews repeatedly reproduced the defect: a passing 48-second suite was misrouted to issues triage.
- Explicit `next --run-gates` currently calls `run_gates` twice on the successful path.

## Workflow state

- [ ] STAGE_DESIGNED
- [ ] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE
- [x] RUN_CONTEXT_CAPTURE

## Work log (current session)

- 2026-07-10: Consolidated completed Stage 33 into HISTORY and advanced to checkpoint 34.0.
- 2026-07-10: Completed the Stage 33 retrospective with four actionable packaging and routing lessons.

## Evidence

- Stage 33 outcome and commit span are archived in `.vibe/HISTORY.md`.
- 34.0 trigger: passing bootstrap/skill verification took 48 seconds but implicit review smoke timed out at 30 seconds and changed the recommended role.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
