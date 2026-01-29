# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 10
- Checkpoint: 11.0
- Status: BLOCKED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Include CONTEXT.md in agent bootstrap flow.

## Deliverables (current checkpoint)

- Update bootstrap prompts to read CONTEXT.md after STATE.md
- agentctl `status` command includes context summary
- Optional: `--with-context` flag for verbose context display

## Acceptance (current checkpoint)

- New sessions start with relevant context loaded
- Agents don't re-discover known gotchas

## Work log (current session)

- 2026-01-29: Blocked - Stage 10 needs consolidation before starting Stage 11.
- 2026-01-29: Advanced to checkpoint 11.0.
- 2026-01-29: Reviewed 10.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.2 - Added context-aware bootstrap reads and status output.
- 2026-01-29: Advanced to checkpoint 10.2.
- 2026-01-29: Reviewed 10.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.1 - Added prompt.context_capture and consolidation guidance.
- 2026-01-29: Advanced to checkpoint 10.1.
- 2026-01-29: Reviewed 10.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.0 - Added context schema and example CONTEXT.md with persistent vs ephemeral guidance.
- 2026-01-29: Consolidation: archived Stage 9 to HISTORY, advanced to Stage 10 checkpoint 10.0.
- 2026-01-29: Reviewed 9.2 - PASS. Deliverables and acceptance criteria met. Demo command is correct.
- 2026-01-29: Resolved issue with incorrect demo command in PLAN.md for checkpoint 9.2.
- 2026-01-29: Reviewed 9.2 - FAIL. Demo command in PLAN.md is incorrect.
- 2026-01-29: Implemented 9.2 - Created quality gate templates for python, typescript and a minimal one. Validated that the templates are correctly structured and can be executed by `agentctl`.
- 2026-01-29: Reviewed 9.1 — PASS. Gate execution logic is sound.
- 2026-01-29: Implemented 9.1 - Enhanced `agentctl.py` to support quality gates.
- 2026-01-29: Reviewed 9.0 — PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 9.0 - Created `docs/quality_gates.md` and added schema to `.vibe/config.json`.
- 2026-01-29: Consolidation: archived Stage 8 to HISTORY, advanced to Stage 9 checkpoint 9.0.

## Evidence

- `cat .vibe/CONTEXT.md`
  - Shows Architecture/Key Decisions/Gotchas/Hot Files/Agent Notes sections with realistic content.
- `docs/context_schema.md`
  - Explicitly separates persistent project context from ephemeral session context.
- `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.context_capture`
  - Prompt includes capture/omit guidance and concise output format.
- `python tools/agentctl.py --repo-root . status --with-context`
  - Status output includes context summary and full sections when requested.

## Active issues

- BLOCKER: Stage transition to 11.0 without consolidation; align STATE/PLAN before proceeding.

## Decisions

- 2026-01-28: Skipped checkpoints 7.1/7.2 (Kimi/IQuest verification) — no access to these agents; generic bootstrap is sufficient.
- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
