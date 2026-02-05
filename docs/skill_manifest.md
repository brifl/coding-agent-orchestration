# Skill manifest format

## Overview

Codex skills require a `SKILL.md` file with YAML front matter. The front matter must include
at least `name` and `description`. Additional fields (for example `version` or `dependencies`)
may be included for internal tooling, but Codex only requires the two core fields.

## Required front matter

- `name` (string): Unique skill identifier.
- `description` (string): Short, human-readable summary.

## Optional front matter

- `version` (string): SemVer or internal version tag.
- `dependencies` (list): Other skills required by this skill.

## Example

```markdown
---
name: vibe-loop
description: Run a single Vibe workflow loop.
version: "1.0.0"
dependencies:
  - vibe-prompts
---

# vibe-loop

Skill docs go here.
```
