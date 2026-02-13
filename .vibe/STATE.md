# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 22
- Checkpoint: 22.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Make review identify top 3 improvements like a code reviewer.

## Deliverables (current checkpoint)

- Updated `prompt.checkpoint_review` in `prompts/template_prompts.md`

## Acceptance (current checkpoint)

- Review includes "Pass C: Code review for improvements".
- Each improvement tagged `[MINOR]`/`[MODERATE]`/`[MAJOR]`.
- `[MODERATE]`/`[MAJOR]` → FAIL; `[MINOR]` → fix in place + PASS.

## Work log (current session)

- 2026-02-13: Consolidated Stage 21 (DONE at 21.11). Transitioned to Stage 22 (22.0/NOT_STARTED). Added Stage 22 checkpoints to PLAN.md.
- 2026-02-13: 22.0 — dispatcher triggers and workflow flags added. All 3 acceptance criteria verified. PASS.
- 2026-02-13: 22.1 — stage design prompt rewritten for strategic focus. Includes STAGE_DESIGNED flag, "next 1-3 stages", intentional design decisions. PASS.
- 2026-02-13: Advanced to 22.2.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE
- [ ] STAGE_DESIGNED
- [ ] MAINTENANCE_CYCLE_DONE

## Evidence

(None yet — checkpoint 22.2 not started.)

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
- 2026-02-13: Stage 22 will improve vibe-run workflow with: focused stage design, enhanced review, periodic maintenance cycles, smoke test gate, preflight checks, and retrospective triggers.
