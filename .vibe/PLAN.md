# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 5 — Expansion readiness (no new features yet)

**Stage objective:**
Prepare the system to safely grow **after** base parity is achieved.

### 5.0 — Skill lifecycle and compatibility policy

- **Objective:**
  Define how new skills will be added without breaking existing workflows.

- **Deliverables:**
  - Policy doc covering versioning, compatibility guarantees, deprecation rules
  - "No breaking changes" rule for base skills

- **Acceptance:**
  - Clear go/no-go criteria for new skills
  - Enforced via review checklist

- **Demo commands:**
  - `(manual)` review policy

- **Evidence:**
  - Paste policy excerpt

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

## Stage 6 — Multi-agent continuous mode verification

**Stage objective:**
Verify that continuous mode works correctly for all supported CLI agents (Claude Code, Gemini Code, Copilot) using the agentctl dispatcher.

### 6.0 — Claude Code CLI continuous mode

* **Objective:**
  Verify Claude Code CLI can run continuous mode using agentctl.

* **Deliverables:**

  * Test transcript showing Claude Code running multiple loops via agentctl
  * Any fixes needed to prompts or agentctl for Claude-specific edge cases

* **Acceptance:**

  * Claude Code can: invoke agentctl next, execute returned prompt, update STATE.md, loop until stop
  * No manual intervention required between loops

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . next --format json`
  * Claude Code executes the prompt and loops

* **Evidence:**

  * Transcript excerpt showing 2+ loop iterations

---

### 6.1 — Gemini Code continuous mode

* **Objective:**
  Verify Gemini Code can run continuous mode using agentctl.

* **Deliverables:**

  * Test transcript showing Gemini Code running multiple loops
  * Any fixes needed for Gemini-specific edge cases

* **Acceptance:**

  * Gemini Code can loop through checkpoints without manual intervention
  * Stage transitions handled correctly

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . next --format json`

* **Evidence:**

  * Transcript excerpt showing 2+ loop iterations

---

### 6.2 — Copilot continuous mode (partial)

* **Objective:**
  Document Copilot's continuous mode limitations and workarounds.

* **Deliverables:**

  * Updated capability docs for Copilot's partial continuous support
  * Workaround instructions for manual re-invocation pattern

* **Acceptance:**

  * Clear documentation of what works and what doesn't
  * User can follow instructions to achieve pseudo-continuous execution

* **Demo commands:**

  * (manual) follow documented workaround

* **Evidence:**

  * Paste workaround instructions

---

## Stage 7 — Self-hosted agent support

**Stage objective:**
Enable self-hosted agents (Kimi 2.5, IQuest Coder, etc.) to participate in the Vibe workflow.

### 7.0 — Generic agent bootstrap

* **Objective:**
  Create a generic bootstrap that works for any tool-enabled agent.

* **Deliverables:**

  * `prompts/init/generic_bootstrap.md` — agent-agnostic bootstrap
  * Configuration guide for self-hosted agents

* **Acceptance:**

  * Bootstrap works without agent-specific assumptions
  * Clear instructions for tool configuration requirements

* **Demo commands:**

  * (manual) paste bootstrap into self-hosted agent

* **Evidence:**

  * Paste bootstrap and configuration guide excerpt

---

### 7.1 — Kimi 2.5 verification

* **Objective:**
  Verify Kimi 2.5 can run the Vibe workflow when properly configured.

* **Deliverables:**

  * Test transcript showing Kimi 2.5 running loops
  * Any Kimi-specific configuration notes

* **Acceptance:**

  * Kimi 2.5 can complete at least one full checkpoint cycle
  * Overnight execution is stable (if applicable)

* **Demo commands:**

  * Run Kimi 2.5 with generic bootstrap

* **Evidence:**

  * Transcript or log excerpt

---

### 7.2 — IQuest Coder verification

* **Objective:**
  Verify IQuest Coder can run the Vibe workflow when properly configured.

* **Deliverables:**

  * Test transcript showing IQuest Coder running loops
  * Any IQuest-specific configuration notes

* **Acceptance:**

  * IQuest Coder can complete at least one full checkpoint cycle

* **Demo commands:**

  * Run IQuest Coder with generic bootstrap

* **Evidence:**

  * Transcript or log excerpt

---

## Stage 8 — End-to-end workflow hardening

**Stage objective:**
Fix remaining rough edges and ensure the workflow is robust across all agents.

### 8.0 — Consolidation automation

* **Objective:**
  Make consolidation trigger automatically at stage boundaries.

* **Deliverables:**

  * agentctl.py enhancement: recommend consolidation before stage transitions
  * Clear indication in dispatcher output when consolidation is needed

* **Acceptance:**

  * agentctl never recommends advancing to a new stage without consolidation first
  * Validation catches stage drift

* **Demo commands:**

  * `python tools/agentctl.py --repo-root . validate --strict`
  * `python tools/agentctl.py --repo-root . next --format json` (at stage boundary)

* **Evidence:**

  * Command output showing consolidation recommendation

---

### 8.1 — Cross-agent test suite

* **Objective:**
  Create a simple test harness to verify workflow correctness across agents.

* **Deliverables:**

  * Test scenarios in `tests/workflow/`
  * CI integration (optional)

* **Acceptance:**

  * Tests can be run manually for any agent
  * Clear pass/fail criteria

* **Demo commands:**

  * `python -m pytest tests/workflow/` (or manual equivalent)

* **Evidence:**

  * Test output showing all scenarios pass

---
