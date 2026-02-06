---
name: continuous-refactor
description: Continuous runner for the continuous-refactor workflow across supported agents.
version: "1.0.0"
agents:
  - codex
  - claude
  - gemini
  - copilot
  - kilo
dependencies:
  - vibe-run
---
# continuous-refactor

## Purpose

Run the `continuous-refactor` workflow in continuous mode until dispatcher stop.

This wraps `vibe-run` and always passes `--workflow continuous-refactor`.

## Scripts

- `scripts/continuous_refactor.py`

## How to use

- Interactive mode (recommended):
  - `python3 scripts/continuous_refactor.py --repo-root . --show-decision`
- Non-interactive mode (advanced):
  - `python3 scripts/continuous_refactor.py --repo-root . --non-interactive --max-loops 10 --show-decision`

## Notes

- Uses the same LOOP_RESULT acknowledgement flow as `vibe-run`.
- Stops automatically when `agentctl` returns `recommended_role: stop`.
