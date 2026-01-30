# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 13
- Checkpoint: 13.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define a standard manifest format for skills.

## Deliverables (current checkpoint)

- `docs/skill_manifest.md` — schema documentation
- `SKILL.yaml` or `SKILL.json` manifest format
- Fields: name, version, description, agents, dependencies, entry points

## Acceptance (current checkpoint)

- Schema supports: multi-agent compatibility, version constraints, capability requirements
- Existing skills can be migrated to new format

## Work log (current session)

- 2026-01-30: Consolidated Stage 12A; advanced to Stage 13.0.
- 2026-01-30: Reviewed 12A.3 - PASS. Deliverables and acceptance criteria met.
- 2026-01-30: Added stage ordering unit + integration tests (12A.3).
- 2026-01-30: Advanced to checkpoint 12A.3.
- 2026-01-30: Implemented 12A.2 stage ID validation and duplicate detection.
- 2026-01-30: Advanced to checkpoint 12A.2.
- 2026-01-30: Implemented 12A.1 stage ordering logic updates.
- 2026-01-30: Advanced to checkpoint 12A.1.
- 2026-01-30: Reviewed 12A.0 - PASS. Deliverables and acceptance criteria met.
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

(No evidence)

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
