# Workflow schema

## Overview

Workflows define ordered steps the agent can execute with triggers and
conditions. They are stored as YAML or JSON.

## Schema

Required fields:
- `name` (string): Unique workflow identifier.
- `description` (string): Short summary.
- `triggers` (list): When the workflow runs.
- `steps` (list): Ordered steps.

Triggers:
- `type`: one of `manual`, `on-status`, `on-issue`, `scheduled`
- `value`: trigger detail (for example `IN_REVIEW`, `BLOCKER`, cron expression)

Steps:
- `prompt_id`: prompt catalog ID to run
- `condition` (optional): expression or label gate
- `every` (optional): frequency (for example `3` for every 3rd checkpoint)

## Example

```yaml
name: refactor-cycle
description: Periodic refactoring loop.
triggers:
  - type: scheduled
    value: "0 9 * * 1"
steps:
  - prompt_id: prompt.refactor_scan
  - prompt_id: prompt.refactor_execute
  - prompt_id: prompt.refactor_verify
```

```yaml
name: auto-triage
description: Auto-triage on blockers.
triggers:
  - type: on-issue
    value: BLOCKER
steps:
  - prompt_id: prompt.issues_triage
```
