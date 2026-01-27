# HISTORY

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Rules

- This file is **non-authoritative**.
- It exists to reduce cognitive load by summarizing completed work and resolved issues.
- Do not rely on this file for current decisions; always check `.vibe/STATE.md` and `.vibe/PLAN.md`.

---

## Completed checkpoints

### 2026-01-26 — Stage 0 / Checkpoint 0.0: Repo scaffold + baseline templates

- Established canonical repo structure for `coding-agent-orchestration`
- Introduced `.vibe/` as the single authoritative location for state/plan/history
- Created baseline templates:
  - `AGENTS.md` (execution contract)
  - `VIBE.md` (pointer doc)
  - `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md`
- Result: target repos can be bootstrapped with minimal, consistent structure

**Evidence pointer**
- Commit: `<initial-structure>`
- Demo: `python3 tools/bootstrap.py init-repo <repo>`

---

### 2026-01-26 — Stage 0 / Checkpoint 0.1: Bootstrap script (init-repo) idempotence

- Implemented `tools/bootstrap.py init-repo`
- Ensured:
  - `.vibe/` is created safely
  - `.vibe/` is added to `.gitignore` exactly once
  - existing repo files are never overwritten
- Verified idempotence by repeated runs

**Evidence pointer**
- Demo output showing “Created” then “Skipped” on subsequent runs

---

### 2026-01-27 — Stage 1 / Checkpoint 1.0: Prompt catalog with stable IDs

- Consolidated all workflow loops into `prompts/template_prompts.md`
- Added stable IDs (`prompt.*`) to enable deterministic lookup
- Introduced shared parser `tools/prompt_catalog.py`
- Updated `clipper.py` to use the shared catalog and stable IDs

**Evidence pointer**
- `python3 tools/prompt_catalog.py prompts/template_prompts.md list`
- `python3 tools/prompt_catalog.py prompts/template_prompts.md get prompt.onboarding`

---

### 2026-01-27 — Stage 1 / Checkpoint 1.1: `.vibe/`-aware agent control plane

- Reworked `tools/agentctl.py` to:
  - read `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md`
  - emit a deterministic `recommended_prompt_id`
  - support `status`, `next`, and `validate` commands
- Validated behavior on a bootstrapped repo

**Evidence pointer**
- `python3 tools/agentctl.py --repo-root . next --format json`

---

## Resolved issues

### 2026-01-26 — ISSUE-BOOT-001: Ambiguity between root and `.vibe` workflow files

- **Resolution:** Declared `.vibe/` as the only authoritative location and removed fallback logic.
- **Impact:** Simplified scripts, reduced agent ambiguity, and lowered cognitive overhead.

---

## Process notes

- 2026-01-26: Decided to keep workflow state out of version control by default (`.vibe/` in `.gitignore`).
- 2026-01-27: Adopted stable prompt IDs as the canonical interface between scripts, UI, and agent skills.
- 2026-01-27: Positioned Codex Agent Skills as the first-class integration point; other agents use thin adapters.
