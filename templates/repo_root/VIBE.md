# VIBE

This repo uses the Vibe coding-agent workflow.

## Start here (read order)

1) `AGENTS.md` (execution contract)
2) `.vibe/STATE.md` (current focus: stage/checkpoint/status)
3) `.vibe/PLAN.md` (checkpoint backlog + acceptance criteria)
4) `.vibe/HISTORY.md` (optional context; non-authoritative)

## Working files

Project-specific workflow files live under `.vibe/` and are typically gitignored:
- `.vibe/STATE.md`
- `.vibe/PLAN.md`
- `.vibe/HISTORY.md`

## How to proceed

- Use the next-step recommendation from your orchestration tools (if installed), or
- Use the prompt catalog (`template_prompts.md` in your orchestration kit) to run one loop:
  - Stage Design → Implementation → Review → Triage (as needed) → Consolidation (as needed)

Log an issue in .vibe/STATE.md and stop if you hit missing info, conflicting instructions, or any scope-changing decision point.

## Workflow

* `IN_PROGRESS` → dispatcher picks implementation → loop ends → dispatcher continues
* `IN_REVIEW` → dispatcher picks review → PASS sets `DONE` → dispatcher picks advance → continues
* `DONE` and no next checkpoint → dispatcher returns `stop` → continuous runner exits
* `BLOCKED` or `BLOCKER` issue → dispatcher returns `issues_triage` (or stop if you choose) → runner handles accordingly
