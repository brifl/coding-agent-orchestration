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

## Example

```yaml
name: vibe-base
description: Core workflow essentials.
skills:
  - name: vibe-prompts
  - name: vibe-loop
  - name: vibe-run
  - name: continuous-refactor
  - name: continuous-test-generation
  - name: continuous-documentation
```

```yaml
name: vibe-core
description: Default bundle for repo workflows.
extends:
  - vibe-base
skills:
  - name: vibe-review-pass
```
