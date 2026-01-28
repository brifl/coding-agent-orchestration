# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.

## Stage 2 — Cross-agent parity for core Vibe workflow

**Stage objective:**
All core Vibe functionality (bootstrap, loop execution, state transitions, stop conditions) works _consistently_ across Codex, Gemini, Claude Code, and Copilot, using the same conceptual model and prompt catalog.

### 2.0 — Agent capability matrix + constraints model

* **Objective:**
  Explicitly model what each agent can and cannot do so the same workflow can adapt without forking logic.

* **Deliverables:**

  * `docs/agent_capabilities.md` defining:

    * file editing support
    * command execution support
    * continuous vs single-loop viability
  * Internal capability map used by bootstraps (not code-executed yet)

* **Acceptance:**

  * Capabilities for Codex, Gemini, Claude Code, Copilot are clearly documented
  * No workflow assumptions contradict documented capabilities

* **Demo commands:**

  * (manual) open `docs/agent_capabilities.md`

* **Evidence:**

  * Paste the capability table

---

### 2.1 — Unified bootstrap prompts for all agents

* **Objective:**
  Ensure every supported agent can be dropped into a repo and correctly orient to the Vibe workflow without copy-paste confusion.

* **Deliverables:**

  * `prompts/init/codex_bootstrap.md`
  * `prompts/init/claude_bootstrap.md`
  * `prompts/init/gemini_bootstrap.md`
  * `prompts/init/copilot_bootstrap.md`
  * All reference the same conceptual steps:

    * read AGENTS.md
    * read `.vibe/STATE.md` and `.vibe/PLAN.md`
    * select or run next loop based on capability

* **Acceptance:**

  * Each bootstrap:

    * is ≤ 40 lines
    * does not embed workflow logic
    * does not contradict single-loop vs continuous semantics
  * Language differs only where agent capability requires it

* **Demo commands:**

  * (manual) paste each bootstrap into a fresh chat

* **Evidence:**

  * Paste each bootstrap header + first successful response snippet

---

### 2.2 — Core loop execution parity (single-loop)

* **Objective:**
  Verify that **Checkpoint Implementation, Review, Issues Triage, Consolidation, Advance** loops can be executed correctly by _all_ agents in single-loop mode.

* **Deliverables:**

  * Adjusted loop prompts (if needed) to remove Codex-only assumptions
  * Documented “manual execution fallback” for non-tool agents

* **Acceptance:**

  * Each agent can:

    * run exactly one loop
    * update `.vibe/STATE.md` correctly
    * stop cleanly
  * No agent requires special-cased prompts

* **Demo commands:**

  * (manual) run one loop per agent on the same repo

* **Evidence:**

  * Paste resulting `.vibe/STATE.md` diffs per agent

---

## Stage 3 — Continuous mode + dispatcher parity

**Stage objective:**
Continuous execution (`$vibe-run`) behaves identically across agents _where possible_, and degrades gracefully where not.

### 3.0 — Continuous-mode semantics finalized

* **Objective:**
  Lock down what “continuous run” means independently of agent.

* **Deliverables:**

  * Documented semantics:

    * when dispatcher is re-invoked
    * when execution stops
    * how BLOCKED and exhausted plans are handled
  * Updated `docs/concepts.md` section

* **Acceptance:**

  * Continuous mode definition is unambiguous
  * No loop prompt self-loops

* **Demo commands:**

  * (manual) review doc section

* **Evidence:**

  * Paste final semantics section

---

### 3.1 — Continuous run for Codex (reference implementation)

* **Objective:**
  Make Codex the reference implementation for continuous execution.

* **Deliverables:**

  * `skills/codex/vibe-run/SKILL.md`
  * Verified interaction with `agentctl next`

* **Acceptance:**

  * `$vibe-run` progresses through multiple checkpoints
  * Stops on plan exhaustion or BLOCKED

* **Demo commands:**

  * `$vibe-run` in a repo with ≥2 checkpoints

* **Evidence:**

  * Paste decision log excerpts + final STATE.md

---

### 3.2 — Continuous-mode adaptation for other agents

* **Objective:**
  Provide the best possible continuous experience for Gemini, Claude, and Copilot.

* **Deliverables:**

  * Clear guidance in bootstraps:

    * “pseudo-continuous” (manual re-invocation)
    * or delegated execution patterns
  * No new skills yet

* **Acceptance:**

  * Agents do not dead-loop or silently stop
  * User expectations are correctly set

* **Demo commands:**

  * (manual) simulate 2–3 loop progression per agent

* **Evidence:**

  * Short transcript excerpts

---

## Stage 4 — Base Vibe skills stabilized across all agents

**Stage objective:**
Declare the **Vibe base skill set “complete”** and frozen before expansion.

### 4.0 — Base skill surface defined

* **Objective:**
  Formally define what “base Vibe skills” include.

* **Deliverables:**

  * `docs/base_skills.md` listing:

    * vibe-prompts
    * vibe-loop
    * vibe-run
    * agentctl semantics
  * Compatibility guarantees per agent

* **Acceptance:**

  * No ambiguity about what is “core”
  * Future skills must layer on top

* **Demo commands:**

  * (manual) review doc

* **Evidence:**

  * Paste base skills list

---

### 4.1 — Publish base skills for all agents

* **Objective:**
  Make the same base Vibe functionality available to all supported agents in their native formats.

* **Deliverables:**

  * Codex skills (already present)
  * Claude / Gemini / Copilot equivalents:

    * instructions
    * prompt packs
    * invocation patterns

* **Acceptance:**

  * Same logical capabilities exist for all agents
  * Differences are explicitly documented

* **Demo commands:**

  * (manual) verify discovery/usage per agent

* **Evidence:**

  * Paste discovery screenshots or logs

---

## Stage 5 — Expansion readiness (no new features yet)

**Stage objective:**
Prepare the system to safely grow **after** base parity is achieved.

### 5.0 — Skill lifecycle and compatibility policy

* **Objective:**
  Define how new skills will be added without breaking existing workflows.

* **Deliverables:**

  * Policy doc covering:

    * versioning
    * compatibility guarantees
    * deprecation rules
  * “No breaking changes” rule for base skills

* **Acceptance:**

  * Clear go/no-go criteria for new skills
  * Enforced via review checklist

* **Demo commands:**

  * (manual) review policy

* **Evidence:**

  * Paste policy excerpt

---

### 5.1 — Repo-level skill readiness (no implementation yet)

* **Objective:**
  Prepare for repo-specific skill overlays without implementing them yet.

* **Deliverables:**

  * `.vibe/config.json` schema (draft)
  * Documentation of intended behavior

* **Acceptance:**

  * Schema supports future expansion
  * No runtime behavior changes yet

* **Demo commands:**

  * (manual) view schema

* **Evidence:**

  * Paste schema file

---
