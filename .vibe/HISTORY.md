# HISTORY

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Rules

- This file is **non-authoritative**. It is to provide context on what has been done already.
- It exists to reduce cognitive load by summarizing completed work and resolved issues.
- Do not rely on this file for current decisions; always check `.vibe/STATE.md` and `.vibe/PLAN.md`.
- When writing to this, keep summaries limited to one or two sentences for the stage/decision/issue.

---

## Completed stages

### 2026-02-06 — Stage 20: RAG Pipeline Hardening (completed)

Hardened the RAG stack end-to-end: deterministic scanner metadata, chunk-aware indexing, chunk-level retrieval formatting/diversity controls, agent-facing packaging, and stdlib TF-IDF semantic/hybrid search.

### 2026-02-06 — Stage 19A: Multi-Directory RAG Skill (completed)

Delivered the foundational scan -> index -> retrieve prototype and packaged it as the `rag-index` skill, establishing the baseline later hardened in Stage 20.

### 2026-02-03 — Stage 19: Templated Prompts Expansion (completed)

Added refactor, testing, and human feedback prompt templates with standardized output formats (checkpoints 19.0–19.2).

### 2026-02-03 — Stage 18: Design-Side Prompts (completed)

Added ideation, architecture, milestones, and PLAN generation prompts (checkpoints 18.0–18.2).

### 2026-02-03 — Stage 17: Configurable Workflows (completed)

Defined workflow configuration, implemented workflow execution and agentctl integration, and added preset workflow configurations (checkpoints 17.0–17.2).

### 2026-02-03 — Stage 16: Skill Subscription (completed)

Repeated subscription flow for Stage 16 with pinning and sync/upgrade commands to validate the new workflow additions (checkpoints 16.0–16.2).

### 2026-02-03 — Stage 15: Skill Subscription (completed)

Defined skill source/trust docs, added subscription + lockfile support, and implemented sync/upgrade behavior for subscribed skills (checkpoints 15.0–15.2).

### 2026-02-03 — Stage 14: Skill Sets (completed)

Defined skill set schema and examples, added resolution in skillctl with dependency trees, and enabled bootstrap installation + config recording for skillsets (checkpoints 14.0–14.2).

### 2026-02-03 — Stage 13: Skill Library Foundation (completed)

Defined skill manifest schema with examples, added skill discovery registry, and introduced a skill management CLI integrated with bootstrap installs (checkpoints 13.0–13.2).

### 2026-02-02 — Stage 13A: SKIP Marker Support (completed)

Added `(SKIP)` marker handling in agentctl, added skip marker tests, and documented SKIP semantics and consolidation preservation for deferred stages/checkpoints (checkpoints 13A.0–13A.2).

### 2026-01-29 — Stage 12: Global vs Repo-Local Separation (completed)

Established clear boundaries between global and repo-local resources, implemented a resource resolver, and updated core tools to use it, enabling skill reuse with project customization. This included checkpoints 12.0, 12.1, and 12.2.

### 2026-01-30 — Stage 12A: Priority stage insertion (completed)

Defined suffix-based stage ordering, updated agent selection/validation logic, and added tests to lock in ordering behavior. This included checkpoints 12A.0 through 12A.3.

### 2026-01-29 ?" Stage 11: Checkpoint Templates (completed)

Enabled reusable checkpoint patterns for common tasks, reducing boilerplate and ensuring consistency. This included a template schema, a core library of templates, and integration with `agentctl` for direct insertion into `PLAN.md`.

### 2026-01-29 — Stage 10: Context snapshots (completed)

Added a context snapshot schema plus capture and restoration flow so runs can be resumed with consistent project context.

### 2026-01-29 — Stage 9: Automated quality gates (completed)

Added a quality gate schema, implemented gate execution in agentctl, and provided reusable gate templates.

### 2026-01-28 — Stage 8: End to end workflow hardening (completed)

Hardened stage transitions and consolidation behavior and added a cross agent workflow test suite to catch regressions.

### 2026-01-28 — Stage 7: Self hosted agent support (completed)

Added a generic bootstrap and configuration guidance for self hosted agents and recorded any skipped verifications due to lack of access.

### 2026-01-28 — Stage 6: Multi agent continuous mode verification (completed)

Verified continuous mode operation across multiple agents and documented partial support and workarounds where full automation is not available.

### 2026-01-28 — Stage 5: Expansion readiness (completed)

Established skill lifecycle and compatibility policies and added repo level schema fields to support future expansion without breaking workflow contracts.

### 2026-01-28 — Stage 4: Base Vibe skills stabilized (completed)

Defined the base skill surface and published agent skill pack documentation to standardize usage across supported agents.

### 2026-01-28 — Stage 3: Continuous mode and dispatcher parity (completed)

Defined continuous mode semantics and provided reference and adaptation guidance so agents can execute multi loop runs with minimal manual intervention.

### 2026-01-28 — Stage 2: Cross agent parity for core Vibe workflow (completed)

Documented agent capability constraints and unified bootstrap prompts so multiple agents can run the same core loop with consistent expectations.

### 2026-01-27 — Stage 1: Prompt catalog and agent control plane (completed)

Introduced stable prompt IDs with a shared catalog and updated agent control tooling to deterministically recommend the next prompt from `.vibe` state.

### 2026-01-26 ?" Stage 0: Repo scaffold and bootstrap foundations (completed)

---

## Archived details (checkpoint level)

### Work log (archived)

- 2026-02-06 — Pruned STATE work log from 32 to 10 entries (2026-02-03 through 2026-02-05 entries covering Stages 19/19A/20.0 implementation, review, and issue resolution).
- 2026-02-02 — Pruned older STATE work log entries from 2026-01-29 through 2026-02-02 during Stage 13A consolidation.

### Resolved issues (archived)

- 2026-02-05 — ISSUE-011: Added installable `vibe-one-loop` and `vibe-run` skills; updated bootstrap + skillset + docs for consistent Codex loop/continuous surface.
- 2026-02-05 — ISSUE-010: Added `vibe-loop` manifest front matter, global install refresh for manifests, and UNC-style `CODEX_HOME` normalization to restore cross-repo skill visibility.
- 2026-02-03 — ISSUE-008: Stage 19A injected to host RAG scanner work; scope/location clarified.
- 2026-02-03 — ISSUE-007: Normalized Stage 19 checkpoint headings so agentctl recognizes 19.1/19.2.
- 2026-02-03 — ISSUE-006: Consolidation prompt updated to preserve future stages in PLAN.md backlog.
- 2026-02-03 — ISSUE-008: JIT inserted Stage 13 to provide skillctl before Stage 14; blocker cleared.
- 2026-02-02 — ISSUE-007: Pytest capture failures resolved by using `--capture=sys` for demo commands.
- 2026-01-26 — ISSUE-BOOT-001: Declared `.vibe/` as the only authoritative workflow location and removed fallback logic.
- 2026-01-27 — ISSUE-001: Updated `vibe_next_and_print.py` to respect CODEX_HOME aware skills roots.
- 2026-01-28 — ISSUE-001: Fixed stage sync and transition detection in agentctl and improved heading parsing robustness.
- 2026-01-30 — ISSUE-002: Fixed bootstrap `init-repo --overwrite` to use canonical templates, byte-for-byte overwrite, logging, and regression test.
- 2026-01-30 — ISSUE-003: Removed duplicate prompt catalog and enforced canonical `prompts/template_prompts.md` validation plus resolver fix.

### Stage 12A — Priority stage insertion (archived plan)

## Stage 12A — Priority stage insertion (no renumbering)

**Stage objective:**
Allow inserting a stage “between” existing numbered stages (e.g., 12A between 12 and 13) without renumbering, and ensure the dispatcher prioritizes it (after BLOCKER issues).

### 12A.0 — Stage ID scheme and ordering semantics

* **Objective:**
  Define a deterministic stage identifier scheme that supports insertions (e.g., `12A`, `12B`) and document ordering rules.
* **Deliverables:**
  * `docs/stage_ordering.md` — stage ID format + ordering rules + examples
  * Stage ID grammar: `<int><optional alpha suffix>` (examples: `12`, `12A`, `12B`, `13`)
  * Ordering definition: numeric first, then suffix (empty suffix sorts before A/B/…)
* **Acceptance:**
  * A human can add `Stage 12A` to PLAN.md and it will be treated as between 12 and 13
  * Ordering rules are unambiguous and testable
* **Demo commands:**
  * `cat docs/stage_ordering.md`
* **Evidence:**
  * Example ordering list (e.g., `11, 12, 12A, 12B, 13`)

---

### 12A.1 — Control plane support (dispatcher + agentctl)

* **Objective:**
  Ensure all “choose next work” code respects stage ordering and picks inserted stages before later numbered stages, while still prioritizing BLOCKER issues above all stages.
* **Deliverables:**
  * Update `tools/agentctl.py` stage selection logic to use the new stage ordering key
  * Update `tools/vibe_next_and_print.py` to use the same ordering function/key
  * Single shared stage ordering implementation (one module/function) used by both
* **Acceptance:**
  * With Stage 12 complete and Stage 12A present and NOT_STARTED, `agentctl next` chooses 12A before 13
  * With any BLOCKER issue present, dispatcher chooses issues/triage before any stage, including 12A
  * `agentctl next` and `vibe_next_and_print.py` agree on the recommendation
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . next`
  * `python tools/vibe_next_and_print.py --repo-root .`
* **Evidence:**
  * Matching output from both tools showing 12A selected

---

### 12A.2 — Validation and fail-fast rules for stage IDs

* **Objective:**
  Fail fast on invalid stage IDs and ensure STATE/PLAN consistency still holds with suffix stages.
* **Deliverables:**
  * Validation update: stage pointer in `.vibe/STATE.md` must match an existing PLAN stage ID (including suffix IDs like `12A`)
  * Validation update: detect duplicate stage IDs and malformed IDs
  * Clear error messages identifying file + offending line
* **Acceptance:**
  * Invalid IDs (e.g., `Stage PRE13`, `Stage 12-1`, `Stage 12.A`) fail validation with actionable errors
  * Valid suffix IDs pass validation and are selectable
* **Demo commands:**
  * `python tools/agentctl.py --repo-root . validate`
* **Evidence:**
  * Example validation error output showing file + line

---

### 12A.3 — Regression tests for ordering and selection

* **Objective:**
  Lock in deterministic behavior across future refactors.
* **Deliverables:**
  * Unit tests for stage ID parsing + ordering
  * Integration test ensuring `agentctl next` prefers `12A` over `13` when `12` is complete
  * Integration test ensuring BLOCKER issues override stage ordering
* **Acceptance:**
  * Tests fail if ordering regresses or tools disagree
* **Demo commands:**
  * `<your test runner command>`
* **Evidence:**
  * Passing test output

### Archived backlog — Stages 16-20

## Stage 16 — Configurable Workflows

**Stage objective:**
Move workflow logic from hard-coded prompts to configurable definitions, enabling custom loop ordering, triggers, and frequency.

### 16.0 — Workflow definition schema

* **Objective:**
  Define how workflows are expressed in configuration.

* **Deliverables:**

  * `docs/workflow_schema.md` — workflow configuration format
  * Schema: triggers, steps, conditions, frequency
  * Trigger types: manual, on-status, on-issue, scheduled

* **Acceptance:**

  * Schema can express: "run refactor every 3rd checkpoint", "auto-triage on BLOCKER"
  * Workflows reference prompts by ID

* **Demo commands:**

  * `cat docs/workflow_schema.md`

* **Evidence:**

  * Example workflow definitions

---

### 16.1 — Workflow engine

* **Objective:**
  Implement a workflow engine that executes configured workflows.

* **Deliverables:**

  * `tools/workflow_engine.py` — interprets and executes workflows
  * Integration with agentctl: `--workflow <name>` flag
  * Workflow state tracking in STATE.md

* **Acceptance:**

  * Engine can execute multi-step workflows
  * Conditions and triggers evaluated correctly

* **Demo commands:**

  * `python tools/workflow_engine.py run refactor-cycle`
  * `python tools/agentctl.py --repo-root . next --workflow auto-triage`

* **Evidence:**

  * Workflow execution trace

---

### 16.2 — Preset workflows

* **Objective:**
  Provide useful preset workflow configurations.

* **Deliverables:**

  * `workflows/standard.yaml` — default Vibe workflow (design→implement→review)
  * `workflows/continuous-refactor.yaml` — periodic refactoring
  * `workflows/auto-triage.yaml` — triggered on issues

* **Acceptance:**

  * Presets work out of the box
  * Users can copy and customize

* **Demo commands:**

  * `python tools/workflow_engine.py list`
  * `python tools/workflow_engine.py describe continuous-refactor`

* **Evidence:**

  * Preset workflow executing successfully

---

## Stage 17 — Design-Side Prompts

**Stage objective:**
Add prompts for upstream planning phases, enabling structured conversations that generate ideas, architecture, milestones, and checkpoints.

### 17.0 — Ideation and feature prompts

* **Objective:**
  Create prompts for early-stage idea development.

* **Deliverables:**

  * `prompt.ideation` — brainstorm features from a problem statement
  * `prompt.feature_breakdown` — decompose a feature into sub-features
  * Output format: structured feature list with priorities

* **Acceptance:**

  * Prompts produce actionable feature lists
  * Output can feed into architecture prompts

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.ideation`

* **Evidence:**

  * Example ideation output

---

### 17.1 — Architecture and milestone prompts

* **Objective:**
  Create prompts for architecture and milestone planning.

* **Deliverables:**

  * `prompt.architecture` — design system architecture from features
  * `prompt.milestones` — break architecture into major milestones
  * Output: architecture doc, milestone list with dependencies

* **Acceptance:**

  * Architecture prompt produces component diagrams / descriptions
  * Milestones are sequenced logically

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.architecture`

* **Evidence:**

  * Example architecture → milestones flow

---

### 17.2 — Stage and checkpoint generation

* **Objective:**
  Create prompts that generate PLAN.md content from milestones.

* **Deliverables:**

  * `prompt.stages_from_milestones` — convert milestones to stages
  * `prompt.checkpoints_from_stage` — break stage into checkpoints
  * Output: valid PLAN.md sections

* **Acceptance:**

  * Generated checkpoints follow schema (objective, deliverables, acceptance, demo, evidence)
  * Output can be pasted directly into PLAN.md

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.stages_from_milestones`

* **Evidence:**

  * Generated PLAN.md section from milestone input

---

## Stage 18 — Templated Prompts Expansion

**Stage objective:**
Add specialized prompts for common development phases: refactoring, testing, and human feedback loops.

### 18.0 — Refactoring prompts

* **Objective:**
  Create prompts for systematic refactoring.

* **Deliverables:**

  * `prompt.refactor_scan` — identify refactoring opportunities
  * `prompt.refactor_execute` — perform a specific refactoring
  * `prompt.refactor_verify` — verify refactoring didn't break anything

* **Acceptance:**

  * Scan produces prioritized refactoring list
  * Execute/verify form a safe refactoring loop

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.refactor_scan`

* **Evidence:**

  * Refactoring cycle example

---

### 18.1 — Testing and coverage prompts

* **Objective:**
  Create prompts for test generation and coverage improvement.

* **Deliverables:**

  * `prompt.test_gap_analysis` — identify untested code paths
  * `prompt.test_generation` — generate tests for specific functions
  * `prompt.test_review` — review test quality and coverage

* **Acceptance:**

  * Gap analysis produces actionable list
  * Generated tests are runnable and meaningful

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.test_gap_analysis`

* **Evidence:**

  * Test generation example

---

### 18.2 — Human feedback prompts

* **Objective:**
  Create prompts for human-in-the-loop testing and feedback.

* **Deliverables:**

  * `prompt.demo_script` — generate demo script for human testing
  * `prompt.feedback_intake` — structured feedback collection
  * `prompt.feedback_triage` — convert feedback to issues/checkpoints

* **Acceptance:**

  * Demo script is executable by non-technical users
  * Feedback converts to actionable items

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.feedback_intake`

* **Evidence:**

  * Feedback → checkpoint flow example

---

## Stage 19 — Multi-Directory RAG Skill

**Stage objective:**
Create a reusable skill that scans directories, builds a searchable index, and supports retrieval-augmented prompting.

### 19.0 — Directory scanner

* **Objective:**
  Build a scanner that indexes multiple directories.

* **Deliverables:**

  * `.codex/skills/rag-index/scanner.py` — recursive directory scanner
  * Configurable: include/exclude patterns, file types, depth
  * Output: file manifest with metadata (path, size, mtime, type)

* **Acceptance:**

  * Scans multiple directories in one pass
  * Respects gitignore and custom exclusions

* **Demo commands:**

  * `python .codex/skills/rag-index/scanner.py /path/to/code --output manifest.json`

* **Evidence:**

  * Manifest output for sample directory

---

### 19.1 — Index builder

* **Objective:**
  Build a searchable index from scanned files.

* **Deliverables:**

  * `.codex/skills/rag-index/indexer.py` — builds embeddings/keyword index
  * Supports: full-text search, semantic search (with embeddings)
  * Storage: local SQLite or JSON for portability

* **Acceptance:**

  * Index is persistent and incremental (only re-index changed files)
  * Search returns ranked results

* **Demo commands:**

  * `python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db`
  * `python .codex/skills/rag-index/indexer.py search \"authentication\" --index index.db`

* **Evidence:**

  * Search results for sample query

---

### 19.2 — RAG retriever and skill packaging

* **Objective:**
  Package the RAG capability as a reusable skill.

* **Deliverables:**

* `.codex/skills/rag-index/SKILL.md` — skill manifest
  * `.codex/skills/rag-index/retrieve.py` — retrieval interface for agents
  * Integration: agents can call retriever to augment prompts

* **Acceptance:**

  * Skill installs via skillctl
  * Retriever returns context snippets suitable for prompt injection

* **Demo commands:**

* `python tools/skillctl.py install rag-index --global`
  * `python .codex/skills/rag-index/retrieve.py \"how does auth work\" --top-k 5`

* **Evidence:**

  * Retrieved context snippets

---

## Stage 20 — RLM (Recursive Language Model) Tools Skill

**Stage objective:**
Implement bounded recursive tool use based on RLM principles, enabling explicit, controlled agent recursion.

### 20.0 — RLM schema and limits

* **Objective:**
  Define the schema for recursive tool invocations with explicit bounds.

* **Deliverables:**

  * `docs/rlm_schema.md` — RLM invocation format and limits
  * Limit types: max depth, max iterations, timeout, token budget
  * Based on: [RLM paper](https://arxiv.org/pdf/2512.24601)

* **Acceptance:**

  * Schema prevents unbounded recursion
  * Limits are configurable per invocation

* **Demo commands:**

  * `cat docs/rlm_schema.md`

* **Evidence:**

  * Example RLM invocation with limits

---

### 20.1 — RLM executor

* **Objective:**
  Implement an executor that runs RLM invocations within bounds.

* **Deliverables:**

  * `skills/rlm-tools/executor.py` — RLM execution engine
  * Tracks: depth, iterations, tokens consumed
  * Halts on limit breach with clear error

* **Acceptance:**

  * Executor respects all configured limits
  * Partial results returned on limit breach

* **Demo commands:**

  * `python skills/rlm-tools/executor.py run task.json --max-depth 3`

* **Evidence:**

  * Execution trace showing recursion and limits

---

### 20.2 — RLM skill packaging

* **Objective:**
  Package RLM as a skill that agents can invoke.

* **Deliverables:**

  * `skills/rlm-tools/SKILL.yaml` — skill manifest
  * Agent integration: prompt templates for RLM invocation
  * Safety: default conservative limits

* **Acceptance:**

  * Skill installs via skillctl
  * Agents can delegate sub-tasks with bounded recursion

* **Demo commands:**

  * `python tools/skillctl.py install skills/rlm-tools --global`
  * `python skills/rlm-tools/invoke.py \"research and summarize X\" --max-depth 2`

* **Evidence:**

  * RLM task completing within bounds

### Archived backlog — Stage 19

## Stage 19 — Templated Prompts Expansion

### Global conventions for Stage 19 prompts

Add these shared constraints into each prompt:

* **Repo safety**

  * Do not create, switch, or delete branches unless explicitly instructed.
  * Prefer small commits with clear messages; do not leave uncommitted changes.
* **Execution discipline**

  * Always run a _minimal_ verification after edits (unit tests, lint, typecheck, or at least import/compile).
  * If verification fails, revert or fix before proceeding.
* **Evidence contract**

  * Each prompt must end with a short “Evidence” section listing commands run + key outputs/paths.

Also standardize response format for all Stage 19 prompts:

* `## Goal`
* `## Inputs`
* `## Plan`
* `## Actions`
* `## Results`
* `## Evidence`
* `## Next safe step`

This reduces variance across agents.

---

### 19.0 — Refactoring prompts

### `prompt.refactor_scan`

**Objective:** produce a prioritized refactor backlog _with justifications and scope bounds_.

**Inputs expected in the prompt text**

* Target scope: path(s) or module(s)
* Constraints: “no behavior change” vs “allowed behavior changes”
* Tooling: linter/typechecker/test runner commands (or “unknown”)

**Required output structure**

1. **Top findings (max 10)** with:

   * _Impact_ (perf/maintainability/safety)
   * _Risk_ (low/med/high)
   * _Effort_ (S/M/L)
   * _Proposed checkpoints_ (atomic steps)
2. **Refactor plan**: ordered checkpoints, each with:

   * “What I will change”
   * “How I will prove equivalence”
   * “Rollback plan”
3. **Selection recommendation**: pick 1–2 best refactors to do first.

**Guardrails**

* Must not propose cross-cutting “rewrite” unless explicitly requested.
* Must identify “tests missing” as a risk and recommend targeted tests first.

**Suggested template text (core directives)**

* “Scan for: duplication, high cyclomatic complexity, unclear boundaries, hidden global state, error-handling inconsistencies, IO mixed with business logic, and missing tests around changed code.”
* “Prefer refactors that can be proven with existing tests or add minimal tests first.”

---

### `prompt.refactor_execute`

**Objective:** apply a single refactor checkpoint safely.

**Inputs**

* One checkpoint from scan output (must be pasted verbatim)
* File/module list
* “Definition of done” (behavioral invariants)
* Verification commands

**Required output**

* Exact file edits summary (files touched, intent per file)
* Any new tests added (and why minimal)
* Commands run + pass/fail
* If fail: either fix or revert, and state which

**Guardrails**

* If checkpoint implies multiple changes, must split into smaller sub-checkpoints.
* No branch creation.

**Key instruction**

* “Stop after completing the checkpoint + verification; do not proceed to the next checkpoint unless asked.”

---

### `prompt.refactor_verify`

**Objective:** confirm refactor didn’t change behavior and didn’t worsen quality.

**Inputs**

* Commit hash or diff summary
* Verification commands
* Performance constraints (if any)

**Required output**

* Pass/fail matrix: tests/lint/typecheck/build
* Risk callouts: what remains unverified and why
* “If this regresses in prod, likely failure modes are …” (max 3)
* Optional: micro-benchmark suggestion (only if relevant)

---

### 19.1 — Testing and coverage prompts

### `prompt.test_gap_analysis`

**Objective:** identify untested paths _tied to actual risk_.

**Inputs**

* Target files/functions/classes
* Test framework + runner command
* Coverage tool command (if available)
* “Allowed to change production code?” (yes/no)

**Required output**

* A table-like list of **test gaps** with:

  * Scenario
  * Code location
  * Why it matters (bug class / regression risk)
  * Proposed test type (unit/integration/property)
  * Minimal fixture strategy
* If coverage tooling exists: include “coverage delta target” (e.g., +X lines / +Y branches) but avoid vanity targets.

**Guardrails**

* If framework/runner unknown: output a “discovery step” first (inspect repo config) then propose gaps.

---

### `prompt.test_generation`

**Objective:** generate runnable tests for _one_ gap.

**Inputs**

* One gap item (pasted verbatim)
* Target function signature(s)
* Existing test patterns (paths/naming) if known

**Required output**

* Exact test file path(s) and test names
* Rationale for assertions (what regression would be caught)
* Any needed fakes/mocks and why
* Commands run

**Guardrails**

* Must follow existing repo conventions (fixtures, snapshot style, etc.)
* Avoid overspecifying behavior; assert stable contracts.

---

### `prompt.test_review`

**Objective:** review tests for signal/noise and maintainability.

**Inputs**

* Diff (or list of test files added/changed)
* What the tests are supposed to validate

**Required output**

* “Good coverage” points (what’s solid)
* “Brittleness” points (what will break unnecessarily)
* Concrete edits to improve (rename, reduce mocking, better assertions)
* Must mention whether tests verify outcomes vs implementation details

---

### 19.2 — Human feedback prompts

### `prompt.demo_script`

**Objective:** produce a non-technical validation script.

**Inputs**

* Feature/change summary
* Target persona (developer, QA, end-user)
* Platforms/OS constraints

**Required output**

* Step-by-step script with expected outcomes per step
* “If you see X, file feedback with Y info”
* A short “reset environment” section

**Guardrails**

* No jargon without a parenthetical definition.

---

### `prompt.feedback_intake`

**Objective:** collect structured feedback with minimal back-and-forth.

**Inputs**

* Product area/module
* Version/commit
* Reporter type (dev/QA/user)

**Required output**

* A copy-paste form with fields:

  * Summary
  * Expected vs actual
  * Repro steps
  * Frequency
  * Logs/screenshots pointers
  * Impact suggestion
  * Workaround (if any)

---

### `prompt.feedback_triage`

**Objective:** convert feedback into issues/checkpoints.

**Inputs**

* One or more completed intake forms
* Current PLAN stage naming rules (including PRE stages)

**Required output**

* Issue list with impact + owners
* Checkpoint proposals using standard template

### Archived backlog — Stage 17

## Stage 17 — Configurable Workflows

**Stage objective:**
Move workflow logic from hard-coded prompts to configurable definitions, enabling custom loop ordering, triggers, and frequency.

### 17.0 — Workflow definition schema

* **Objective:**
  Define how workflows are expressed in configuration.
* **Deliverables:**
  * `docs/workflow_schema.md` — workflow configuration format
  * Schema: triggers, steps, conditions, frequency
  * Trigger types: manual, on-status, on-issue, scheduled
* **Acceptance:**
  * Schema can express: "run refactor every 3rd checkpoint", "auto-triage on BLOCKER"
  * Workflows reference prompts by ID
* **Demo commands:**
  * `cat docs/workflow_schema.md`
* **Evidence:**
  * Example workflow definitions

---

### 17.1 — Workflow engine

* **Objective:**
  Implement a workflow engine that executes configured workflows.
* **Deliverables:**
  * `tools/workflow_engine.py` — interprets and executes workflows
  * Integration with agentctl: `--workflow <name>` flag
  * Workflow state tracking in STATE.md
* **Acceptance:**
  * Engine can execute multi-step workflows
  * Conditions and triggers evaluated correctly
* **Demo commands:**
  * `python tools/workflow_engine.py run refactor-cycle`
  * `python tools/agentctl.py --repo-root . next --workflow auto-triage`
* **Evidence:**
  * Workflow execution trace

---

### 17.2 — Preset workflows

* **Objective:**
  Provide useful preset workflow configurations.
* **Deliverables:**
  * `workflows/standard.yaml` — default Vibe workflow (design -> implement -> review)
  * `workflows/continuous-refactor.yaml` — periodic refactoring
  * `workflows/auto-triage.yaml` — triggered on issues
* **Acceptance:**
  * Presets work out of the box
  * Users can copy and customize
* **Demo commands:**
  * `python tools/workflow_engine.py list`
  * `python tools/workflow_engine.py describe continuous-refactor`
* **Evidence:**
  * Preset workflow executing successfully
