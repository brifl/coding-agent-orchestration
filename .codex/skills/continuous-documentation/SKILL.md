---
name: continuous-documentation
description: Continuous runner for the continuous-documentation workflow across supported agents.
version: "1.0.0"
agents:
  - codex
  - claude
  - gemini
  - copilot
dependencies:
  - vibe-run
---
# continuous-documentation

## Purpose

Run the `continuous-documentation` workflow in continuous mode until dispatcher stop.

This wraps `vibe-run` and always passes `--workflow continuous-documentation`.

## Scripts

- `scripts/continuous_documentation.py`

## How to use

- Interactive mode (recommended):
  - `python3 scripts/continuous_documentation.py --repo-root . --show-decision`
- Non-interactive mode (advanced):
  - `python3 scripts/continuous_documentation.py --repo-root . --non-interactive --max-loops 10 --show-decision`

## Notes

- Uses the same LOOP_RESULT acknowledgement flow as `vibe-run`.
- Stops automatically when `agentctl` returns `recommended_role: stop`.
