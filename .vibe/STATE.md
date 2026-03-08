# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 27
- Checkpoint: 27.1
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Remove bootstrap/install behavior that copies the core prompt catalog into non-`vibe-prompts` skill resources.

## Deliverables (current checkpoint)

- `tools/bootstrap.py` only syncs the core catalog into the installed `vibe-prompts` skill resource path
- Repo-local `.codex/skills/*/resources/template_prompts.md` duplication is eliminated outside `vibe-prompts`
- Runtime helpers that previously fell back to per-skill catalog copies are simplified
- Regression coverage updated in bootstrap/install tests

## Acceptance (current checkpoint)

- Repo-local skill trees do not carry duplicated `template_prompts.md` files outside `vibe-prompts`.
- Global install flow still yields a working `vibe-prompts/resources/template_prompts.md`.
- Bootstrap/install tests cover the reduced sync behavior.
- `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py tests/workflow/test_vibe_run.py -v --capture=sys` passes.

## Work log (current session)

- 2026-03-07: Backlog expanded again — added Stage 30 to complement Codex's built-in thinking with execution briefs, invariant memory, and a falsification pass for planned work.
- 2026-03-08: Stage 31 designed and started — added a Codex runtime self-sufficiency checkpoint to remove downstream patch requirements from installed/runtime helper layouts and dispatcher triage flow.
- 2026-03-08: 31.0 implemented — added standalone fallbacks for `agentctl.py`/`resource_resolver.py`, synced runtime helper dependencies during init/install flows, and preserved triage acknowledgement across same-state loop-result updates.
- 2026-03-08: 31.0 review PASS — `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_agentctl_routing.py tests/workflow/test_loop_result_protocol.py -v --capture=sys` passed (64 tests) and `python3 tools/agentctl.py --repo-root . validate --strict` returned `ok: True`; checkpoint marked `(DONE)` in PLAN and focus returned to 27.0 NOT_STARTED.
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

- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json validate` -> `ok: true` before the current consolidation; warnings were the 11-entry work log and optional evidence path.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json validate` -> `ok: true` after the current consolidation; only the optional evidence-path warning remains.
- `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_vibe_run.py -v --capture=sys` -> `16 passed in 8.15s`.
- `python3 tools/agentctl.py --repo-root . --format json next` -> `prompt_catalog_path: /mnt/c/src/coding-agent-orchestration/prompts/template_prompts.md`, `recommended_role: implement`, `checkpoint: 27.0`.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> `ok: True`.
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True`.
- `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_vibe_run.py -v --capture=sys` -> `16 passed in 6.79s` during review re-check.
- `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py::test_rejects_duplicate_prompt_catalogs -v --capture=sys` -> `1 passed in 0.29s`.
- `python3 -m pytest tests/workflow/test_vibe_run.py::test_vibe_run_falls_back_to_installed_vibe_prompts_catalog -v --capture=sys` -> `1 passed in 1.20s`.

## Active issues

- None.

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
