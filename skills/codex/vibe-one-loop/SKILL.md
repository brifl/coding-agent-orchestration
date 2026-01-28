---
name: vibe-one-loop
description: Run exactly one Vibe workflow loop (decide next prompt, execute it, update .vibe/STATE.md), then stop.
---

## Procedure (single loop only)

1) Run:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) Execute the printed prompt body verbatim.
   - Do the work described (read files, run commands, edit files).
   - Update `.vibe/STATE.md` as required by the prompt.

3) Stop immediately after completing that one loop.
- Do not run a second loop.
- Do not re-run the script unless the printed prompt explicitly requires it.

## Failure mode

If the script fails, report the error and stop.
