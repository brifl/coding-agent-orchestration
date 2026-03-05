# VIBE

Minimal markdown workflow.

## Read order

1. `AGENTS.md`
2. `.vibe/STATE.md`
3. `.vibe/PLAN.md`
4. `.vibe/HISTORY.md` (optional)
5. `.vibe/CONTEXT.md` (optional)

## Workflow

- Define checkpoints in `.vibe/PLAN.md`.
- Track current work in `.vibe/STATE.md`.
- Implement one checkpoint at a time.
- Record evidence.
- Open a PR.
- Human review.

## Status values

- `NOT_STARTED`
- `IN_PROGRESS`
- `IN_REVIEW`
- `BLOCKED`
- `DONE`

## Stop conditions

Record an issue in `.vibe/STATE.md` and pause when:

- required information is missing,
- instructions conflict,
- a scope/architecture decision is needed,
- external credentials/secrets are required,
- tests fail for unclear reasons.
