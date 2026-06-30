# PLAN

## Stage 33 — Codex-Native Backlog Bootstrap

**Stage objective:**
Make a newly installed Vibe repo immediately useful in current Codex: one repo-path install, one `$vibe-run` invocation, then repository-aware backlog design followed by execution.

### Stage invariants

- Use Codex repository inspection and planning instead of requiring an external provider to seed the backlog.
- Keep one obvious install and execution path; preserve compatibility only for demonstrated consumers.
- Preserve substantive project work while removing placeholder, stale, or speculative workflow scaffolding.

### 33.0 — Bootstrap a repository-aware executable backlog

* **Objective:**
  Make fresh installs and exhausted `$vibe-run` sessions inspect the target repository, build a meaningful checkpoint backlog, and continue into execution without placeholder work or retrospective noise.
* **Deliverables:**
  * `tools/bootstrap.py` accepts a target repo path directly as the only repo-bootstrap command and installs clean skill trees without cache artifacts
  * Fresh templates route their first dispatcher step to repository-aware stage design; explicit `vibe-run` replenishes an exhausted backlog without bypassing blockers
  * Canonical `AGENTS.md` and core prompts require senior ownership, bounded planning, proportional verification, and removal of directly related clutter
  * Redundant launch aliases, nonstandard skill metadata, and additive-only lifecycle guidance are removed in the same ownership area
  * Regression coverage and operator docs prove the install-to-plan-to-execute path and its simplified surface
* **Acceptance:**
  * `python3 tools/bootstrap.py /path/to/repo` is the only repo-bootstrap form and has exactly one required argument.
  * The legacy `init-repo` subcommand and redundant `vibe-one-loop` alias are absent from code, installed skill sets, and operator docs.
  * A fresh install first dispatches repository-aware `design`; explicit `vibe-run` replenishes exhausted plans while default dispatch and blockers retain their stop behavior.
  * Canonical instructions treat parameters, stale docs, compatibility paths, diagnostics, and speculative tests as project risk; this PLAN contains only the current and next few committed stages plus bounded verification work.
  * Reinstall preserves substantive workflow files, installed skills contain no cache artifacts, focused tests pass, and strict validation succeeds.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py::test_direct_repo_path_install_routes_first_vibe_run_step_to_design tests/workflow/test_bootstrap.py::test_legacy_init_repo_subcommand_is_not_supported tests/workflow/test_bootstrap.py::test_reinstall_preserves_substantive_workflow_files tests/workflow/test_skill_tooling.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_run.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
  * `tmp=$(mktemp -d) && git init -q "$tmp" && python3 tools/bootstrap.py "$tmp" && python3 "$tmp/.codex/skills/vibe-loop/scripts/agentctl.py" --repo-root "$tmp" --format json next --workflow vibe-run`
* **Evidence:**
  * Focused test output covering direct install, removed aliases, plan preservation, exhausted-plan replenishment, and blocker behavior.
  * Fresh-repo output showing the single install path and initial repository-aware design decision.

---

## Stage 34 — State And Roadmap Hygiene

**Stage objective:**
Keep active workflow context small enough that operators and agents can see the next decision without excavating historical noise.

### 34.0 — Bound active state and plan content

* **Objective:**
  Make consolidation reliably keep only current roadmap/state material while archiving durable outcomes.
* **Deliverables:**
  * Consolidation behavior that bounds PLAN to current plus near-term committed stages and a concise verification backlog
  * STATE compaction that retains active constraints/issues while moving completed evidence and work-log detail to HISTORY
  * Removal of stale context flags or helpers that duplicate the same hygiene decision
  * Regression coverage for compaction without loss of active issues or acceptance criteria
* **Acceptance:**
  * PLAN and STATE remain bounded across stage transitions without manual archaeology.
  * Completed outcomes remain discoverable in HISTORY, while stale/speculative scaffolding is removed.
  * Active issues, current acceptance, and next committed checkpoints survive compaction.
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py tests/workflow/test_issue_schema_validation.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py tests/workflow/test_issue_schema_validation.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Before/after state bundle and compaction regression output.

---

## Non-blocking verification backlog

- Repair the two pre-existing feedback-channel fixtures that omit `_DecisionContext.recent_resolved_triage_for_current_state`, then restore a fully green `tests/workflow` run.
- Manually smoke-test repo installation from native Windows and one Claude Code environment when those runtimes are available; this does not block the Codex-first path.
