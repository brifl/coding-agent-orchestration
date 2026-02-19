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
- Repo-local skills live in `.codex/skills` and take precedence over global skills with the same name.
- Global skills live in `$CODEX_HOME/skills` (defaults to `~/.codex/skills`) and are never overwritten by repo-local installs.

## Manual execution fallback (non-tool agents)

If an agent cannot edit files or run commands, it should still execute **exactly one loop** by
producing explicit instructions for a human (or tool-enabled agent) to apply. The fallback is:

1) Read `AGENTS.md`, `.vibe/STATE.md`, `.vibe/PLAN.md`.
2) Decide the next loop (design / implement / review / issues_triage / advance / consolidation / context_capture / improvements / stop).
3) Provide the concrete file edits or commands a tool-enabled operator should perform.
4) Stop after one loop and wait for the updated `.vibe/STATE.md`.

This keeps single-loop parity while respecting environments without direct tool access.

## Continuous mode semantics

Continuous mode is a **dispatcher-driven loop** that repeats only after the current loop
has completed and `.vibe/STATE.md` is updated. The dispatcher is re-invoked after each loop
to determine the next prompt.

Stop conditions:
- **Plan exhausted**: no next checkpoint exists in `.vibe/PLAN.md` → stop and record evidence.
- **BLOCKED state**: `.vibe/STATE.md` is set to BLOCKED → stop immediately.
- **BLOCKER issue**: any active issue marked BLOCKER → stop immediately.
- **Dispatcher recommends stop**: respect a `stop` recommendation from `agentctl`.

This definition prevents self-looping prompts and keeps control in `agentctl` rather than
inside individual prompt bodies.

## Checkpoint dependency DAG

`PLAN.md` checkpoints can declare dependencies via `depends_on: [X.Y, ...]`, which
turns linear checkpoint ordering into a dependency graph.

Core rules:
- Dependencies are satisfied only when referenced checkpoints are marked `(DONE)` or `(SKIP)` in `PLAN.md`.
- `STATE.md` status does not satisfy dependencies by itself.
- `agentctl validate` enforces graph correctness (self-deps, dangling refs, cycles).
- `agentctl dag` renders graph structure and per-node readiness.
- `agentctl next --parallel N` can return multiple dependency-satisfied checkpoints.

See `docs/checkpoint_dependencies.md` for syntax, commands, and worked examples.
