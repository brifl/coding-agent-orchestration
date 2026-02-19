# RLM Task Schema

## Purpose

`tools/rlm/validate_task.py` enforces this schema before any RLM run starts.
The validator fails fast on malformed inputs and reports file/line diagnostics.

## Required top-level fields

- `task_id` (string)
- `query` (string)
- `context_sources` (array)
- `bundle` (object)
- `mode` (`baseline` | `subcalls`)
- `provider_policy` (object)
- `limits` (object)
- `outputs` (object)
- `trace` (object)

## Field details

### `context_sources[]`

Each source entry must be an object with:
- `type` (string; for example `file`, `dir`, `snapshot`)
- `path` (string)

Optional fields:
- `include` (array of strings)
- `exclude` (array of strings)

### `bundle`

- `chunking_strategy` (string)
- `max_chars` (positive integer)

### `provider_policy`

- `primary` (string)
- `allowed` (non-empty array of strings)
- `fallback` (array of strings)

### `limits`

- `max_root_iters` (integer >= 1)
- `max_depth` (integer >= 0)
- `max_subcalls_total` (integer >= 0)
- `max_subcalls_per_iter` (integer >= 0)
- `timeout_s` (integer >= 1)
- `max_stdout_chars` (integer >= 1)

### `outputs`

- `final_path` (string)
- `artifact_paths` (array of strings)

### `trace`

- `trace_path` (string)
- `redaction_mode` (string)

## Example (valid)

See `tasks/rlm/example.json`.

## Usage

```bash
python3 tools/rlm/validate_task.py tasks/rlm/example.json
```

## Example invalid output

```text
INVALID: tasks/rlm/malformed_missing_query.json
tasks/rlm/malformed_missing_query.json:1: Missing required top-level field 'query'. (field: query)
```
