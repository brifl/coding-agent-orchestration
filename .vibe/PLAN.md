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

