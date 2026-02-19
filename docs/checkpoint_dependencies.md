# Checkpoint Dependencies

This guide explains how to model checkpoint dependencies in `.vibe/PLAN.md`,
how validation works, and how dispatch/visualization uses the dependency graph.

## Why dependencies exist

Checkpoint dependencies let you represent non-linear work in a stage:
- Keep related work in separate checkpoints.
- Prevent dispatch from routing to work that is not ready.
- Enable parallel implementation on independent checkpoints.

Dependencies are represented as a DAG (directed acyclic graph):
- Nodes are checkpoint IDs (`N.M`).
- An edge `A -> B` means `B` depends on `A`.

## Syntax

Add an optional `depends_on:` line directly after a checkpoint heading.

Example:

```md
### 25.2 — Dispatcher integration
  depends_on: [25.1]
```

Rules:
- Value must be a bracketed list: `[X.Y, A.B]`.
- Whitespace is allowed.
- Checkpoint IDs are normalized using the same ID parser as headings.
- Checkpoints without `depends_on:` are treated as having no dependencies.

## Dependency satisfaction semantics

A dependency is satisfied only when the referenced checkpoint is marked:
- `(DONE)`, or
- `(SKIP)`.

`STATE.md` status is not used for dependency satisfaction; only `PLAN.md` markers
are consulted.

## Validation rules

`agentctl validate` runs DAG validation automatically. It reports:
- Self-dependency: checkpoint depends on itself.
- Dangling dependency: dependency points to a checkpoint ID not present in PLAN.
- Cycle: dependency cycle exists (for example `1.0 -> 1.1 -> 1.0`).
- Parse errors for malformed `depends_on:` syntax.

Run:

```bash
python3 tools/agentctl.py --repo-root . validate --strict
```

## Visualizing the graph

Use `agentctl dag` to render dependencies.

JSON output:

```bash
python3 tools/agentctl.py --repo-root . dag --format json
```

Schema:
- `nodes`: `{id, title, status, deps}`
- `edges`: `{from, to}`

Node status values:
- `DONE`
- `SKIP`
- `READY`
- `DEP_BLOCKED`

ASCII output:

```bash
python3 tools/agentctl.py --repo-root . dag --format ascii
```

ASCII markers:
- `[+]` done
- `[-]` skipped
- `[>]` ready
- `[!]` dependency blocked

## Dispatch behavior (`agentctl next`)

When current checkpoint status is `DONE`, dispatcher:
1. Finds next checkpoints in document order.
2. Skips `(DONE)` and `(SKIP)` checkpoints.
3. Skips dependency-blocked checkpoints (unmet dependencies).
4. Routes to first dependency-satisfied checkpoint.
5. Returns `stop` if all remaining checkpoints are dependency blocked.

## Parallel dispatch (`--parallel N`)

Use `agentctl next --parallel N` to request up to `N` simultaneously runnable
checkpoints.

```bash
python3 tools/agentctl.py --repo-root . --format json next --parallel 2
```

Output includes:
- `recommended_role` (single-role compatibility field)
- `recommended_roles` (list of up to `N` runnable checkpoints)

Readiness for `recommended_roles` is based on:
- Not marked `(DONE)`/`(SKIP)`.
- All dependencies satisfied.

## Worked example: diamond dependency

Plan snippet:

```md
### (DONE) 1.0 — Foundation

### 1.1 — Path A
  depends_on: [1.0]

### 1.2 — Path B
  depends_on: [1.0]

### 1.3 — Merge
  depends_on: [1.1, 1.2]
```

Interpretation:
- `1.1` and `1.2` are both runnable after `1.0` is done.
- `1.3` remains blocked until both `1.1` and `1.2` are `(DONE)` or `(SKIP)`.
- `agentctl next --parallel 2` can return `1.1` and `1.2` together.
