# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 15 — Skill Subscription

**Stage objective:**
Enable subscribing to skills from external repositories, with trust, pinning, and auto-update capabilities.

### 15.0 — Subscription sources

* **Objective:**
  Define how external skill sources are specified and trusted.

* **Deliverables:**

  * `docs/skill_sources.md` — source configuration and trust model
  * Source format: git URL, branch/tag, subdirectory path
  * Trust levels: verified, community, untrusted

* **Acceptance:**

  * Sources can be GitHub repos, git URLs, or local paths
  * Trust level affects installation warnings

* **Demo commands:**

  * `cat docs/skill_sources.md`

* **Evidence:**

  * Example source configuration

---

### 15.1 — Subscription and pinning

* **Objective:**
  Implement skill subscription with version pinning.

* **Deliverables:**

  * `skillctl.py` enhancement: `subscribe` command
  * Pin format: `source@version` or `source@commit`
  * Lock file: `.vibe/skill-lock.json`

* **Acceptance:**

  * `skillctl subscribe https://github.com/anthropics/skills skill-name`
  * Lock file records exact versions for reproducibility

* **Demo commands:**

  * `python tools/skillctl.py subscribe https://github.com/anthropics/skills claude-memory --pin v1.0.0`

* **Evidence:**

  * Lock file showing pinned subscription

---

### 15.2 — Subscription sync and update

* **Objective:**
  Enable syncing subscribed skills to latest (or pinned) versions.

* **Deliverables:**

  * `skillctl.py` enhancement: `sync` command
  * Respects pins, warns on major version changes
  * `--upgrade` flag to update pins

* **Acceptance:**

  * `skillctl sync` updates all subscribed skills
  * Breaking changes require explicit `--upgrade`

* **Demo commands:**

  * `python tools/skillctl.py sync`
  * `python tools/skillctl.py sync --upgrade`

* **Evidence:**

  * Sync output showing updates applied

---

## Stage 16 — Skill Subscription

**Stage objective:**
Enable subscribing to skills from external repositories, with trust, pinning, and auto-update capabilities.

### 16.0 — Subscription sources

* **Objective:**
  Define how external skill sources are specified and trusted.
* **Deliverables:**
  * `docs/skill_sources.md` — source configuration and trust model
  * Source format: git URL, branch/tag, subdirectory path
  * Trust levels: verified, community, untrusted
* **Acceptance:**
  * Sources can be GitHub repos, git URLs, or local paths
  * Trust level affects installation warnings
* **Demo commands:**
  * `cat docs/skill_sources.md`
* **Evidence:**
  * Example source configuration
---

### 16.1 — Subscription and pinning

* **Objective:**
  Implement skill subscription with version pinning.
* **Deliverables:**
  * `skillctl.py` enhancement: `subscribe` command
  * Pin format: `source@version` or `source@commit`
  * Lock file: `.vibe/skill-lock.json`
* **Acceptance:**
  * `skillctl subscribe https://github.com/anthropics/skills skill-name`
  * Lock file records exact versions for reproducibility
* **Demo commands:**
  * `python tools/skillctl.py subscribe https://github.com/anthropics/skills claude-memory --pin v1.0.0`
* **Evidence:**
  * Lock file showing pinned subscription
---

### 16.2 — Subscription sync and update

* **Objective:**
  Enable syncing subscribed skills to latest (or pinned) versions.
* **Deliverables:**
  * `skillctl.py` enhancement: `sync` command
  * Respects pins, warns on major version changes
  * `--upgrade` flag to update pins
* **Acceptance:**
  * `skillctl sync` updates all subscribed skills
  * Breaking changes require explicit `--upgrade`
* **Demo commands:**
  * `python tools/skillctl.py sync`
  * `python tools/skillctl.py sync --upgrade`
* **Evidence:**
  * Sync output showing updates applied
---

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

**Stage objective:**
Add specialized prompts for common development phases: refactoring, testing, and human feedback loops.

### 19.0 — Refactoring prompts

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

### 19.1 — Testing and coverage prompts

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

### 19.2 — Human feedback prompts

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

## Stage 20 — Multi-Directory RAG Skill

**Stage objective:**
Create a reusable skill that scans directories, builds a searchable index, and supports retrieval-augmented prompting.

### 20.0 — Directory scanner

* **Objective:**
  Build a scanner that indexes multiple directories.
* **Deliverables:**
  * `skills/rag-index/scanner.py` — recursive directory scanner
  * Configurable: include/exclude patterns, file types, depth
  * Output: file manifest with metadata (path, size, mtime, type)
* **Acceptance:**
  * Scans multiple directories in one pass
  * Respects gitignore and custom exclusions
* **Demo commands:**
  * `python skills/rag-index/scanner.py /path/to/code --output manifest.json`
* **Evidence:**
  * Manifest output for sample directory
---

### 20.1 — Index builder

* **Objective:**
  Build a searchable index from scanned files.
* **Deliverables:**
  * `skills/rag-index/indexer.py` — builds embeddings/keyword index
  * Supports: full-text search, semantic search (with embeddings)
  * Storage: local SQLite or JSON for portability
* **Acceptance:**
  * Index is persistent and incremental (only re-index changed files)
  * Search returns ranked results
* **Demo commands:**
  * `python skills/rag-index/indexer.py build --manifest manifest.json --output index.db`
  * `python skills/rag-index/indexer.py search "authentication" --index index.db`
* **Evidence:**
  * Search results for sample query
---

### 20.2 — RAG retriever and skill packaging

* **Objective:**
  Package the RAG capability as a reusable skill.
* **Deliverables:**
  * `skills/rag-index/SKILL.yaml` — skill manifest
  * `skills/rag-index/retrieve.py` — retrieval interface for agents
  * Integration: agents can call retriever to augment prompts
* **Acceptance:**
  * Skill installs via skillctl
  * Retriever returns context snippets suitable for prompt injection
* **Demo commands:**
  * `python tools/skillctl.py install skills/rag-index --global`
  * `python skills/rag-index/retrieve.py "how does auth work" --top-k 5`
* **Evidence:**
  * Retrieved context snippets
---

## Stage 21 — RLM (Recursive Language Model) Tools Skill

**Stage objective:**
Implement bounded recursive tool use based on RLM principles, enabling explicit, controlled agent recursion.

### 21.0 — RLM schema and limits

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
---
