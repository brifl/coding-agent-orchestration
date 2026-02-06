# VIBE

This repo uses the Vibe coding-agent workflow.

## Start here (read order)

1) `AGENTS.md` (execution contract)
2) `.vibe/STATE.md` (current focus: stage/checkpoint/status)
3) `.vibe/PLAN.md` (checkpoint backlog + acceptance criteria)
4) `.vibe/HISTORY.md` (optional context; non-authoritative)

## Working files

Project-specific workflow files live under `.vibe/` and are typically gitignored:
- `.vibe/STATE.md`
- `.vibe/PLAN.md`
- `.vibe/HISTORY.md`

## Canonical STATE.md format

Use this canonical shape for `.vibe/STATE.md`:

```md
# STATE

## Session read order
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus
- Stage: 0
- Checkpoint: 0.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)
<!-- 1 sentence; keep in sync with PLAN.md -->

## Deliverables (current checkpoint)
<!-- concrete files/modules/behaviors -->

## Acceptance (current checkpoint)
<!-- verifiable conditions -->

## Work log (current session)
<!-- append-only bullets -->

## Evidence
<!-- command outputs/links relevant to acceptance -->

## Active issues
- [ ] ISSUE-001: <short title>
  - Impact: QUESTION <!-- QUESTION | MINOR | MAJOR | BLOCKER -->
  - Status: OPEN <!-- OPEN | IN_PROGRESS | BLOCKED | RESOLVED -->
  - Owner: agent|human
  - Unblock Condition: <what must be true to proceed>
  - Evidence Needed: <command/output/link proving resolution>
  - Notes: <optional context>

## Decisions
- YYYY-MM-DD: <decision> (1-2 line rationale)
```

## Canonical PLAN.md format

Use this canonical shape for `.vibe/PLAN.md`:

```md
# PLAN

## How to use this file
- This is the checkpoint backlog.
- Each checkpoint must include: Objective, Deliverables, Acceptance, Demo commands, Evidence.

## Stage 0 — <stage name>

### 0.0 — <checkpoint name>
- Objective:
  - <1 sentence>
- Deliverables:
  - <file/module/behavior>
- Acceptance:
  - [ ] <verifiable condition>
- Demo commands:
  - `<exact command>`
- Evidence:
  - <what to paste into .vibe/STATE.md Evidence>
```

Validation notes:
- Stage IDs use `<int>` or `<int><suffix>` (for example `19`, `19A`).
- Checkpoint IDs use `<stage>.<minor>` (for example `19A.2`).
- Keep the current checkpoint in `STATE.md` in sync with an existing checkpoint in `PLAN.md`.

## How to proceed

- Use the next-step recommendation from your orchestration tools (if installed), or
- Use the prompt catalog (`template_prompts.md` in your orchestration kit) to run one loop:
  - Stage Design → Implementation → Review → Triage (as needed) → Consolidation (as needed)

Log an issue in .vibe/STATE.md and stop if you hit missing info, conflicting instructions, or any scope-changing decision point.

## Workflow

* `IN_PROGRESS` → dispatcher picks implementation → loop ends → dispatcher continues
* `IN_REVIEW` → dispatcher picks review → PASS sets `DONE` → dispatcher picks advance → continues
* `DONE` and no next checkpoint → dispatcher returns `stop` → continuous runner exits
* `BLOCKED` or `BLOCKER` issue → dispatcher returns `issues_triage` (or stop if you choose) → runner handles accordingly
