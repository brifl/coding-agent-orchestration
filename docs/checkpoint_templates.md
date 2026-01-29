# Checkpoint Templates

Checkpoint templates provide reusable scaffolds for PLAN.md checkpoints.
Templates live in `templates/checkpoints/` and are rendered by
`tools/checkpoint_templates.py`.

## Template schema

Templates are stored as `.yaml` files using a minimal YAML subset
(mapping + lists + simple scalars).

Required fields:
- `name`: template id (matches filename stem)
- `title`: checkpoint title
- `description`: short summary
- `parameters`: list of parameter objects
- `objective`: single-line objective
- `deliverables`: list of deliverable bullets
- `acceptance`: list of acceptance bullets
- `demo_commands`: list of demo commands (backticks recommended)
- `evidence`: list of evidence bullets

Parameter object fields:
- `name`: placeholder name (used as `{{name}}`)
- `description`: what the parameter represents
- `required`: true/false
- `default`: optional default value

## Placeholder syntax

Use `{{param_name}}` inside strings to substitute provided values.

## Example template

```yaml
name: add-endpoint
title: Add API endpoint
description: Add a new HTTP endpoint with routing and contract updates.
parameters:
  - name: endpoint
    description: API path, e.g. /users
    required: true
objective: Add the {{endpoint}} endpoint and wire it into {{module_path}}.
deliverables:
  - Implement handler for {{endpoint}}.
  - Register route in {{module_path}}.
acceptance:
  - Endpoint responds with expected status and schema.
  - Routing changes are covered by tests.
demo_commands:
  - "`python -m pytest -k {{endpoint}}`"
evidence:
  - Test output showing the new endpoint coverage.
```

## Commands

List templates:

```
python tools/checkpoint_templates.py list
```

Preview a template:

```
python tools/checkpoint_templates.py preview add-endpoint --endpoint /users
```

Instantiate a template (ready to paste into PLAN.md):

```
python tools/checkpoint_templates.py instantiate fix-bug --issue ISSUE-123
```

## Parser constraints

- Only simple scalars and lists are supported.
- Avoid block scalars (`|`/`>`). Use single-line strings instead.
- Comments are allowed but ignored.
