# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 19
- Checkpoint: 19.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define testing and coverage prompts.

## Deliverables (current checkpoint)

- `prompt.test_gap_analysis` — identify untested paths tied to risk
- `prompt.test_generation` — generate runnable tests for one gap
- `prompt.test_review` — review tests for signal/noise and maintainability

## Acceptance (current checkpoint)

- Test gap analysis output includes scenario, location, risk, proposed test type, fixture strategy
- Test generation output includes exact paths, rationale, mocks, commands
- Test review output includes coverage, brittleness, and concrete edits

## Work log (current session)
- 2026-02-03: Added test gap/generation/review prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 19.0 → 19.1; status set to NOT_STARTED.
- 2026-02-03: Detected checkpoint headings for 19.1/19.2 not parsed by agentctl; logged ISSUE-007.
- 2026-02-03: Review PASS — 19.0 acceptance met; status set to DONE.
- 2026-02-03: Added refactor scan/execute/verify prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 18; advanced to checkpoint 19.0; status set to NOT_STARTED.
- 2026-02-03: Clarified consolidation prompt to preserve future stages; resolved ISSUE-006.
- 2026-02-03: Restored Stage 21 backlog to PLAN.md after consolidation policy update.
- 2026-02-03: Synced consolidation prompt wording in skill prompt resources.
- 2026-02-03: Review PASS — 18.2 acceptance met; status set to DONE.
- 2026-02-03: Added stage/checkpoint generation prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 18.1 → 18.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 18.1 acceptance met; status set to DONE.
- 2026-02-03: Added architecture and milestones prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 18.0 → 18.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 17.2 acceptance met; status set to DONE.
- 2026-02-03: Added preset workflows; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 17.1 → 17.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 17.1 acceptance met; status set to DONE.
- 2026-02-03: Implemented workflow engine + agentctl workflow selection; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 17.0 → 17.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 17.0 acceptance met; status set to DONE.
- 2026-02-03: Added workflow schema doc; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 16; advanced to checkpoint 17.0; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 16.2 acceptance met; status set to DONE.
- 2026-02-03: Ran sync demo for 16.2; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 16.1 → 16.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 16.1 acceptance met; status set to DONE.
- 2026-02-03: Ran subscription demo for 16.1; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 16.0 → 16.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 16.0 acceptance met; status set to DONE.
- 2026-02-03: Verified skill source docs for 16.0; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 15; advanced to checkpoint 16.0; status set to NOT_STARTED.

## Workflow state
- Name: refactor-cycle
- Last run: 1 step(s)
- Steps: prompt.checkpoint_implementation

## Evidence

- `python3 tools/prompt_catalog.py prompts/template_prompts.md get prompt.test_gap_analysis` prints the new test gap analysis prompt.

## Active issues

(None)

## Decisions

(No decisions)
