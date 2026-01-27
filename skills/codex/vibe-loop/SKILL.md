# vibe-loop

## Purpose

Drive the Vibe workflow deterministically for a target repository.

This skill uses `.vibe/STATE.md` and `.vibe/PLAN.md` to recommend the next loop prompt and to validate invariants.

## Inputs

- Repo root path (default: current working directory)
- Optional: `--strict` validation for CI-grade checks

## Scripts

- `scripts/agentctl.py`

## How to use

- Show current status:
  - Run: `python3 scripts/agentctl.py --repo-root . status --format json`
- Recommend next loop:
  - Run: `python3 scripts/agentctl.py --repo-root . next --format json`
- Validate invariants:
  - Run: `python3 scripts/agentctl.py --repo-root . validate --format json`
  - Strict mode (recommended in CI): add `--strict`

## Intended usage pattern

1) Run `next` to obtain `recommended_prompt_id`.
2) Use the `vibe-prompts` skill to print the corresponding prompt body.
3) Execute that prompt loop in the agent session.
4) Stop after one loop completes and `.vibe/STATE.md` is updated.

This skill intentionally does not implement product code by itself; it selects and gates the next action.
