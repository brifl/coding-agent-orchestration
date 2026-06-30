---
name: vibe-prompts
description: Deterministic access to the Vibe prompt catalog.
---
# vibe-prompts

## Purpose

Provide deterministic access to the Vibe prompt catalog.

This skill can:
- list available prompt IDs/titles from the prompt catalog
- print a prompt body by stable ID (or title) so it can be pasted into a chat or used as context

## Inputs

- Prompt identifier (preferred): stable ID like `prompt.onboarding`
- Prompt title (fallback): exact header title

## Resources

- Source repo: `prompts/template_prompts.md` is the single editable catalog.
- Installed skill: `resources/template_prompts.md` is generated from the source catalog by bootstrap tooling.

## Scripts

- Source repo: `tools/prompt_catalog.py` is the editable parser source.
- Installed skill: `scripts/prompt_catalog.py` is generated from `tools/prompt_catalog.py` by bootstrap tooling.
- Skill-owned wrapper: `scripts/vibe_get_prompt.py`.

## How to use

- List prompts:
  - Source repo: `python3 tools/prompt_catalog.py prompts/template_prompts.md list`
  - Installed skill directory: `python3 scripts/prompt_catalog.py resources/template_prompts.md list`
- Get a prompt body:
  - Source repo: `python3 tools/prompt_catalog.py prompts/template_prompts.md get prompt.stage_design`
  - Installed skill directory: `python3 scripts/vibe_get_prompt.py resources/template_prompts.md prompt.stage_design`
  - `vibe_get_prompt.py` wraps `prompt_catalog.py get` and prints only the prompt body so it can be pasted directly into a loop

## Output

The script prints the prompt body (no fences) to stdout.
