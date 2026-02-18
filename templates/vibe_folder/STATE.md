# STATE

## Session read order

1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 0
- Checkpoint: 0.0
- Status: NOT_STARTED  <!-- one of: NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)
<!-- 1 sentence. Keep in sync with PLAN.md for the active checkpoint. -->

## Deliverables (current checkpoint)
<!-- Concrete files/modules/behaviors. Keep in sync with PLAN.md for the active checkpoint. -->

## Acceptance (current checkpoint)
<!-- Verifiable conditions. Keep in sync with PLAN.md for the active checkpoint. -->

## Work log (current session)
<!-- Append-only bullets for what changed and why. Prefer file/line references. -->

## Evidence
<!-- Paste command outputs, links to commits/PRs, screenshots, etc. -->
<!-- Keep this short and relevant to acceptance. -->

## Workflow state
<!-- Dispatcher flags. Checked = active/needed. Cleared by the loop that handles each flag. -->
- [ ] RUN_CONTEXT_CAPTURE
- [ ] STAGE_DESIGNED
- [ ] MAINTENANCE_CYCLE_DONE
- [ ] RETROSPECTIVE_DONE

## Active issues
<!-- Keep only active issues here. Move resolved items to HISTORY.md. -->
- [ ] ISSUE-001: <short title>
  - Impact: QUESTION <!-- QUESTION | MINOR | MAJOR | BLOCKER -->
  - Status: OPEN <!-- OPEN | IN_PROGRESS | BLOCKED | RESOLVED | DECISION_REQUIRED -->
  - Owner: agent|human
  - Unblock Condition: <what must be true to proceed>
  - Evidence Needed: <command/output/link proving resolution>
  - Notes: <optional context>

## Decisions
<!-- Only decisions that matter for future work. -->
- YYYY-MM-DD: <decision> (rationale in 1–2 lines)
