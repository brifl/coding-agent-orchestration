# AGENTS.md — Markdown-only workflow contract

## Purpose

Use this repository as a **lightweight, human-in-the-loop planning system**.
No Python orchestrator is required.

## Precedence

1. User instructions in chat
2. This file
3. `.vibe/STATE.md`
4. `.vibe/PLAN.md`
5. `.vibe/HISTORY.md`
6. `.vibe/CONTEXT.md`

## Required read order

1. `AGENTS.md`
2. `.vibe/STATE.md`
3. `.vibe/PLAN.md`
4. `.vibe/HISTORY.md` (optional)
5. `.vibe/CONTEXT.md` (optional)

## Scope and cadence

- Do one checkpoint at a time (unless explicitly requested more).
- Keep diffs small and reviewable.
- Limit interventions and changes to what is necessary to meet acceptance criteria
- Human reviews after each checkpoint.

## Checkpoint format (PLAN.md)

For each checkpoint we should have:
- Objective
- Deliverables
- Acceptance
- Demo commands (if any)
- Evidence

## State format (STATE.md)

This tracks:
- Current stage/checkpoint/status
- Work log (append-only)
- Active issues
- Decisions

## Stop conditions

Stop and record an issue in `.vibe/STATE.md` when:
- Required info is missing
- Instructions conflict
- Scope/architecture decision is needed
- External credentials/secrets are required
- Tests fail for unclear reasons

## Version control policy

- Work on current branch only.
- Do not create/switch/delete branches unless user asks.
- Commit coherent changes.
- Commit message prefix: `<checkpoint-id>: <imperative summary>`

