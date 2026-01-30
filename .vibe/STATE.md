# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 12
- Checkpoint: 12.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Update bootstrap and agentctl to use the resource resolver.

## Deliverables (current checkpoint)

- `bootstrap.py` uses resolver for skill installation
- `agentctl.py` uses resolver for prompt lookup
- `--global` and `--local` flags where disambiguation needed

## Acceptance (current checkpoint)

- Existing functionality preserved
- New resolution logic is transparent to users

## Work log (current session)

- 2026-01-29: Advanced to checkpoint 12.2.
- 2026-01-29: Reviewed 12.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.1 - Implemented resource resolver and verified with demo commands.
- 2026-01-29: Advanced to checkpoint 12.1.
- 2026-01-29: Reviewed 12.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.0 - Defined and documented the global vs repo-local resource model.
- 2026-01-29: Resolved ISSUE-005: Corrected the status of checkpoint 11.2 to DONE, as it was already reviewed and passed.
- 2026-01-29: Resolved ISSUE-004: Replaced Kimi with Kilo in all agent references and parity groupings.
- 2026-01-30: Resolved ISSUE-002 (bootstrap overwrite) and ISSUE-003 (prompt catalog canonicalization) with overwrite logging, catalog validation, resolver fix, and tests.
- 2026-01-29: Resolved ISSUE-002 (dispatcher mismatch) by preferring repo-local tools in vibe_next_and_print.
- 2026-01-29: Reviewed 11.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 11.2 - Added agentctl add-checkpoint command and stage insertion logic.
- 2026-01-29: Advanced to checkpoint 11.2.

## Evidence

(No evidence)

## Active issues

(No active issues)

## Decisions

(No decisions)
