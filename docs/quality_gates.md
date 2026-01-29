# Quality Gates

Quality gates are automated checks that run before a checkpoint can be marked as `IN_REVIEW`. They help enforce code quality, and prevent regressions. Gates can be defined globally or per-checkpoint.

## Configuration

Gates are configured in `.vibe/config.json` under the `quality_gates` key.

### Global Gates

Global gates run for every checkpoint.

```json
{
  "quality_gates": {
    "global": [
      {
        "name": "Lint",
        "type": "lint",
        "command": "ruff check .",
        "required": true
      },
      {
        "name": "Type Check",
        "type": "typecheck",
        "command": "mypy .",
        "required": true
      }
    ]
  }
}
```

### Checkpoint-specific Gates

Checkpoint-specific gates run only for the specified checkpoint. They are defined under a key matching the checkpoint ID.

```json
{
  "quality_gates": {
    "9.1": [
      {
        "name": "Pytest",
        "type": "test",
        "command": "pytest",
        "required": true
      }
    ]
  }
}
```

## Gate Types

There are four types of gates:

- `test`: For running automated tests.
- `lint`: For static analysis and code style checks.
- `typecheck`: For type checking.
- `custom`: For any other custom command.

## Gate Definition Schema

Each gate is an object with the following properties:

- `name` (string, required): A human-readable name for the gate.
- `type` (string, required): One of `test`, `lint`, `typecheck`, `custom`.
- `command` (string, required): The command to execute.
- `required` (boolean, optional): If `true`, the gate must pass for the checkpoint to be accepted. Defaults to `false`.
- `pass_criteria` (object, optional): Defines the conditions for the gate to pass. If not specified, a zero exit code is considered a pass.
  - `exit_code` (number, optional): The expected exit code for a pass.
  - `stdout_contains` (string, optional): A string that must be present in the command's standard output.
  - `stderr_contains` (string, optional): A string that must be present in the command's standard error.


## Examples

### Pytest

```json
{
  "name": "Pytest",
  "type": "test",
  "command": "pytest",
  "required": true
}
```

### Ruff

```json
{
  "name": "Ruff Lint",
  "type": "lint",
  "command": "ruff check .",
  "required": true
}
```

### MyPy

```json
{
  "name": "MyPy Type Check",
  "type": "typecheck",
  "command": "mypy .",
  "required": true
}
```
