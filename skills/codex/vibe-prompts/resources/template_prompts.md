# Template Prompts

This repo is executed via a small set of repeating prompt loops. Plans and state are tracked in files, not in prompt text.

### Source of truth (read order)

1) AGENTS.md (execution contract)
2) .vibe/STATE.md (current stage/checkpoint/status + active issues)
3) .vibe/PLAN.md (near-term plan: stages + checkpoints)
4) README.md (optional, codebase context)
5) .vibe/HISTORY.md (optional; non-authoritative rollups)

### Common rules (apply to all loops)

- The plan is in .vibe/PLAN.md; the current truth is in .vibe/STATE.md. If they conflict, update the plan to match the state (unless the state is clearly wrong, in which case open an issue in .vibe/STATE.md first).
- If you are missing key information, ask 1-2 clarifying questions in the form of issues in STATE.md and stop.
- Keep changes tight and minimize churn.
- Prefer deterministic, verifiable outputs:
  - concrete files
  - exact commands
  - short evidence snippets
- When you change state, update .vibe/STATE.md accordingly.

---

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
1) AGENTS.md
2) .vibe/STATE.md (authoritative current stage/checkpoint/status)
3) .vibe/PLAN.md
4) README.md (optional, codebase context)
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
  - clearer stage definitions (1-3 stages)
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
Advance the project by traversing checkpoints from .vibe/PLAN.md in sequence. After each checkpoint you must update .vibe/STATE.md and then proceed to the next checkpoint until a blocking issue is recorded or there are no checkpoints left.

GENERAL RULES
- Treat .vibe/STATE.md as authoritative for what to do next.
- Implement only the current checkpoint's deliverables.
- Keep diffs small and focused.
- If you discover missing requirements or contradictions, add an issue to .vibe/STATE.md and stop.

READ FIRST
- AGENTS.md
- .vibe/STATE.md
- .vibe/PLAN.md
- README.md (optional)

EXECUTION
1) Identify current checkpoint from .vibe/STATE.md.
2) Locate that checkpoint entry in .vibe/PLAN.md.
3) Implement the deliverables.
4) Run the demo commands (or the closest equivalents).
5) Update .vibe/STATE.md:
   - set Status to IN_REVIEW
   - add a short work log
   - add evidence snippets or command outputs
   - add issues if anything failed
6) When .vibe/STATE.md lists no blocking issues and the plan defines another checkpoint:
   - continue looping by re-running this prompt with the new current checkpoint.
   Repeat until either the backlog is exhausted or a blocking issue is raised.

OUTPUT FORMAT
- What you changed (files)
- Commands you ran + results (short); include each checkpoint run if multiple executed
- Evidence pasted into .vibe/STATE.md
- Any new issues created (with severity)

STOP CONDITION
Continue looping (re-run this prompt) while checkpoints remain and no blocking issue exists. Stop only when you record a blocking issue or there are no further checkpoints defined.
```

---

## prompt.checkpoint_review — Checkpoint Review Prompt

```md
ROLE: Active reviewer (adversarial)

GOAL
Decide whether the IN_REVIEW checkpoint is truly complete per AGENTS.md + .vibe/PLAN.md, and whether we are ready to move on.

GENERAL RULES
- You are allowed to run commands/tests and read code.
- Prefer catching subtle incompleteness and drift.

PROCESS
1) Identify the checkpoint marked IN_REVIEW in .vibe/STATE.md.
2) Find the same checkpoint in .vibe/PLAN.md.
3) Verify:
   - Deliverables exist and match the plan.
   - Acceptance criteria are satisfied.
   - Demo commands run cleanly (or documented deviations are justified).
4) If anything is missing:
   - add issues to .vibe/STATE.md (severity QUESTION/MINOR/MAJOR/BLOCKER)
   - set status to IN_PROGRESS or BLOCKED as appropriate
   - clearly list what remains

OUTPUT FORMAT (must follow)
A) Verdict: PASS | FAIL
B) Evidence review (brief)
- Acceptance items: ✅/❌ with notes
- Demo commands: ✅/❌ with notes
C) Issues created/updated (if any)
D) Next action
- If PASS: set status to DONE and recommend next checkpoint
- If FAIL: set status to IN_PROGRESS or BLOCKED and point to the issues

STOP CONDITION
Stop this loop after updating .vibe/STATE.md and providing the verdict. Return to dispatcher.
```

---

## prompt.issues_triage — Issues Triage Prompt

```md
ROLE: Engineer / Triage

TASK
Resolve or clarify issues in .vibe/STATE.md with minimal disruption to the active checkpoint.

SCOPE
- Prefer doc/config/plan fixes.
- Only make code changes if required to unblock a BLOCKER.
- Do not expand scope.

READ FIRST
- AGENTS.md
- .vibe/STATE.md
- .vibe/PLAN.md
- README.md (optional)

PROCESS
1) List active issues from .vibe/STATE.md in priority order:
   BLOCKER > MAJOR > MINOR > QUESTION
2) For the top 1–2 issues:
   - determine the smallest change that resolves it
   - implement or ask a clarifying question if needed
3) Update .vibe/STATE.md:
   - mark resolved issues as done (and move them to .vibe/HISTORY.md if desired)
   - add evidence for the resolution
   - if resolution changes the plan, update .vibe/PLAN.md accordingly

OUTPUT
- Issues addressed
- Changes made
- Evidence / commands run
- Any new questions (max 2)

STOP CONDITION
Stop after resolving blocking / critical issues or after asking questions needed to proceed. Return to dispatcher.
```

---

## prompt.stage_breakout — Stage Breakout Prompt

```md
Define the next 3 stages in more detail. Break out the checkpoint level details in the following format:

### Checkpoint <S.C>: <Checkpoint name>

**Objective**
- One sentence

**Deliverables**
- Core completion behaviors/functionality, in bulleted form

**Acceptance**
- Verifiable criteria

**Demo commands**
- Local commands to demo/verify

**Evidence**
- What to paste into .vibe/STATE.md
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
- AGENTS.md
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
Stop after docs are aligned and clutter is reduced.
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
1) AGENTS.md
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

## guide.create_checkpoints — Design: Create checkpoints (external)

```md
Let's grab the next 1 to 3 stages and break out some checkpoints for imminent work to be done. 
- Crisp up the stages themselves and create 1 to 6 checkpoints within the stages. 
- Do not make any "optional" - either it is in the stage/checkpoint or it isn't. 
- This should be the next 1 to 3 stages and their checkpoints.

Each checkpoint needs:
- Objective (1 sentence)
- Deliverables (concrete files/modules/behaviors)
- Acceptance (verifiable)
- Demo commands (exact, local, minimal)
- Evidence (what to paste into .vibe/STATE.md)

```

---

## prompt.onboarding — Onboarding Prompt (deprecated)

```md
ROLE: New contributor LLM (Claude Code / other)

CONTEXT
You are joining an existing vibecoding workflow that uses:
- Stable execution contract (AGENTS.md)
- Current work pointer (.vibe/STATE.md)
- Near-term plan (.vibe/PLAN.md)
- Templates for the prompt loops (template_prompts.md)
Optional:
- History rollups (.vibe/HISTORY.md)

GOAL
Before you take any action, build an accurate mental model of:
1) how work is selected,
2) how state moves (CURRENT → IN_REVIEW → COMPLETED),
3) what constitutes “done” for a checkpoint,
4) where evidence and issues live,
5) which prompt loop should run next.

SCOPE (this prompt is questions-only)
- Do NOT modify any files.
- Do NOT propose code changes.
- Do NOT start implementing.
- Your job is to ask clarifying questions and report your understanding.

READ FIRST (in order)
1) AGENTS.md
2) .vibe/STATE.md
3) .vibe/PLAN.md
4) README.md (optional, codebase context)
5) .vibe/HISTORY.md (optional; non-authoritative)
6) template_prompts.md (prompt catalog; optional)

OUTPUT FORMAT (must follow)
A) Your current understanding (brief)
- Current stage/checkpoint/status from .vibe/STATE.md
- What the next loop/prompt should be (and why)
- What “done” means for the current checkpoint (from AGENTS.md + .vibe/PLAN.md)
- Where you will record evidence and issues

B) Clarifying questions (max 10; prioritize highest leverage)
Ask only questions that materially change what you would do next. Categorize them:

1) Blocking questions (must be answered before action)
- <question>
- <why it matters in 1 sentence>

2) Non-blocking questions (helpful but not required)
- <question>
- <why it matters in 1 sentence>

C) Assumptions (only if needed)
If you cannot get answers, list up to 5 assumptions you would proceed with.

D) Proposed next prompt loop
Name exactly one loop from template_prompts.md you would run next:
- Stage Design Prompt
- Checkpoint Implementation Prompt
- Checkpoint Review Prompt
- Issues Triage Prompt
- Consolidation Prompt
- Process Improvements Prompt
Provide a 2–4 bullet justification.

STOP CONDITION
Stop after producing the output. Wait for human answers before proceeding.
```

## prompt.advance_checkpoint — Advance Checkpoint Prompt

```md
ROLE: Workflow operator (mechanical)

TASK
Advance `.vibe/STATE.md` from a DONE checkpoint to the next checkpoint in `.vibe/PLAN.md`, then get the next command from `tools\agentctl.py`.

RULES
- Do not implement code.
- Do not change `.vibe/PLAN.md`.
- Do not skip ahead more than one checkpoint.
- If no next checkpoint exists in `.vibe/PLAN.md`, set no new checkpoint; instead add a note under Evidence that the plan is exhausted and stop.

PROCESS
1) Read: AGENTS.md, .vibe/STATE.md, .vibe/PLAN.md
2) Identify the current checkpoint in .vibe/STATE.md.
3) Find the next checkpoint id in .vibe/PLAN.md (next heading with X.Y).
4) Update .vibe/STATE.md:
   - set Checkpoint to the next id
   - set Status to NOT_STARTED
   - append a Work log line
5) Stop.

STOP CONDITION
Stop this step after updating `.vibe/STATE.md`.
```
