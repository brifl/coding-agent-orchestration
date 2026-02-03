# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 18 — Design-Side Prompts

**Stage objective:**
Add prompts for upstream planning phases, enabling structured conversations that generate ideas, architecture, milestones, and checkpoints.

### 18.0 — Ideation and feature prompts

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

### 18.1 — Architecture and milestone prompts

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

### 18.2 — Stage and checkpoint generation

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

## 19.0 — Refactoring prompts

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

## 19.1 — Testing and coverage prompts

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

## 19.2 — Human feedback prompts

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
  * Severity suggestion
  * Workaround (if any)

---

### `prompt.feedback_triage`

**Objective:** convert feedback into issues/checkpoints.

**Inputs**

* One or more completed intake forms
* Current PLAN stage naming rules (including PRE stages)

**Required output**

* Proposed `STATE.md` issue entries and/or checkpoints
* Severity, owner suggestion, and “what is needed to proceed”
* Identify whether it blocks current stage

---

## Stage 20 — Multi-Directory RAG Skill

Codex often fails here unless you pin down **chunking, indexing, and retrieval contract**.

### 20.0 — Directory scanner (more detail)

**Add deliverables**

* `scanner.py` must output a **stable manifest schema**:

  * `path`, `rel_path`, `sha256` (or content hash), `size`, `mtime`, `language`, `mime`, `ignored_reason?`
* Gitignore handling:

  * Must respect `.gitignore`, `.ignore`, and explicit excludes
  * Must allow `--no-gitignore` override

**Acceptance tests**

* Scanning same tree twice yields identical manifest ordering + same hashes (unless files changed)
* Exclusions are reported (count by reason)

---

### 20.1 — Index builder (more detail)

Treat this as two parallel indexes:

1. **Lexical index** (BM25-ish) for precision and cheap retrieval
2. **Vector index** for semantic recall

**Chunking contract**

* Deterministic chunking:

  * Markdown: split by headings then cap size
  * Code: split by symbols (functions/classes) where possible, else by lines
* Store:

  * `chunk_id`, `doc_id`, `start_line`, `end_line`, `text`, `token_estimate`, `hash`

**Incremental indexing**

* Skip unchanged chunks via `hash`
* Remove chunks for deleted files

**Storage**

* SQLite is usually easiest for portability + incremental updates:

  * tables: `docs`, `chunks`, `lex_terms` (or FTS5), `vectors` (if stored), `meta`

**Acceptance**

* Re-index after a one-line change only updates affected chunks
* Search returns:

  * `score`, `path`, `line range`, `snippet`, `chunk_id`

---

### 20.2 — Retriever and skill packaging (more detail)

**Retriever interface contract (CLI + library)**

* Input: `query`, optional `paths scope`, `top_k`, `mode={lex|sem|hybrid}`
* Output: **prompt-ready** snippets:

  * each snippet: header line with provenance + fenced content
  * enforce max total chars returned (e.g. `--max-context-chars`)

**Hybrid ranking**

* Combine normalized lexical + semantic scores
* Diversity: avoid returning 5 chunks from same file unless asked

**When-to-use guidance (critical for agent behavior)**

* Add a short policy blurb for agents:

  * Use RAG when:

    * question references repo-specific behavior
    * answer requires exact names/paths/config keys
    * agent is unsure and needs grounding
  * Don’t use RAG when:

    * purely generic knowledge
    * user already provided the relevant snippet

**Evidence requirement**

* Include example query showing lexical beats semantic (exact symbol) and vice versa.

---

---

## Stage 21 — RLM tooling (deferred)

### 21.1 — RLM executor

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

### 21.2 — RLM skill packaging

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
  * `python skills/rlm-tools/invoke.py "research and summarize X" --max-depth 2`
* **Evidence:**
  * RLM task completing within bounds
