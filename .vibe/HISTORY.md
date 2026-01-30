# HISTORY

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Rules

- This file is **non-authoritative**. It is to provide context on what has been done already.
- It exists to reduce cognitive load by summarizing completed work and resolved issues.
- Do not rely on this file for current decisions; always check `.vibe/STATE.md` and `.vibe/PLAN.md`.
- When writing to this, keep summaries limited to one or two sentences for the stage/decision/issue.

---

## Completed stages

### 2026-01-29 — Stage 12: Global vs Repo-Local Separation (completed)

Established clear boundaries between global and repo-local resources, implemented a resource resolver, and updated core tools to use it, enabling skill reuse with project customization. This included checkpoints 12.0, 12.1, and 12.2.

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

### Resolved issues (archived)

- 2026-01-26 — ISSUE-BOOT-001: Declared `.vibe/` as the only authoritative workflow location and removed fallback logic.
- 2026-01-27 — ISSUE-001: Updated `vibe_next_and_print.py` to respect CODEX_HOME aware skills roots.
- 2026-01-28 — ISSUE-001: Fixed stage sync and transition detection in agentctl and improved heading parsing robustness.
- 2026-01-30 — ISSUE-002: Fixed bootstrap `init-repo --overwrite` to use canonical templates, byte-for-byte overwrite, logging, and regression test.
- 2026-01-30 — ISSUE-003: Removed duplicate prompt catalog and enforced canonical `prompts/template_prompts.md` validation plus resolver fix.
