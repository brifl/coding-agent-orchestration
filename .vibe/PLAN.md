# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

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
