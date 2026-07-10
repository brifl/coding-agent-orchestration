# STATE

## Current focus

- Stage: 34
- Checkpoint: 34.0
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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
- `status` and normal `next` no longer execute subprocesses or PLAN demo commands.
- Review routing is based on checkpoint state; implementation/review prompts select proportional verification explicitly.
- `next --run-gates` stores and reports one gate execution result instead of invoking successful gates twice.

## Workflow state

- [x] STAGE_DESIGNED
- [x] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE
- [ ] RUN_CONTEXT_CAPTURE

## Work log (current session)

- 2026-07-10: Consolidated completed Stage 33 into HISTORY and advanced to checkpoint 34.0.
- 2026-07-10: Completed the Stage 33 retrospective with four actionable packaging and routing lessons.
- 2026-07-10: Confirmed Stage 34 checkpoints remain executable against current dispatcher evidence; no roadmap changes required.
- 2026-07-10: Folded the modulo-selected maintenance test gaps into 34.0 and reused the freshly updated CONTEXT instead of duplicating non-building loops.
- 2026-07-10: Removed implicit review smoke execution, deduplicated explicit gates, and aligned tests/prompts/docs with proportional verification.

## Evidence

- Commit `a05dfff`: subprocess-free routing, one-run explicit gates, proportional verification guidance, and stale smoke-surface removal.
- `128 passed` focused routing/agentctl/feedback/prompt suites; full workflow suite `289 passed`; Ruff and strict validation passed.
- Subprocess spy covers both status and normal next; invocation-count fixture proves successful `next --run-gates` calls `run_gates` once.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
