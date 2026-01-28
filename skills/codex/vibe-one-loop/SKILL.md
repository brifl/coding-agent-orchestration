---
name: vibe-one-loop
description: Run exactly one Vibe workflow loop by calling agentctl to choose the next prompt and printing it from the catalog.
---

## Procedure (follow exactly)

1) Run:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) Use the printed prompt body as the instruction for the loop.
   - Execute it verbatim.
   - Respect all stop conditions.

3) Update `.vibe/STATE.md` as required by the loop.

4) Stop. Do not run a second loop.

## Failure mode

If the script fails, report the error and stop.
