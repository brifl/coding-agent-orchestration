# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 25
- Checkpoint: 25.5
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Full test suite for dependency graph features and end-user documentation.

## Deliverables (current checkpoint)

- `tests/workflow/test_checkpoint_dag.py` covering all Stage 25 DAG features
- `docs/checkpoint_dependencies.md` — dependency graph guide with syntax, validation, dag usage, and parallel dispatch
- `docs/concepts.md` updated with DAG concepts

## Acceptance (current checkpoint)

- All tests pass.
- `agentctl validate --strict` passes.
- Docs include a worked example of a diamond dependency.

## Work log (current session)

- 2026-02-19: 25.0 implemented — `_parse_checkpoint_dependencies`; bug fix: PROCESS_IMPROVEMENTS_DONE suppression; 206 tests pass.
- 2026-02-19: 25.0 review PASS — auto-advanced to 25.1 NOT_STARTED.
- 2026-02-19: 25.1 implemented — `_validate_checkpoint_dag` (DFS cycle detection, dangling refs, self-deps); integrated into `validate()`; 206 tests pass.
- 2026-02-19: 25.1 review PASS — auto-advanced to 25.2 NOT_STARTED.
- 2026-02-19: 25.2 implemented — `_get_satisfied_deps`, `_get_unmet_deps`; dep-blocked skip loop + stop in `_decide_role`; 206 tests pass.
- 2026-02-19: 25.2 review PASS — all 3 ACs met. Auto-advanced to 25.3 NOT_STARTED.
- 2026-02-19: 25.3 implemented — `_parse_checkpoint_titles`, `_compute_dag_node_status`, `cmd_dag`; JSON+ASCII output; `dag --format` subparser; 206 tests pass.
- 2026-02-19: 25.3 review PASS — all 3 ACs met. Auto-advanced to 25.4 NOT_STARTED.
- 2026-02-19: 25.4 implemented — `_get_ready_checkpoints`; `--parallel N` flag on `next`; `recommended_roles` always in output; 206 tests pass.
- 2026-02-19: 25.4 review PASS — all 3 ACs met. Auto-advanced to 25.5 NOT_STARTED.
- 2026-02-19: 25.5 implemented — added `tests/workflow/test_checkpoint_dag.py` (11 tests), authored `docs/checkpoint_dependencies.md` with diamond example, updated `docs/concepts.md`, and normalized 25.5 demo commands to `python3` + `--capture=sys` for smoke-gate parity.
- 2026-02-19: 25.5 review PASS — acceptance met with adversarial probes; no follow-up checkpoint in PLAN order, so checkpoint remains 25.5 and status set to DONE (plan exhausted).
- 2026-02-19: continuous-refactor review loop — verified working-tree refactor diff is line-ending-only (`git diff --ignore-cr-at-eol` empty); workflow regression suite (57 tests) passed; skill-packaged strict validate still fails on known ISSUE-255 while repo-local strict validate passes.
- 2026-02-19: continuous-refactor scan loop — generated 10 refactor candidates across maintainability/safety/testability families; all surfaced as [MINOR] cleanup opportunities (exception narrowing, duplication cleanup, docs/prompt catalog line-ending normalization) with no justified [MAJOR]/[MODERATE] candidate in current DONE-state scope.
- 2026-02-19: continuous-refactor execute loop (approved ideas 1-5) — narrowed skillset loader exception handling, improved prompt-catalog fallback diagnostics, added shared CLI error formatting helper, tightened provider call exception branching, and centralized workflow test tools-path bootstrap in `tests/workflow/conftest.py`.
- 2026-02-19: continuous-refactor verify loop (post-execute) — reran workflow regression matrix (108 tests passed), confirmed repo-local strict validation still passes, and re-confirmed skill-packaged strict-validate failure remains unchanged under known ISSUE-255.
- 2026-02-19: continuous-refactor scan loop (post-approved 1-5) — generated the next minor-only tail set (remaining broad catches and duplicated workflow-test `sys.path` bootstraps), preserving ISSUE-255 parity note as out-of-scope for this loop.
- 2026-02-19: continuous-refactor execute loop (approved idea 5) — aligned `.codex/skills/vibe-loop/scripts/agentctl.py` workflow prompt-role mappings for all continuous-documentation prompts and added regression coverage in `tests/workflow/test_continuous_aux_workflow_overrides.py`.
- 2026-02-19: continuous-refactor verify loop (post-approved idea 5) — `tests/workflow/test_continuous_aux_workflow_overrides.py` passed (10 tests) and both strict validation entrypoints now return `ok: True`, resolving ISSUE-255 mismatch evidence.
- 2026-02-19: continuous-refactor scan loop (post-approved idea 5) — generated next minor-only backlog focusing on remaining broad exception branches and repeated workflow-test `sys.path` bootstraps now that ISSUE-255 parity is fixed.
- 2026-02-20: continuous-refactor verify loop — confirmed active refactor diff is line-ending-only (`git diff --ignore-cr-at-eol --stat` empty despite large `git diff --stat` churn), reran workflow regression slice (57 passed), and both strict validation entrypoints return `ok: True`.
- 2026-02-20: continuous-refactor scan loop — generated 10 `[MINOR]` candidates across maintainability/safety/testability from remaining hotspots (`except Exception` branches and repeated workflow-test `sys.path` bootstraps); recommended first moves are narrowing CLI exception handling in `tools/agentctl.py`/`tools/bootstrap.py` and centralizing workflow-test import bootstrap usage.
- 2026-02-20: continuous-refactor stop gate — workflow stopped on minor-only scan findings and exposed approval-required idea IDs 1-5 for optional execution through `workflow-approve`.
- 2026-02-20: continuous-documentation preflight — recorded a context-capture LOOP_RESULT acknowledgement to clear pending STATE sync before entering workflow dispatch.
- 2026-02-20: continuous-documentation execute loop (`prompt.docs_refactor_fix`) — ran deterministic refactor analysis/fix pipeline; applied 2 finding-mapped doc changes (`merge_duplicates`, `migrate_to_wiki`) with zero consistency validation errors; post-fix refactor report moved from `MODERATE:1/MINOR:2` to `MODERATE:0/MINOR:3`.
- 2026-02-20: continuous-documentation stop gate — workflow stopped on minor-only documentation findings and exposed approval-required idea IDs 1-3 for optional follow-up execution.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [x] STAGE_DESIGNED
- [x] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE
- [x] PROCESS_IMPROVEMENTS_DONE

## Evidence

- `python3 -m pytest tests/workflow/test_checkpoint_dag.py -v --capture=sys` -> 11 passed.
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True`.
- `python3 tools/agentctl.py --repo-root . --format json next` -> `recommended_role: review`.
- Adversarial probe 1: `python3 -m pytest tests/workflow/test_checkpoint_dag.py -k "malformed or dep_blocked" -v --capture=sys` -> 3 passed.
- Adversarial probe 2: `python3 tools/agentctl.py --repo-root . --format json next --parallel 2` -> `recommended_roles` returns two checkpoints.
- Review transition note: no checkpoint exists after 25.5 in PLAN order; plan exhausted with checkpoint 25.5 marked DONE in STATE.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> fails on pre-existing `continuous-documentation.yaml` prompt-role mappings; repo-local `tools/agentctl.py` is used for checkpoint acceptance.
- `git diff --ignore-cr-at-eol --stat` -> no output (line-ending-only diff across 12 files).
- `python3 -m pytest tests/workflow/test_issue_schema_validation.py tests/workflow/test_plan_pipeline.py tests/workflow/test_skip_marker.py tests/workflow/test_stage_ordering.py -v --capture=sys` -> 57 passed.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> still fails on known ISSUE-255 prompt-role mapping mismatch.
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True` (no errors).
- `rg -n "TODO|FIXME|type: ignore|except Exception|pass  #|pragma: no cover" tools tests docs -S` -> scan hotspots found (for example `tools/skillset_utils.py:71`, `tools/skillset_utils.py:151`, `tools/plan_pipeline.py:164`, `tools/agentctl.py:2722`).
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` (scan loop rerun) -> unchanged failure on known ISSUE-255 mapping mismatch.
- `python3 -m pytest tests/workflow/test_continuous_minor_approval.py tests/workflow/test_continuous_refactor_workflow_override.py tests/workflow/test_continuous_aux_workflow_overrides.py tests/workflow/test_vibe_run.py tests/workflow/test_skill_tooling.py tests/workflow/test_bootstrap.py tests/workflow/test_plan_pipeline.py tests/workflow/test_agentctl_routing.py -v --capture=sys` -> 108 passed.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> still fails on known ISSUE-255 prompt-role mapping mismatch (unchanged).
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True` (warnings only: work-log length + optional evidence path).
- `rg -n "except Exception|sys.path.insert\\(0, str\\(Path\\(__file__\\)\\.parent\\.parent\\.parent / \"tools\"\\)\\)" tools tests/workflow -S` -> remaining minor candidates found in `tools/skillctl.py`, `tools/plan_pipeline.py`, `tools/bootstrap.py`, and multiple `tests/workflow/test_*.py` modules.
- `python3 -m pytest tests/workflow/test_continuous_aux_workflow_overrides.py -v --capture=sys` -> 10 passed.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> `ok: True` (errors cleared for continuous-documentation prompt-role mappings).
- `rg -n "except Exception|sys.path.insert\\(0, str\\(Path\\(__file__\\)\\.parent\\.parent\\.parent / \\\"tools\\\"\\)\\)|TODO|FIXME" tools tests/workflow -S` -> remaining minor hotspots concentrated in `tools/skillctl.py`, `tools/plan_pipeline.py`, `tools/bootstrap.py`, `tools/agentctl.py`, and legacy workflow test modules.
- `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-refactor` -> `recommended_prompt_id: prompt.refactor_verify` (`recommended_role: review`).
- `git diff --stat` -> 9 files changed, 5420 insertions, 5420 deletions (textual churn due line ending normalization).
- `git diff --ignore-cr-at-eol --stat` -> no output (content-equivalent after CRLF normalization).
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> `ok: True` (warning only: optional evidence path).
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True` (warnings only: work-log length + optional evidence path).
- `python3 -m pytest tests/workflow/test_issue_schema_validation.py tests/workflow/test_plan_pipeline.py tests/workflow/test_skip_marker.py tests/workflow/test_stage_ordering.py -v --capture=sys` -> 57 passed in 8.25s.
- `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-refactor` -> `recommended_prompt_id: prompt.refactor_scan` (`recommended_role: implement`).
- `rg -n "except Exception|sys.path.insert\\(0, str\\(Path\\(__file__\\)\\.parent\\.parent\\.parent / \\\"tools\\\"\\)\\)|TODO|FIXME|type: ignore|pragma: no cover" tools tests/workflow docs -S` -> hotspot inventory captured for scan ranking.
- `rg --count-matches "except Exception" tools tests/workflow -S` -> `tools/agentctl.py:6`, `tools/bootstrap.py:2`, `tools/plan_pipeline.py:1`, `tools/skillctl.py:1`, `tools/rlm/runtime.py:1`, `tools/rlm/provider_check.py:1`.
- `rg --count-matches "sys.path.insert\\(0, str\\(Path\\(__file__\\)\\.parent\\.parent\\.parent / \\\"tools\\\"\\)\\)" tests/workflow -S` -> 14 workflow test modules still perform local `sys.path` bootstrap.
- `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-refactor` -> `recommended_role: stop`, `approval_required: true`, and `workflow-approve --ids <n>` command surfaced for minor-idea selection.
- `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-documentation` -> first call returned `requires_loop_result: true` (pending acknowledgement); after recording loop result, dispatcher selected `prompt.docs_refactor_fix`.
- `python3 tools/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...context_capture...}'` -> `ok: true` (acknowledgement cleared).
- `python3 tools/docs/doc_refactor_report.py --repo-root . --out .vibe/docs/refactor_report.before.current.json` -> summary `MAJOR:0, MODERATE:1, MINOR:2`.
- `python3 tools/docs/apply_refactor_fixes.py --repo-root . --report .vibe/docs/refactor_report.before.current.json --log .vibe/docs/refactor_fix_log.jsonl --apply` -> `changed_rows: 2`, `validation_errors: []`.
- `python3 tools/docs/doc_refactor_report.py --repo-root . --out .vibe/docs/refactor_report.after.current.json` -> summary `MAJOR:0, MODERATE:0, MINOR:3`.
- `.vibe/docs/refactor_fix_log.jsonl` -> applied rows for `docs/wiki-export/workflow_improvements.md` and `docs/skill_reference.md`; `split_to_code_specific_doc` was `noop_exists`.
- `docs/wiki-export/map.json` -> added mapping for `docs/workflow_improvements.md` to `docs/wiki-export/workflow_improvements.md`.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> `ok: True` (warning only: optional evidence path).
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...docs_refactor_fix...}'` -> `ok: true` (implement loop recorded with minor-only findings).
- `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-documentation` -> `recommended_role: stop`, `approval_required: true`, and `workflow-approve --ids <n>` command surfaced for minor-idea selection.

## Active issues

- None.

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
