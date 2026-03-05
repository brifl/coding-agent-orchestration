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

## Canonical templates (DRY)

Use these as the single source of truth for structure and allowed values:

- `templates/META_TEMPLATES/PLAN.md`
- `templates/META_TEMPLATES/STATE.md`
- `templates/META_TEMPLATES/HISTORY.md`

## Stop conditions

Record an issue in `.vibe/STATE.md` and pause when:

- required information is missing,
- instructions conflict,
- a scope/architecture decision is needed,
- external credentials/secrets are required,
- tests fail for unclear reasons.
