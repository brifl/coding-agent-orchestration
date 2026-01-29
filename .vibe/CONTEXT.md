# Context

This file captures key context for the project. Sections below are intentionally
simple so they can be updated incrementally.

## Architecture

- `tools/agentctl.py` orchestrates the Vibe workflow using `.vibe/STATE.md` and
  `.vibe/PLAN.md`.
- Prompt templates live in `prompts/` and are queried via `tools/prompt_catalog.py`.

## Key Decisions

- 2026-01-28: Use `.vibe/` as the authoritative location for state/plan/history.
- 2026-01-28: `agentctl.py` validates that the stage in STATE matches PLAN.
- 2026-01-29: Stage 10 focuses on context snapshots to reduce re-discovery.

## Gotchas

- Some Vibe tooling expects to be run from the repo root to resolve paths.
- Keep STATE evidence cleared when advancing to a new stage.

## Hot Files

- `.vibe/STATE.md` — current checkpoint state and issues.
- `.vibe/PLAN.md` — backlog and acceptance criteria.
- `tools/agentctl.py` — workflow CLI entry point.
- `prompts/` — template prompts and bootstrap flows.

## Agent Notes

- 2026-01-29: Implementing checkpoint 10.0 (context schema and example file).
- Next: update `.vibe/STATE.md` evidence once demo command is run.
