# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 1
- Checkpoint: 1.2
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Ship a usable Codex global skill MVP that can (a) recommend the next loop, and (b) print the corresponding prompt body deterministically.

## Deliverables (current checkpoint)

- `skills/codex/vibe-prompts/` includes:
  - `SKILL.md`
  - `scripts/vibe_get_prompt.py`
  - `resources/template_prompts.md` synced from `prompts/template_prompts.md`
- `skills/codex/vibe-loop/` includes:
  - `SKILL.md`
  - `scripts/vibe_next_and_print.py` that respects `CODEX_HOME` when set
- `tools/bootstrap.py install-skills --global --agent codex` is reliable + idempotent
- End-to-end demo works from a bootstrapped target repo

## Acceptance (current checkpoint)

- [ ] `python3 tools/bootstrap.py install-skills --global --agent codex` installs/updates into the correct global Codex skills folder (supports `CODEX_HOME`)
- [ ] From a bootstrapped target repo, `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root .` prints a valid loop prompt body to stdout
- [ ] `agentctl next --format json` returns a `recommended_prompt_id` that exists in the prompt catalog
- [ ] Scripts fail with clear errors when `.vibe/STATE.md` or prompt catalog is missing

## Work log (current session)

- 2026-01-27: Bootstrapped this repo as a “real” example repo; populated plan/state.
- 2026-01-27: Added the vibe-prompts catalog resource, refreshed both skill SKILL.md files, made `vibe_next_and_print.py` obey CODEX_HOME, reinstalled the codex skills, and exercised the `--show-decision` demonstration path.
- 2026-01-27: Verified `agentctl next --format json` now surfaces `prompt.checkpoint_review`, confirming the scripts output a stable loop recommendation after the install changes.

## Evidence

- `python3 tools/bootstrap.py install-skills --global --agent codex`
  ```
  install-skills summary (codex global)
  - Destination: C:\Users\brian\.codex\skills
  - Skills: vibe-prompts, vibe-loop
  - Updated:
    - C:\Users\brian\.codex\skills\vibe-prompts\SKILL.md
    - C:\Users\brian\.codex\skills\vibe-loop\SKILL.md
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\vibe_next_and_print.py
    - C:\Users\brian\.codex\skills\vibe-prompts\scripts\vibe_get_prompt.py
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\vibe_next_and_print.py
    - C:\Users\brian\.codex\skills\vibe-prompts\resources\template_prompts.md
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\agentctl.py
    - C:\Users\brian\.codex\skills\vibe-prompts\scripts\prompt_catalog.py
  ```
- `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`
  ```
  ROLE: Primary software engineer

  TASK
  Advance the project by EXACTLY ONE checkpoint from .vibe/PLAN.md (the checkpoint currently marked CURRENT in .vibe/STATE.md), then stop.

  GENERAL RULES
  - Treat .vibe/STATE.md as authoritative for what to do next.
  - Implement only the current checkpoint's deliverables.
  - Keep diffs small and focused.
  - If you discover missing requirements or contradictions, add an issue to .vibe/STATE.md and stop.

  READ FIRST
  - README.md (optional)
  - AGENTS.md
  - .vibe/STATE.md
  - .vibe/PLAN.md

  EXECUTION
  1) Identify current checkpoint from .vibe/STATE.md.
  2) Locate that checkpoint entry in .vibe/PLAN.md.
  3) Implement the deliverables.
  4) Run the demo commands (or the closest equivalents).
  5) Update .vibe/STATE.md:
     - set Status to IN_REVIEW
     - add a short work log
     - add evidence snippets or command outputs
     - add issues if anything failed

  OUTPUT FORMAT
  - What you changed (files)
  - Commands you ran + results (short)
  - Evidence pasted into .vibe/STATE.md
  - Any new issues created (with severity)

  STOP CONDITION
  Stop after completing one checkpoint and updating .vibe/STATE.md. Wait for review.
  {
    "checkpoint": "1.2",
    "reason": "Checkpoint status is IN_PROGRESS.",
    "recommended_prompt_id": "prompt.checkpoint_implementation",
    "recommended_prompt_title": "Checkpoint Implementation Prompt",
    "recommended_role": "implement",
    "stage": "1",
    "status": "IN_PROGRESS"
  }
  ```
- `python tools/agentctl.py --repo-root . --format json next`
  ```
  {
    "checkpoint": "1.2",
    "reason": "Checkpoint status is IN_REVIEW.",
    "recommended_prompt_id": "prompt.checkpoint_review",
    "recommended_prompt_title": "Checkpoint Review Prompt",
    "recommended_role": "review",
    "stage": "1",
    "status": "IN_REVIEW"
  }
  ```

## Active issues

- None.

## Decisions

- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
