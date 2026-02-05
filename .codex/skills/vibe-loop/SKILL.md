---
name: vibe-loop
description: Run one deterministic Vibe dispatcher step and print the selected prompt body.
version: "1.0.0"
dependencies:
  - vibe-prompts
---

## Purpose

Drive the Vibe workflow deterministically for a target repository.

This skill uses `.vibe/STATE.md` and `.vibe/PLAN.md` to recommend the next loop prompt and to validate invariants.

## Inputs

- Repo root path (default: current working directory)
- Optional: `--strict` validation for CI-grade checks

## Scripts

- `scripts/agentctl.py`
- `scripts/vibe_next_and_print.py`

## How to use

- Show current status:
  - Run: `python3 scripts/agentctl.py --repo-root . status --format json`
- Recommend next loop:
  - Run: `python3 scripts/agentctl.py --repo-root . next --format json`
- Validate invariants:
  - Run: `python3 scripts/agentctl.py --repo-root . validate --format json`
  - Strict mode (recommended in CI): add `--strict`
- Print the next loop prompt body directly:
  - Run: `python3 scripts/vibe_next_and_print.py --repo-root . --show-decision`
  - The helper uses the same CODEX_HOME-aware layout detection as `tools/bootstrap.py` so it works from both repo trees and global installs.

## Intended usage pattern

1) Run `next` to obtain `recommended_prompt_id`.
2) Use the `vibe-prompts` skill to print the corresponding prompt body.
3) Execute that prompt loop in the agent session.
4) Select next loop from `next`. Repeat until dispatcher returns stop or blocking.

The `vibe_next_and_print.py` helper wraps `agentctl.py` and `prompt_catalog.py`, prints the decision JSON (when `--show-decision` is set), and then emits the prompt body from the catalog. It locates the installed `vibe-prompts` skill via the same CODEX_HOME-aware logic as `tools/bootstrap.py` so it works from both repo sources and global installs.

This skill intentionally does not implement product code by itself; it selects and gates the next action.
