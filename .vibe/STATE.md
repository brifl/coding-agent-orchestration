# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 8
- Checkpoint: 8.1
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Create a simple test harness to verify workflow correctness across agents.

## Deliverables (current checkpoint)

- `tests/workflow/test_agentctl.py` — unit tests for agentctl dispatcher logic
- `tests/workflow/test_state_parsing.py` — tests for STATE.md parsing
- `tests/workflow/conftest.py` — fixtures for temporary .vibe directories

## Acceptance (current checkpoint)

- [ ] Tests cover: state parsing, checkpoint advancement, stage transition detection, consolidation triggering
- [ ] All tests pass with `python -m pytest tests/workflow/`

## Work log (current session)

- 2026-01-28: Reviewed 8.1 — PASS. All 37 tests pass, coverage complete.
- 2026-01-28: Implemented 8.1 — created test suite (37 tests, all passing).
- 2026-01-28: Advanced to checkpoint 8.1 — Cross-agent test suite.
- 2026-01-28: Reviewed 8.0 — PASS. Both acceptance criteria verified.
- 2026-01-28: Design loop: 8.0 already implemented (stage transition, consolidation), marking IN_REVIEW.
- 2026-01-28: Consolidation: archived Stage 7 to HISTORY, advanced to Stage 8 checkpoint 8.0.
- 2026-01-28: Fixed agentctl.py to handle (SKIPPED) checkpoints in stage detection.
- 2026-01-28: Skipped 7.1/7.2 per user request — no Kimi/IQuest access.
- 2026-01-28: Reviewed 7.0 — PASS. Bootstrap is agent-agnostic, config guide is clear.
- 2026-01-28: Implemented 7.0 — created generic_bootstrap.md and self-hosted config guide.
- 2026-01-28: Consolidation: archived Stage 6 to HISTORY, advanced to Stage 7 checkpoint 7.0.
- 2026-01-28: Checkpoint 6.1 — Gemini verified continuous mode; added Claude/Copilot/Kimi to bootstrap.py.
- 2026-01-28: Checkpoint 6.0 — Claude Code continuous mode demonstrated through this session.
- 2026-01-28: Consolidation: archived Stage 5 to HISTORY, advanced to Stage 6 checkpoint 6.0.
- 2026-01-28: Implemented checkpoint 5.0 — created docs/skill_lifecycle.md.

## Evidence

```
$ python -m pytest tests/workflow/ -v
============================= 37 passed in 0.14s ==============================

Tests cover:
- State parsing (TestParseKvBullets, TestCleanStatus, TestSliceActiveIssuesSection, TestParseIssues)
- Checkpoint advancement (TestNextCheckpointAfter)
- Stage transition detection (TestDetectStageTransition, TestGetStageForCheckpoint)
- Consolidation triggering (TestIsCheckpointMarkedDone)
```

## Active issues

- None.

## Decisions

- 2026-01-28: Skipped checkpoints 7.1/7.2 (Kimi/IQuest verification) — no access to these agents; generic bootstrap is sufficient.
- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
