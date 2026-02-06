# Skill sets

## Overview

Skill sets are named collections of skills that can be deployed together.
They provide a stable way to describe common bundles and allow inheritance
between sets.

## Schema

A skill set is a YAML or JSON document with the following fields:

- `name` (string, required): Unique identifier for the set.
- `description` (string, required): Human-readable summary of the set.
- `extends` (list of strings, optional): Other skill set names to inherit from.
- `skills` (list, required): Skills included in this set.
  - `name` (string, required): Skill name.
  - `version` (string, optional): Version pin or range (for example `">=1.2.0"`).

## Example

```yaml
name: vibe-base
description: Core workflow essentials.
skills:
  - name: vibe-prompts
    version: ">=1.0.0"
  - name: vibe-loop
    version: ">=1.0.0"
  - name: vibe-one-loop
    version: ">=1.0.0"
  - name: vibe-run
    version: ">=1.0.0"
  - name: continuous-refactor
    version: ">=1.0.0"
  - name: continuous-test-generation
    version: ">=1.0.0"
  - name: continuous-documentation
    version: ">=1.0.0"
```

```yaml
name: vibe-core
description: Default bundle for repo workflows.
extends:
  - vibe-base
skills:
  - name: vibe-review-pass
    version: ">=1.0.0"
```
