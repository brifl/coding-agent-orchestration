# Vibe Coding-Agent Orchestration (Basic Markdown-only version)

This repository tracks agentic work using state files only.

## Core files

- `AGENTS.md` — execution contract and operating policy.
- `.vibe/PLAN.md` — checkpoint backlog with acceptance criteria.
- `.vibe/STATE.md` — active checkpoint, status, and current session evidence.
- `.vibe/HISTORY.md` — optional archive for completed checkpoints and resolved issues.
- `.vibe/CONTEXT.md` — optional handoff notes and durable project context.

## Workflow loop

1. Read `AGENTS.md`, `.vibe/STATE.md`, and `.vibe/PLAN.md` (plus optional history/context if needed).
2. Pick the active checkpoint from `.vibe/STATE.md`.
3. Implement only that checkpoint.
4. Run required demo/test commands.
5. Update `.vibe/STATE.md` with work log + evidence.
6. Open a PR.
7. Human reviews.

## Quick consistency checks (agent + human)

Use this before or after each checkpoint to keep planning artifacts aligned:

- **Checkpoint sync:** `STATE.md` objective/deliverables/acceptance exactly match the active checkpoint in `PLAN.md`.
- **Status accuracy:** `STATE.md` status is one of `NOT_STARTED`, `IN_PROGRESS`, `IN_REVIEW`, `BLOCKED`, `DONE` and reflects reality.
- **Issue hygiene:** active blockers/questions live in `STATE.md` with impact + unblock condition; resolved ones move to `HISTORY.md`.
- **Evidence quality:** all acceptance claims point to concrete commands, outputs, commits, or screenshots.
- **Scope discipline:** only one checkpoint is active unless explicitly requested otherwise.

## Checkpoint template (`PLAN.md`)

```md
### <stage>.<n> — <title>
- Objective:
- Deliverables:
- Acceptance:
- Demo commands:
- Evidence:
```

## State template (`STATE.md`)

```md
## Current focus
- Stage: <id>
- Checkpoint: <id>
- Status: NOT_STARTED|IN_PROGRESS|IN_REVIEW|BLOCKED|DONE

## Work log (current session)
- YYYY-MM-DD: <change summary>

## Evidence
- `<command>` -> <result>

## Active issues
- [ ] ISSUE-<id>: <title>
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: <condition>
  - Evidence Needed: <proof>
```

## Philosophy

Keep it simple:

- small checkpoints,
- frequent human review,
- no autonomous long-running loops.
