---
name: vibe-run
description: Repeatedly execute Vibe workflow loops until interrupted, stopped, credits/tool budget exhausted, all checkpoints are complete, or a blocking issue exists.
---

## Continuous run protocol (follow exactly)

Repeat the following cycle:

1) Determine the next loop prompt by running:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) If the decision indicates STOP (recommended_prompt_id == "stop"), stop immediately.

3) Execute the printed prompt body verbatim.
   - Do the work (read files, run commands, edit files).
   - Update `.vibe/STATE.md` as required by the prompt.
   - If you create issues, put them under "## Active issues" with severity.

4) Stop immediately if any of these occur:
   - You are interrupted by the user
   - You cannot run required tools/commands (budget/credits/permissions)
   - `.vibe/STATE.md` status becomes BLOCKED
   - Any issue of severity BLOCKER exists in "## Active issues"
   - `recommended_prompt_id == "stop"`

5) Otherwise, start the next cycle.

Important:
- Do not skip review. If status is IN_REVIEW, run the review loop.
- Do not run more than one loop without re-running the decision script between loops.
- If `recommended_prompt_id == "stop"`: stop.
- If it prints `prompt.advance_checkpoint`: execute that loop (edits only STATE), then continue.
