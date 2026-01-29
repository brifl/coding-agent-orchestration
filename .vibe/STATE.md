# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 9
- Checkpoint: 9.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define a schema for specifying quality gates per checkpoint or globally.

## Deliverables (current checkpoint)

- `docs/quality_gates.md` — gate types, configuration, and examples
- Schema addition to `.vibe/config.json` for gate definitions
- Gate types: `test`, `lint`, `typecheck`, `custom`

## Acceptance (current checkpoint)

- [ ] Schema supports: command to run, pass/fail criteria, optional vs required gates
- [ ] Documentation covers common use cases (pytest, ruff, mypy)

## Work log (current session)

- 2026-01-29: Consolidation: archived Stage 8 to HISTORY, advanced to Stage 9 checkpoint 9.0.
- 2026-01-28: Reviewed 8.1 — PASS. All 37 tests pass, coverage complete.
- 2026-01-28: Implemented 8.1 — created test suite (37 tests, all passing).
- 2026-01-28: Advanced to checkpoint 8.1 — Cross-agent test suite.
- 2026-01-28: Reviewed 8.0 — PASS. Both acceptance criteria verified.
- 2026-01-28: Design loop: 8.0 already implemented (stage transition, consolidation), marking IN_REVIEW.
- 2026-01-28: Consolidation: archived Stage 7 to HISTORY, advanced to Stage 8 checkpoint 8.0.
- 2026-01-28: Fixed agentctl.py to handle (SKIPPED) checkpoints in stage detection.
- 2026-01-28: Skipped 7.1/7.2 per user request — no Kimi/IQuest access.
- 2026-01-28: Reviewed 7.0 — PASS. Bootstrap is agent-agnostic, config guide is clear.

## Evidence

(Cleared — new stage)

## Active issues

- None.

## Decisions

- 2026-01-28: Skipped checkpoints 7.1/7.2 (Kimi/IQuest verification) — no access to these agents; generic bootstrap is sufficient.
- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
