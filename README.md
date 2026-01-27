# coding-agent-orchestration

A lightweight toolkit for running consistent, low-overhead workflows with coding agents
(OpenAI Codex first; Gemini/Claude next; Copilot later).

This repo is the **canonical source** for:
- a minimal repository contract (`AGENTS.md`)
- a project-local workspace folder (`.vibe/`) for state/plan/history
- a prompt catalog (`template_prompts.md`) used by tools and (eventually) agent skills
- bootstrapping and installation scripts that keep things consistent across repos and agents

## Design goals

- **Low cognitive overhead**: every target repo follows the same layout.
- **Deterministic control**: scripts decide the next workflow step; the agent executes it.
- **Separation of concerns**:
  - repo contract can drift per project
  - project state/plan are always project-specific
  - reusable workflows live here

## Target repo layout

A bootstrapped repo looks like:

```

<repo>/
AGENTS.md          # repo-specific execution contract (can drift)
.vibe/             # project-local working state (gitignored)
STATE.md         # current stage/checkpoint/status
PLAN.md          # checkpoint backlog with acceptance/demo/evidence
HISTORY.md       # rollups + archive
.gitignore         # contains ".vibe/"

````

### Why `.vibe/` is gitignored

`STATE.md` and `PLAN.md` are inherently project-specific and frequently rewritten. For most workflows,
keeping them out of version control reduces noise and merge friction. If a project benefits from
tracking them, you can remove the ignore entry for that repo.

## What’s in this repo

- `templates/`  
  Files copied into target repos during bootstrap (AGENTS baseline and `.vibe` templates).

- `prompts/`  
  The prompt catalog and optional per-agent bootstrap prompts. The catalog is the canonical
  source used by helper tools and (eventually) agent skills.

- `tools/`  
  Deterministic scripts that support the workflow.
  - `agentctl.py` provides commands like `status`, `validate`, and `next` (the recommended next loop).

- `skills/`  
  Agent Skills packages (Codex first) that can:
  - fetch the right prompt text from the catalog
  - drive a “run one loop, stop” workflow using `agentctl.py`

## Quick start

### 1) Bootstrap a repo

From this repo:

```bash
python3 tools/bootstrap.py init-repo /path/to/your/repo
````

This will:

* create `/path/to/your/repo/.vibe/` with templates
* add `.vibe/` to that repo’s `.gitignore`
* add a baseline `AGENTS.md` if missing

### 2) Install global Codex skills

```bash
python3 tools/bootstrap.py install-skills --global codex
```

This installs/upgrades skills under your Codex global skill directory and syncs the prompt catalog
into skill resources.

### 3) Start an agent session (Codex)

Open the target repo in VS Code, start a Codex chat, and use the repo’s initialization prompt
(from `prompts/init/codex_bootstrap.md`) or invoke the installed skills (once added).

## Workflow model (short)

* `AGENTS.md` defines the contract and precedence rules.
* `.vibe/STATE.md` is the current truth (what we are doing now).
* `.vibe/PLAN.md` is the backlog of checkpoints with acceptance criteria.
* `.vibe/HISTORY.md` is non-authoritative rollups.

The “next step” is chosen deterministically (via `agentctl.py next`) and executed using the
prompt catalog loops.

## Agent support roadmap

Priority order:

1. OpenAI Codex (VS Code extension): global skills + deterministic scripts
2. Gemini: thin adapter prompts/rules that point to the repo contract
3. Claude: thin adapter prompts/rules that point to the repo contract
4. Copilot: mirrored Agent Skills layout later

## License

See `LICENSE`.
