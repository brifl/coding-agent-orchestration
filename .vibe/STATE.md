# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 13A
- Checkpoint: 13A.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Add unit and integration tests covering (SKIP) parsing, advance-over-skip, and consolidation preservation.

## Deliverables (current checkpoint)

- `tests/workflow/test_skip_marker.py` — dedicated test module for (SKIP) behavior
- Tests: checkpoint parser includes (SKIP) IDs, advance skips them, `_is_checkpoint_skipped` returns correct values, consolidation preserves (SKIP) items, removing (SKIP) reactivates checkpoint

## Acceptance (current checkpoint)

- All tests pass with `pytest tests/workflow/test_skip_marker.py`
- No regressions in existing tests: `pytest tests/`

## Work log (current session)
- 2026-02-02: Re-ran pytest with --capture=sys; tests pass; status set to IN_REVIEW.
- 2026-02-02: Implemented 13A.1 tests; pytest -v capture fails (FileNotFoundError); status set to BLOCKED.
- 2026-02-02: Advanced checkpoint 13A.0 → 13A.1; status set to NOT_STARTED.
- 2026-02-02: Review PASS — 13A.0 acceptance met; status set to DONE.
- 2026-02-02: Added consolidation prompt rule to preserve (SKIP) items; ran demo commands + skip behavior check; status set to IN_REVIEW.
- 2026-02-02: Review FAIL — consolidation prompt lacks (SKIP) preservation guidance; status set to IN_PROGRESS.
- 2026-02-02: Implemented 13A.0 — (SKIP) marker support in agentctl. Updated parser, advance logic, and all stage/checkpoint heading patterns. 44/44 tests pass, no regressions.
- 2026-02-02: JIT injected Stage 13A (SKIP Marker Support); advanced from 13.0 DONE to 13A.0 NOT_STARTED.
- 2026-01-30: Review PASS → status set to DONE

- 2026-01-30: Consolidated Stage 12A; advanced to Stage 13.0.
- 2026-01-30: Reviewed 12A.3 - PASS. Deliverables and acceptance criteria met.
- 2026-01-30: Added stage ordering unit + integration tests (12A.3).
- 2026-01-30: Advanced to checkpoint 12A.3.
- 2026-01-30: Implemented 12A.2 stage ID validation and duplicate detection.
- 2026-01-30: Advanced to checkpoint 12A.2.
- 2026-01-30: Implemented 12A.1 stage ordering logic updates.
- 2026-01-30: Advanced to checkpoint 12A.1.
- 2026-01-30: Reviewed 12A.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-30: Added stage ordering documentation for suffix-based stage IDs.
- 2026-01-29: Consolidated Stage 12, pruned logs, and advanced to 13.0.
- 2026-01-29: Reviewed 12.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.2 - Updated bootstrap.py and agentctl.py to use the resource resolver. Verified changes with demo commands.
- 2026-01-29: Advanced to checkpoint 12.2.
- 2026-01-29: Reviewed 12.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.1 - Implemented resource resolver and verified with demo commands.
- 2026-01-29: Advanced to checkpoint 12.1.
- 2026-01-29: Reviewed 12.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 12.0 - Defined and documented the global vs repo-local resource model.
- 2026-01-29: Resolved ISSUE-005: Corrected the status of checkpoint 11.2 to DONE, as it was already reviewed and passed.

## Evidence

- Added `tests/workflow/test_skip_marker.py` (5 tests covering parsing, skip detection, advance skip, reactivation, consolidation prompt).
- `pytest tests/workflow/test_skip_marker.py -v` → FAIL (capture FileNotFoundError; collected 0 items).
- `pytest tests/ -v` → FAIL (capture FileNotFoundError; collected 0 items).
- `pytest tests/workflow/test_skip_marker.py -v -s` → PASS (5 passed).
- `pytest tests/ -v -s` → PASS (49 passed).
- `pytest tests/workflow/test_skip_marker.py -v --capture=sys` → PASS (5 passed).
- `pytest tests/ -v --capture=sys` → PASS (49 passed).

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
