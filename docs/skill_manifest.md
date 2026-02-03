# Skill manifest schema

## Overview

Each skill ships with a `SKILL.yaml` or `SKILL.json` manifest that describes
compatibility, dependencies, and entry points. Manifests are intended to be
machine-readable and stable for tooling.

## Fields

Required:
- `name` (string): Unique skill identifier.
- `version` (string): SemVer version or compatible version constraint.
- `description` (string): Short, human-readable summary.
- `agents` (list of strings): Compatible agent runtimes (for example `codex`, `claude`).
- `dependencies` (list): Other skills required by this skill.
  - `name` (string): Skill name.
  - `version` (string, optional): Version constraint (for example `">=1.2.0"`).
- `entry_points` (list): Commands or scripts that expose the skill.
  - `name` (string): Entry point name.
  - `command` (string): Command to invoke.

Optional:
- `capabilities` (list of strings): Required capabilities (for example `filesystem`, `network`).
- `metadata` (object): Implementation-specific details.

## Example (YAML)

```yaml
name: vibe-loop
version: "1.0.0"
description: Run a single Vibe workflow loop.
agents:
  - codex
  - claude
dependencies:
  - name: vibe-prompts
    version: ">=1.0.0"
capabilities:
  - filesystem
  - process
entry_points:
  - name: loop
    command: "python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision"
```
