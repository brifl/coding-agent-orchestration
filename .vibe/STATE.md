# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 17
- Checkpoint: 17.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Implement a workflow engine that executes configured workflows.

## Deliverables (current checkpoint)

- `tools/workflow_engine.py` — interprets and executes workflows
- Integration with agentctl: `--workflow <name>` flag
- Workflow state tracking in STATE.md

## Acceptance (current checkpoint)

- Engine can execute multi-step workflows
- Conditions and triggers evaluated correctly

## Work log (current session)
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

- `python3 tools/workflow_engine.py run refactor-cycle` prints: `SKIP prompt.refactor_checkpoint (frequency)` then `RUN prompt.checkpoint_implementation`.
- `python3 tools/agentctl.py --repo-root . next --workflow auto-triage` recommends `prompt.issues_triage`.

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
