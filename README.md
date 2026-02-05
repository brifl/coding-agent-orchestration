# Vibe Coding-Agent Orchestration

A practical system for running coding agents with predictable loops, explicit state, and low overhead.
This repository is the canonical reference implementation of the workflow.

## Why this exists

Agent work gets messy without a shared contract. This system makes the workflow explicit:
- **State lives in files** so any agent can pick up where the last one left off.
- **Next actions are deterministic** (chosen by tooling, not improv).
- **Small checkpoints** keep scope bounded and reviewable.
- **Context snapshots** reduce repeated rediscovery between sessions.

## The mental model

Everything runs off four files in `.vibe/`:

- `.vibe/STATE.md` -- the current truth (stage, checkpoint, status, issues).
- `.vibe/PLAN.md` -- a backlog of checkpoints with objective/deliverables/acceptance.
- `.vibe/HISTORY.md` -- non-authoritative rollups and archived logs.
- `.vibe/CONTEXT.md` -- short-lived context snapshot (decisions, gotchas, hot files, notes).

Agents do **not** invent workflows. They run the prompt loop recommended by `agentctl.py`.

## How work progresses

1) `agentctl.py next` chooses the next loop (implement, review, triage, consolidation, etc.).
2) The loop prompt is fetched from `prompts/template_prompts.md` and executed.
3) The agent updates `.vibe/STATE.md` with evidence and status changes.
4) Repeat until the plan is exhausted or blocked.

Stages are expected to be consolidated before moving to the next stage.

## Repository layout (authoritative)

```
<repo>/
  AGENTS.md               # repo-specific execution contract (can drift)
  .vibe/
    STATE.md              # current stage/checkpoint/status/issues
    PLAN.md               # checkpoint backlog
    HISTORY.md            # rollups and archived work
    CONTEXT.md            # snapshot of key context
  prompts/                # prompt catalog + bootstrap prompts
  tools/                  # deterministic workflow tools
  templates/              # repo bootstrap + checkpoint/gate templates
  .codex/
    skills/               # Codex skill packages (SKILL.md)
```

`.vibe/` is ignored by default to avoid constant churn. If your repo benefits from versioning
workflow state, remove the ignore entry locally.

## Core tooling

### `tools/agentctl.py`
The control plane for the workflow. Key commands:

- `status` -- current stage/checkpoint + issue summary (use `--with-context` for full context).
- `next` -- deterministic recommendation for the next loop prompt.
- `validate` -- invariants for STATE/PLAN/HISTORY consistency.
- `add-checkpoint` -- insert a checkpoint from a template into PLAN.md.

### `tools/prompt_catalog.py`
Lists and retrieves prompts from `prompts/template_prompts.md` by stable ID.

### `tools/checkpoint_templates.py`
Lists, previews, and instantiates checkpoint templates from `templates/checkpoints/`.

## Workflow loops (what they do)

Loops are defined in `prompts/template_prompts.md` and chosen by `agentctl.py`:

- **Implementation** -- build the current checkpoint.
- **Review** -- verify acceptance; mark DONE or add issues.
- **Triage** -- resolve or clarify issues with minimal scope.
- **Consolidation** -- archive completed stages, prune logs/evidence, sync stage pointer.
- **Process improvements** -- improve the orchestration system itself (bounded scope).

## Context snapshots

Stage 10 introduced `.vibe/CONTEXT.md` to capture only the critical context:

- Architecture (high-level system shape)
- Key decisions (dated)
- Gotchas (pitfalls and traps)
- Hot files (high-traffic files/paths)
- Agent notes (session-scoped)

Use `prompt.context_capture` to update it at session end or after stage boundaries.
Bootstrap prompts now read CONTEXT.md after STATE.md to reduce rediscovery.

## Quality gates

Stage 9 added deterministic quality gates to `agentctl.py`:

- Configure gates in `.vibe/config.json`.
- Run gates with `agentctl.py next --run-gates`.
- Templates for gates live in `templates/gates/`.

This keeps objective checks close to the workflow instead of ad-hoc "please run tests".

## Checkpoint templates

Stage 11 added checkpoint templates to reduce planning boilerplate:

- Templates live in `templates/checkpoints/`.
- Use `tools/checkpoint_templates.py list|preview|instantiate`.
- Use `agentctl add-checkpoint --template <name> --params ...` to insert into PLAN.md.

Templates cover common patterns (feature, bug, refactor, endpoint, coverage) and
include sensible default acceptance criteria.

## Bootstrapping and skills

### Bootstrap a repo

```
python3 tools/bootstrap.py init-repo /path/to/your/repo
```

This creates `.vibe/`, adds `.vibe/` to `.gitignore`, and installs a baseline `AGENTS.md`.

### Install global skills

```
python3 tools/bootstrap.py install-skills --global --agent <agent_name>
```

Supported agents: `codex`, `claude`, `gemini`, `copilot`, `kilo`.

Codex is the reference implementation for continuous mode. Other agents rely on
manual bootstraps found in `prompts/init/`.

## Single-loop vs continuous

- **Single loop**: run one loop and stop (use `$vibe-one-loop` or manual prompts).
- **Continuous**: loop until `agentctl` returns `recommended_role == "stop"`.

Codex's `$vibe-run` skill implements continuous mode. It must keep looping until
the dispatcher says stop--never just one cycle.

## How to start a session

1) Open the target repo.
2) Use the appropriate bootstrap prompt in `prompts/init/`.
3) Run the loop recommended by `agentctl.py`.
4) Update `.vibe/STATE.md` and repeat until done.

## License

See `LICENSE`.
