# Vibe Coding-Agent Orchestration (Basic Markdown-only version)

This repository tracks agentic work using state files only.

## Core files for agentic workflow

All files in `.vibe` track the progress of work. 

- `AGENTS.md` — execution contract and operating policy.
- `.vibe/PLAN.md` — checkpoint backlog with acceptance criteria.
- `.vibe/STATE.md` — active checkpoint, status, and current session evidence.
- `.vibe/HISTORY.md` — optional archive for completed checkpoints and resolved issues.
- `.vibe/CONTEXT.md` — optional handoff notes and durable project context.

## Canonical templates (DRY)

To avoid drift, treat these as the single source of truth for structure:

- `templates/META_TEMPLATES/PLAN.md`
- `templates/META_TEMPLATES/STATE.md`
- `templates/META_TEMPLATES/HISTORY.md`

## Workflow loop

1. Read `AGENTS.md`, `.vibe/STATE.md`, and `.vibe/PLAN.md` (plus optional history/context if needed).
2. Pick the active checkpoint from `.vibe/STATE.md`.
3. Implement only that checkpoint.
4. Run required demo/test commands.
5. Update `.vibe/STATE.md` and `.vibe/HISTORY.md` (and `.vibe/CONTEXT.md` if relevant)
7. Human reviews.

## Quick consistency checks (agent + human)

Use this before or after each checkpoint to keep planning artifacts aligned:

- **Checkpoint sync:** `STATE.md` objective/deliverables/acceptance exactly match the active checkpoint in `PLAN.md`.
- **Status accuracy:** `STATE.md` status is one of `NOT_STARTED`, `IN_PROGRESS`, `IN_REVIEW`, `BLOCKED`, `DONE` and reflects reality.
- **Issue hygiene:** active blockers/questions live in `STATE.md` with impact + unblock condition; resolved ones move to `HISTORY.md`.
- **Evidence quality:** all acceptance claims point to concrete commands, outputs, commits, or screenshots.
- **Scope discipline:** only one checkpoint is active unless explicitly requested otherwise.

## Templates and examples

When creating or updating planning docs, link to and follow the canonical templates in
`templates/META_TEMPLATES/` rather than copying template blocks into additional docs.

## Philosophy

Keep it simple:

- small checkpoints,
- frequent human review,
- no autonomous long-running loops.
