# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 33
- Checkpoint: 33.0
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Make fresh installs and exhausted `$vibe-run` sessions inspect the target repository, build a meaningful checkpoint backlog, and continue into execution without placeholder work or retrospective noise.

## Deliverables (current checkpoint)

- Direct repo-path bootstrap command with backward compatibility and clean skill copying
- Fresh-template routing into repository-aware stage design without overwriting existing workflow files
- Explicit `$vibe-run` replenishment for empty/exhausted plans with blocker preservation
- Current Codex-aligned `vibe-run` skill metadata/instructions and stage-design prompt
- Regression coverage and operator documentation for the install-to-plan-to-execute path

## Acceptance (current checkpoint)

- `python3 tools/bootstrap.py /path/to/repo` works with one required argument.
- Fresh install dispatches `design`; explicit `$vibe-run` replenishes exhausted plans without weakening blocker behavior.
- Reinstall preserves substantive workflow files and excludes Python cache artifacts.
- Planning prompt inspects code and produces aligned, executable PLAN/STATE content.
- Focused workflow tests and strict validation pass.

## Work log (current session)

- 2026-06-30: User-prioritized Stage 33.0 started to modernize repo installation and make `$vibe-run` bootstrap a repository-aware executable backlog before implementation.
- 2026-06-30: 33.0 implemented — direct repo-path installation, clean/preserving bootstrap behavior, fresh/exhausted-plan design routing, Codex-native skill metadata, repository-aware planning prompts, docs, and regression coverage committed in `38620d0`.

- 2026-03-08: Backlog expanded again — added Stage 32 to make the system actively handle overwhelming project complexity through working-set derivation, pressure-triggered decomposition, explicit fork tracking, and resume packets.
- 2026-03-08: context_capture loop — refreshed `.vibe/CONTEXT.md` so the current Stage 27 work, Stage 31 completion, and Stage 32 backlog can be resumed without rediscovery; recorded `LOOP_RESULT`.
- 2026-03-08: consolidation loop — archiving completed Stages 25, 26, and 31 into HISTORY, pruning them from PLAN, and trimming STATE work-log/evidence noise back to a current handoff set for 27.0.
- 2026-03-08: 27.0 implemented — repo tooling now resolves `prompts/template_prompts.md` as the canonical repo catalog, packaged loop entrypoints fall back only to `vibe-prompts/resources/template_prompts.md`, and regression coverage now proves both repo and installed layouts.
- 2026-03-08: 27.0 review PASS — demo commands and two adversarial probes passed, no additional code-review improvements were identified outside the existing Stage 27 backlog, and focus auto-advanced to 27.1 NOT_STARTED.
- 2026-03-08: consolidation loop — trimmed the oldest stale work-log entries and cleared archived-stage evidence so Stage 27.1 can resume without immediately re-triggering housekeeping.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [x] STAGE_DESIGNED
- [x] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE
- [x] PROCESS_IMPROVEMENTS_DONE

## Evidence

- `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_run.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys` -> `80 passed in 48.85s`.
- Fresh-repo probe -> direct path install printed `Invoke $vibe-run`; first explicit dispatch returned only `recommended_role: design` / `prompt.stage_design`; fetched prompt required repository inventory, plan assessment, Codex planning inputs, and relevant-skill use.
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True`; skill-creator `quick_validate.py` and `tools/skillctl.py validate` both passed for `vibe-run`.
- `python3 -m pytest tests/workflow -v --capture=sys` -> `269 passed, 2 failed`; both failures pre-exist in `HEAD` because unchanged feedback tests omit the already-required `_DecisionContext.recent_resolved_triage_for_current_state` constructor field.

## Active issues

- None.

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
