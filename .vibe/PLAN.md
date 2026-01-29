# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 9 — Automated Quality Gates

**Stage objective:**
Enforce quality standards automatically before allowing checkpoints to advance to review, catching issues early and making reviews meaningful.

### 9.0 — Gate configuration schema

* **Objective:**
  Define a schema for specifying quality gates per checkpoint or globally.

* **Deliverables:**

  * `docs/quality_gates.md` — gate types, configuration, and examples
  * Schema addition to `.vibe/config.json` for gate definitions
  * Gate types: `test`, `lint`, `typecheck`, `custom`

* **Acceptance:**

  * Schema supports: command to run, pass/fail criteria, optional vs required gates
  * Documentation covers common use cases (pytest, ruff, mypy)

* **Demo commands:**

  * `cat docs/quality_gates.md`

* **Evidence:**

  * Example config with gates defined

---

### 9.1 — Gate execution in agentctl

* **Objective:**
  Integrate gate execution into the dispatcher before recommending IN_REVIEW.

* **Deliverables:**

  * `agentctl.py` enhancement: `--run-gates` flag for `next` command
  * Gate runner that executes configured checks
  * Clear pass/fail output with actionable errors

* **Acceptance:**

  * `agentctl next --run-gates` runs configured gates before recommending review
  * Failing gates block advancement and report which gate failed
  * Passing gates are logged in STATE.md evidence

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . next --run-gates --format json`

* **Evidence:**

  * Output showing gates executed and results

---

### 9.2 — Pre-built gate templates

* **Objective:**
  Provide ready-to-use gate configurations for common stacks.

* **Deliverables:**

  * `templates/gates/python.json` — pytest, ruff, mypy
  * `templates/gates/typescript.json` — vitest/jest, eslint, tsc
  * `templates/gates/minimal.json` — just syntax check

* **Acceptance:**

  * Templates can be copied into `.vibe/config.json` and work out of the box
  * Each template documents required dependencies

* **Demo commands:**

  * `python tools/bootstrap.py init-repo . --gates python`

* **Evidence:**

  * Show gate template applied and running

---

## Stage 10 — Context Snapshots

**Stage objective:**
Enable agents to capture and restore key context between sessions, improving continuity and reducing repeated discovery.

### 10.0 — Snapshot schema and storage

* **Objective:**
  Define what context to capture and how to store it.

* **Deliverables:**

  * `.vibe/CONTEXT.md` — structured context file (decisions, gotchas, key files)
  * Schema in `docs/context_schema.md`
  * Sections: Architecture, Key Decisions, Gotchas, Hot Files, Agent Notes

* **Acceptance:**

  * Schema is simple enough for agents to update incrementally
  * Clear separation between ephemeral (session) and persistent (project) context

* **Demo commands:**

  * `cat .vibe/CONTEXT.md`

* **Evidence:**

  * Example CONTEXT.md with realistic content

---

### 10.1 — Context capture prompt

* **Objective:**
  Add a prompt that captures context at session end or stage boundaries.

* **Deliverables:**

  * `prompt.context_capture` in template_prompts.md
  * Guidance on what to capture vs what to omit
  * Integration with consolidation prompt (optional context refresh)

* **Acceptance:**

  * Running the capture prompt produces useful CONTEXT.md updates
  * Context is concise (not a brain dump)

* **Demo commands:**

  * `python tools/prompt_catalog.py prompts/template_prompts.md get prompt.context_capture`

* **Evidence:**

  * Before/after CONTEXT.md showing captured insights

---

### 10.2 — Context restoration in bootstrap

* **Objective:**
  Include CONTEXT.md in agent bootstrap flow.

* **Deliverables:**

  * Update bootstrap prompts to read CONTEXT.md after STATE.md
  * agentctl `status` command includes context summary
  * Optional: `--with-context` flag for verbose context display

* **Acceptance:**

  * New sessions start with relevant context loaded
  * Agents don't re-discover known gotchas

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . status --with-context`

* **Evidence:**

  * Status output showing context summary

---

## Stage 11 — Checkpoint Templates

**Stage objective:**
Enable reusable checkpoint patterns for common tasks, reducing boilerplate and ensuring consistency.

### 11.0 — Template schema and catalog

* **Objective:**
  Define how checkpoint templates are structured and discovered.

* **Deliverables:**

  * `templates/checkpoints/` directory for template definitions
  * Schema: parameters, objective template, deliverables template, acceptance template
  * `docs/checkpoint_templates.md` — usage guide

* **Acceptance:**

  * Templates are parameterized (e.g., `{{endpoint_name}}`, `{{module_path}}`)
  * Templates can be listed and previewed

* **Demo commands:**

  * `python tools/checkpoint_templates.py list`
  * `python tools/checkpoint_templates.py preview add-endpoint --endpoint /users`

* **Evidence:**

  * List of available templates with descriptions

---

### 11.1 — Core template library

* **Objective:**
  Create templates for the most common checkpoint patterns.

* **Deliverables:**

  * `add-feature.yaml` — new feature with tests
  * `fix-bug.yaml` — bug fix with regression test
  * `refactor-module.yaml` — refactoring with before/after validation
  * `add-endpoint.yaml` — API endpoint with OpenAPI spec
  * `add-test-coverage.yaml` — increase test coverage for a module

* **Acceptance:**

  * Each template produces valid checkpoint YAML/MD
  * Templates include sensible default acceptance criteria

* **Demo commands:**

  * `python tools/checkpoint_templates.py instantiate fix-bug --issue ISSUE-123`

* **Evidence:**

  * Generated checkpoint content from template

---

### 11.2 — Template integration with PLAN.md

* **Objective:**
  Allow templates to be inserted directly into PLAN.md.

* **Deliverables:**

  * `agentctl add-checkpoint --template <name> --params ...` command
  * Automatic stage detection (add to current stage or create new)
  * Validation that inserted checkpoint follows schema

* **Acceptance:**

  * Templates can be added without manual editing
  * Inserted checkpoints pass `agentctl validate`

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . add-checkpoint --template add-feature --name "user-auth"`

* **Evidence:**

  * PLAN.md before and after template insertion

---

## Stage 12 — Global vs Repo-Local Separation

**Stage objective:**
Establish clear boundaries between global (user-level) and repo-local (project-level) resources, enabling skill reuse while allowing project customization.

### 12.0 — Separation architecture

* **Objective:**
  Define and document the global vs repo-local resource model.

* **Deliverables:**

  * `docs/resource_model.md` — where things live, precedence rules, discovery order
  * Clear definitions: global = `~/.<agent>/`, repo-local = `.vibe/`
  * Precedence: repo-local overrides global (explicit shadow)

* **Acceptance:**

  * Document covers: skills, prompts, config, state
  * Git-ignore strategy documented (`.vibe/` ignored, global not in repo)

* **Demo commands:**

  * `cat docs/resource_model.md`

* **Evidence:**

  * Architecture diagram or table showing resource locations

---

### 12.1 — Discovery and resolution

* **Objective:**
  Implement resource discovery that respects precedence.

* **Deliverables:**

  * `tools/resource_resolver.py` — finds resources by name across locations
  * Resolution order: repo-local → global → built-in
  * Clear error messages when resource not found

* **Acceptance:**

  * Resolver finds skills/prompts from correct location
  * Shadowing works (repo-local skill overrides global)

* **Demo commands:**

  * `python tools/resource_resolver.py skill vibe-loop --show-path`
  * `python tools/resource_resolver.py prompt prompt.consolidation --show-path`

* **Evidence:**

  * Output showing resolution from different locations

---

### 12.2 — Bootstrap and agentctl integration

* **Objective:**
  Update bootstrap and agentctl to use the resource resolver.

* **Deliverables:**

  * `bootstrap.py` uses resolver for skill installation
  * `agentctl.py` uses resolver for prompt lookup
  * `--global` and `--local` flags where disambiguation needed

* **Acceptance:**

  * Existing functionality preserved
  * New resolution logic is transparent to users

* **Demo commands:**

  * `python tools/bootstrap.py install-skills --global --agent claude`
  * `python tools/agentctl.py --repo-root . next` (uses resolved prompts)

* **Evidence:**

  * Before/after showing same behavior with new resolver

---

## Stage 13 — Skill Library Foundation

**Stage objective:**
Treat skills as first-class, reusable artifacts with proper metadata, discovery, and management.

### 13.0 — Skill manifest schema

* **Objective:**
  Define a standard manifest format for skills.

* **Deliverables:**

  * `docs/skill_manifest.md` — schema documentation
  * `SKILL.yaml` or `SKILL.json` manifest format
  * Fields: name, version, description, agents, dependencies, entry points

* **Acceptance:**

  * Schema supports: multi-agent compatibility, version constraints, capability requirements
  * Existing skills can be migrated to new format

* **Demo commands:**

  * `cat skills/vibe-loop/SKILL.yaml`

* **Evidence:**

  * Example manifest with all fields populated

---

### 13.1 — Skill discovery and registry

* **Objective:**
  Enable programmatic skill discovery and listing.

* **Deliverables:**

  * `tools/skill_registry.py` — discovers and indexes available skills
  * Scans: global, repo-local, built-in locations
  * Caching for performance

* **Acceptance:**

  * `skill_registry.py list` shows all available skills with metadata
  * `skill_registry.py info <name>` shows detailed skill info

* **Demo commands:**

  * `python tools/skill_registry.py list --format json`
  * `python tools/skill_registry.py info vibe-loop`

* **Evidence:**

  * List output showing skills from multiple sources

---

### 13.2 — Skill CLI and management

* **Objective:**
  Provide a unified CLI for skill management.

* **Deliverables:**

  * `tools/skillctl.py` — skill management commands
  * Commands: list, info, install, uninstall, update, validate
  * Integration with bootstrap.py (skillctl as the backend)

* **Acceptance:**

  * All skill operations go through skillctl
  * Consistent UX across install/update/remove

* **Demo commands:**

  * `python tools/skillctl.py list`
  * `python tools/skillctl.py install vibe-prompts --global`
  * `python tools/skillctl.py validate skills/vibe-loop`

* **Evidence:**

  * Full skill lifecycle demo (install, use, update, uninstall)

---

## Stage 14 — Skill Sets

**Stage objective:**
Enable named collections of skills that can be deployed together, simplifying configuration and ensuring compatibility.

### 14.0 — Skill set schema

* **Objective:**
  Define how skill sets are structured and stored.

* **Deliverables:**

  * `docs/skill_sets.md` — schema and usage documentation
  * `skillsets/` directory for set definitions
  * Set format: name, description, skills list, version constraints

* **Acceptance:**

  * Sets can reference skills by name with optional version pins
  * Sets can extend other sets (inheritance)

* **Demo commands:**

  * `cat skillsets/vibe-core.yaml`

* **Evidence:**

  * Example skill set with multiple skills

---

### 14.1 — Skill set resolution

* **Objective:**
  Resolve skill sets to concrete skill lists.

* **Deliverables:**

  * `skillctl.py` enhancement: `resolve-set` command
  * Dependency resolution (skill A requires skill B)
  * Conflict detection (incompatible versions)

* **Acceptance:**

  * `skillctl resolve-set vibe-core` outputs resolved skill list
  * Circular dependencies detected and reported

* **Demo commands:**

  * `python tools/skillctl.py resolve-set vibe-core --format json`

* **Evidence:**

  * Resolution output with dependency tree

---

### 14.2 — Bootstrap with skill sets

* **Objective:**
  Enable bootstrapping with a skill set reference.

* **Deliverables:**

  * `bootstrap.py` enhancement: `--skillset <name>` flag
  * Auto-install all skills in set
  * Record set reference in `.vibe/config.json`

* **Acceptance:**

  * `bootstrap.py init-repo . --skillset vibe-core` installs all vibe-core skills
  * Config records which set was used

* **Demo commands:**

  * `python tools/bootstrap.py init-repo /tmp/test --skillset vibe-core`

* **Evidence:**

  * New repo with all skills from set installed

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

### 19.1 — Index builder

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

### 19.2 — RAG retriever and skill packaging

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
  * `python skills/rlm-tools/invoke.py "research and summarize X" --max-depth 2`

* **Evidence:**

  * RLM task completing within bounds

---
