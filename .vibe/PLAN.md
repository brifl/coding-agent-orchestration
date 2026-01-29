# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

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

  * `tests/workflow/test_agentctl.py` — unit tests for agentctl dispatcher logic
  * `tests/workflow/test_state_parsing.py` — tests for STATE.md parsing
  * `tests/workflow/conftest.py` — fixtures for temporary .vibe directories

* **Acceptance:**

  * Tests cover: state parsing, checkpoint advancement, stage transition detection, consolidation triggering
  * All tests pass with `python -m pytest tests/workflow/`

* **Demo commands:**

  * `python -m pytest tests/workflow/ -v`

* **Evidence:**

  * Paste pytest output showing all tests pass

---
