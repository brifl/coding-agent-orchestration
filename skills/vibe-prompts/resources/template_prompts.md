# Template Prompts

## prompt.stage_design — Stage Design Prompt

```md
ROLE: Primary software architect (design pass)

TASK
Tighten the plan for the next stage or checkpoint(s) in .vibe/PLAN.md to make implementation smoother. This is not a blank-slate redesign, but meaningful restructuring is allowed.

SCOPE
- Modify only .vibe/PLAN.md and (if needed) .vibe/STATE.md.
- Do not implement product code.
- Do not add large new architecture; keep it pragmatic.
- If the current stage/checkpoint is wrong or missing, fix .vibe/STATE.md first.

SOURCE OF TRUTH (read in order)
1) AGENTS.md (optional if already read this session)
2) .vibe/STATE.md
3) .vibe/PLAN.md
4) README.md (optional)
5) .vibe/HISTORY.md (optional; non-authoritative)

PRIMARY OBJECTIVE
.vibe/PLAN.md must be a near-term plan aligned to .vibe/STATE.md:
- It MUST contain the current stage S and current checkpoint C from .vibe/STATE.md.
- It MUST NOT contain detailed plans for distant stages beyond the next 1 to 3 stages.
- Each checkpoint MUST be implementable in one focused iteration.

CHECKPOINT TEMPLATE (use this exact structure for each checkpoint)
- Objective (1 sentence)
- Deliverables (concrete files/modules/behaviors)
- Acceptance (verifiable)
- Demo commands (exact, local, minimal)
- Evidence (what to paste into .vibe/STATE.md)

OUTPUT
- Update .vibe/PLAN.md with:
  - clearer stage definitions (1–3 stages)
  - 1 to 6 checkpoints per stage (for the next stage or two)
  - acceptance criteria that are testable
- If you change the current checkpoint or stage, update .vibe/STATE.md accordingly.

STOP CONDITION
Stop this loop after updating .vibe/PLAN.md (and .vibe/STATE.md if needed). Return to dispatcher.

```

---

## prompt.checkpoint_implementation — Checkpoint Implementation Prompt

```md
ROLE: Primary software engineer

TASK
Advance the project by completing EXACTLY ONE checkpoint: the checkpoint currently indicated in .vibe/STATE.md.

GENERAL RULES
- Treat .vibe/STATE.md as authoritative for what to do next.
- Implement only the current checkpoint's deliverables.
- Keep diffs small and focused.
- If you discover missing requirements or contradictions, add an issue to .vibe/STATE.md and stop.

READ FIRST
- AGENTS.md (optional if already read this session)
- .vibe/STATE.md
- .vibe/PLAN.md
- README.md (optional)

EXECUTION (exactly one checkpoint)
1) Identify current checkpoint from .vibe/STATE.md.
2) Locate that checkpoint entry in .vibe/PLAN.md.
3) Implement the deliverables (only those deliverables).
4) Run the demo commands (or the closest equivalents; document deviations).
5) Update .vibe/STATE.md:
   - set Status to IN_REVIEW
   - add a short work log entry
   - paste evidence snippets or command outputs
   - add issues if anything failed or is unclear
   - if a blocking issue exists, set Status to BLOCKED

OUTPUT FORMAT
- Checkpoint completed: <id>
- Files changed (list)
- Commands run + short results
- Evidence pasted into .vibe/STATE.md
- Issues created/updated (if any)

STOP CONDITION
Stop after completing EXACTLY ONE checkpoint and updating .vibe/STATE.md. Return to dispatcher.

```

---

## prompt.checkpoint_review — Checkpoint Review Prompt

```md
ROLE: Primary software architect (design pass)

TASK
Tighten the plan for the next stage or checkpoint(s) in .vibe/PLAN.md to make implementation smoother. This is not a blank-slate redesign, but meaningful restructuring is allowed.

SCOPE
- Modify only .vibe/PLAN.md and (if needed) .vibe/STATE.md.
- Do not implement product code.
- Do not add large new architecture; keep it pragmatic.
- If the current stage/checkpoint is wrong or missing, fix .vibe/STATE.md first.

SOURCE OF TRUTH (read in order)
1) AGENTS.md (optional if already read this session)
2) .vibe/STATE.md
3) .vibe/PLAN.md
4) README.md (optional)
5) .vibe/HISTORY.md (optional; non-authoritative)

PRIMARY OBJECTIVE
.vibe/PLAN.md must be a near-term plan aligned to .vibe/STATE.md:
- It MUST contain the current stage S and current checkpoint C from .vibe/STATE.md.
- It MUST NOT contain detailed plans for distant stages beyond the next 1 to 3 stages.
- Each checkpoint MUST be implementable in one focused iteration.

CHECKPOINT TEMPLATE (use this exact structure for each checkpoint)
- Objective (1 sentence)
- Deliverables (concrete files/modules/behaviors)
- Acceptance (verifiable)
- Demo commands (exact, local, minimal)
- Evidence (what to paste into .vibe/STATE.md)

OUTPUT
- Update .vibe/PLAN.md with:
  - clearer stage definitions (1–3 stages)
  - 1 to 6 checkpoints per stage (for the next stage or two)
  - acceptance criteria that are testable
- If you change the current checkpoint or stage, update .vibe/STATE.md accordingly.

STOP CONDITION
Stop this loop after updating .vibe/PLAN.md (and .vibe/STATE.md if needed). Return to dispatcher.

```

---

## prompt.issues_triage — Issues Triage Prompt

```md
ROLE: Engineer / Triage

TASK
Resolve or clarify the top 1–2 active issues in .vibe/STATE.md with minimal disruption to the active checkpoint.

SCOPE
- Prefer doc/config/plan fixes.
- Only make code changes if required to unblock a BLOCKER.
- Do not expand scope.

READ FIRST
- AGENTS.md (optional if already read this session)
- .vibe/STATE.md
- .vibe/PLAN.md
- README.md (optional)

PROCESS
1) List active issues from the "Active issues" section of .vibe/STATE.md in priority order:
   BLOCKER > MAJOR > MINOR > QUESTION
2) Pick the top 1–2 issues.
3) For each selected issue:
   - determine the smallest change that resolves it
   - implement that change OR ask a clarifying question (max 2 total)
4) Update .vibe/STATE.md:
   - mark resolved issues as done (checked) or remove them if fully resolved
   - add evidence for the resolution
   - if resolution changes the plan, update .vibe/PLAN.md accordingly
   - if a BLOCKER remains unresolved, set Status to BLOCKED

OUTPUT
- Issues addressed (which ones)
- Changes made (files)
- Evidence / commands run
- Any new questions (max 2)

STOP CONDITION
Stop after resolving the selected issues or after asking blocking questions. Return to dispatcher.

```

---

## prompt.consolidation — Consolidation Prompt (docs sync + archival)

```md
ROLE: Engineering lead (mechanical docs maintenance)

TASK
Bring planning docs back into alignment with the current execution state, and archive stale plan content to reduce cognitive/compute load.

SCOPE
- Allowed files:
  - .vibe/STATE.md
  - .vibe/PLAN.md
  - .vibe/HISTORY.md
- Do not modify product code.

READ FIRST
- AGENTS.md (optional if already read this session)
- .vibe/STATE.md
- .vibe/PLAN.md
- .vibe/HISTORY.md (optional)
- README.md (optional)

PROCESS
1) Ensure .vibe/STATE.md accurately points to the current stage/checkpoint/status.
2) Ensure .vibe/PLAN.md includes:
   - the current stage/checkpoint
   - the next 1–3 stages only (near-term)
   - checkpoints using the standard template
3) Move completed or stale plan content into .vibe/HISTORY.md:
   - completed checkpoints
   - resolved issues
   - past stage notes
4) Keep .vibe/PLAN.md tight: remove historical clutter.

OUTPUT
- Summary of doc changes (short)
- Any inconsistencies found and how you resolved them

STOP CONDITION
Stop after docs are aligned and clutter is reduced. Return to dispatcher.

```

---

## prompt.process_improvements — Process Improvements Prompt (system uplift)

This is the “improve the vibecoding system itself” loop, rewritten to match how Codex behaves: it needs bounded scope, objective tests, and a concrete “done” that doesn’t sprawl into product work.

```md
ROLE: Process engineer

TASK
Improve the agent workflow system in a bounded, testable way. Focus on determinism, reducing friction, and improving correctness of the loops.

SCOPE
- Allowed files:
  - prompts/template_prompts.md
  - AGENTS.md (baseline contract in the target repo, if applicable)
  - tools/agentctl.py (and tests for it, if desired)
  - CI config (e.g., GitHub Actions)
  - .gitignore hygiene for .vibe/
- Do not implement product features.

INPUTS (read in order)
1) AGENTS.md (optional if already read this session)
2) .vibe/STATE.md
3) .vibe/PLAN.md
4) .vibe/HISTORY.md (optional; non-authoritative)
5) template_prompts.md (prompt catalog; optional)
6) tools/agentctl.py (if present)
7) README.md (optional, codebase context)
8) Optional: `./var/process_log.jsonl` (untracked)

GOAL
Pick exactly one improvement that:
- reduces repeated agent overhead, OR
- makes correctness more reliable, OR
- makes failures easier to diagnose

CONSTRAINTS
- One improvement per run.
- Must include objective acceptance checks (e.g., a validation command, unit test, or CI step).
- Must not require significant repo-specific context.

SUGGESTED IMPROVEMENTS (examples)
- agentctl: add `--strict` mode; validate .vibe file presence; validate current checkpoint exists; improve error messages
- CI: add `agentctl validate --strict` step; add ruff/pytest ordering
- template_prompts.md: reduce ambiguity; add stable IDs; make stop conditions more explicit

VALIDATION
If you modify any script:
- add/adjust tests
- show exact commands to run

OUTPUT FORMAT (must follow)
A) Chosen improvement (1 sentence)
B) Files changed (list)
C) Acceptance checks (exact commands)
D) Result summary (brief)
E) Next recommendation (optional; one bullet)

STOP CONDITION
Stop this loop after the improvement is implemented and validated. Return to dispatcher.

```

---

## prompt.advance_checkpoint — Advance Checkpoint Prompt

```md
ROLE: Workflow operator (mechanical)

TASK
Advance `.vibe/STATE.md` from a DONE checkpoint to the next checkpoint in `.vibe/PLAN.md`.

RULES
- Do not implement code.
- Do not change `.vibe/PLAN.md`.
- Do not skip ahead more than one checkpoint.
- If no next checkpoint exists, do not invent work.

PROCESS
1) Read: AGENTS.md (optional if already read this session), .vibe/STATE.md, .vibe/PLAN.md
2) Confirm .vibe/STATE.md Status is DONE.
3) Find the next checkpoint id in .vibe/PLAN.md (the next heading with X.Y after the current checkpoint).
4) Update .vibe/STATE.md:
   - If a next checkpoint exists:
     - set Checkpoint to the next id
     - set Status to NOT_STARTED
     - append a Work log line
   - If no next checkpoint exists:
     - keep current checkpoint
     - add an Evidence note that the plan appears exhausted
5) Stop.

STOP CONDITION
Stop after updating `.vibe/STATE.md`. Return to dispatcher.

```
