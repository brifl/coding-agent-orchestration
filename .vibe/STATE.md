# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 19A
- Checkpoint: 19A.0
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Build a scanner that indexes multiple directories.

## Deliverables (current checkpoint)

- `skills/rag-index/scanner.py` — recursive directory scanner
- Configurable: include/exclude patterns, file types, depth
- Output: file manifest with metadata (path, size, mtime, type)

## Acceptance (current checkpoint)

- Scans multiple directories in one pass
- Respects gitignore and custom exclusions

## Work log (current session)
- 2026-02-03: Updated plan to Stage 19A; unblocked and set checkpoint 19A.0 to NOT_STARTED.
- 2026-02-03: Blocked on Stage 20.0 scope/placement; clarification requested.
- 2026-02-03: Consolidated Stage 19; advanced to checkpoint 20.0; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 19.2 acceptance met; status set to DONE.
- 2026-02-03: Added demo/feedback prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 19.1 → 19.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 19.1 acceptance met; status set to DONE.
- 2026-02-03: Added test gap/generation/review prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 19.0 → 19.1; status set to NOT_STARTED.
- 2026-02-03: Detected checkpoint headings for 19.1/19.2 not parsed by agentctl; logged ISSUE-007.
- 2026-02-03: Review PASS — 19.0 acceptance met; status set to DONE.
- 2026-02-03: Added refactor scan/execute/verify prompts; ran demo command; status set to IN_REVIEW.
## Workflow state
- Name: refactor-cycle
- Last run: 1 step(s)
- Steps: prompt.checkpoint_implementation

## Evidence

(None yet)

## Active issues

(None)

## Decisions

(No decisions)
