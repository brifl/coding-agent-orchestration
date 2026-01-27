# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.

## Stage 0 — Baseline workflow + bootstrapping (DONE)

### 0.0 — Repo scaffold + baseline templates

- Objective:
  - Establish the canonical repo structure and baseline templates for bootstrapping target repos.
- Deliverables:
  - `templates/repo_root/AGENTS.md`
  - `templates/repo_root/VIBE.md`
  - `templates/vibe_folder/STATE.md`, `PLAN.md`, `HISTORY.md`
  - `README.md` describing the system
- Acceptance:
  - [x] Target repo structure is stable and minimal
  - [x] Templates are consistent with `.vibe/` being authoritative
- Demo commands:
  - `python3 tools/bootstrap.py init-repo /path/to/target/repo`
- Evidence:
  - Screenshot/paste of init-repo summary output

### 0.1 — Bootstrap script (init-repo) is idempotent

- Objective:
  - Provide a safe initializer that creates `.vibe/` and adds `.vibe/` to `.gitignore` without overwriting project files.
- Deliverables:
  - `tools/bootstrap.py` with `init-repo <path>`
- Acceptance:
  - [x] Running `init-repo` twice results in no destructive changes
  - [x] `.vibe/` is added to `.gitignore` exactly once
- Demo commands:
  - `python3 tools/bootstrap.py init-repo .`
  - `python3 tools/bootstrap.py init-repo .`
- Evidence:
  - Paste the two summaries showing “Created” then “Skipped”

## Stage 1 — Codex-first MVP skills + deterministic control plane (IN PROGRESS)

### 1.0 — Prompt catalog + stable IDs

- Objective:
  - Make prompt retrieval deterministic and scriptable with stable IDs.
- Deliverables:
  - `prompts/template_prompts.md` uses stable IDs (`## prompt.* — ...`)
  - `tools/prompt_catalog.py` supports `list` and `get`
- Acceptance:
  - [x] `python3 tools/prompt_catalog.py prompts/template_prompts.md list` prints IDs + titles
  - [x] `... get prompt.onboarding` prints the correct body
- Demo commands:
  - `python3 tools/prompt_catalog.py prompts/template_prompts.md list`
  - `python3 tools/prompt_catalog.py prompts/template_prompts.md get prompt.onboarding`
- Evidence:
  - Paste list output + one retrieved prompt body

### 1.1 — `.vibe/`-aware agent control plane

- Objective:
  - Provide a deterministic `agentctl` that reads `.vibe/STATE.md` and recommends the next loop prompt.
- Deliverables:
  - `tools/agentctl.py` supports `status|next|validate` and emits `recommended_prompt_id`
- Acceptance:
  - [x] `python3 tools/agentctl.py status` works in a bootstrapped repo
  - [x] `python3 tools/agentctl.py next --format json` includes `recommended_prompt_id`
- Demo commands:
  - `python3 tools/agentctl.py --repo-root . status`
  - `python3 tools/agentctl.py --repo-root . next --format json`
- Evidence:
  - Paste JSON output from `next`

### 1.2 — Codex global skills MVP (CURRENT)

- Objective:
  - Install global Codex skills and provide one-command prompt retrieval and “next-and-print” for a target repo.
- Deliverables:
  - `skills/codex/vibe-prompts/SKILL.md`
  - `skills/codex/vibe-prompts/scripts/vibe_get_prompt.py`
  - `skills/codex/vibe-loop/SKILL.md`
  - `skills/codex/vibe-loop/scripts/vibe_next_and_print.py` (respects `CODEX_HOME`)
  - `tools/bootstrap.py install-skills --global --agent codex`
- Acceptance:
  - [ ] Global install works and is idempotent
  - [ ] `vibe_next_and_print.py` prints a valid loop prompt body for the repo’s current state
  - [ ] Clear error messages for missing `.vibe` or missing catalog
- Demo commands:
  - `python3 tools/bootstrap.py install-skills --global --agent codex`
  - `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`
- Evidence:
  - Paste install summary + `--show-decision` output (decision JSON + prompt body)

## Stage 2 — Multi-agent adapters (Gemini + Claude), still canonical in this repo

### 2.0 — Thin bootstraps (no duplication of workflow)

- Objective:
  - Provide short, agent-specific initialization prompts that route to `AGENTS.md` + `.vibe/*` + the prompt catalog.
- Deliverables:
  - `prompts/init/gemini_bootstrap.md`
  - `prompts/init/claude_bootstrap.md`
- Acceptance:
  - [ ] Each bootstrap is ≤ 30 lines and contains only routing + stop conditions
  - [ ] Both explicitly reference `.vibe/STATE.md` and `.vibe/PLAN.md`
- Demo commands:
  - (manual) paste prompt into a new agent chat and verify it asks/acts correctly
- Evidence:
  - Paste the bootstrap text and a short transcript snippet showing correct behavior

### 2.1 — Parameterized “design conversation” prompts (non-coding LLM friendly)

- Objective:
  - Add design-side prompt loops that facilitate structured conversations without coding, using the same catalog mechanism.
- Deliverables:
  - New `prompt.design_*` entries in `prompts/template_prompts.md`
  - `tools/clipper.py --catalog <path>` documented usage
- Acceptance:
  - [ ] `clipper.py` can point to a design-catalog file and render buttons
- Demo commands:
  - `python3 tools/clipper.py --catalog prompts/template_prompts.md`
- Evidence:
  - Screenshot of UI with new design prompts visible

## Stage 3 — Repo-specific skill sets (overlay on top of global skills)

### 3.0 — Skill set spec + bootstrap option

- Objective:
  - Allow a repo to specify a “skill set” that adds repo-local skills on top of global ones.
- Deliverables:
  - `docs/concepts.md` section defining skill sets (name, selection, precedence)
  - `tools/bootstrap.py init-repo --skillset <name>` (initial stub ok)
- Acceptance:
  - [ ] CLI accepts `--skillset` and stores selection in a repo-local config file (e.g., `.vibe/config.json`)
  - [ ] No behavior changes unless skill set is present
- Demo commands:
  - `python3 tools/bootstrap.py init-repo . --skillset minimal`
- Evidence:
  - Paste created config file contents

### 3.1 — Repo-local skills install (Codex)

- Objective:
  - Install additional skills into the repo in a predictable location (in addition to global).
- Deliverables:
  - `tools/bootstrap.py install-skills --repo --agent codex` (or similar)
  - A small example repo-local skill for validation or prompting
- Acceptance:
  - [ ] Repo-local skills do not break global skills
  - [ ] Clear precedence rules documented
- Demo commands:
  - `python3 tools/bootstrap.py install-skills --repo --agent codex`
- Evidence:
  - Paste tree snippet showing installed repo-local skills

## Stage 4+ — Future (stage-only, not checkpoint resolution yet)

### Stage 4 — Advanced skills (RLM tools, multi-dir scan, RAG)

- Build an “RLM tools” skill (recursive tool use / self-driven subloops)
- Multi-directory scan skill + lightweight local index
- RAG skill (pluggable backends; local-first)

### Stage 5 — Skill subscriptions and curation

- Subscribe to skills from public repos (e.g., Anthropics skill repo) and pin versions
- Trust model: allowlist + checksums/signatures + update workflow
- Conflict resolution when two skills export similar capabilities

### Stage 6 — Prompt library expansion + clipper UI upgrades

- Add refactoring loop (hardcore/strict)
- Add human-interactive testing/feedback loop (explicit “paste outputs” checkpoints)
- Re-parameterize clipper input catalog(s) and improve UI (search, grouping, favorites)

### Stage 7 — Workflow configuration and triggers

- Config model for intended loop frequency and triggers
- “Autonomous issue addressing” rules (bounded, safe)
- Reporting: periodic summaries of state/progress/issues
