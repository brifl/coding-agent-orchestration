# Context

This file captures key context for the project. Sections below are intentionally
simple so they can be updated incrementally.

## Architecture

- `tools/agentctl.py` remains the workflow authority for dispatch (`next`),
  strict validation, and `LOOP_RESULT` protocol state transitions.
- Prompt contracts live in `prompts/template_prompts.md`; loop selection and
  orchestration are driven by `.codex/skills/vibe-run/scripts/vibe_run.py`.
- Stage 21A (continuous-documentation) is complete and archived to HISTORY.md.
- Stage 21 (RLM) is the current active stage, starting at checkpoint 21.0.

## Key Decisions

- 2026-01-28: Use `.vibe/` as the authoritative location for state/plan/history.
- 2026-01-28: `agentctl.py` validates that the stage in STATE matches PLAN.
- 2026-02-06: Added headless `vibe-run --executor` mode for automated loop runs.
- 2026-02-06: Hardened plan parsing to ignore fenced-code headings.
- 2026-02-06: Completed Stage 21 checkpoints through `21.11` (RLM tooling).
- 2026-02-06: Transitioned pointer to Stage `21A` for continuous-documentation.
- 2026-02-07: Consolidated Stage 21A (DONE) back into Stage 21 at checkpoint 21.0.

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

- 2026-02-13: Current checkpoint is `21.0` (`NOT_STARTED`): Define what RLM means
  in this system, when it should be used, and how it differs from standard prompts
  and RAG. Deliverables: `docs/rlm_overview.md`, `docs/rlm_glossary.md`, and a
  decision table (RLM vs RAG vs standard Vibe loops).
- Next expected dispatcher role: `implement` (checkpoint 21.0 deliverables).
