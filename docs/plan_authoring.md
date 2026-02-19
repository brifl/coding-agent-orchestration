# Plan Authoring Guide

`agentctl plan` generates a structured `PLAN.md` from a problem statement by orchestrating a sequence of LLM design prompts (ideation → feature breakdown → architecture → milestones → stages → checkpoints).

## Quick start

```bash
# Validate config without writing anything
python3 tools/agentctl.py --repo-root . plan \
  --problem-statement "Build a todo app with user auth" \
  --provider anthropic \
  --dry-run

# Generate PLAN.md (requires configured provider)
python3 tools/agentctl.py --repo-root . plan \
  --problem-statement "Build a todo app with user auth" \
  --provider anthropic

# Overwrite an existing PLAN.md
python3 tools/agentctl.py --repo-root . plan \
  --problem-statement "Redesign the API layer" \
  --provider anthropic \
  --overwrite

# Write to a custom location
python3 tools/agentctl.py --repo-root . plan \
  --problem-statement "Build a CLI tool" \
  --provider anthropic \
  --output .vibe/PLAN_draft.md
```

## CLI reference

| Flag | Description | Default |
|------|-------------|---------|
| `--problem-statement` | What to build (required unless set in config) | — |
| `--provider` | LLM provider: `anthropic`, `openai`, etc. | — |
| `--dry-run` | Validate config and print settings; skip all LLM calls | `false` |
| `--output` | Output path for generated PLAN.md | `.vibe/PLAN.md` |
| `--overwrite` | Overwrite output file if it already exists | `false` |
| `--resume RUN_ID` | Resume a previous interrupted run by run ID | — |

## Provider configuration

Provider credentials are **never** stored in config files — use environment variables.

Supported providers and their expected env vars:

| Provider | Env var |
|----------|---------|
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `OPENAI_API_KEY` |

Provider settings (not secrets) can be configured in JSON:

**Repo-local** `.vibe/plan_pipeline.json` (takes priority over global):
```json
{
  "provider": "anthropic",
  "provider_options": {}
}
```

**Global** `~/.vibe/plan_pipeline.json`:
```json
{
  "provider": "openai"
}
```

Resolution order (highest wins): CLI flags → repo-local config → global config.

## Pipeline steps

The plan authoring pipeline runs these 6 prompts in sequence:

1. `prompt.ideation` — brainstorm features from the problem statement
2. `prompt.feature_breakdown` — decompose features into sub-features
3. `prompt.architecture` — design system architecture
4. `prompt.milestones` — break architecture into milestones
5. `prompt.stages_from_milestones` — convert milestones to stages
6. `prompt.checkpoints_from_stage` — break stages into checkpoints

Each step's output is saved to `.vibe/plan_pipeline/<run_id>/step_<N>_<name>.json`.

## Resuming an interrupted run

If a run is interrupted (network failure, rate limit, etc.), resume it using the run ID printed during execution:

```bash
# Resume from step where failure occurred
python3 tools/agentctl.py --repo-root . plan \
  --problem-statement "Build a todo app" \
  --provider anthropic \
  --resume abc12345
```

Resume behavior:
- Steps with existing output files are **loaded from disk** (no provider call)
- Steps with missing output files are **re-executed**
- To re-run a specific step, delete its output file before resuming

## Complexity warnings

Generated checkpoints are checked against the complexity budget:

| Section | Budget |
|---------|--------|
| Deliverables | 5 items |
| Acceptance | 6 items |
| Demo commands | 4 items |

Over-budget checkpoints emit a `WARNING:` line to stderr but do **not** block writing. Consider splitting over-budget checkpoints manually after generation.

## Validating the generated plan

```bash
python3 tools/agentctl.py --repo-root . validate --strict
```

The generated PLAN.md is designed to pass validation out of the box. If validation fails, check that STATE.md's `Stage` and `Checkpoint` pointers match a stage/checkpoint in the generated PLAN.md.
