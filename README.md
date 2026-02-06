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

| Loop role | Prompt ID | Intended job |
| --- | --- | --- |
| `design` | `prompt.stage_design` | Tighten or repair near-term checkpoints in `.vibe/PLAN.md` so execution is unambiguous. |
| `implement` | `prompt.checkpoint_implementation` | Implement exactly one active checkpoint, run demo commands, commit, and set status to `IN_REVIEW`. |
| `review` | `prompt.checkpoint_review` | Verify deliverables and acceptance criteria, then mark `DONE` or open issues. |
| `issues_triage` | `prompt.issues_triage` | Resolve or clarify blocking/non-blocking issues with minimal scope changes. |
| `advance` | `prompt.advance_checkpoint` | Move `.vibe/STATE.md` from a `DONE` checkpoint to the next checkpoint and reset status to `NOT_STARTED`. |
| `consolidation` | `prompt.consolidation` | Archive completed stages and realign `.vibe/STATE.md` / `.vibe/PLAN.md` before crossing stage boundaries. |
| `improvements` | `prompt.process_improvements` | Improve the orchestration system itself (prompts, tooling, validation, docs). |
| `stop` | `stop` | End the loop when the backlog is exhausted. |

With a defined backlog in `.vibe/PLAN.md` and no active issues, the common cadence is:
`implement -> review -> advance` (repeat), with `consolidation` inserted at stage transitions.

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

### `$vibe-run` happy-path flow (no issues, defined backlog)

```mermaid
flowchart TD
    A[Start $vibe-run] --> B[Run agentctl.py next]
    B --> C{recommended_role}
    C -->|implement| D[Run prompt.checkpoint_implementation]
    D --> E[STATE status becomes IN_REVIEW]
    E --> B
    C -->|review| F[Run prompt.checkpoint_review]
    F --> G[STATE status becomes DONE]
    G --> B
    C -->|advance| H[Run prompt.advance_checkpoint]
    H --> I[STATE moves to next checkpoint with NOT_STARTED]
    I --> B
    C -->|consolidation| J[Run prompt.consolidation at stage boundary]
    J --> B
    C -->|stop| Z[Exit loop]
```

`issues_triage`, `design`, and `improvements` are outside this no-issues path and
are only selected when state or planning conditions call for them.

## How to start a session

1) Open the target repo.
2) Use the appropriate bootstrap prompt in `prompts/init/`.
3) Run the loop recommended by `agentctl.py`.
4) Update `.vibe/STATE.md` and repeat until done.

## License

See `LICENSE`.
