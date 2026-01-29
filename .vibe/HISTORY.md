# HISTORY

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Rules

- This file is **non-authoritative**.
- It exists to reduce cognitive load by summarizing completed work and resolved issues.
- Do not rely on this file for current decisions; always check `.vibe/STATE.md` and `.vibe/PLAN.md`.

---

## Completed stages

### 2026-01-28 — Stage 2: Cross-agent parity for core Vibe workflow (completed)

- **2.0**: Agent capability matrix + constraints model — documented capabilities for Codex, Claude, Gemini, Copilot
- **2.1**: Unified bootstrap prompts for all agents — created bootstrap prompts in `prompts/init/`
- **2.2**: Core loop execution parity (single-loop) — verified all agents can run single loops, documented manual fallback

### 2026-01-28 — Stage 3: Continuous mode + dispatcher parity (completed)

- **3.0**: Continuous-mode semantics finalized — documented in `docs/concepts.md`
- **3.1**: Continuous run for Codex (reference implementation) — verified `$vibe-run` skill
- **3.2**: Continuous-mode adaptation for other agents — added pseudo-continuous guidance to bootstraps

### 2026-01-28 — Stage 4: Base Vibe skills stabilized (completed)

- **4.0**: Base skill surface defined — created `docs/base_skills.md`
- **4.1**: Publish base skills for all agents — created `docs/agent_skill_packs.md`

### 2026-01-28 — Stage 5: Expansion readiness (completed)

- **5.0**: Skill lifecycle and compatibility policy — created `docs/skill_lifecycle.md` with versioning, go/no-go criteria, review checklist
- **5.1**: Repo-level skill readiness — created `docs/config_schema.md` with JSON schema and future expansion fields

### 2026-01-28 — Stage 6: Multi-agent continuous mode verification (completed)

- **6.0**: Claude Code CLI continuous mode — verified through live session (7+ loop iterations without manual intervention)
- **6.1**: Gemini Code continuous mode — verified via bootstrap; added Claude/Copilot/Kimi to bootstrap.py agent choices
- **6.2**: Copilot continuous mode (partial) — documented workarounds in `docs/agent_capabilities.md`

### 2026-01-28 — Stage 7: Self-hosted agent support (completed)

- **7.0**: Generic agent bootstrap — created `prompts/init/generic_bootstrap.md` and self-hosted configuration guide in `docs/agent_capabilities.md`
- **7.1**: Kimi 2.5 verification — SKIPPED (no access to Kimi 2.5)
- **7.2**: IQuest Coder verification — SKIPPED (no access to IQuest Coder)

### 2026-01-28 — Stage 8: End-to-end workflow hardening (completed)

- **8.0**: Consolidation automation — enhanced agentctl.py to recommend consolidation before stage transitions; validation catches stage drift
- **8.1**: Cross-agent test suite — created `tests/workflow/` with 37 tests covering state parsing, checkpoint advancement, stage transition detection, and consolidation triggering

---

## Completed checkpoints (legacy)

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

### 2026-01-27 — Stage 1 / Checkpoint 1.2: Codex skills MVP + deterministic loop helper

- Added the prompt catalog resource and documentation to `skills/codex/vibe-prompts`.
- Updated `vibe_next_and_print.py` to respect CODEX_HOME, enforce UTF-8 I/O, and prefer the installed skills layout.
- Reinstalled the skills globally and confirmed the loop helper / `agentctl next` still produce the expected recommended prompt.

**Evidence pointer**
- `python3 tools/bootstrap.py install-skills --global --agent codex`
- `python3 tools/agentctl.py --repo-root . --format json next`
- `python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`

---

## Resolved issues

### 2026-01-28 — ISSUE-001: Stage sync was broken

- **Resolution:** Implemented programmatic fixes in agentctl.py:
  1. Added `_get_stage_for_checkpoint()` to detect which stage a checkpoint belongs to
  2. Added `_detect_stage_transition()` to detect when advancing crosses stage boundaries
  3. Modified `validate` command to detect stage drift (STATE.md stage doesn't match PLAN.md)
  4. Modified `next` command to recommend consolidation before stage transitions
  5. Fixed heading regex to accept both `*` and `-` bullet formats
- **Impact:** Stage advancement is now validated programmatically; stage drift is detected automatically.

### 2026-01-26 — ISSUE-BOOT-001: Ambiguity between root and `.vibe` workflow files

- **Resolution:** Declared `.vibe/` as the only authoritative location and removed fallback logic.
- **Impact:** Simplified scripts, reduced agent ambiguity, and lowered cognitive overhead.

### 2026-01-27 — ISSUE-001: `vibe_next_and_print.py` assumed the default `~/.codex/skills` path

- **Resolution:** Updated `vibe_next_and_print.py` to prefer the CODEX_HOME-aware skills root, added the catalog resources to the skill tree, and refreshed skill docs/scripts via the bootstrap installer.
- **Impact:** The helper now works from both the repo and any CODEX_HOME-defined global install, eliminating the previous minor blocker.

---

## Archived work log entries

- 2026-01-28: Implemented 7.0 — created generic_bootstrap.md and self-hosted config guide.
- 2026-01-28: Consolidation: archived Stage 6 to HISTORY, advanced to Stage 7 checkpoint 7.0.
- 2026-01-28: Checkpoint 6.1 — Gemini verified continuous mode; added Claude/Copilot/Kimi to bootstrap.py.
- 2026-01-28: Checkpoint 6.0 — Claude Code continuous mode demonstrated through this session.
- 2026-01-28: Consolidation: archived Stage 5 to HISTORY, advanced to Stage 6 checkpoint 6.0.
- 2026-01-28: Implemented checkpoint 5.0 — created docs/skill_lifecycle.md.

## Process notes

- 2026-01-26: Decided to keep workflow state out of version control by default (`.vibe/` in `.gitignore`).
- 2026-01-27: Adopted stable prompt IDs as the canonical interface between scripts, UI, and agent skills.
- 2026-01-27: Positioned Codex Agent Skills as the first-class integration point; other agents use thin adapters.
