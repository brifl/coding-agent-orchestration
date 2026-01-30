# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 12A
- Checkpoint: 12A.0
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define a deterministic stage identifier scheme that supports insertions (e.g., `12A`, `12B`) and document ordering rules.

## Deliverables (current checkpoint)

- `docs/stage_ordering.md` — stage ID format + ordering rules + examples
- Stage ID grammar: `<int><optional alpha suffix>` (examples: `12`, `12A`, `12B`, `13`)
- Ordering definition: numeric first, then suffix (empty suffix sorts before A/B/…)

## Acceptance (current checkpoint)

- A human can add `Stage 12A` to PLAN.md and it will be treated as between 12 and 13
- Ordering rules are unambiguous and testable

## Work log (current session)

- 2026-01-30: Added stage ordering documentation for suffix-based stage IDs.
- 2026-01-29: Consolidated Stage 12, pruned logs, and advanced to 13.0.
- 2026-01-29: Reviewed 12.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.2 - Updated bootstrap.py and agentctl.py to use the resource resolver. Verified changes with demo commands.
- 2026-01-29: Advanced to checkpoint 12.2.
- 2026-01-29: Reviewed 12.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.1 - Implemented resource resolver and verified with demo commands.
- 2026-01-29: Advanced to checkpoint 12.1.
- 2026-01-29: Reviewed 12.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.0 - Defined and documented the global vs repo-local resource model.
- 2026-01-29: Resolved ISSUE-005: Corrected the status of checkpoint 11.2 to DONE, as it was already reviewed and passed.

## Evidence

- `cat docs/stage_ordering.md`

## Active issues

(No active issues)

## Decisions

(No decisions)
