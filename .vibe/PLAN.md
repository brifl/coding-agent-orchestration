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
