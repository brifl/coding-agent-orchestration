---
name: vibe-run
description: Continuous Vibe loop runner for Codex.
version: "1.0.0"
dependencies:
  - vibe-loop
  - vibe-prompts
---
# vibe-run

## Purpose

Provide a continuous loop runner that repeats workflow selection until the
dispatcher returns `recommended_role == "stop"`.

## Scripts

- `scripts/vibe_run.py`

## How to use

- Interactive continuous mode (recommended):
  - `python3 scripts/vibe_run.py --repo-root . --show-decision`
- Non-interactive mode (advanced):
  - `python3 scripts/vibe_run.py --repo-root . --non-interactive --max-loops 10 --show-decision`

## Notes

- Interactive mode prints one prompt body per loop, then waits for Enter so you
  can execute that loop in your agent session before continuing.
- After each interactive loop, the runner asks for the emitted `LOOP_RESULT: {...}`
  line and records it through `agentctl loop-result` before selecting the next loop.
- The runner stops automatically when `agentctl` returns `recommended_role: stop`.
