---
name: vibe-run
description: Continuously run Vibe loops until interrupted, out of tool budget, plan exhausted, or blocked.
---

Repeat:
1) Run:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

2) If the decision indicates no work remains (recommended_role == "stop"), stop.
3) Execute the printed prompt body verbatim.
4) Stop if `.vibe/STATE.md` becomes BLOCKED or any BLOCKER issue exists.
5) Otherwise, repeat.
