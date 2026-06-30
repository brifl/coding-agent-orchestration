---
name: vibe-loop
description: Run one deterministic Vibe dispatcher step and print the selected prompt body.
---

## Purpose

Drive the Vibe workflow deterministically for a target repository.

This skill uses `.vibe/STATE.md` and `.vibe/PLAN.md` to recommend the next loop prompt and to validate invariants.

## Inputs

- Repo root path (default: current working directory)
- Optional: `--strict` validation for CI-grade checks

## Runtime helpers

- Source repo: `tools/agentctl.py` is the editable dispatcher source.
- Installed skill: `scripts/agentctl.py` is generated from `tools/agentctl.py` by bootstrap tooling.
- Skill-owned wrapper: `scripts/vibe_next_and_print.py`.

## How to use

- Show current status:
  - Source repo: `python3 tools/agentctl.py --repo-root . --format json status`
  - Installed skill directory: `python3 scripts/agentctl.py --repo-root . --format json status`
- Recommend next loop:
  - Source repo: `python3 tools/agentctl.py --repo-root . --format json next`
  - Installed skill directory: `python3 scripts/agentctl.py --repo-root . --format json next`
- Recommend next loop using a named workflow (for example `workflows/continuous-refactor.yaml`):
  - Source repo: `python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-refactor`
  - Installed skill directory: `python3 scripts/agentctl.py --repo-root . --format json next --workflow continuous-refactor`
  - Pass the workflow file stem (`continuous-refactor`), not the `.yaml` filename.
- Validate invariants:
  - Source repo: `python3 tools/agentctl.py --repo-root . --format json validate`
  - Installed skill directory: `python3 scripts/agentctl.py --repo-root . --format json validate`
  - Strict mode (recommended in CI): add `--strict`
- Record loop completion from emitted LOOP_RESULT:
  - Source repo: `python3 tools/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...}'`
  - Installed skill directory: `python3 scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...}'`
- Print the next loop prompt body directly:
  - Run: `python3 scripts/vibe_next_and_print.py --repo-root . --show-decision`
  - The helper uses the same CODEX_HOME-aware layout detection as `tools/bootstrap.py` so it works from both repo trees and global installs.

## Intended usage pattern

1) Run `next` to obtain `recommended_prompt_id`.
2) Use the `vibe-prompts` skill to print the corresponding prompt body.
3) Execute that prompt loop in the agent session.
4) Record LOOP_RESULT via `agentctl loop-result`.
5) Select next loop from `next`. Repeat until dispatcher returns stop or blocking.

The `vibe_next_and_print.py` helper wraps `agentctl.py` and `prompt_catalog.py`, prints the decision JSON (when `--show-decision` is set), and then emits the prompt body from the catalog. It prefers source `tools/` helpers when present and otherwise uses generated installed skill scripts.

This skill intentionally does not implement product code by itself; it selects and gates the next action.
