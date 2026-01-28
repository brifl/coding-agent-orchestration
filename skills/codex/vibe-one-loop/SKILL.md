---
name: vibe-one-loop
description: Run exactly one Vibe workflow loop by calling agentctl to choose the next prompt and printing it from the catalog.
---

## Procedure (loop relentlessly until blocked or checkpoints are complete)

1) Run:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) Treat the printed prompt body as the active instruction set for this loop.
   You MUST execute it (read files, run commands, edit files) exactly as it says.

3) If the printed prompt is "Checkpoint Review Prompt":
   - You MUST produce a PASS/FAIL verdict.
   - If PASS, you MUST update `.vibe/STATE.md` status to DONE (and add evidence).
   - If FAIL, you MUST update `.vibe/STATE.md` status to IN_PROGRESS or BLOCKED and add issues.

4) After updating `.vibe/STATE.md`, immediately re-run this procedure if:
   - there is another checkpoint defined in `.vibe/PLAN.md`,
   - and `.vibe/STATE.md` does not list a blocking issue.
   Stop only when a blocking issue appears or the backlog of defined checkpoints is exhausted.

Non-negotiable rule:
- Printing the prompt is NOT completing the loop. You must do the work described by the prompt.

## Failure mode

If the script fails, report the error as a blocking issue in `.vibe/STATE.md` and stop.
