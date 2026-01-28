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
