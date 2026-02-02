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
Implement **exactly one** checkpoint: the checkpoint currently selected in `.vibe/STATE.md`.
Do not advance to other checkpoints in this prompt. Looping (continuous mode) is owned by the runner/dispatcher.

GENERAL RULES
- Treat `.vibe/STATE.md` as authoritative for what to do next.
- Implement only the current checkpoint's deliverables from `.vibe/PLAN.md`.
- Keep diffs small and focused.
- If you discover missing requirements, contradictions, or unplanned scope, add an issue to `.vibe/STATE.md` and stop.
- Version control: **work on the current branch**; **do not create or switch branches** unless explicitly instructed.

READ FIRST
- `AGENTS.md` (optional if already read this session)
- `.vibe/STATE.md`
- `.vibe/PLAN.md`
- `README.md` (optional)

EXECUTION
1) Identify the current checkpoint from `.vibe/STATE.md`.
2) Locate the same checkpoint entry in `.vibe/PLAN.md`.
3) Implement the deliverables.
4) Run the demo commands (or closest equivalents). If they fail:
   - record an issue in `.vibe/STATE.md` with severity (MINOR/MAJOR/BLOCKER)
   - stop unless the fix is obvious and strictly in-scope.
5) Commit the work:
   - Ensure branch is unchanged.
   - Create at least one commit that implements the checkpoint.
   - Use message prefix `<checkpoint_id>:` in imperative mood.
6) Update `.vibe/STATE.md`:
   - set Status to `IN_REVIEW`
   - add a short work log
   - add evidence snippets or command outputs
   - add issues if anything failed or is ambiguous

OUTPUT FORMAT
- Current checkpoint ID
- What you changed (files)
- Commands you ran + results (short)
- Commit(s) created (hash + message)
- Evidence pasted into `.vibe/STATE.md`
- Any new issues created (with severity)

STOP CONDITION
Stop after completing the steps above. Return control to the dispatcher/runner for the next loop decision.

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
- AGENTS.md (optional if already read this session)
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

## prompt.consolidation — Consolidation Prompt (docs sync + archival)

```md
ROLE: Engineering lead (mechanical docs maintenance)

TASK
Bring planning docs back into alignment with the current execution state, archive completed stages, and reduce cognitive/compute load. This prompt MUST run before advancing to a new stage.

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

CRITICAL CHECKS (do these first)
1) Verify .vibe/STATE.md Stage matches the actual stage in .vibe/PLAN.md for the current checkpoint.
   - If checkpoint 5.0 is under "## Stage 5" in PLAN.md, then STATE.md must say "Stage: 5"
   - Fix any drift immediately before proceeding.
2) Run `python tools/agentctl.py --repo-root . validate` to detect issues.

PROCESS
1) Archive completed stages to .vibe/HISTORY.md:
   - For each completed stage, add ONE summary entry with format:
     "### YYYY-MM-DD — Stage N: [Stage Title] (completed)"
   - Include: checkpoints completed, key deliverables, resolved issues
   - Do NOT copy full evidence - just summarize what was accomplished

2) Prune .vibe/STATE.md:
   - Work log: keep only the last 10 entries; move older to HISTORY
   - Evidence: CLEAR ALL evidence from previous stages
     - Keep only evidence for current checkpoint (if any)
     - Evidence exists to verify acceptance; once reviewed, it's no longer needed
   - Active issues: keep only unresolved; move resolved to HISTORY
   - Objective/Deliverables/Acceptance: update to match current checkpoint from PLAN.md

3) Prune .vibe/PLAN.md:
   - Remove completed stages entirely (they're now in HISTORY)
   - Preserve any stages/checkpoints marked (SKIP); they are deferred, not completed
   - Keep: current stage + next 1–2 stages only
   - If a stage has no remaining checkpoints, remove it

4) Sync stage pointer:
   - If advancing to a new stage, update .vibe/STATE.md "Stage:" field
   - Verify checkpoint exists in the stage you're pointing to
5) Optional context refresh:
   - If CONTEXT.md is stale or missing Agent Notes, run prompt.context_capture.
   - Preserve persistent sections; only trim session-only notes.

OUTPUT
- Stages archived (list)
- Work log entries moved (count)
- Evidence cleared (yes/no)
- Stage pointer updated (old → new, if changed)
- Any drift/inconsistencies found and fixed

STOP CONDITION
Stop after docs are aligned, evidence is cleared, and stage pointers are correct.
```

---

## prompt.context_capture — Context Capture Prompt

```md
ROLE: Documentarian (concise, factual)

TASK
Capture current context in `.vibe/CONTEXT.md` so the next session can resume
without re-discovery. Keep it short and structured.

READ FIRST
- AGENTS.md (optional if already read this session)
- .vibe/STATE.md
- .vibe/PLAN.md
- .vibe/CONTEXT.md (if it exists)

WHAT TO CAPTURE
- Architecture: stable system description, major components, data flow.
- Key Decisions: decisions with dates and brief rationale.
- Gotchas: pitfalls, edge cases, environment quirks.
- Hot Files: files or paths that are frequently touched.
- Agent Notes: session-scoped notes, current checkpoint focus, open threads.

WHAT TO OMIT
- Long logs, raw command output, or stack traces (summarize instead).
- Evidence that already lives in STATE/PLAN.
- Personal opinions or speculative guesses without labels.

PROCESS
1) If `.vibe/CONTEXT.md` exists, update it in place. Otherwise create it.
2) Keep persistent sections concise and incrementally updated.
3) Update Agent Notes with the current checkpoint focus and any open threads.
4) Do not bloat the file; prefer bullets and short phrases.

OUTPUT FORMAT
- Files changed
- Summary of context captured (1-3 bullets)

STOP CONDITION
Stop after updating `.vibe/CONTEXT.md`.
```

---

## prompt.process_improvements — Process Improvements Prompt (system uplift)

This is the "improve the vibecoding system itself" loop. Keep scope bounded, tests objective, and "done" concrete so it doesn't sprawl into product work.

```md
ROLE: Process engineer

TASK
Improve the agent workflow system in a bounded, testable way. Focus on determinism, reducing friction, and improving correctness of the loops.

SCOPE
- Allowed files:
  - prompts/template_prompts.md
  - AGENTS.md (baseline contract in the target repo, if applicable)
  - tools/agentctl.py (and tests for it, if desired)
  - docs/*.md (capability matrices, concepts, etc.)
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

DIAGNOSTIC CHECKLIST (run these first)
Before picking an improvement, diagnose the current state:

1) Run `python tools/agentctl.py --repo-root . validate --strict`
   - Look for: stage drift, missing checkpoints, invalid status

2) Check STATE.md for bloat:
   - Work log > 15 entries? → needs consolidation
   - Evidence section > 50 lines? → needs clearing
   - Evidence references old checkpoints? → stale, needs clearing

3) Check STATE.md / PLAN.md alignment:
   - Does STATE.md "Stage: X" match the stage containing "Checkpoint: Y" in PLAN.md?
   - Example bug: STATE says "Stage: 2, Checkpoint: 5.0" but 5.0 is in Stage 5

4) Check HISTORY.md completeness:
   - Are completed stages summarized there?
   - Is it growing unboundedly? (Should be ~1 entry per completed stage)

5) Check capability matrices for accuracy:
   - Do docs/agent_capabilities.md and prompts/init/capability_map.md match?
   - Are agent capabilities up to date? (Claude Code CLI, Gemini Code, etc.)

6) Check for prompt ambiguity:
   - Do prompts have clear STOP CONDITIONS?
   - Do prompts reference specific file paths consistently?

GOAL
Pick exactly one improvement that:
- fixes a diagnosed issue from the checklist above, OR
- reduces repeated agent overhead, OR
- makes correctness more reliable, OR
- makes failures easier to diagnose

CONSTRAINTS
- One improvement per run.
- Must include objective acceptance checks (e.g., a validation command, unit test, or CI step).
- Must not require significant repo-specific context.
- Prefer fixing diagnosed issues over speculative improvements.

SUGGESTED IMPROVEMENTS (prioritized)
High priority (fix if found):
- Stage drift between STATE.md and PLAN.md
- Evidence bloat (>50 lines or referencing old checkpoints)
- Work log sprawl (>15 entries without consolidation)
- Capability matrix inaccuracies

Medium priority:
- agentctl: improve stage boundary detection; add consolidation triggers
- prompts: make stop conditions unambiguous; add validation commands
- CI: add `agentctl validate --strict` step

Low priority:
- Minor wording improvements
- Documentation formatting

VALIDATION
If you modify any script:
- add/adjust tests
- show exact commands to run

OUTPUT FORMAT (must follow)
A) Diagnostic findings (what issues were found)
B) Chosen improvement (1 sentence)
C) Files changed (list)
D) Acceptance checks (exact commands)
E) Result summary (brief)
F) Remaining issues (list any not addressed this run)

STOP CONDITION
Stop this loop after the improvement is implemented and validated. Return to dispatcher.
```

---

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
1) Read: AGENTS.md (optional if already read this session), .vibe/STATE.md, .vibe/PLAN.md
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

---

## init.codex_bootstrap — Codex Bootstrap

```md
ROLE
You are Codex operating inside the Vibe workflow.

CONTRACT
- Follow `AGENTS.md`.
- `.vibe/STATE.md` is authoritative for stage/checkpoint/status/issues.
- `.vibe/PLAN.md` defines deliverables/acceptance/demo/evidence.

MODE
- Single-loop: run exactly one loop, then stop; prefer `$vibe-one-loop`.
- Continuous: only when asked; use `$vibe-run` and keep looping until the
  dispatcher returns `recommended_role == "stop"`.
- Do not invent your own looping or stop `$vibe-run` after one cycle.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/CONTEXT.md` (if present)
4) `.vibe/PLAN.md`
5) `.vibe/HISTORY.md` (optional)

OUTPUT
A) Current focus (stage / checkpoint / status / issues count)
B) Next loop (design / implement / review / triage / consolidation / improvements)
C) If running a loop, do it now and stop afterward.
D) If blocked, add up to 2 questions as issues in `.vibe/STATE.md`, then stop.
```

---

## init.claude_bootstrap — Claude Bootstrap

```md
ROLE
You are Claude Code CLI joining a Vibe workflow.

CONTRACT
- Follow `AGENTS.md`.
- `.vibe/STATE.md` is the current truth.
- `.vibe/PLAN.md` lists checkpoints with acceptance criteria.

MODE
- Single-loop: execute one loop, update STATE.md, then stop.
- Continuous: invoke `python tools/agentctl.py next` to get the next prompt, execute it, repeat until stop.
- You have full file editing and command execution capabilities.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

EXECUTION
- Run `python tools/agentctl.py --repo-root . next --format json` to get recommended prompt
- Fetch prompt body: `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
- Execute the prompt, update STATE.md, commit changes
- For continuous mode: loop until agentctl returns `recommended_role: "stop"`

OUTPUT
A) Current focus (stage / checkpoint / status)
B) Next loop choice (design / implement / review / triage / consolidation / improvements)
C) Clarifying questions (max 2) if blocking; otherwise "None"

STOP
Stop after completing one loop and updating STATE.md. For continuous mode, return to agentctl.
```

---

## init.gemini_bootstrap — Gemini Bootstrap

```md
ROLE
You are Gemini Code joining a Vibe workflow.

CONTRACT
- Follow `AGENTS.md`.
- `.vibe/STATE.md` is the active pointer (stage/checkpoint/status/issues).
- `.vibe/PLAN.md` is the checkpoint backlog with acceptance criteria.

MODE
- Single-loop: execute one loop, update STATE.md, then stop.
- Continuous: invoke `python tools/agentctl.py next` to get the next prompt, execute it, repeat until stop.
- You have full file editing and command execution capabilities.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

EXECUTION
- Run `python tools/agentctl.py --repo-root . next --format json` to get recommended prompt
- Fetch prompt body: `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
- Execute the prompt, update STATE.md, commit changes
- For continuous mode: loop until agentctl returns `recommended_role: "stop"`

REQUIRED OUTPUT
1) Current focus (stage / checkpoint / status).
2) Next loop (design / implement / review / triage / consolidation / improvements).
3) Files you will update in that loop.
4) Clarifying questions (max 2) if needed; otherwise "None".

STOP
Stop after completing one loop and updating STATE.md. For continuous mode, return to agentctl.
```

---

## init.copilot_bootstrap — Copilot Bootstrap

```md
ROLE
You are GitHub Copilot joining a Vibe workflow.

CONTRACT
- Follow `AGENTS.md`.
- `.vibe/STATE.md` is the current truth (stage/checkpoint/status/issues).
- `.vibe/PLAN.md` is the checkpoint backlog with acceptance and demo commands.

MODE
- Single-loop: execute one loop, update STATE.md, then stop.
- Continuous: invoke `python tools/agentctl.py next` to get the next prompt, execute it, repeat.
- You have file editing and command execution capabilities in VS Code / CLI mode.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

EXECUTION
- Run `python tools/agentctl.py --repo-root . next --format json` to get recommended prompt
- Fetch prompt body: `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
- Execute the prompt, update STATE.md, commit changes
- For continuous mode: loop until agentctl returns `recommended_role: "stop"` or manual stop

REQUIRED OUTPUT
1) Current focus (stage / checkpoint / status).
2) Next loop (design / implement / review / triage / consolidation / improvements).
3) Files you expect to update in that loop.
4) Clarifying questions (max 2) if needed; otherwise "None".

STOP
Stop after completing one loop and updating STATE.md. For continuous mode, return to agentctl.
```
