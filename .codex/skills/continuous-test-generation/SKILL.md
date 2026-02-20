---
name: continuous-test-generation
description: Continuous runner for the continuous-test-generation workflow across supported agents.
version: "1.0.0"
agents:
  - codex
  - claude
  - gemini
  - copilot
dependencies:
  - vibe-run
---
# continuous-test-generation

## Purpose

Run the `continuous-test-generation` workflow in continuous mode until the
dispatcher returns `recommended_role: stop` (only `[MINOR]` test gaps remain).

The workflow rotates through three prompt steps in a strict cycle:

1. `prompt.test_gap_analysis` — identify untested code paths (runs every 3rd checkpoint)
2. `prompt.test_generation` — generate tests for identified gaps
3. `prompt.test_review` — review generated tests for correctness

Cold starts are handled automatically — the infrastructure initialises the
rotation at step 1 when no prior runtime entry exists.

## Agent execution protocol

Run one dispatcher step at a time:

```bash
# 1. Ask the dispatcher for the next prompt
python3 tools/agentctl.py --repo-root . --format json next --workflow continuous-test-generation

# 2. Read the prompt body from the catalog
python3 tools/prompt_catalog.py prompts/template_prompts.md get <recommended_prompt_id>

# 3. Execute the prompt body (do the actual test generation work)

# 4. After execution, record the loop result
python3 tools/agentctl.py --repo-root . --format json loop-result --line "LOOP_RESULT: <json>"

# 5. Repeat from step 1 until recommended_role == "stop"
```

The `--workflow continuous-test-generation` flag is **required** — it activates
the continuous override that ignores normal plan-state routing and selects from
the test generation prompt rotation instead.

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
The workflow stops when only `[MINOR]` test gaps remain.

## Scripts (wrapper)

- `scripts/continuous_test_generation.py`

Wraps `vibe-run` with `--workflow continuous-test-generation`. Useful for
terminal or headless modes:

```bash
# Interactive (terminal)
python3 .codex/skills/continuous-test-generation/scripts/continuous_test_generation.py --repo-root . --show-decision

# Headless dry-run
python3 .codex/skills/continuous-test-generation/scripts/continuous_test_generation.py --repo-root . --non-interactive --simulate-loop-result --max-loops 10 --show-decision
```

## Notes

- Uses the same LOOP_RESULT acknowledgement flow as `vibe-run`.
- The dispatcher handles cold starts (no `workflow_runtime.json` entry) by
  starting the rotation at step 1 — no manual initialisation is needed.
- If the dispatcher returns `requires_loop_result: true`, record the pending
  LOOP_RESULT before calling `next` again.
- `test_gap_analysis` has an `every: 3` frequency gate — the dispatcher
  automatically skips it on non-matching checkpoints and rotates to the next
  eligible step.
- Refer to `resources/test-generation-guide.md` for high-value test target
  heuristics.
