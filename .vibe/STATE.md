# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 5
- Checkpoint: 5.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define how new skills will be added without breaking existing workflows.

## Deliverables (current checkpoint)

- Policy doc covering versioning, compatibility, deprecation rules
- "No breaking changes" rule for base skills

## Acceptance (current checkpoint)

- [ ] Clear go/no-go criteria for new skills
- [ ] Enforced via review checklist

## Work log (current session)

- 2026-01-28: Fixed stage drift (was Stage 2, should be Stage 5 for checkpoint 5.0).
- 2026-01-28: Archived completed stages 2, 3, 4 to HISTORY.md.
- 2026-01-28: Cleared stale evidence from previous checkpoints.
- 2026-01-28: Updated capability matrices to reflect Claude/Gemini full capabilities.
- 2026-01-28: Improved prompt.consolidation with stage boundary handling.
- 2026-01-28: Improved prompt.process_improvements with diagnostic checklist.
- 2026-01-28: Added stage drift detection to agentctl.py validate command.
- 2026-01-28: Added stage transition detection to agentctl.py next command.

## Evidence

(None yet - checkpoint not started)

## Active issues

- None.

## Decisions

- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
