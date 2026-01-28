---
name: vibe-one-loop
description: Run exactly one Vibe workflow loop by calling agentctl to choose the next prompt and printing it from the catalog.
---

## Procedure (follow exactly)
1) Run:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) Treat the printed prompt body as the active instruction set for this run.
   You MUST execute it (read files, run commands, edit files) exactly as it says.

3) If the printed prompt is "Checkpoint Review Prompt":
   - You MUST produce a PASS/FAIL verdict.
   - If PASS, you MUST update `.vibe/STATE.md` status to DONE (and add evidence).
   - If FAIL, you MUST update `.vibe/STATE.md` status to IN_PROGRESS or BLOCKED and add issues.

4) Stop immediately after completing that one loop and updating `.vibe/STATE.md`.

Non-negotiable rule:
- Printing the prompt is NOT completing the loop. You must do the work described by the prompt.

## Failure mode

If the script fails, report the error and stop.
