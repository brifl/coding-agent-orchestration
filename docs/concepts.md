# Concepts

## Skill Sets

A repo can declare a skill set in `.vibe/config.json` to add optional skills and prompt catalogs
without changing behavior when the file is absent.

Example:

```json
{
  "name": "minimal",
  "skill_folders": [],
  "prompt_catalogs": []
}
```

Fields:
- `name`: label for the skill set (string).
- `skill_folders`: additional skill directories to load (array of paths).
- `prompt_catalogs`: additional prompt catalog files (array of paths).

Skill precedence:
- Repo-local skills live in `.vibe/skills` and take precedence over global skills with the same name.
- Global skills remain in the Codex install directory and are never overwritten by repo-local installs.

## Manual execution fallback (non-tool agents)

If an agent cannot edit files or run commands, it should still execute **exactly one loop** by
producing explicit instructions for a human (or tool-enabled agent) to apply. The fallback is:

1) Read `AGENTS.md`, `.vibe/STATE.md`, `.vibe/PLAN.md`.
2) Decide the next loop (design / implement / review / triage / consolidation / improvements).
3) Provide the concrete file edits or commands a tool-enabled operator should perform.
4) Stop after one loop and wait for the updated `.vibe/STATE.md`.

This keeps single-loop parity while respecting environments without direct tool access.
