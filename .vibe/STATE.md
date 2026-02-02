# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 13A
- Checkpoint: 13A.0
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Update agentctl.py to recognize `(SKIP)` as a checkpoint/stage heading marker. Skipped checkpoints are parsed but bypassed during advance. They are NOT treated as done and NOT archived during consolidation.

## Deliverables (current checkpoint)

- `tools/agentctl.py` — updated regex in `_parse_plan_checkpoint_ids` to include `SKIP` in the marker alternation
- `tools/agentctl.py` — new `_is_checkpoint_skipped()` helper
- `tools/agentctl.py` — updated `_recommend_next` advance loop to skip over `(SKIP)` checkpoints
- `tools/agentctl.py` — updated `_is_checkpoint_marked_done` to NOT match `(SKIP)`
- `tools/agentctl.py` — updated heading parsers to handle `(SKIP)` prefix
- Consolidation prompt awareness: `(SKIP)` items preserved during cleanup

## Acceptance (current checkpoint)

- `(SKIP)` checkpoints appear in parsed checkpoint ID list but are skipped during advance
- `(SKIP)` checkpoints are not archived or removed during consolidation
- Removing `(SKIP)` from a heading makes the checkpoint active and picked up in order
- `agentctl validate` passes with `(SKIP)` markers present
- `agentctl next` correctly skips over `(SKIP)` checkpoints when advancing

## Work log (current session)
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

- `prompts/template_prompts.md` consolidation step now includes: "Preserve any stages/checkpoints marked (SKIP); they are deferred, not completed."
- `python3 tools/agentctl.py --repo-root . --format json validate` → `{"ok": true, "errors": []}`
- `python3 tools/agentctl.py --repo-root . --format json next` → `{"recommended_role": "review", "reason": "Checkpoint status is IN_REVIEW."}`
- `agentctl next` synthetic repo (with SKIP 1.1) → `{"reason": "Checkpoint is DONE; next checkpoint is 1.2."}`
- `agentctl next` synthetic repo (without SKIP 1.1) → `{"reason": "Checkpoint is DONE; next checkpoint is 1.1."}`

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
