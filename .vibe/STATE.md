# STATE

## Current focus

- Stage: 34
- Checkpoint: 34.1
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Reduce the normal lifecycle to design when needed, implementation, review, and one bounded stage rollover.

## Deliverables (current checkpoint)

- Remove automatic retrospective, maintenance, context-capture, and process-improvement routing
- Remove obsolete lifecycle flags from templates, prompts, parser logic, and tests
- Keep one bounded stage-rollover path that designs only when the next checkpoint is not executable
- Represent maintenance as explicit PLAN work or explicitly invoked specialized workflows

## Acceptance (current checkpoint)

- Fresh install reaches implementation immediately after its initial design.
- A stage transition consumes at most two loops before implementation.
- Routing depends on no wall-clock age, stage number, line count, or lifecycle booleans.
- Maintenance scans cannot enter normal product review implicitly.

## Current truth

- Stage 33 is archived: consumers now execute and reinstall one provenance-visible managed runtime without local framework patches.
- Checkpoint 34.0 made role queries subprocess-free and explicit gates single-run.
- The Stage 34 transition still consumed consolidation, retrospective, design, modulo maintenance, and context bookkeeping before implementation.
- Maintenance prompt selection has no automatic flag-closing contract and can loop or route its scan into normal review.
- Context, work-log, stage-number, and lifecycle-flag heuristics remain in `_decide_role` and its context gatherer.

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
- 2026-07-10: Review PASS; routing purity, one-run gates, and proportional verification acceptance all pass with the full workflow suite green.
- 2026-07-10: Advanced to 34.1 to delete the transition ceremony directly observed while entering Stage 34.

## Evidence

- Checkpoint 34.0: commits `a05dfff` and `c6efdc4`; full workflow suite `289 passed`.
- 34.1 trigger evidence: the Stage 34 transition required four non-building flag updates and selected a modulo test prompt that could not close its own flag.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
