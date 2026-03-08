# CONTEXT

## Architecture

- `tools/agentctl.py` is the workflow authority for dispatch, strict validation, and `LOOP_RESULT` acknowledgement.
- Core prompt contracts currently resolve through `.codex/skills/vibe-prompts/resources/template_prompts.md`; Stage `27.0` exists to make `prompts/template_prompts.md` the single repo authoring source.
- Runtime/bootstrap behavior for installed Codex layouts was hardened in Stage `31.0`; `tools/bootstrap.py` now force-syncs the required helper bundle into skill runtimes.
- Continuous execution is driven by `.codex/skills/vibe-run/scripts/vibe_run.py`, but real work should use real loop results rather than simulated acknowledgements.

## Key Decisions

- 2026-01-28: `.vibe/` is the authoritative workflow state location for active work.
- 2026-03-07: Workflow agent support was intentionally reduced to `codex` and `claude`; other platform surfaces were removed.
- 2026-03-08: Stage `31.0` made Codex runtime installs self-sufficient so downstream repos no longer need local `agentctl.py`/`resource_resolver.py` patches.
- 2026-03-08: Stage `32` was added to make the system proactively handle overwhelming complexity through working-set derivation, pressure-triggered decomposition, fork tracking, and resume packets.

## Gotchas

- `.vibe/*` is ignored by git; commits that intentionally include workflow state require `git add -f`.
- `agentctl` global flags must appear before the subcommand, for example `python3 tools/agentctl.py --repo-root . --format json next`.
- The current dispatcher still routes through `context_capture` when `.vibe/CONTEXT.md` is stale relative to workflow docs.
- The active backlog pointer is Stage `27.0`, but later backlog stages (`28`-`32`) are already designed; avoid mistaking backlog design work for the current implementation target.
- There are unrelated pre-existing dirty files in the worktree; do not fold them into checkpoint commits unless the task explicitly touches them.

## Hot Files

- `.vibe/STATE.md` — active checkpoint pointer, work log, and workflow flags.
- `.vibe/PLAN.md` — Stage `27` prompt-catalog work plus later backlog stages through `32`.
- `prompts/template_prompts.md` — intended canonical prompt authoring source for Stage `27`.
- `tools/agentctl.py` — prompt-catalog resolution and workflow dispatch surface.
- `tools/bootstrap.py` — install/init sync behavior that still depends on current prompt-catalog layout.
- `tools/clipper.py` — one of the Stage `27.0` deliverables for shared prompt-catalog resolution.
- `.codex/skills/vibe-run/scripts/vibe_run.py` and `.codex/skills/vibe-loop/scripts/vibe_next_and_print.py` — runtime entrypoints that will need the canonical catalog contract.

## Agent Notes

- Current focus is Stage `27`, checkpoint `27.0`, status `NOT_STARTED`.
- Immediate next step after this context refresh should be to re-dispatch and begin Stage `27.0` implementation if no new blocker appears.
- `agentctl next` was recommending `context_capture` because this file was stale; that should clear after recording the loop result for this update.
- Unrelated dirty files currently present: `.codex/skills/continuous-refactor/resources/refactoring-guide.md`, `.gitignore`, `docs/plan_authoring.md`, `docs/workflow_improvements.md`, `tests/workflow/test_issue_schema_validation.py`, `tests/workflow/test_plan_pipeline.py`, and `tests/workflow/test_stage_ordering.py`.
