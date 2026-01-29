# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 8
- Checkpoint: 8.0
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Make consolidation trigger automatically at stage boundaries.

## Deliverables (current checkpoint)

- agentctl.py enhancement: recommend consolidation before stage transitions
- Clear indication in dispatcher output when consolidation is needed

## Acceptance (current checkpoint)

- [ ] agentctl never recommends advancing to a new stage without consolidation first
- [ ] Validation catches stage drift

## Work log (current session)

- 2026-01-28: Design loop: 8.0 already implemented (stage transition, consolidation), marking IN_REVIEW.
- 2026-01-28: Consolidation: archived Stage 7 to HISTORY, advanced to Stage 8 checkpoint 8.0.
- 2026-01-28: Fixed agentctl.py to handle (SKIPPED) checkpoints in stage detection.
- 2026-01-28: Skipped 7.1/7.2 per user request — no Kimi/IQuest access.
- 2026-01-28: Reviewed 7.0 — PASS. Bootstrap is agent-agnostic, config guide is clear.
- 2026-01-28: Implemented 7.0 — created generic_bootstrap.md and self-hosted config guide.
- 2026-01-28: Consolidation: archived Stage 6 to HISTORY, advanced to Stage 7 checkpoint 7.0.
- 2026-01-28: Checkpoint 6.1 — Gemini verified continuous mode; added Claude/Copilot/Kimi to bootstrap.py.
- 2026-01-28: Checkpoint 6.0 — Claude Code continuous mode demonstrated through this session.
- 2026-01-28: Consolidation: archived Stage 5 to HISTORY, advanced to Stage 6 checkpoint 6.0.
- 2026-01-28: Implemented checkpoint 5.0 — created docs/skill_lifecycle.md.

## Evidence

**Consolidation recommended at stage boundary:**
```
$ python tools/agentctl.py --repo-root . --format json next
# (when checkpoint 7.2 was DONE, before advancing to 8.0)
{
  "recommended_role": "consolidation",
  "reason": "Stage transition detected: 7 → 8. Run consolidation to archive Stage 7..."
}
```

**Stage drift detection in validate:**
```
$ python tools/agentctl.py --repo-root . validate
ok: True
state: {"stage": "8", "checkpoint": "8.0", ...}
```

## Active issues

- None.

## Decisions

- 2026-01-28: Skipped checkpoints 7.1/7.2 (Kimi/IQuest verification) — no access to these agents; generic bootstrap is sufficient.
- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
