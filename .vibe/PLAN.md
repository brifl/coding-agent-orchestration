# PLAN

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

## Stage 32 — Complexity Control And Focus Retention

**Stage objective:**
Make the orchestration system actively reduce cognitive load during large vibecoding efforts by constraining the working set, detecting overload early, isolating unresolved forks, and making interruption recovery cheap.

### Stage invariants (apply to all checkpoints)

- **Focus over exhaustiveness:** The system should surface the minimum context needed to make the next correct move, not the maximum context available.
- **Complexity must be compressed:** Large plans and repos are normal; the workflow should continuously shrink them into a tractable active slice.
- **Ambiguity must be isolated:** Open forks, assumptions, and non-decisions should be tracked explicitly instead of leaking into implementation loops.
- **Resumption must be fast:** Losing session context should cost minutes, not hours.

---

### 32.0 — Derive an active working set for the current checkpoint

* **Objective:**
  Generate a compact, deterministic working set so the active checkpoint starts from the files, tests, commands, and constraints that matter now.
* **Deliverables:**
  * A helper or command that derives the active working set from STATE, PLAN, recent loop evidence, and repo structure
  * Working-set output that includes hot files, likely tests, immediate commands, and excluded distractions
  * Integration path for surfacing the working set through status/briefing flows without re-reading broad repo context
  * Regression coverage for working-set generation on representative checkpoints
* **Acceptance:**
  * The active checkpoint can be rendered as a bounded working set directly from repo state.
  * The working set favors the highest-signal files/tests and explicitly excludes irrelevant backlog noise.
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl.py tests/workflow/test_prompt_flow_integrity.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Example working-set output for the active checkpoint.
  * Tests showing deterministic file/test selection.

---

### 32.1 — Detect checkpoint pressure and force decomposition before thrash

* **Objective:**
  Detect when a checkpoint has grown beyond a sane working set and route back to decomposition before implementation quality collapses.
* **Deliverables:**
  * Pressure heuristics based on scope size, file spread, unresolved issues, and acceptance breadth
  * Dispatcher or tooling behavior that recommends design/decomposition when the active checkpoint is overloaded
  * Clear operator feedback explaining why the checkpoint is considered too broad
  * Regression coverage for pressure detection and decomposition routing
* **Acceptance:**
  * Oversized checkpoints are surfaced before prolonged implementation churn.
  * The system can distinguish healthy complexity from genuine checkpoint overload.
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_plan_pipeline.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_agentctl_routing.py tests/workflow/test_plan_pipeline.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . --format json next`
* **Evidence:**
  * Tests showing overloaded checkpoints route to decomposition-oriented handling.
  * Example dispatcher output explaining pressure-based intervention.

---

### 32.2 — Add an explicit fork and assumption ledger

* **Objective:**
  Keep unresolved architectural forks and working assumptions visible but quarantined so implementation loops can stay on one chosen path at a time.
* **Deliverables:**
  * A structured fork/assumption ledger for active work
  * Support for marking one branch as the current execution path while retaining alternatives and evidence
  * Integration into briefing/status flows so the current path and unresolved forks are obvious
  * Regression coverage for parsing/rendering fork state
* **Acceptance:**
  * The repo can show the chosen path, open alternatives, and required evidence without burying them in prose.
  * Implementation loops no longer need to rediscover unresolved forks from scattered notes.
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_state_parsing.py tests/workflow/test_agentctl_routing.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Example fork/assumption ledger for a checkpoint.
  * Tests showing stable parsing and display of branch choices.

---

### 32.3 — Generate resume packets after each meaningful loop

* **Objective:**
  Make interruptions cheap by emitting a compact resume packet that tells the next Codex session exactly where to restart.
* **Deliverables:**
  * A generated resume packet sourced from the latest real loop result, state, and working set
  * Resume content covering last completed action, next best move, hot files, proof of progress, and immediate risk
  * Integration path for surfacing the packet in status/dispatch flows
  * Regression coverage for resume-packet generation and stale-session recovery
* **Acceptance:**
  * The repo can render a high-signal “resume now” packet for the current work.
  * Losing chat/session context no longer requires reconstructing intent from raw history.
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py -v --capture=sys` passes.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_loop_result_protocol.py tests/workflow/test_agentctl_routing.py -v --capture=sys`
  * `python3 tools/agentctl.py --repo-root . status --with-context`
* **Evidence:**
  * Example resume packet derived from a real loop result.
  * Tests showing deterministic recovery output.
