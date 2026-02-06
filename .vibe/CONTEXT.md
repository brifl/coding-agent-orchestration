# Context

This file captures key context for the project. Sections below are intentionally
simple so they can be updated incrementally.

## Architecture

- `tools/agentctl.py` remains the workflow authority for dispatch (`next`),
  strict validation, and `LOOP_RESULT` protocol state transitions.
- Prompt contracts live in `prompts/template_prompts.md`; loop selection and
  orchestration are driven by `.codex/skills/vibe-run/scripts/vibe_run.py`.
- Stage 21 (RLM) is complete; current active backlog is Stage 21A
  (continuous-documentation skill design + implementation checkpoints).

## Key Decisions

- 2026-01-28: Use `.vibe/` as the authoritative location for state/plan/history.
- 2026-01-28: `agentctl.py` validates that the stage in STATE matches PLAN.
- 2026-02-06: Added headless `vibe-run --executor` mode for automated loop runs.
- 2026-02-06: Hardened plan parsing to ignore fenced-code headings.
- 2026-02-06: Completed Stage 21 checkpoints through `21.11` (RLM tooling).
- 2026-02-06: Transitioned pointer to Stage `21A` and moved JIT stage to top
  of `.vibe/PLAN.md` to prioritize continuous-documentation.

## Gotchas

- Some Vibe tooling expects to be run from the repo root to resolve paths.
- `agentctl` global flags must appear before the subcommand (for example:
  `python3 tools/agentctl.py --repo-root . --format json next`).
- If `.vibe/LOOP_RESULT.json` is stale for the current state hash, dispatcher may
  gate progression until a new loop result is recorded.
- Plan ordering is positional; if the current stage is not set in STATE when a
  prior stage reaches `DONE`, dispatcher may report `stop` as plan-exhausted.

## Hot Files

- `.vibe/STATE.md` — current checkpoint state and issues.
- `.vibe/PLAN.md` — backlog and acceptance criteria.
- `tools/agentctl.py` — workflow CLI entry point.
- `prompts/template_prompts.md` — role prompt contracts and LOOP_RESULT schema.
- `.codex/skills/vibe-run/scripts/vibe_run.py` — continuous runner + executor mode.

## Agent Notes

- 2026-02-06: Current checkpoint is `21A.0` (`NOT_STARTED`): define
  documentation scope, severity rubric (`MAJOR|MODERATE|MINOR`), and finding
  schema for gap/refactor phases.
- 2026-02-06: Context capture run should clear `RUN_CONTEXT_CAPTURE` in STATE.
- Next expected dispatcher role after this loop: `implement` (if no issues).
