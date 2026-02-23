---
name: continuous-documentation
description: Continuous runner for the continuous-documentation workflow across supported agents.
version: "1.0.0"
agents:
  - codex
  - claude
  - gemini
  - copilot
dependencies:
  - vibe-run
---
# continuous-documentation

## Purpose

Run the `continuous-documentation` workflow in continuous mode until the dispatcher
returns `recommended_role: stop` (no MAJOR/MODERATE findings remain).

The workflow rotates through four prompt steps in a strict cycle:

1. `prompt.docs_gap_analysis` — detect missing documentation
2. `prompt.docs_gap_fix` — apply targeted gap fixes
3. `prompt.docs_refactor_analysis` — analyze existing doc quality
4. `prompt.docs_refactor_fix` — apply refactors

Cold starts are handled automatically — the infrastructure initialises the
rotation at step 1 when no prior runtime entry exists.

## Agent execution protocol

Run one dispatcher step at a time:

```bash
# 1. Ask the dispatcher for the next prompt
python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next --workflow continuous-documentation

# 2. Read the prompt body from the catalog
python3 .codex/skills/vibe-prompts/scripts/prompt_catalog.py .codex/skills/vibe-prompts/resources/template_prompts.md get <recommended_prompt_id>

# 3. Execute the prompt body (do the actual documentation work)

# 4. After execution, record the loop result
python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line "LOOP_RESULT: <json>"

# 5. Repeat from step 1 until recommended_role == "stop"
```

The `--workflow continuous-documentation` flag is **required** — it activates the
continuous override that ignores normal plan-state routing and selects from the
documentation prompt rotation instead.

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
The workflow stops when only `[MINOR]` findings remain.

## Scripts (wrapper)

- `scripts/continuous_documentation.py`

Wraps `vibe-run` with `--workflow continuous-documentation`. Useful for terminal
or headless modes:

```bash
# Interactive (terminal)
python3 .codex/skills/continuous-documentation/scripts/continuous_documentation.py --repo-root . --show-decision

# Headless dry-run
python3 .codex/skills/continuous-documentation/scripts/continuous_documentation.py --repo-root . --non-interactive --simulate-loop-result --max-loops 10 --show-decision
```

## Notes

- Uses the same LOOP_RESULT acknowledgement flow as `vibe-run`.
- The dispatcher handles cold starts (no `workflow_runtime.json` entry) by
  starting the rotation at step 1 — no manual initialisation is needed.
- If the dispatcher returns `requires_loop_result: true`, record the pending
  LOOP_RESULT before calling `next` again.
- Refer to `resources/documentation-guide.md` for gap/refactor heuristics.
