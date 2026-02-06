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
- Headless executor mode (CI/agent automation):
  - `python3 scripts/vibe_run.py --repo-root . --max-loops 10 --executor "python3 ./scripts/run_one_loop.py" --show-decision`
- Run a specific workflow continuously (for example `continuous-refactor`):
  - `python3 scripts/vibe_run.py --repo-root . --workflow continuous-refactor --show-decision`
- Run the continuous test workflow:
  - `python3 scripts/vibe_run.py --repo-root . --workflow continuous-test-generation --show-decision`

## Notes

- Interactive mode prints one prompt body per loop, then waits for Enter so you
  can execute that loop in your agent session before continuing.
- After each interactive loop, the runner asks for the emitted `LOOP_RESULT: {...}`
  line and records it through `agentctl loop-result` before selecting the next loop.
- In executor mode, the command is run after each prompt and must print a
  `LOOP_RESULT: {...}` line; the runner records it automatically.
- The runner stops automatically when `agentctl` returns `recommended_role: stop`.
