---
name: vibe-run
description: Continuous Vibe loop runner for Codex.
version: "1.0.0"
dependencies:
  - vibe-loop
  - vibe-prompts
---
# vibe-run

## Purpose

Provide a continuous loop runner that repeats workflow selection until the
dispatcher returns `recommended_role == "stop"` or a hard blocker requires
human input.

## Agent execution protocol

Each loop iteration follows this sequence:

1. **Dispatch** — call `agentctl next` (with `--workflow` if running a continuous workflow)
2. **Fetch prompt** — call `prompt_catalog get <prompt_id>` using the `recommended_prompt_id` from step 1
3. **Execute** — perform the work described by the prompt body
4. **Record** — emit a `LOOP_RESULT: {...}` JSON line and record it via `agentctl loop-result`
5. **Repeat** — go to step 1; do not stop after one completed checkpoint, review pass, or
   auto-advance. Stop only when `recommended_role == "stop"` or a hard blocker
   must be surfaced to the user.

### Operating contract

- `$vibe-run` is for end-to-end backlog execution, not one-checkpoint convenience.
  When the user delegates ongoing work, keep looping through `implement`,
  `review`, `consolidation`, `context_capture`, and the next checkpoint
  selection until the dispatcher stops you.
- Returning a normal status update after one successful checkpoint is not a stop
  condition for `$vibe-run`.
- A dirty worktree is not automatically a blocker. If unrelated files are dirty
  only because of CRLF/line-ending churn or other mechanical noise, reconcile or
  stash them and continue.

### Direct commands (from repo root)

```bash
# Step 1: dispatch
python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next --workflow <workflow-name>

# Step 2: fetch prompt body
python3 .codex/skills/vibe-prompts/scripts/prompt_catalog.py prompts/template_prompts.md get <recommended_prompt_id>

# Step 4: record loop result
python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line "LOOP_RESULT: <json>"
```

### LOOP_RESULT required fields

```json
{
  "loop": "<loop_name>",
  "result": "<outcome>",
  "stage": "<current_stage>",
  "checkpoint": "<current_checkpoint>",
  "status": "<current_status>",
  "next_role_hint": "<hint>",
  "report": {
    "acceptance_matrix": [...],
    "top_findings": [
      {"impact": "MAJOR|MODERATE|MINOR", "title": "...", "evidence": "...", "action": "..."}
    ]
  }
}
```

### Cold start handling

The dispatcher and workflow engine handle cold starts automatically:
- Missing `.vibe/LOOP_RESULT.json` → protocol is initialised on first `next` call
- Missing `workflow_runtime.json` entry → rotation starts at step 1
- No manual initialisation or seeding is needed

### Requires-loop-result gate

If the dispatcher returns `requires_loop_result: true`, a previous loop's
LOOP_RESULT has not been acknowledged. Record the pending result before calling
`next` again.

## Scripts

- `scripts/vibe_run.py`

### Terminal and headless usage

```bash
# Interactive continuous mode (terminal)
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --show-decision

# Non-interactive simulation (dry-run, no executor)
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --non-interactive --simulate-loop-result --max-loops 10 --show-decision

# Headless executor mode (CI/agent automation)
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --max-loops 10 --executor "python3 ./scripts/run_one_loop.py" --show-decision

# Continuous workflow (e.g. refactor)
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --workflow continuous-refactor --show-decision
```

## Notes

- Interactive mode prints one prompt body per loop, then waits for Enter so you
  can execute that loop in your agent session before continuing.
- After each interactive loop, the runner asks for the emitted `LOOP_RESULT: {...}`
  line and records it through `agentctl loop-result` before selecting the next loop.
- Interactive users should press on to the next dispatched loop after recording a
  result; the session should not end just because one checkpoint reached
  `IN_REVIEW`, `DONE`, or auto-advanced.
- In executor mode, the command is run after each prompt and must print a
  `LOOP_RESULT: {...}` line; the runner records it automatically.
- The runner stops automatically when `agentctl` returns `recommended_role: stop`.
- In non-interactive environments without an executor, use `--simulate-loop-result`
  to auto-acknowledge LOOP_RESULT and keep cycling (dry-run semantics).
