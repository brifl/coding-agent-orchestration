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

- `resources/template_prompts.md` (canonical prompt catalog; synced by bootstrap)

## Scripts

- `scripts/prompt_catalog.py`

## How to use

- List prompts:
  - Run: `python3 scripts/prompt_catalog.py resources/template_prompts.md list`
- Get a prompt body:
  - Run: `python3 scripts/prompt_catalog.py resources/template_prompts.md get <prompt_id_or_title>`

## Output

The script prints the prompt body (no fences) to stdout.
