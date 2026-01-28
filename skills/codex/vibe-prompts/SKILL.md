# vibe-prompts

## Purpose

Provide deterministic access to the Vibe prompt catalog.

This skill can:
- list available prompt IDs/titles from `resources/template_prompts.md`
- print a prompt body by stable ID (or title) so it can be pasted into a chat or used as context

## Inputs

- Prompt identifier (preferred): stable ID like `prompt.onboarding`
- Prompt title (fallback): exact header title

## Resources

- `resources/template_prompts.md` (canonical prompt catalog; synced from `prompts/template_prompts.md`)

## Scripts

- `scripts/prompt_catalog.py`
- `scripts/vibe_get_prompt.py`

## How to use

- List prompts:
  - Run: `python3 scripts/prompt_catalog.py resources/template_prompts.md list`
- Get a prompt body:
  - Run: `python3 scripts/vibe_get_prompt.py resources/template_prompts.md prompt.onboarding`
  - `vibe_get_prompt.py` wraps `prompt_catalog.py get` and prints only the prompt body so it can be pasted directly into a loop

## Output

The script prints the prompt body (no fences) to stdout.
