# PLAN

## Stage 25 — Checkpoint Dependency Graph

**Stage objective:**
Extend PLAN.md with optional `depends_on: [X.Y, ...]` annotations per checkpoint, build a DAG validator integrated into `agentctl validate`, update the dispatcher to skip checkpoints whose dependencies are not yet (DONE), and implement `agentctl dag` to visualize the dependency graph. Optionally extend `agentctl next --parallel N` to return up to N simultaneously-runnable checkpoints.

### Stage invariants (apply to all checkpoints)

- **Backward compatible:** Existing PLANs without `depends_on:` annotations work identically to today. No defaults change.
- **Validate-integrated:** DAG validation runs inside `agentctl validate` — not a separate command. No extra step required for the common case.
- **Dep resolution is status-based:** A dependency is satisfied iff the referenced checkpoint is marked (DONE) or (SKIP) in PLAN.md. Live STATE.md status is not consulted.
- **No cross-stage restriction:** `depends_on:` may reference checkpoints in any stage; intra-stage and cross-stage deps are treated identically.
- **Additive parallel dispatch:** `--parallel N` is a new optional flag; the default (`agentctl next` with no flag) returns exactly one role as today.

---

### 25.0 — Dependency syntax design and parser

* **Objective:**
  Define the `depends_on:` syntax in PLAN.md checkpoint headers and implement `_parse_checkpoint_dependencies()` with backward-compatible parsing.
* **Deliverables:**
  * Syntax: optional line `depends_on: [1.4, 2.1]` (indented 2 spaces) immediately following the `### N.M — Title` heading
  * `_parse_checkpoint_dependencies(plan_text) -> dict[str, list[str]]` in `tools/agentctl.py` — returns `{checkpoint_id: [dep_id, ...]}` for all checkpoints; checkpoints without `depends_on:` have empty lists
  * Parsing is whitespace-tolerant and order-independent relative to other checkpoint metadata
  * Normalized checkpoint IDs (same `normalize_checkpoint_id()` used elsewhere)
* **Acceptance:**
  * Checkpoints without `depends_on:` → empty dep list (unchanged behavior).
  * Checkpoints with `depends_on: [1.4, 2.1]` → `{"2.0": ["1.4", "2.1"]}`.
  * Malformed `depends_on:` value → parse error captured for validation (not crash).
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . --format json validate`
* **Evidence:**
  * Tests showing parsed deps for checkpoints with and without `depends_on:`.

---

### 25.1 — DAG validation (cycles, dangling deps, self-deps)

* **Objective:**
  Implement `_validate_checkpoint_dag()` with cycle detection, dangling reference detection, and self-dependency detection, integrated into `agentctl validate`.
* **Deliverables:**
  * `_validate_checkpoint_dag(checkpoint_ids, deps) -> list[str]` in `tools/agentctl.py`
  * Cycle detection: DFS with grey/black coloring; error message names the cycle path (e.g., "Cycle: 1.2 → 2.0 → 1.2")
  * Dangling reference: dep ID not present in `checkpoint_ids`
  * Self-dependency: `checkpoint_id` in its own dep list
  * Integration: `validate()` calls `_validate_checkpoint_dag()` and routes errors to `errors` list (strict mode) or `warnings` list (non-strict)
* **Acceptance:**
  * Cycle in deps → error with cycle path.
  * Dep referencing non-existent checkpoint → error with checkpoint ID.
  * Self-dep → error.
  * Valid DAG with no cycles or dangling refs → no errors.
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Tests showing all error cases. `agentctl validate` catches a cyclic dep in a test fixture.

---

### 25.2 — Dispatcher integration: dep-aware ready-checkpoint selection

* **Objective:**
  Update `_recommend_next()` so that in the DONE state, it skips checkpoints whose `depends_on` deps are not yet (DONE)/(SKIP), surfaces the first dep-satisfied checkpoint, and emits a dep-blocked reason when all remaining checkpoints are dep-blocked.
* **Deliverables:**
  * `_get_satisfied_deps(plan_text, checkpoint_id) -> bool` helper — returns True iff all deps of `checkpoint_id` are (DONE) or (SKIP) in `plan_text`
  * Updated DONE-state branch in `_recommend_next()`: after skipping (DONE)/(SKIP) checkpoints, also skip dep-blocked checkpoints
  * Dep-blocked stop: if the only remaining checkpoints are dep-blocked, route to `stop` with reason listing the specific unmet deps
* **Acceptance:**
  * Checkpoint with all deps (DONE) → dispatcher routes to it normally.
  * Checkpoint with an unmet dep → dispatcher skips it and finds the next dep-satisfied checkpoint.
  * All remaining checkpoints dep-blocked → dispatcher routes to `stop` with unmet dep list.
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . validate`
* **Evidence:**
  * Tests showing all three cases.

---

### 25.3 — `agentctl dag` render command

* **Objective:**
  Implement `agentctl dag` that renders the checkpoint dependency graph as JSON or ASCII, with node status annotations (DONE/SKIP/READY/BLOCKED).
* **Deliverables:**
  * `agentctl dag` subcommand in `tools/agentctl.py`
  * JSON output (`--format json`): `{nodes: [{id, title, status, deps}], edges: [{from, to}]}`
    * `status`: `DONE` | `SKIP` | `READY` (deps satisfied, not yet done) | `DEP_BLOCKED` (unmet deps)
  * ASCII output (`--format ascii`, default): indented tree with status icons
    * `[✓] 1.0 — Title`, `[→] 1.1 — Title (ready)`, `[✗] 2.0 — Title (blocked: 1.2)`
  * Reads both PLAN.md (structure + deps + done markers) and STATE.md (current checkpoint)
* **Acceptance:**
  * `agentctl dag --format json` produces valid JSON with all checkpoints and their statuses.
  * `agentctl dag --format ascii` renders a readable tree.
  * A repo with no `depends_on:` annotations produces a linear graph (no edges in JSON).
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . dag --format json`
  * `python tools/agentctl.py --repo-root . dag --format ascii`
* **Evidence:**
  * JSON and ASCII output for a PLAN.md with and without deps.

---

### 25.4 — Parallel dispatch: `agentctl next --parallel N`

* **Objective:**
  Extend `agentctl next` with `--parallel N` that returns up to N simultaneously-runnable checkpoints (dep-satisfied leaves), enabling multiple agents to work in parallel on independent tracks.
* **Deliverables:**
  * `--parallel N` flag on `agentctl next` (N ≥ 1; N=1 is identical to current behavior)
  * `_get_ready_checkpoints(plan_text, state) -> list[str]` — returns all dep-satisfied, not-yet-done checkpoints in document order
  * Parallel output format: `recommended_roles: [{checkpoint, role, prompt_id, reason}, ...]` list instead of single `recommended_role`
  * Single-item list when N=1 or only one ready checkpoint exists (backward compatible JSON shape with both `recommended_role` and `recommended_roles` present)
* **Acceptance:**
  * `--parallel 2` with two independent ready checkpoints returns both.
  * `--parallel 2` with only one ready checkpoint returns one.
  * `--parallel 1` output is structurally identical to `agentctl next` without the flag.
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . validate`
* **Evidence:**
  * JSON output showing two recommended roles from a PLAN.md with parallel-ready checkpoints.

---

### 25.5 — Integration tests and documentation

* **Objective:**
  Full test suite for dependency graph features and end-user documentation.
* **Deliverables:**
  * `tests/workflow/test_checkpoint_dag.py` covering: dep parsing, DAG validation (cycles, dangling, self), dispatcher dep-aware skip, dep-blocked stop, `agentctl dag` JSON/ASCII output, parallel dispatch
  * `docs/checkpoint_dependencies.md` — dependency graph guide with syntax reference, validation rules, `agentctl dag` usage, and `--parallel` dispatch guide
  * `docs/concepts.md` updated with DAG concepts
* **Acceptance:**
  * All tests pass.
  * `agentctl validate --strict` passes.
  * Docs include a worked example of a diamond dependency (1.0 → 1.1 and 1.0 → 1.2 → 1.3, where 1.3 depends_on [1.1, 1.2]).
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_checkpoint_dag.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. `docs/checkpoint_dependencies.md` exists with diamond example.

---

## Stage 26 — Agent Platform Simplification

**Stage objective:**
Remove workflow support surfaces for all agent platforms except Codex and Claude Code, while leaving provider integrations unchanged.

### Stage invariants (apply to all checkpoints)

- **Codex/Claude only:** `codex` and `claude` are the only supported workflow agent identifiers.
- **Stable repo layout:** Repo-local installs still target `.codex/skills`; this stage only trims unsupported agent paths and docs.
- **No provider churn:** LLM provider integrations (`anthropic`, `openai`, `google`, `triton`, etc.) are out of scope for this stage.
- **Prompt catalog parity:** Repo prompt sources and copied skill resource catalogs must stay in sync.

---

### 26.0 — Remove non-Codex/Claude platform support

* **Objective:**
  Remove Gemini, Copilot, and generic agent-platform surfaces from tooling, prompts, docs, manifests, and tests.
* **Deliverables:**
  * `tools/constants.py`, `tools/bootstrap.py`, `tools/skillctl.py`, `tools/skill_registry.py`, `tools/resource_resolver.py`, and `.codex/skills/vibe-loop/scripts/resource_resolver.py` only accept Codex/Claude agent identifiers and default to Codex
  * Prompt/bootstrap cleanup across `.codex/skills/*/resources/template_prompts.md`, `prompts/template_prompts.md`, and `prompts/init/` removes Gemini/Copilot/generic bootstraps
  * Agent-support docs updated in `README.md`, `docs/agent_skill_packs.md`, `docs/agent_capabilities.md`, `docs/base_skills.md`, `docs/skill_lifecycle.md`, and `prompts/init/capability_map.md`
  * Continuous workflow skill manifests advertise only Codex and Claude support
  * Regression coverage updated in `tests/workflow/test_bootstrap.py`, `tests/workflow/test_prompt_flow_integrity.py`, and `tests/workflow/test_skill_tooling.py`
* **Acceptance:**
  * CLI/tool defaults use `codex`, and unsupported agent values such as `gemini` and `copilot` are rejected by agent-selection entry points
  * No Gemini/Copilot/generic bootstrap files or prompt-catalog entries remain
  * Agent-support docs and skill manifests list only Codex and Claude Code
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_skill_tooling.py -v --capture=sys` passes
  * `python3 tools/agentctl.py --repo-root . validate --strict` passes
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_skill_tooling.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing unsupported-agent rejection and prompt/doc cleanup.
  * Strict validation output.

---

## Stage 27 — Core Prompt Catalog Canonicalization

**Stage objective:**
Collapse duplicated core prompt catalogs into a single repo-authoring source so prompt changes stop creating multi-file churn across the Codex/Claude workflow stack.

### Stage invariants (apply to all checkpoints)

- **Single repo authoring source:** `prompts/template_prompts.md` is the only human-edited core prompt catalog in the repo.
- **Runtime compatibility preserved:** Codex and Claude runtime entrypoints must still resolve a usable catalog in both repo-local and global-install layouts.
- **No prompt semantics drift:** Prompt IDs and prompt bodies stay behaviorally equivalent; this stage changes location/resolution, not the workflow contract.
- **Generated copies are minimized:** Any installed skill-resource copy must be derived from the canonical source, not treated as a second source of truth.

---

### 27.0 — Define canonical catalog resolution contract

* **Objective:**
  Make repo tools and runtime entrypoints resolve the core prompt catalog from one canonical source instead of probing multiple duplicated skill-resource copies.
* **Deliverables:**
  * Canonical catalog resolution helper(s) in the repo tooling layer and mirrored skill-runtime entrypoint(s)
  * `tools/agentctl.py`, `tools/bootstrap.py`, `tools/clipper.py`, `.codex/skills/vibe-run/scripts/vibe_run.py`, and `.codex/skills/vibe-loop/scripts/vibe_next_and_print.py` updated to use the shared contract
  * Repo mode resolves `prompts/template_prompts.md`; installed-skill mode resolves the `vibe-prompts` resource copy
  * Regression coverage updated in prompt-catalog/runtime tests for repo and installed layouts
* **Acceptance:**
  * Repo-local workflow commands surface `prompts/template_prompts.md` as the active catalog path.
  * Installed runtime entrypoints still work when only the `vibe-prompts` resource copy is present.
  * No tool still requires non-`vibe-prompts` skill resource catalogs for prompt lookup.
  * `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_vibe_run.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_vibe_run.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . --format json next`
* **Evidence:**
  * Test output showing repo and installed catalog resolution both work.
  * `agentctl next` output showing the canonical repo prompt catalog path.

---

### 27.1 — Stop syncing the core catalog into every skill

* **Objective:**
  Remove bootstrap/install behavior that copies the core prompt catalog into non-`vibe-prompts` skill resources.
* **Deliverables:**
  * `tools/bootstrap.py` only syncs the core catalog into the installed `vibe-prompts` skill resource path
  * Repo-local `.codex/skills/*/resources/template_prompts.md` duplication is eliminated outside `vibe-prompts`
  * Runtime helpers that previously fell back to per-skill catalog copies are simplified
  * Regression coverage updated in bootstrap/install tests
* **Acceptance:**
  * Repo-local skill trees do not carry duplicated `template_prompts.md` files outside `vibe-prompts`.
  * Global install flow still yields a working `vibe-prompts/resources/template_prompts.md`.
  * Bootstrap/install tests cover the reduced sync behavior.
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py tests/workflow/test_vibe_run.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py tests/workflow/test_vibe_run.py -v --capture=sys`
  * `rg --files .codex/skills | rg 'template_prompts\\.md$'`
* **Evidence:**
  * Test output showing install behavior still works.
  * File inventory proving only the intended core catalog copy remains under `.codex/skills`.

---

### 27.2 — Document and validate the single-source catalog model

* **Objective:**
  Update docs and validation so the canonical prompt-catalog model is explicit and future duplicate copies are caught early.
* **Deliverables:**
  * Documentation updates in `README.md`, `docs/resource_model.md`, `docs/agent_skill_packs.md`, and prompt-catalog/skill docs that describe the single-source + derived-copy model
  * Validation/test guardrails that fail when duplicate core catalog copies reappear in repo-authoring paths
  * Cleanup of stale wording that still describes copied skill-resource catalogs as canonical in repo mode
* **Acceptance:**
  * Docs consistently identify `prompts/template_prompts.md` as the repo authoring source and `vibe-prompts/resources/template_prompts.md` as the installed runtime copy.
  * Validation/tests catch duplicate core catalog drift.
  * `python3 tools/agentctl.py --repo-root . validate --strict` passes.
  * `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
  * `python3 -m pytest tests/workflow/test_prompt_catalog_validation.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
* **Evidence:**
  * Strict validation output.
  * Tests showing duplicate-catalog guardrails and doc assumptions are enforced.

---

## Stage 28 — Packaged Tool Mirror Elimination

**Stage objective:**
Replace hand-maintained packaged tool copies with generated or manifest-driven artifacts so repo tooling and installed skill tooling stop drifting apart.

### Stage invariants (apply to all checkpoints)

- **One source per tool:** Each packaged helper script must map back to one repo-owned source or generation step.
- **CLI stability:** User-facing CLI entrypoints and installed skill commands remain backward-compatible.
- **Drift must be testable:** The repo must be able to prove whether packaged copies match their source of truth.
- **Codex/Claude scope only:** Packaging decisions only need to satisfy the remaining supported agents and layouts.

---

### 28.0 — Define packaged-tool source-of-truth manifest

* **Objective:**
  Make the repo explicit about which files in `.codex/skills/**/scripts` are source-owned, generated, or synced, and centralize that mapping.
* **Deliverables:**
  * A manifest or equivalent source-of-truth mapping for packaged script/resource sync
  * `tools/bootstrap.py` and related sync/install paths updated to use the manifest instead of scattered hard-coded file lists
  * Documentation of which artifacts are editable sources versus generated outputs
  * Regression coverage for manifest-driven sync behavior
* **Acceptance:**
  * Packaged tool sync no longer depends on duplicated hard-coded path lists spread across the codebase.
  * A new packaged script/resource mapping can be added in one place.
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py -v --capture=sys`
  * `rg -n "helper_pairs|template_prompts|scripts/agentctl.py" tools .codex/skills -S`
* **Evidence:**
  * Tests showing manifest-driven sync behavior.
  * Scan output showing hard-coded packaged-tool sync paths removed or reduced.

---

### 28.1 — Split shared dispatcher/runtime logic out of giant script mirrors

* **Objective:**
  Move reusable dispatcher/runtime behavior into shared repo modules so packaged entrypoints become thin wrappers rather than full forked copies.
* **Deliverables:**
  * Shared modules extracted from `tools/agentctl.py` / packaged script mirrors for reusable logic
  * Thin CLI wrappers for repo and packaged entrypoints
  * Updated packaged skill scripts that import or generate from the shared implementation path
  * Regression coverage proving repo and packaged entrypoints stay behaviorally aligned
* **Acceptance:**
  * `.codex/skills/vibe-loop/scripts/agentctl.py` is no longer a hand-maintained near-fork of `tools/agentctl.py`.
  * Core dispatcher/runtime tests pass for repo and packaged entrypoints.
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_run.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_run.py -v --capture=sys`
  * `wc -l tools/agentctl.py .codex/skills/vibe-loop/scripts/agentctl.py`
* **Evidence:**
  * Tests showing repo and packaged entrypoints remain aligned.
  * File-size/source-of-truth comparison showing the near-fork is removed or materially reduced.

---

### 28.2 — Add drift detection for packaged artifacts

* **Objective:**
  Prevent future repo/tool drift by making packaged-artifact mismatches a first-class validation failure.
* **Deliverables:**
  * Drift-detection check integrated into tests or validation tooling
  * Documentation for how to regenerate packaged artifacts
  * Guardrails covering packaged scripts and packaged prompt/runtime resources
* **Acceptance:**
  * The repo fails fast when packaged artifacts diverge from their declared source.
  * Regeneration workflow is documented and deterministic.
  * `python3 tools/agentctl.py --repo-root . validate --strict` passes.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
  * `python3 -m pytest tests/workflow/test_skill_tooling.py tests/workflow/test_bootstrap.py -v --capture=sys`
* **Evidence:**
  * Strict validation output.
  * Tests showing drift detection is enforced.

---

## Stage 29 — Context And State Hygiene Automation

**Stage objective:**
Reduce friction from stale context snapshots and bloated work logs so long-running repos stay cheap to resume and the dispatcher blocks less often on housekeeping.

### Stage invariants (apply to all checkpoints)

- **State remains auditable:** Nothing about context/work-log cleanup should hide completed work or reduce traceability.
- **Low-friction resume:** Resuming a repo should require the minimum necessary context refresh, not blanket maintenance loops.
- **Automation over ceremony:** Prefer deterministic helpers and guardrails over manual cleanup instructions.
- **Backward compatibility:** Existing STATE/HISTORY/CONTEXT formats remain readable throughout the transition.

---

### 29.0 — Make context freshness more targeted

* **Objective:**
  Refresh context only when material workflow state or hot files changed enough to justify a new capture.
* **Deliverables:**
  * Refined context-staleness heuristic in dispatcher/runtime tooling
  * Context-capture trigger criteria based on meaningful repo/workflow changes instead of broad elapsed-time heuristics alone
  * Regression coverage for stale-versus-fresh context routing
* **Acceptance:**
  * `agentctl next` only routes to `context_capture` when the context snapshot is materially stale.
  * Fresh repos with unchanged workflow context do not get unnecessary context-capture stops.
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . --format json next`
* **Evidence:**
  * Tests showing stale/fresh context routing behavior.
  * `agentctl next` output demonstrating the refined trigger.

---

### 29.1 — Add work-log and evidence compaction helpers

* **Objective:**
  Keep `.vibe/STATE.md` readable by automatically or semi-automatically rolling older work-log/evidence entries into durable summaries.
* **Deliverables:**
  * Deterministic compaction/archive helper(s) for old work-log and evidence entries
  * Updated consolidation/history flow that preserves auditability while trimming active STATE noise
  * Regression coverage for compaction and archive behavior
* **Acceptance:**
  * Long-running repos can prune oversized work logs without losing key evidence.
  * STATE validation warnings for oversized work logs are actionable through a documented helper flow.
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_issue_schema_validation.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_issue_schema_validation.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Tests showing compaction preserves required state structure.
  * Validation output showing the resulting STATE remains acceptable.

---

### 29.2 — Surface true blockers in dispatcher output

* **Objective:**
  Make `agentctl next` explain housekeeping blockers and recovery steps more directly so humans and agents waste less time rediscovering why they were stopped.
* **Deliverables:**
  * Improved dispatcher messaging for context/work-log/loop-result blockers
  * Tests covering the top housekeeping stop conditions
  * Documentation updates showing what each blocker means and how to clear it
* **Acceptance:**
  * Housekeeping-related `stop` recommendations include clear, actionable recovery steps.
  * Tests cover stale-context, pending-loop-result, and oversized-state flows.
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_troubleshoot.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_troubleshoot.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . --format json next`
* **Evidence:**
  * Tests showing actionable blocker output.
  * Example `agentctl next` payloads for the main housekeeping stops.

---

## Stage 30 — Codex Guidance Primitives

**Stage objective:**
Add deterministic guidance artifacts that complement Codex's built-in reasoning by giving it tighter task packets, durable constraint memory, and an explicit falsification step before implementation.

### Stage invariants (apply to all checkpoints)

- **Guide, do not replace:** These primitives should sharpen native model reasoning, not introduce a second planner that competes with it.
- **Low-token, high-signal:** Guidance artifacts must compress intent, constraints, and risks instead of restating the entire repo.
- **Deterministic from repo state:** Generated guidance must derive from STATE/PLAN/code, not ad-hoc chat memory.
- **Optional but composable:** Each primitive should be usable independently, while also fitting into the main loop when enabled.

---

### 30.0 — Compile a checkpoint execution brief

* **Objective:**
  Generate a compact, deterministic execution brief for the active checkpoint so Codex starts with the exact scope, files, commands, and stop conditions that matter.
* **Deliverables:**
  * A tooling command or helper that compiles the active checkpoint into a concise execution brief
  * Brief structure covering objective, deliverables, acceptance, hot files, demo commands, and immediate risks
  * Integration path for using the brief from implementation/review loops without copying large prompt text
  * Regression coverage for brief generation on representative checkpoints
* **Acceptance:**
  * The active checkpoint can be rendered as a compact execution brief directly from repo state.
  * The brief excludes irrelevant backlog/context while preserving enough detail to act correctly.
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Example execution brief for the active checkpoint.
  * Tests showing deterministic brief generation.

---

### 30.1 — Add a durable invariant and decision ledger

* **Objective:**
  Give Codex a stable, compact memory of non-negotiable constraints and architectural decisions so each loop starts from the right frame without re-reading everything.
* **Deliverables:**
  * A structured invariant/decision artifact derived from STATE, PLAN, and selected docs
  * Support for capturing constraints such as forbidden scope, required compatibility, acceptance-critical files, and architectural non-goals
  * Guidance for when invariants should be refreshed versus reused
  * Regression coverage for parsing/rendering invariant memory
* **Acceptance:**
  * The repo can surface a compact invariant/decision ledger for the active work without requiring a full document reread.
  * Critical constraints and non-goals are represented in a structured, machine-readable way.
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Example invariant/decision ledger for the current checkpoint.
  * Tests showing stable rendering/parsing behavior.

---

### 30.2 — Add a preflight challenge and falsification pass

* **Objective:**
  Require a short adversarial check before implementation so Codex actively looks for scope mistakes, hidden dependencies, missing tests, and likely failure modes.
* **Deliverables:**
  * A deterministic preflight challenge helper or loop adjunct that asks targeted “what could make this wrong?” questions for the active checkpoint
  * Challenge output covering dependency conflicts, ambiguous acceptance, rollback risk, and test blind spots
  * Integration path for using the challenge results in implementation/review loops
  * Regression coverage for challenge routing or output contracts
* **Acceptance:**
  * The active checkpoint can be evaluated through a compact falsification pass before edits begin.
  * The challenge output is actionable and tied to concrete repo files/tests, not generic advice.
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_troubleshoot.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_troubleshoot.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . --format json next`
* **Evidence:**
  * Example preflight challenge output for a checkpoint.
  * Tests showing the challenge pass stays deterministic and actionable.

---

## Stage 31 — Codex Runtime Self-Sufficiency

**Stage objective:**
Eliminate downstream Codex-specific patching by making the workflow runtime/install surface self-contained, predictable, and aligned with the intended dispatcher behavior.

### Stage invariants (apply to all checkpoints)

- **No downstream patching required:** A Codex user following the documented install/bootstrap flow should not need to edit vendored runtime scripts.
- **Installed layouts remain supported:** Repo-local and installed skill layouts must both work with the same runtime contract.
- **Codex/Claude scope preserved:** This stage improves runtime packaging/behavior, not agent-platform scope.
- **Behavioral fixes need regression coverage:** Any runtime-routing or install-layout fix added here must be locked in with tests.

---

### (DONE) 31.0 — Remove hidden runtime patch requirements

* **Objective:**
  Make the shipped workflow tooling work in repo and installed Codex layouts without local `agentctl.py`/`resource_resolver.py` patching.
* **Deliverables:**
  * `tools/agentctl.py` and `tools/resource_resolver.py` tolerate standalone/runtime-script layouts that do not include the full repo `tools/` module set
  * `tools/bootstrap.py` installs the helper-script dependencies required by packaged `vibe-loop`/`vibe-prompts` runtimes instead of assuming repo-only siblings exist
  * Dispatcher/loop-result handling no longer bounces immediately back into `issues_triage` after the current checkpoint/state just resolved a triage loop
  * Regression coverage added in `tests/workflow/test_bootstrap.py`, `tests/workflow/test_agentctl_routing.py`, and `tests/workflow/test_loop_result_protocol.py`
* **Acceptance:**
  * Installed/runtime helper layouts do not require a downstream `constants.py` patch to run.
  * A recently resolved `issues_triage` loop for the active state does not immediately re-route back to triage with no intervening work.
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_agentctl_routing.py tests/workflow/test_loop_result_protocol.py -v --capture=sys` passes.
  * `python3 tools/agentctl.py --repo-root . validate --strict` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_agentctl_routing.py tests/workflow/test_loop_result_protocol.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing installed-layout helper coverage and triage acknowledgement behavior.
  * Strict validation output.
