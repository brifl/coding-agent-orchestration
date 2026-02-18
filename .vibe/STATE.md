# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 23
- Checkpoint: 23.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define the `PipelineConfig` schema and the `agentctl plan` CLI entry point with argument parsing, config resolution, and dry-run stub.

## Deliverables (current checkpoint)

- `tools/plan_pipeline.py` — `PipelineConfig` dataclass (problem_statement, provider, dry_run, output_path, overwrite)
- `agentctl plan` subcommand wired into `tools/agentctl.py`
- Config resolution: repo-local `.vibe/plan_pipeline.json` overrides global `~/.vibe/plan_pipeline.json`
- Fail-fast validation: missing problem statement, output-path conflict (exists + no --overwrite), missing provider config

## Acceptance (current checkpoint)

- `agentctl plan --help` shows all flags.
- Running without `--problem-statement` exits with a clear error.
- Running with `--dry-run` prints "(dry run — no files written)" without touching disk.

## Work log (current session)

- 2026-02-18: Stage 22 (Vibe-Run Workflow Improvements) complete. 6 checkpoints (22.0–22.5). Archived to HISTORY.md. Advancing to Stage 23.
- 2026-02-18: Retrospective: [Stage 22.5] demo commands must be subprocess-portable. RETROSPECTIVE_DONE set.
- 2026-02-18: Stage design for 23.0–23.4. Decisions: @dataclass PipelineConfig, Protocol-based PipelineProvider (injectable), config resolution via json files, resume via step output files. STAGE_DESIGNED set.
- 2026-02-18: Maintenance cycle (docs, stage 23%3==2). Top gaps: concepts.md missing workflow flags [MAJOR], no agentctl_reference.md [MAJOR], stop conditions stale [MODERATE]. MAINTENANCE_CYCLE_DONE set.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [x] STAGE_DESIGNED
- [x] MAINTENANCE_CYCLE_DONE
- [x] RETROSPECTIVE_DONE

## Evidence

(None yet — checkpoint 23.0 not started.)

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
