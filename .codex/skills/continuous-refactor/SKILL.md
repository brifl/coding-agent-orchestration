---
name: continuous-refactor
description: Continuous runner for the continuous-refactor workflow across supported agents.
version: "1.0.0"
agents:
  - codex
  - claude
  - gemini
  - copilot
dependencies:
  - vibe-run
---
# continuous-refactor

## Purpose

Run the `continuous-refactor` workflow in continuous mode until the dispatcher
returns `recommended_role: stop` (only `[MINOR]` refactoring ideas remain).

The workflow rotates through three prompt steps in a strict cycle:

1. `prompt.refactor_scan` — identify code smells and refactoring candidates
2. `prompt.refactor_execute` — apply selected refactorings
3. `prompt.refactor_verify` — verify refactored code correctness

Cold starts are handled automatically — the infrastructure initialises the
rotation at step 1 when no prior runtime entry exists.

## Agent execution protocol

Run one dispatcher step at a time:

```bash
# 1. Ask the dispatcher for the next prompt
python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-refactor

# 2. Read the prompt body from the catalog
python3 tools/prompt_catalog.py prompts/template_prompts.md get <recommended_prompt_id>

# 3. Execute the prompt body (do the actual refactoring work)

# 4. After execution, record the loop result
python3 tools/agentctl.py --repo-root . --format json loop-result --line "LOOP_RESULT: <json>"

# 5. Repeat from step 1 until recommended_role == "stop"
```

The `--workflow continuous-refactor` flag is **required** — it activates the
continuous override that ignores normal plan-state routing and selects from the
refactor prompt rotation instead.

### LOOP_RESULT format

After executing each prompt, emit a LOOP_RESULT JSON line with these required fields:

```json
{
  "loop": "implement",
  "result": "ready_for_review",
  "stage": "<current_stage>",
  "checkpoint": "<current_checkpoint>",
  "status": "<current_status>",
  "next_role_hint": "implement|review|stop",
  "report": {
    "acceptance_matrix": [],
    "top_findings": [
      {"impact": "MAJOR|MODERATE|MINOR", "title": "...", "evidence": "...", "action": "..."}
    ]
  }
}
```

Use impact tags (`[MAJOR]`, `[MODERATE]`, `[MINOR]`) in `top_findings` titles.
The workflow stops when only `[MINOR]` ideas remain.

## Scripts (wrapper)

- `scripts/continuous_refactor.py`

Wraps `vibe-run` with `--workflow continuous-refactor`. Useful for terminal
or headless modes:

```bash
# Interactive (terminal)
python3 .codex/skills/continuous-refactor/scripts/continuous_refactor.py --repo-root . --show-decision

# Headless dry-run
python3 .codex/skills/continuous-refactor/scripts/continuous_refactor.py --repo-root . --non-interactive --simulate-loop-result --max-loops 10 --show-decision
```

## Notes

- Uses the same LOOP_RESULT acknowledgement flow as `vibe-run`.
- The dispatcher handles cold starts (no `workflow_runtime.json` entry) by
  starting the rotation at step 1 — no manual initialisation is needed.
- If the dispatcher returns `requires_loop_result: true`, record the pending
  LOOP_RESULT before calling `next` again.
- Refer to `resources/refactoring-guide.md` for code smell heuristics.
