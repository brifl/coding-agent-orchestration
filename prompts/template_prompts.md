# Template Prompts

## prompt.stage_design — Stage Design Prompt

```md
ROLE: Primary software architect (design pass)

GOAL
Make `.vibe/PLAN.md` near-term, deterministic, and aligned with `.vibe/STATE.md`
without implementing product code.

PREFLIGHT
1) Read, in order: `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `README.md` (optional), `.vibe/HISTORY.md` (optional).
2) Verify current Stage/Checkpoint in `.vibe/STATE.md` exists in `.vibe/PLAN.md`.
3) If the pointer is wrong, fix `.vibe/STATE.md` first, then continue.

ALLOWED FILES
- `.vibe/PLAN.md`
- `.vibe/STATE.md` (only for pointer alignment or status cleanup)

REQUIRED STATE MUTATIONS
- If stage/checkpoint pointer changes, update `Current focus` in `.vibe/STATE.md` and append one work-log line.
- Do not set status to `IN_REVIEW` or `DONE` in this loop.

REQUIRED COMMANDS
- Run `python tools/agentctl.py --repo-root . validate --format json` after edits.

EXECUTION
1) Keep detailed planning to the next 1-3 stages only.
2) Ensure every checkpoint uses this exact shape:
   - Objective (1 sentence)
   - Deliverables (concrete files/modules/behaviors)
   - Acceptance (verifiable)
   - Demo commands (exact local commands)
   - Evidence (what to paste into `.vibe/STATE.md`)
3) Ensure each checkpoint is executable in one focused loop.
4) Keep edits minimal and mechanical; avoid architecture rewrites.

REQUIRED OUTPUT
- Current stage/checkpoint before and after edits.
- Files changed.
- Validation command result (pass/fail).
- Short summary of plan changes.

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop"}

STOP CONDITION
Stop after updating `.vibe/PLAN.md` (and `.vibe/STATE.md` only if needed), emitting LOOP_RESULT, and returning control to dispatcher.
```

---

## prompt.checkpoint_implementation — Checkpoint Implementation Prompt

```md
ROLE: Primary software engineer

GOAL
Implement exactly one checkpoint selected in `.vibe/STATE.md`, prove it, commit it,
and hand off to review.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `README.md` (optional).
2) Confirm the checkpoint in `.vibe/STATE.md` exists in `.vibe/PLAN.md`.
3) If deliverables are ambiguous or contradictory, create an issue and stop.

ALLOWED FILES
- Product/code files needed for the active checkpoint
- `.vibe/STATE.md`
- `.vibe/PLAN.md` only when required for strict in-scope clarification

REQUIRED STATE MUTATIONS
- Set status to `IN_REVIEW`.
- Add one work-log entry summarizing implemented deliverables.
- Add evidence from demo/verification commands.
- Add or update issues for any unresolved ambiguity/failure.

ACTIVE ISSUE BLOCK (required format)
- [ ] ISSUE-123: Short title
  - Severity: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

REQUIRED COMMANDS
- Run checkpoint demo commands from `.vibe/PLAN.md` (or closest equivalent if paths changed).
- Run `git status --porcelain` before and after commit.

EXECUTION
1) Implement only current checkpoint deliverables.
2) Keep diffs small and scoped.
3) Run verification/demo commands.
4) If verification fails and fix is not strictly in-scope, record issue and stop.
5) Commit at least once using `<checkpoint_id>:` prefix (imperative mood).

REQUIRED OUTPUT
- Checkpoint ID.
- Files changed.
- Commands run + short results.
- Commit hash(es) + message(s).
- Evidence added to `.vibe/STATE.md`.
- Issues created/updated.

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"implement","result":"ready_for_review|blocked","stage":"<id>","checkpoint":"<id>","status":"IN_REVIEW|BLOCKED","next_role_hint":"review|issues_triage"}

STOP CONDITION
Stop after commit(s), state updates, LOOP_RESULT output, and return control to dispatcher.

```

---

## prompt.checkpoint_review — Checkpoint Review Prompt

```md
ROLE: Active reviewer (adversarial)

GOAL
Decide PASS/FAIL for the `IN_REVIEW` checkpoint and perform deterministic state
transitions, including automatic same-stage advance on PASS.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`.
2) Locate the checkpoint marked `IN_REVIEW` in STATE and matching checkpoint in PLAN.
3) Gather acceptance/demo requirements from PLAN before running checks.

ALLOWED FILES
- `.vibe/STATE.md`
- `.vibe/PLAN.md` (read-only unless fixing an obvious typo that blocks review)
- Test/log/output files produced by verification commands

REQUIRED STATE MUTATIONS
- FAIL path:
  - Set status to `IN_PROGRESS` or `BLOCKED`.
  - Add/update issues using the required issue block schema.
- PASS path:
  - Determine next checkpoint in PLAN order (skip `(DONE)`, `(SKIPPED)`, `(SKIP)` entries).
  - If no next checkpoint exists: keep current checkpoint, set status `DONE`, add "plan exhausted" evidence note.
  - If next checkpoint is in the same stage: update checkpoint to next and set status `NOT_STARTED` (auto-advance).
  - If next checkpoint is in a different stage: keep current checkpoint as `DONE` so dispatcher routes to consolidation.

ACTIVE ISSUE BLOCK (required format)
- [ ] ISSUE-123: Short title
  - Severity: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

REQUIRED COMMANDS
- Re-run demo commands from the active checkpoint (or equivalent).
- Run focused checks needed to verify acceptance claims.

EXECUTION
1) Verify deliverables and acceptance criteria.
2) Record evidence for each acceptance item (pass/fail).
3) Apply FAIL or PASS state mutation rules above.
4) On FAIL, capture precise gaps instead of broad "needs work" notes.

REQUIRED OUTPUT
A) Verdict: PASS | FAIL
B) Acceptance and demo evidence matrix
C) Issues created/updated
D) State transition applied (including whether auto-advanced)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"review","result":"pass|fail","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE|IN_PROGRESS|BLOCKED","next_role_hint":"implement|consolidation|issues_triage|stop"}

STOP CONDITION
Stop after state updates, LOOP_RESULT output, and return control to dispatcher.
```

---

## prompt.issues_triage — Issues Triage Prompt

```md
ROLE: Engineer / Triage

GOAL
Resolve or clarify the highest-priority active issues with the smallest safe
change set.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `README.md` (optional).
2) Rank issues by severity: `BLOCKER > MAJOR > MINOR > QUESTION`.
3) Select top 1-2 issues only.

ALLOWED FILES
- `.vibe/STATE.md`
- `.vibe/PLAN.md` (if issue resolution changes plan scope/wording)
- Minimal product files only when needed to unblock a `BLOCKER`

REQUIRED STATE MUTATIONS
- For resolved issues: mark resolved and move to HISTORY if your repo uses that pattern.
- For unresolved issues: keep active and update notes with what is still required.
- Add evidence for each resolved issue.
- If blocked on missing information, add up to 2 explicit questions.

ACTIVE ISSUE BLOCK (required format)
- [ ] ISSUE-123: Short title
  - Severity: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

REQUIRED COMMANDS
- Run only commands needed to prove issue resolution (or validate no code change needed).

EXECUTION
1) Resolve one issue at a time.
2) Prefer docs/plan/config changes over product code changes.
3) Avoid scope expansion; do not silently start implementation work.

REQUIRED OUTPUT
- Issues addressed (IDs + severity).
- Files changed.
- Commands run + short results.
- Remaining unresolved questions (max 2).

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"issues_triage","result":"resolved|partial|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop"}

STOP CONDITION
Stop after top issues are resolved/clarified and LOOP_RESULT is emitted.
```

---

## prompt.consolidation — Consolidation Prompt (docs sync + archival)

```md
ROLE: Engineering lead (mechanical docs maintenance)

GOAL
Archive completed stage docs, realign state/plan pointers, and hand off cleanly
to the next stage.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md` (optional), `README.md` (optional).
2) Run `python tools/agentctl.py --repo-root . validate`.
3) Determine whether this consolidation is tied to a stage transition.

ALLOWED FILES
- `.vibe/STATE.md`
- `.vibe/PLAN.md`
- `.vibe/HISTORY.md`

REQUIRED STATE MUTATIONS
- Fix stage/checkpoint drift first, if present.
- Keep only unresolved active issues in STATE.
- Trim stale evidence/work-log noise from completed stages.
- If transitioning stages:
  - Set `Stage` to the stage containing the next checkpoint.
  - Set `Checkpoint` to the next checkpoint.
  - Set `Status` to `NOT_STARTED`.
  - Ensure `## Workflow state` contains `- [x] RUN_CONTEXT_CAPTURE`.

REQUIRED COMMANDS
- `python tools/agentctl.py --repo-root . validate --format json` before and after edits.

EXECUTION
1) Archive completed stages into `.vibe/HISTORY.md` with concise stage summaries.
2) Prune `.vibe/STATE.md`:
   - keep recent work log entries only
   - clear evidence for old checkpoints
   - sync objective/deliverables/acceptance to active checkpoint
3) Prune `.vibe/PLAN.md`:
   - remove only fully completed stages
   - Preserve any stages/checkpoints marked (SKIP); they are deferred, not completed
   - keep future backlog stages
4) If no stage transition is needed, do not change checkpoint status unless required for alignment.

REQUIRED OUTPUT
- Stages archived.
- State pointer changes (`Stage/Checkpoint/Status` old -> new).
- Validation command results before/after.
- Any drift fixed.

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"consolidation","result":"aligned|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"context_capture|implement|issues_triage"}

STOP CONDITION
Stop after docs are aligned, validation passes, LOOP_RESULT is emitted, and control returns to dispatcher.
```

---

## prompt.context_capture — Context Capture Prompt

```md
ROLE: Documentarian (concise, factual)

GOAL
Refresh `.vibe/CONTEXT.md` so the next loop/session can resume with minimal
rediscovery.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/CONTEXT.md` (if present).
2) Identify the current checkpoint and top open threads.

ALLOWED FILES
- `.vibe/CONTEXT.md`
- `.vibe/STATE.md` only to clear `RUN_CONTEXT_CAPTURE` workflow flag

REQUIRED STATE MUTATIONS
- If `## Workflow state` includes `- [x] RUN_CONTEXT_CAPTURE`, clear it to `- [ ] RUN_CONTEXT_CAPTURE` after context update.

REQUIRED COMMANDS
- None required beyond local file updates.

EXECUTION
1) Create/update `.vibe/CONTEXT.md` with concise sections:
   - Architecture
   - Key Decisions (dated)
   - Gotchas
   - Hot Files
   - Agent Notes
2) Keep entries short, factual, and current.
3) Avoid copying long logs/evidence.

REQUIRED OUTPUT
- Files changed.
- 1-3 bullets summarizing what was captured/refreshed.

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"context_capture","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop"}

STOP CONDITION
Stop after context update, optional flag clear, and LOOP_RESULT emission.
```

---

## prompt.process_improvements — Process Improvements Prompt (system uplift)

This is the "improve the vibecoding system itself" loop. Keep scope bounded, tests objective, and "done" concrete so it doesn't sprawl into product work.

```md
ROLE: Process engineer

GOAL
Implement one bounded improvement to the workflow system with objective validation.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md` (optional), `prompts/template_prompts.md`, `tools/agentctl.py` (if relevant), `README.md` (optional).
2) Run `python tools/agentctl.py --repo-root . validate --strict`.
3) Diagnose at least one concrete process problem before choosing work.

ALLOWED FILES
- `prompts/template_prompts.md`
- `AGENTS.md`
- `tools/agentctl.py` (+ tests)
- `docs/*.md`
- CI config files
- `.gitignore`
- `.vibe/STATE.md` only for workflow-state flag maintenance

REQUIRED STATE MUTATIONS
- If `## Workflow state` has `- [x] RUN_PROCESS_IMPROVEMENTS`, clear it to unchecked (`[ ]`) when the selected improvement is complete.
- Add a work-log note summarizing what was improved and how it was validated.

REQUIRED COMMANDS
- `python tools/agentctl.py --repo-root . validate --strict`
- Additional test/validation commands required by the chosen improvement.

EXECUTION
1) Choose exactly one improvement that addresses a diagnosed issue.
2) Keep scope bounded to workflow system assets (not product features).
3) Add/adjust tests when behavior changes in scripts.
4) Validate and report pass/fail with concrete command output summaries.

REQUIRED OUTPUT
A) Diagnostic findings
B) Chosen improvement
C) Files changed
D) Validation commands + results
E) Result summary
F) Remaining workflow issues

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"improvements","result":"completed|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop"}

STOP CONDITION
Stop after one validated improvement and LOOP_RESULT emission.
```

---

## prompt.advance_checkpoint — Advance Checkpoint Prompt

```md
ROLE: Workflow operator (mechanical)

GOAL
Fallback/manual pointer advance when checkpoint should move but was not advanced
by review/consolidation.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`.
2) Confirm current status is `DONE` (or explicitly requested override).
3) Identify next checkpoint in PLAN order.

ALLOWED FILES
- `.vibe/STATE.md`

REQUIRED STATE MUTATIONS
- Set `Checkpoint` to the immediate next checkpoint only.
- Set `Status` to `NOT_STARTED`.
- Append one work-log entry noting manual advance.
- If no next checkpoint exists, keep checkpoint unchanged and add a "plan exhausted" evidence note.

REQUIRED COMMANDS
- `python tools/agentctl.py --repo-root . validate --format json`

EXECUTION
1) Move forward by one checkpoint at most.
2) Do not change `.vibe/PLAN.md`.
3) Do not implement product code.

REQUIRED OUTPUT
- Previous pointer and new pointer.
- Validation command result.
- Any exhaustion note added.

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"advance","result":"advanced|exhausted|blocked","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE","next_role_hint":"implement|stop"}

STOP CONDITION
Stop after updating `.vibe/STATE.md`, emitting LOOP_RESULT, and returning to dispatcher.
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
B) Next loop (`design` / `implement` / `review` / `issues_triage` / `advance` / `consolidation` / `context_capture` / `improvements` / `stop`)
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
- Single-loop: execute exactly one loop, update STATE, stop.
- Continuous: repeat dispatcher loops until `recommended_role: "stop"`.
- You have file editing + shell command capability.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

STANDARD COMMANDS
1) `python tools/agentctl.py --repo-root . --format json next`
2) `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.

OUTPUT
A) Current focus (stage / checkpoint / status)
B) Next loop choice (`design` / `implement` / `review` / `issues_triage` / `advance` / `consolidation` / `context_capture` / `improvements` / `stop`)
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
- Single-loop: execute exactly one loop, update STATE, stop.
- Continuous: repeat dispatcher loops until `recommended_role: "stop"`.
- You have file editing + shell command capability.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

STANDARD COMMANDS
1) `python tools/agentctl.py --repo-root . --format json next`
2) `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.

REQUIRED OUTPUT
1) Current focus (stage / checkpoint / status).
2) Next loop (`design` / `implement` / `review` / `issues_triage` / `advance` / `consolidation` / `context_capture` / `improvements` / `stop`).
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
- Single-loop: execute exactly one loop, update STATE, stop.
- Continuous: repeat dispatcher loops until `recommended_role: "stop"` (or manual stop if required by environment).
- You have file editing + shell command capability in VS Code/CLI mode.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

STANDARD COMMANDS
1) `python tools/agentctl.py --repo-root . --format json next`
2) `python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.

REQUIRED OUTPUT
1) Current focus (stage / checkpoint / status).
2) Next loop (`design` / `implement` / `review` / `issues_triage` / `advance` / `consolidation` / `context_capture` / `improvements` / `stop`).
3) Files you expect to update in that loop.
4) Clarifying questions (max 2) if needed; otherwise "None".

STOP
Stop after completing one loop and updating STATE.md. For continuous mode, return to agentctl.
```

---

## prompt.ideation — Ideation Prompt

```md
ROLE: Product designer (ideation)

TASK
Generate a structured feature list from a problem statement.

INPUT
- Problem statement
- Target users (if known)
- Constraints (time, budget, platform)

OUTPUT FORMAT
- Problem summary (1-2 sentences)
- Assumptions (bullets, optional)
- Feature list:
  - Feature name
  - Priority: P0 | P1 | P2
  - Rationale (1 sentence)
  - Success signal (1 metric/indicator)

RULES
- Prefer clarity over breadth.
- Keep the list actionable and implementation-oriented.
- If inputs are missing, make minimal assumptions and state them.

STOP CONDITION
Stop after producing the structured feature list.
```

---

## prompt.feature_breakdown — Feature Breakdown Prompt

```md
ROLE: Product engineer (feature decomposition)

TASK
Decompose a single feature into sub-features and deliverable slices.

INPUT
- Feature name
- Feature goal (1-2 sentences)
- Constraints (optional)

OUTPUT FORMAT
- Feature summary (1-2 sentences)
- Sub-features (bullets):
  - Name
  - Scope (1 sentence)
  - Priority: P0 | P1 | P2
  - Dependencies (if any)
- Risks / open questions (bullets, optional)

RULES
- Aim for slices that are independently shippable.
- Keep scope tight; avoid architecture detours.
- If missing info, call it out under Risks / open questions.

STOP CONDITION
Stop after listing sub-features and any risks.
```

---

## prompt.architecture — Architecture Prompt

```md
ROLE: Software architect (system design)

TASK
Design a system architecture from a prioritized feature list.

INPUT
- Feature list (prioritized)
- Non-functional requirements (performance, security, scale)
- Constraints (stack, budget, timeline)

OUTPUT FORMAT
- Architecture summary (1-2 paragraphs)
- Components:
  - Name
  - Responsibility
  - Interfaces (APIs/events)
- Data flow (bullets)
- Risks / assumptions (bullets)

RULES
- Keep the design pragmatic and implementable.
- Prefer explicit component boundaries.
- If inputs are missing, note assumptions.

STOP CONDITION
Stop after producing the architecture output.
```

---

## prompt.milestones — Milestones Prompt

```md
ROLE: Program planner (milestones)

TASK
Translate an architecture description into sequenced milestones with dependencies.

INPUT
- Architecture summary
- Component list
- Constraints (timeline, team size)

OUTPUT FORMAT
- Milestone list (ordered):
  - Milestone name
  - Scope (1-2 sentences)
  - Dependencies (if any)
  - Exit criteria (1-2 bullets)

RULES
- Keep milestones small enough for 1-2 week slices.
- Dependencies should be explicit.
- Highlight any risk if sequencing is uncertain.

STOP CONDITION
Stop after listing the milestones.
```

---

## prompt.stages_from_milestones — Stages From Milestones Prompt

```md
ROLE: Planning author (stages)

TASK
Convert a milestone list into PLAN.md stage sections.

INPUT
- Milestone list (ordered)
- Optional constraints (scope/time)

OUTPUT FORMAT
- Stage sections in PLAN.md format:
  - Stage heading
  - Stage objective
  - 1-3 checkpoint headings (titles only)

RULES
- Keep stages small and sequential.
- Use consistent numbering (next available stage ID if provided).
- Do not write full checkpoint details here.

STOP CONDITION
Stop after producing the stage sections.
```

---

## prompt.checkpoints_from_stage — Checkpoints From Stage Prompt

```md
ROLE: Planning author (checkpoints)

TASK
Break a single stage into full checkpoint entries for PLAN.md.

INPUT
- Stage title
- Stage objective
- Stage scope notes (optional)

OUTPUT FORMAT
- Checkpoint sections (repeat for each):
  - Objective (1 sentence)
  - Deliverables (concrete files/modules/behaviors)
  - Acceptance (verifiable)
  - Demo commands (exact local commands)
  - Evidence (what to paste into STATE.md)

RULES
- Each checkpoint should be implementable in one focused iteration.
- Keep demo commands minimal and local.
- Match the PLAN.md checkpoint template exactly.

STOP CONDITION
Stop after generating the checkpoint sections.
```

---

## prompt.refactor_scan — Refactor Scan Prompt

```md
ROLE: Senior engineer (refactor scan)

TASK
Produce a prioritized refactor backlog with justifications and scope bounds.

INPUTS
- Target scope (paths/modules)
- Constraints (no behavior change vs allowed behavior change)
- Tooling commands (linter/typechecker/tests) or "unknown"

OUTPUT FORMAT
## Goal
- Summarize the refactor intent and scope.

## Inputs
- Restate scope, constraints, and tooling commands.

## Plan
- Brief scan approach (1-3 bullets).

## Actions
1) Top findings (max 10), each with:
   - Impact (perf/maintainability/safety)
   - Risk (low/med/high)
   - Effort (S/M/L)
   - Proposed checkpoints (atomic steps)
2) Refactor plan: ordered checkpoints, each with:
   - What I will change
   - How I will prove equivalence
   - Rollback plan
3) Selection recommendation: pick 1-2 best refactors to do first.

## Results
- Summarize the chosen top recommendations.

## Evidence
- Commands run (if any) and key outputs/paths.

## Next safe step
- Single next action to start execution.

RULES
- Do not propose a cross-cutting rewrite unless explicitly requested.
- Identify missing tests as a risk and recommend targeted tests first.
- Scan for: duplication, high cyclomatic complexity, unclear boundaries, hidden global state,
  error-handling inconsistencies, IO mixed with business logic, and missing tests around changed code.
- Prefer refactors that can be proven with existing tests or add minimal tests first.
- Do not create or switch branches.
- If you modify code, run the minimal verification command available.
```

---

## prompt.refactor_execute — Refactor Execute Prompt

```md
ROLE: Senior engineer (refactor execution)

TASK
Apply a single refactor checkpoint safely.

INPUTS
- One checkpoint from scan output (pasted verbatim)
- File/module list
- Definition of done (behavioral invariants)
- Verification commands

OUTPUT FORMAT
## Goal
- Restate the checkpoint intent and constraints.

## Inputs
- Checkpoint, files/modules, definition of done, verification commands.

## Plan
- Small, ordered steps to implement the checkpoint.

## Actions
- Exact file edits summary (files touched, intent per file)
- Any new tests added (and why minimal)
- Commands run + pass/fail
- If fail: either fix or revert, and state which

## Results
- What changed and whether verification passed.

## Evidence
- Commands run and outputs (or note if none).

## Next safe step
- Single next action to proceed (or stop if blocked).

RULES
- If the checkpoint implies multiple changes, split into smaller sub-checkpoints.
- Do not create or switch branches.
- Stop after completing the checkpoint + verification; do not proceed to the next checkpoint unless asked.
```

---

## prompt.refactor_verify — Refactor Verify Prompt

```md
ROLE: Senior engineer (refactor verification)

TASK
Confirm the refactor did not change behavior and did not worsen quality.

INPUTS
- Commit hash or diff summary
- Verification commands
- Performance constraints (if any)

OUTPUT FORMAT
## Goal
- Summarize what is being verified.

## Inputs
- Commit/diff, commands, constraints.

## Plan
- Brief verification plan (1-3 bullets).

## Actions
- Pass/fail matrix: tests/lint/typecheck/build
- Risk callouts: what remains unverified and why
- "If this regresses in prod, likely failure modes are ..." (max 3)
- Optional: micro-benchmark suggestion (only if relevant)

## Results
- Overall pass/fail and risk summary.

## Evidence
- Commands run and outputs (or note if none).

## Next safe step
- Single next action (ship, monitor, or investigate).

RULES
- Do not create or switch branches.
- If verification fails, recommend fix or revert.
```

---

## prompt.test_gap_analysis — Test Gap Analysis Prompt

```md
ROLE: Test strategist (gap analysis)

TASK
Identify untested paths tied to real risk in the target code.

INPUTS
- Target files/functions/classes
- Test framework + runner command
- Coverage tool command (if available)
- "Allowed to change production code?" (yes/no)

OUTPUT FORMAT
## Goal
- Summarize the test gap analysis scope.

## Inputs
- Restate targets, commands, and constraints.

## Plan
- Brief approach (1-3 bullets).

## Actions
- Test gaps list (table-like):
  - Scenario
  - Code location
  - Why it matters (bug class / regression risk)
  - Proposed test type (unit/integration/property)
  - Minimal fixture strategy
- If coverage tooling exists: include "coverage delta target" (e.g., +X lines / +Y branches).

## Results
- Key gaps and recommended next tests.

## Evidence
- Commands run and outputs (or note if none).

## Next safe step
- Single next action to start test work.

RULES
- If framework/runner unknown: output a discovery step first, then propose gaps.
- Avoid vanity coverage targets.
- Do not create or switch branches.
```

---

## prompt.test_generation — Test Generation Prompt

```md
ROLE: Test engineer (test generation)

TASK
Generate runnable tests for a single identified gap.

INPUTS
- One gap item (pasted verbatim)
- Target function signature(s)
- Existing test patterns (paths/naming) if known

OUTPUT FORMAT
## Goal
- Restate the test gap and target.

## Inputs
- Gap item, targets, existing patterns.

## Plan
- Brief plan for test creation (1-3 bullets).

## Actions
- Exact test file path(s) and test names
- Rationale for assertions (what regression would be caught)
- Any needed fakes/mocks and why
- Commands run

## Results
- Summary of tests created and expected coverage impact.

## Evidence
- Commands run + key outputs/paths.

## Next safe step
- Single next action to validate tests.

RULES
- Follow existing repo conventions (fixtures, snapshot style, etc.).
- Avoid overspecifying behavior; assert stable contracts.
- Do not create or switch branches.
```

---

## prompt.test_review — Test Review Prompt

```md
ROLE: Test reviewer (signal/noise)

TASK
Review tests for signal, maintainability, and brittleness.

INPUTS
- Diff (or list of test files added/changed)
- What the tests are supposed to validate

OUTPUT FORMAT
## Goal
- Summarize review intent.

## Inputs
- Tests under review + intended behaviors.

## Plan
- Brief review approach (1-3 bullets).

## Actions
- Good coverage points (what’s solid)
- Brittleness points (what will break unnecessarily)
- Concrete edits to improve (rename, reduce mocking, better assertions)
- Call out whether tests verify outcomes vs implementation details

## Results
- Overall quality assessment and key fixes.

## Evidence
- Commands run or files inspected.

## Next safe step
- Single next action to improve or accept tests.

RULES
- Be explicit about outcome vs implementation assertions.
- Do not create or switch branches.
```

---

## prompt.demo_script — Demo Script Prompt

```md
ROLE: Product guide (demo)

TASK
Produce a non-technical validation script for a change.

INPUTS
- Feature/change summary
- Target persona (developer, QA, end-user)
- Platforms/OS constraints

OUTPUT FORMAT
## Goal
- Summarize the demo intent and persona.

## Inputs
- Restate feature summary, persona, platforms.

## Plan
- Brief structure of the demo (1-3 bullets).

## Actions
- Step-by-step script with expected outcomes per step
- "If you see X, file feedback with Y info"
- Reset environment section

## Results
- Summary of what success looks like.

## Evidence
- Any tools used or links referenced (if applicable).

## Next safe step
- Single next action to collect feedback.

RULES
- Avoid jargon without a parenthetical definition.
- Do not create or switch branches.
```

---

## prompt.feedback_intake — Feedback Intake Prompt

```md
ROLE: Feedback facilitator (intake)

TASK
Collect structured feedback with minimal back-and-forth.

INPUTS
- Product area/module
- Version/commit
- Reporter type (dev/QA/user)

OUTPUT FORMAT
## Goal
- Summarize the intake scope.

## Inputs
- Restate area, version, reporter.

## Plan
- Brief intake approach (1-3 bullets).

## Actions
- Copy-paste form with fields:
  - Summary
  - Expected vs actual
  - Repro steps
  - Frequency
  - Logs/screenshots pointers
  - Severity suggestion
  - Workaround (if any)

## Results
- How the feedback will be processed next.

## Evidence
- Form delivered.

## Next safe step
- Single next action for the reporter.

RULES
- Keep the form concise and unambiguous.
- Do not create or switch branches.
```

---

## prompt.feedback_triage — Feedback Triage Prompt

```md
ROLE: Triage lead (feedback)

TASK
Convert feedback intake forms into issues and checkpoints.

INPUTS
- One or more completed intake forms
- Current PLAN stage naming rules (including PRE stages)

OUTPUT FORMAT
## Goal
- Summarize the triage scope.

## Inputs
- Count of forms and stage naming rules.

## Plan
- Brief triage approach (1-3 bullets).

## Actions
- Issue list:
  - Title
  - Severity (BLOCKER/MAJOR/MINOR/QUESTION)
  - Summary
  - Proposed owner
- Checkpoint proposals (if appropriate):
  - Stage
  - Objective
  - Deliverables (concrete)
  - Acceptance (verifiable)
  - Demo commands
  - Evidence

## Results
- Suggested ordering/priorities.

## Evidence
- Intake forms referenced.

## Next safe step
- Single next action to file issues or update PLAN.

RULES
- Keep proposed checkpoints small and implementable in one iteration.
- Do not create or switch branches.
```
