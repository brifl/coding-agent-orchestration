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
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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
- 2026-02-19: 25.5 implemented — added `tests/workflow/test_checkpoint_dag.py` (11 tests), authored `docs/checkpoint_dependencies.md` with diamond example, and updated `docs/concepts.md`; demo commands pass in repo-local agentctl.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [x] STAGE_DESIGNED
- [x] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE
- [x] PROCESS_IMPROVEMENTS_DONE

## Evidence

- `python3 -m pytest tests/workflow/test_checkpoint_dag.py -v --capture=sys` -> 11 passed.
- `python3 tools/agentctl.py --repo-root . validate --strict` -> `ok: True`.
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` -> fails on pre-existing `continuous-documentation.yaml` prompt-role mappings; repo-local `tools/agentctl.py` is used for checkpoint acceptance.

## Active issues

- [ ] ISSUE-255: Skill-packaged strict validate mismatch
  - Impact: MINOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Align prompt-role mapping behavior between `tools/agentctl.py` and `.codex/skills/vibe-loop/scripts/agentctl.py`.
  - Evidence Needed: Both strict validation commands pass with identical role-mapping behavior.
  - Notes: Checkpoint 25.5 acceptance uses `tools/agentctl.py` and passes; mismatch is outside this checkpoint scope.

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
