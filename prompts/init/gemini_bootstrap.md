ROLE
You are a coding agent joining an existing workflow.

CONTRACT
- `AGENTS.md` is the authoritative execution contract.
- `.vibe/STATE.md` is the active pointer (stage/checkpoint/status/issues).
- `.vibe/PLAN.md` is the checkpoint backlog with acceptance criteria.
- `.vibe/HISTORY.md` is non-authoritative context.

READ ORDER (do this now)
1) `AGENTS.md`
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`

REQUIRED OUTPUT
1) Echo the current focus (stage / checkpoint / status).
2) Identify the next loop to run (one of: design / implement / review / triage / consolidation / improvements).
3) State exactly what file(s) you will update in that loop.
4) Ask up to 2 clarifying questions if required; otherwise ask none.

STOP
Stop after the output. Do not begin implementation in this message.
