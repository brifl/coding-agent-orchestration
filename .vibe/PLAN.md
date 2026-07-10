# PLAN

## Stage 33 — Managed Consumer Runtime

**Stage objective:**
Make fresh and existing consumer repositories execute one current, framework-owned runtime without local Python or prompt-catalog patches.

### Stage invariants

- Preserve substantive project workflow files and project-owned skills/rules.
- Installed runners use their sibling managed runtime; target-repo overrides are explicit and diagnosable.
- Reinstall converges managed files by content and removes retired managed artifacts.

### (DONE) 33.0 — Bootstrap a repository-aware executable backlog

* **Objective:**
  Give a fresh repository one install path and a repository-aware `$vibe-run` entry that designs or replenishes an executable backlog.
* **Deliverables:**
  * Direct repo-path bootstrap with clean fresh skill copying
  * Fresh-template repository-aware design and exhausted-plan replenishment
  * Senior-ownership, bounded-roadmap, lightweight-evidence, and deferral guidance
  * Removal of the legacy `init-repo` and `vibe-one-loop` launch aliases
* **Acceptance:**
  * Fresh install routes first to design and explicit `$vibe-run` replenishes an exhausted plan.
  * Substantive STATE/PLAN files survive reinstall.
  * Fresh installed skills contain no Python cache artifacts or removed launch aliases.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_agentctl_routing.py tests/workflow/test_vibe_run.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
* **Evidence:**
  * Commits `1abe5ff` through `ed17740`; focused bootstrap/routing/deferral suites passed.

### 33.1 — Make installed execution self-first and provenance-visible

* **Objective:**
  Ensure installed Vibe entrypoints execute their sibling managed runtime and prompt catalog instead of silently preferring stale target-repo framework copies.
* **Deliverables:**
  * Installed `vibe-run` and one-loop wrappers resolve sibling generated helpers before target-repo `tools/`
  * Installed prompt lookup prefers the sibling `vibe-prompts` resource; source-repo execution keeps `prompts/template_prompts.md`
  * Installed workflow selection cannot silently import a target-repo `workflow_engine.py`
  * Dispatcher output reports compact runtime/catalog path, digest, and source mode
  * Regression tests cover stale target tools/catalogs and source-vs-installed behavior
* **Acceptance:**
  * A deliberately stale or broken target `tools/agentctl.py` is not executed by an installed runner.
  * A target `prompts/template_prompts.md` does not shadow the installed catalog without an explicit compatible override.
  * Source-repo commands still use canonical source tools/prompts.
  * Decision JSON makes active runtime and catalog provenance immediately visible.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_vibe_run.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_agentctl_workflow_selector_fallback.py -v --capture=sys`
  * `python3 -m pytest tests/workflow/test_bootstrap.py tests/workflow/test_skill_tooling.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Installed-runtime fixture output showing managed paths/digests despite stale target copies.
  * Focused wrapper, catalog, workflow-selector, and strict-validation results.

### 33.2 — Make managed reinstall converge

* **Objective:**
  Make repeated installs atomically converge framework-owned files while preserving project-owned work.
* **Deliverables:**
  * Content-addressed install manifest with framework-managed skills/files and digests
  * Managed skill refresh that does not trust destination mtimes
  * Removal of previously managed retired files/skills, caches, bytecode, and obsolete prompt resources
  * Preservation of unrelated project skills, AGENTS project content, and substantive `.vibe` files
  * Tartu-style upgrade fixture plus concise install provenance summary
* **Acceptance:**
  * Fresh install and upgrade from the legacy fixture produce the same managed tree.
  * Removed `vibe-one-loop`, `__pycache__`, `.pyc`, and obsolete resources do not survive reinstall.
  * A project-defined skill and customized STATE/PLAN remain byte-identical.
  * Locally modified formerly-managed files are reported with a clear ownership outcome rather than silently winning by mtime.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_bootstrap.py -v --capture=sys`
  * `python3 -m pytest tests/workflow/test_skill_tooling.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Before/after manifest and managed-tree comparison for fresh and legacy fixtures.
  * Focused bootstrap/skill validation results.

---

## Stage 34 — Pure Monotonic Core Loop

**Stage objective:**
Make dispatch side-effect free, retry-safe, and focused on product progress instead of automatic ceremony.

### 34.0 — Separate routing from verification

* **Objective:**
  Make `status` and `next` pure queries and execute each explicitly requested verification command at most once.
* **Deliverables:**
  * Removal of implicit demo-command execution from decision gathering
  * Single execution path for explicit gates with no successful double-run
  * Review guidance that selects proportional verification without automatic duplication
  * Regression tests proving routing performs no subprocess work
* **Acceptance:**
  * `status` and `next` succeed when `subprocess.run` is patched to fail.
  * Dispatcher executes zero PLAN commands and owns no per-command smoke timeout.
  * `next --run-gates` runs each configured gate once.
  * A legitimate demo longer than 30 seconds does not require PLAN surgery merely to obtain a role decision.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_agentctl.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --format json`
* **Evidence:**
  * Subprocess-spy test and one explicit-gate invocation-count receipt.

### 34.1 — Remove broken automatic meta loops

* **Objective:**
  Reduce the normal lifecycle to design when needed, implementation, review, and one bounded stage rollover.
* **Deliverables:**
  * Removal of mtime/count/modulo-driven maintenance, retrospective, context-capture, and process-improvement routing
  * Removal of obsolete lifecycle flags from templates, prompts, parser logic, and tests
  * One stage-rollover path that archives compact outcomes and designs only when the next checkpoint is not executable
  * Maintenance work represented as explicit evidence-backed PLAN checkpoints or explicitly invoked specialized workflows
* **Acceptance:**
  * Fresh install dispatches implementation immediately after its initial design completion.
  * A stage transition consumes at most two agent loops before implementation.
  * No transition depends on wall-clock age, stage number, line count, or lifecycle booleans.
  * There is no route that sends a maintenance scan into normal product review.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_state_parsing.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
  * `python3 -m pytest tests/workflow/test_vibe_run.py -v --capture=sys`
* **Evidence:**
  * End-to-end fresh install and two-stage transition role sequences.

### 34.2 — Make dispatch completion transactional

* **Objective:**
  Prevent retries from skipping work and make checkpoint/dependency completion an atomic tool-owned transition.
* **Deliverables:**
  * Pending dispatch identity that is stable across repeated `next` calls
  * Cursor advancement only after successful completion acknowledgement
  * Tool-owned checkpoint completion ledger/PLAN mutation used by dependency readiness
  * No-progress detection with an actionable stop reason
* **Acceptance:**
  * Ten `next` calls before completion return the same dispatch and prompt.
  * Wrong or stale completion identity is rejected.
  * Normal review PASS makes dependent checkpoints ready without manual PLAN edits.
  * Two consecutive no-progress completions stop instead of looping indefinitely.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_workflow_engine_runtime.py tests/workflow/test_checkpoint_dag.py -v --capture=sys`
* **Evidence:**
  * Retry/idempotency and dependency-unlock receipts.

---

## Stage 35 — Bounded Working Set

**Stage objective:**
Give each loop only the durable policy and active repository evidence it needs.

### 35.0 — Establish compact policy, state, and work packets

* **Objective:**
  Replace repeated full-document reads with a bounded active checkpoint packet while keeping project intent durable.
* **Deliverables:**
  * Managed AGENTS core plus preserved project-owned and path-scoped rule surfaces
  * PLAN-owned checkpoint definitions; STATE limited to pointer/status, current truth, active issues, and latest receipts
  * `agentctl brief` active work packet with dependency, issue, evidence, and provenance data
  * Removal of manual CONTEXT from required routing, or automatic hash-valid regeneration
  * Byte/word budget validation for AGENTS, STATE, PLAN active horizon, and stage-history summaries
* **Acceptance:**
  * STATE remains below 250 words after repeated checkpoint transitions.
  * A very large PLAN/HISTORY fixture produces a correct active packet below 1,200 estimated tokens.
  * Implementation/review do not require full PLAN or HISTORY reads.
  * Framework updates replace only the managed AGENTS block and preserve project policy.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_issue_schema_validation.py tests/workflow/test_bootstrap.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . brief --format json`
* **Evidence:**
  * Before/after instruction sizes and large-fixture work-packet receipt.

---

## Stage 36 — Slim Protocol And Surface Consolidation

**Stage objective:**
Remove redundant model-authored protocol fields, mechanical roles, and superseded optional surfaces.

### 36.0 — Replace verbose loop reports with compact completion

* **Objective:**
  Reduce checkpoint protocol overhead while retaining trustworthy evidence and specialized-workflow findings.
* **Deliverables:**
  * Completion contract limited to dispatch identity, result, short summary, and optional findings
  * Tool-derived stage/checkpoint/status/transition and next role
  * Role-specific prompts without repeated schemas, numeric confidence scoring, or forced finding quotas
  * Risk-based review path with mechanical low-risk completion and full review for meaningful risk
  * Context-budget and public transition-table tests
* **Acceptance:**
  * Typical completion metadata is below 250 bytes excluding its summary.
  * Implementation prompt is below 250 words and review below 350.
  * Core prompt/protocol overhead per checkpoint falls by at least 65%.
  * Tests no longer construct private decision context or mirrored result reports.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_prompt_flow_integrity.py tests/workflow/test_agentctl_routing.py -v --capture=sys`
* **Evidence:**
  * Before/after prompt and completion sizes plus end-to-end checkpoint transition.

---

## Non-blocking consolidation backlog

- Delete the mechanical `advance` agent role after transactional completion owns pointer movement.
- Remove the superseded provider-driven `agentctl plan` pipeline and its design-prompt/docs/test surface after repository-aware design fully owns backlog creation.
- Collapse workflow order definitions to one canonical registry; remove runtime/YAML/hardcoded duplicates.
- Remove decorative `--parallel`/`recommended_roles` until checkpoint leases and isolated results make concurrency real.
- Reduce `VIBE.md`, unused config promises, historical workflow docs, and wiki mirrors to current operator-facing contracts.
- Separate RLM/RAG/documentation experiments from the default orchestration maintenance surface.
- Derive a human-facing action queue from active `Owner: human` issues instead of maintaining a second current-truth file.
- Smoke-test native Windows and one Claude Code install when those runtimes are available.
