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

# Stage 2 — Multi-agent adapters (Codex-led, Claude/Gemini compatible)

**Purpose:**
Make this repo the canonical, agent-agnostic reference implementation. Codex executes; other agents reason, plan, and review without breaking the contract.

## 2.0 — Canonical bootstrap prompts (Codex, Claude, Gemini, Copilot)

**Objective**
Provide minimal, unambiguous bootstrap prompts that orient each agent into the Vibe workflow without duplicating logic or embedding loops.

**Deliverables**

* `prompts/init/codex_bootstrap.md`
* `prompts/init/claude_bootstrap.md`
* `prompts/init/gemini_bootstrap.md`
* `prompts/init/copilot_bootstrap.md`
* Corresponding stable-ID entries in `prompts/template_prompts.md`

**Acceptance**

* Each bootstrap is ≤ 30 lines.
* Each bootstrap:

  * points to `AGENTS.md`, `.vibe/STATE.md`, `.vibe/PLAN.md`
  * clearly distinguishes **single-loop vs continuous** execution
  * does **not** embed looping behavior
* Codex bootstrap explicitly references `$vibe-one-loop` and `$vibe-run`.

**Demo commands**

```bash
python tools/prompt_catalog.py prompts/template_prompts.md get init.codex_bootstrap
python tools/prompt_catalog.py prompts/template_prompts.md get init.claude_bootstrap
```

**Evidence**

* Paste the four bootstrap texts.
* Paste a short transcript excerpt from each agent showing correct orientation (stage / checkpoint / status identified).

---

## 2.1 — Continuous runner skill (Codex)

**Objective**
Enable Codex to autonomously progress a repo until interruption, plan exhaustion, or blocking issue.

**Deliverables**

* `skills/codex/vibe-run/SKILL.md`
* Installer wiring in `tools/bootstrap.py`
* Documentation note in `README.md` describing continuous mode vs single-loop

**Acceptance**

* `$vibe-run` repeatedly:

  * dispatches via `agentctl`
  * executes exactly one loop per iteration
  * advances checkpoints when DONE
* Stops when:

  * no next checkpoint exists
  * status becomes BLOCKED
  * a BLOCKER issue exists

**Demo commands**

```bash
python tools/bootstrap.py install-skills --global --agent codex
# In Codex chat:
$vibe-run
```

**Evidence**

* Paste a run transcript showing at least:

  * implementation → review → advance → next implementation
  * clean stop when plan is exhausted

---

## 2.2 — Agent capability contract

**Objective**
Make agent differences explicit so the workflow behaves predictably across tools.

**Deliverables**

* Section in `README.md` or `docs/concepts.md`:

  * Codex: executes loops + edits files
  * Claude/Gemini: propose, review, design; may execute only if tools allow
* Clear rule: only Codex runs `$vibe-run` by default

**Acceptance**

* A new user can tell which agent to use for which role in <5 minutes.

**Demo commands**

```bash
# none (doc-only)
```

**Evidence**

* Paste the capability matrix section.

---

# Stage 3 — Repo-specific skill sets (Claude/Gemini design-led)

**Purpose:**
Allow repos to extend or constrain behavior without mutating global skills.

## 3.0 — Skill set configuration model

**Objective**
Define how a repo declares additional skills and prompt catalogs.

**Deliverables**

* `.vibe/config.json` schema (documented)
* `docs/concepts.md` section: “Skill Sets”
* `tools/bootstrap.py init-repo --skillset <name>`

**Acceptance**

* Skill set config can specify:

  * name
  * additional skill folders
  * additional prompt catalogs
* No behavior changes if config is absent.

**Demo commands**

```bash
python tools/bootstrap.py init-repo . --skillset minimal
cat .vibe/config.json
```

**Evidence**

* Paste generated `.vibe/config.json`.

---

## 3.1 — Repo-local skill installation (Codex)

**Objective**
Install repo-local skills alongside global ones with deterministic precedence.

**Deliverables**

* `tools/bootstrap.py install-skills --repo --agent codex`
* Example repo-local skill:

  * e.g. `skills/repo/example-validation/SKILL.md`

**Acceptance**

* Repo-local skills:

  * do not overwrite global skills
  * are discoverable by Codex
* Precedence rules documented and enforced.

**Demo commands**

```bash
python tools/bootstrap.py install-skills --repo --agent codex
tree .vibe/skills
```

**Evidence**

* Paste tree showing global + repo-local skill coexistence.

---

# Stage 4 — Advanced capability expansion (Codex execution, Claude/Gemini design)

**Purpose:**
Add power without sacrificing determinism or safety.

## 4.0 — Multi-directory scan + index skill

**Objective**
Allow agents to reason over large repos without ad-hoc globbing.

**Deliverables**

* `skills/*/vibe-scan/SKILL.md`
* Script to:

  * scan configured directories
  * produce a lightweight index (paths + summaries)
* Optional `.vibe/scan.json` config

**Acceptance**

* Scan completes deterministically.
* Index is readable by prompts and tools.
* No implicit recursion beyond configured roots.

**Demo commands**

```bash
python ~/.codex/skills/vibe-scan/scripts/scan.py --repo-root .
```

**Evidence**

* Paste index file snippet.

---

## 4.1 — RLM tools skill (bounded recursion)

**Objective**
Introduce recursive tool use with explicit bounds and auditability.

**Deliverables**

* `skills/*/vibe-rlm/SKILL.md`
* Guardrails:

  * max depth
  * explicit subtask logging
  * automatic abort on loop or ambiguity

**Acceptance**

* Recursive behavior is visible, logged, and bounded.
* Failure modes are explicit (no silent looping).

**Demo commands**

```bash
# Via Codex skill invocation
$vibe-rlm
```

**Evidence**

* Paste a short run log showing bounded recursion.
---

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
