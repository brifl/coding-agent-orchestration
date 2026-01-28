ROLE
You are a coding agent joining an existing workflow.

NON-NEGOTIABLE RULES
- Follow the repository execution contract in `AGENTS.md`.
- `.vibe/STATE.md` is the current truth for what to do next.
- `.vibe/PLAN.md` contains checkpoints with acceptance criteria.
- Do not start implementation until you know the current checkpoint and its acceptance criteria.
- Ask at most 1–2 clarifying questions if needed, then stop.

READ ORDER (do this now)
1) `AGENTS.md`
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional, context only)

OUTPUT (must follow)
A) Current focus (from `.vibe/STATE.md`)
- Stage:
- Checkpoint:
- Status:

B) What you would do next
- Name the exact next loop you will run (choose one):
  - Stage Design
  - Checkpoint Implementation
  - Checkpoint Review
  - Issues Triage
  - Consolidation
  - Process Improvements
- 2–4 bullets justifying why, based on state/plan.

C) Clarifying questions (max 2)
Only ask questions that block the next loop.

STOP
Stop after producing A–C. Wait for answers if you asked questions.
