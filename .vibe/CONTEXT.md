# Context

This file captures key context for the project. Sections below are intentionally
simple so they can be updated incrementally.

## Architecture

- `tools/agentctl.py` is the workflow authority: dispatch (`next`), validation,
  and `LOOP_RESULT` protocol recording.
- Prompt contracts live in `prompts/template_prompts.md`; continuous selection
  is automated by `.codex/skills/vibe-run/scripts/vibe_run.py`.
- Stage 21 introduces an RLM toolchain under `tools/rlm/` and
  `skills/rlm-tools/` (not implemented yet in this checkpoint).

## Key Decisions

- 2026-01-28: Use `.vibe/` as the authoritative location for state/plan/history.
- 2026-01-28: `agentctl.py` validates that the stage in STATE matches PLAN.
- 2026-02-06: Archived Stage 19A and Stage 20; active work is Stage 21 (RLM).
- 2026-02-06: Added headless `vibe-run --executor` mode for automated loop runs.
- 2026-02-06: Hardened plan parsing to ignore fenced-code headings.

## Gotchas

- Some Vibe tooling expects to be run from the repo root to resolve paths.
- `agentctl` global flags must appear before the subcommand (for example:
  `python3 tools/agentctl.py --repo-root . --format json next`).
- If `.vibe/LOOP_RESULT.json` is stale for the current state hash, dispatcher may
  gate progression until a new loop result is recorded.

## Hot Files

- `.vibe/STATE.md` — current checkpoint state and issues.
- `.vibe/PLAN.md` — backlog and acceptance criteria.
- `tools/agentctl.py` — workflow CLI entry point.
- `prompts/template_prompts.md` — role prompt contracts and LOOP_RESULT schema.
- `.codex/skills/vibe-run/scripts/vibe_run.py` — continuous runner + executor mode.

## Agent Notes

- 2026-02-06: Current checkpoint is 21.0 (`NOT_STARTED`): define RLM concepts,
  glossary, and decision table (RLM vs RAG vs standard loops).
- 2026-02-06: Context capture run should clear `RUN_CONTEXT_CAPTURE` in STATE.
- Next expected dispatcher role after this loop: `implement`.
