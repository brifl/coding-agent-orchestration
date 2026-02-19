# Context

This file captures key context for the project. Sections below are intentionally
simple so they can be updated incrementally.

## Architecture

- `tools/agentctl.py` remains the workflow authority for dispatch (`next`),
  strict validation, and `LOOP_RESULT` protocol state transitions.
- Prompt contracts live in `prompts/template_prompts.md`; loop selection and
  orchestration are driven by `.codex/skills/vibe-run/scripts/vibe_run.py`.
- Stage 23 (Interactive Plan Authoring Pipeline) complete. Stage 24 (Structured
  Human Feedback Channel) is active at checkpoint 24.0.
- `tools/plan_pipeline.py` implements the full plan pipeline (PipelineConfig, PipelineProvider,
  _run_pipeline_step, run_plan_pipeline, render_plan_md); `agentctl plan` is the CLI entry point.

## Key Decisions

- 2026-01-28: Use `.vibe/` as the authoritative location for state/plan/history.
- 2026-01-28: `agentctl.py` validates that the stage in STATE matches PLAN.
- 2026-02-06: Added headless `vibe-run --executor` mode for automated loop runs.
- 2026-02-06: Hardened plan parsing to ignore fenced-code headings.
- 2026-02-13: Stage 22 complete through 22.4; improved dispatcher with stage
  design, enhanced review, smoke gate, preflight, and retrospective triggers.
- 2026-02-18: Added 4 dispatcher improvements (human BLOCKER → stop, resolved
  issue warning, stop → LOOP_RESULT.json, checkpoint minor ordering validation).
- 2026-02-18: Stage 22 complete (22.0–22.5). 20 E2E tests added; docs/workflow_improvements.md created.

## Gotchas

- Some Vibe tooling expects to be run from the repo root to resolve paths.
- `agentctl` global flags must appear before the subcommand (for example:
  `python3 tools/agentctl.py --repo-root . --format json next`).
- If `.vibe/LOOP_RESULT.json` is stale for the current state hash, dispatcher may
  gate progression until a new loop result is recorded.
- Plan ordering is positional; if the current stage is not set in STATE when a
  prior stage reaches `DONE`, dispatcher may report `stop` as plan-exhausted.
- On Windows, run `python3` commands through `cmd /c` or use absolute paths when
  shell quoting becomes an issue.

## Hot Files

- `.vibe/STATE.md` — current checkpoint state and issues.
- `.vibe/PLAN.md` — backlog and acceptance criteria.
- `tools/agentctl.py` — workflow CLI entry point.
- `prompts/template_prompts.md` — role prompt contracts and LOOP_RESULT schema.
- `.codex/skills/vibe-run/scripts/vibe_run.py` — continuous runner + executor mode.

## Agent Notes

- 2026-02-19: Stage 23 complete (23.0–23.4). Current checkpoint is `24.0` (`NOT_STARTED`):
  FEEDBACK.md schema, `FeedbackEntry` dataclass, and `agentctl feedback validate` subcommand.
  Stage flags reset; retrospective pending. Next role after retrospective is `implement`.

## Loop Execution Checklist

After **every** loop (implement, review, consolidation, design, retrospective, etc.):

1. Set the correct STATUS in STATE.md (NOT_STARTED → IN_PROGRESS → IN_REVIEW → DONE).
2. Update the Work log entry in STATE.md for this loop.
3. Run `python3 tools/agentctl.py --repo-root . --format json validate --strict` and confirm `ok: true`.
4. Submit LOOP_RESULT via `agentctl loop-result --line 'LOOP_RESULT: {...}'`.
5. **Commit and push:** `git add -u && git commit -m "<stage>.<checkpoint>: <description>"` then `git push origin main`.
6. Check `agentctl next` for the next role before starting it.

Skipping any step — especially 3, 4, or 5 — breaks the vibe-run protocol. Do not batch steps across loops.

## Stage Retrospective Notes

*Retrospective covers Stage 21 (RLM Tools) and Stage 22 checkpoints 22.0–22.4
(Vibe-Run Workflow Improvements).*

- **[Stage 21] Small-scope checkpoints beat big ones:** Stage 21 ran 12 checkpoints
  (21.0–21.11). Checkpoints that bundled multiple concerns (e.g., 21.5: three
  providers at once) required more review cycles than single-concern ones. Next time:
  if a checkpoint has >2 deliverable types, split it.

- **[Stage 21] Deferred work needs a re-evaluation anchor:** DEFERRED 21.7 (Kilo
  provider) was the right call, but the deferral decision lives only in a comment.
  Future deferrals should include a trigger condition in the PLAN.md note (e.g.,
  "revisit when 3+ real users request it") so the decision doesn't silently rot.

- **[Stage 22] Stage invariants prevent regression drift:** Declaring "backward
  compatible" and "no protocol break" as stage-level invariants in PLAN.md (not just
  per-checkpoint) was effective — it set a clear bar that each checkpoint accepted
  without re-arguing it. Use this pattern for every stage with cross-cutting
  constraints.

- **[Stage 22] Flag-based workflow state has low cognitive overhead:** The
  STAGE_DESIGNED / MAINTENANCE_CYCLE_DONE / RETROSPECTIVE_DONE pattern proved trivial
  to implement and easy to reason about. The unchecked=pending / checked=done
  checkbox model is the right abstraction. Extend it consistently (Stage 24
  FEEDBACK_PROCESSED should follow the same pattern).

- **[Stage 22] Test-first on dispatcher logic catches subtle routing bugs early:**
  The 2-value destructuring bug (`role, reason = _recommend_next(...)`) existed across
  multiple test files as a pre-existing error. Adding tests in the same checkpoint as
  the dispatcher change would have caught this immediately. Rule: any change to
  `_recommend_next()` must include a routing test in the same checkpoint.

- **[Stage 22.5] Demo commands must be subprocess-portable:** The smoke gate runs
  commands via `subprocess.run(shell=True)` which on Windows uses cmd.exe, not the
  activated venv. `python3 -m pytest` resolved to the Windows Store Python (no pytest).
  Rule: PLAN.md demo commands should only use tools reliably on PATH in the subprocess
  environment — prefer `python3 tools/agentctl.py` (known-working) over bare
  `python3 -m <module>` for smoke gate validation.

- **[Stage 23] Long stages guarantee mid-stage work log overflow:** 5 checkpoints × 2
  entries (implement + review) = 10 entries, which overflows any prior work log entries.
  For stages with 4+ checkpoints, plan for ≥1 mid-stage consolidation. The dispatcher
  handles it gracefully, but budgeting for it avoids surprise context pressure.

- **[Stage 23] Circular import order constrains shared constants:** `plan_pipeline.py`
  is imported by `agentctl.py`, so complexity budget constants had to be duplicated
  rather than shared. When introducing a utility module imported by `agentctl.py`,
  extract shared constants to a third file (`tools/vibe_constants.py`) before the stage
  starts to avoid duplication.

- **[Stage 23] Sub-module test docstrings drift as new classes are added:** The module
  docstring in `test_plan_pipeline.py` still said "checkpoint 23.1" after 23.4 tests
  were added. Rule: when adding test classes to an existing file, update the module
  docstring before submitting to review.
