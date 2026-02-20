---
name: vibe-one-loop
description: Compatibility alias for one-shot Vibe loop execution.
version: "1.0.0"
dependencies:
  - vibe-loop
  - vibe-prompts
---
# vibe-one-loop

## Purpose

Provide a stable single-loop entrypoint for Codex sessions.

This skill is an alias of `vibe-loop` and exists for compatibility with docs
and prompt packs that reference `$vibe-one-loop`.

## Scripts

- `scripts/vibe_one_loop.py`

## How to use

- Run exactly one loop and stop:
  - `python3 scripts/vibe_one_loop.py --repo-root . --show-decision`
- Optional: provide an explicit prompt catalog path:
  - `python3 scripts/vibe_one_loop.py --repo-root . --catalog .codex/skills/vibe-one-loop/resources/template_prompts.md --show-decision`

## Output

Prints a single prompt body selected by the dispatcher.
