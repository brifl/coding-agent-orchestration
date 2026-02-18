# Template Prompts

## prompt.stage_design — Stage Design Prompt

```md
ROLE: Strategic architect (stage design)

GOAL
Design the next 1-3 stages with intentional architectural decisions. Focus on
the big picture: what needs to be built, why, and how the pieces fit together.
Break out stages or checkpoints when scope exceeds one focused loop.

Do NOT implement product code. Do NOT focus on formatting or paperwork — focus
on making good design decisions.

PREFLIGHT
1) Read, in order: `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `README.md` (optional), `.vibe/HISTORY.md` (optional).
2) Verify current Stage/Checkpoint in `.vibe/STATE.md` exists in `.vibe/PLAN.md`.
3) If the pointer is wrong, fix `.vibe/STATE.md` first, then continue.
4) Review recent work log and completed stages to understand what just finished.

ALLOWED FILES
- `.vibe/PLAN.md`
- `.vibe/STATE.md` (pointer alignment, status cleanup, or workflow flags)

REQUIRED STATE MUTATIONS
- Set `STAGE_DESIGNED` workflow flag: `- [x] STAGE_DESIGNED`
- If stage/checkpoint pointer changes, update `Current focus` in `.vibe/STATE.md` and append one work-log line.
- Do not set status to `IN_REVIEW` or `DONE` in this loop.

REQUIRED COMMANDS
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --format json` after edits.

STRATEGIC DESIGN PROCESS
1) **Understand context:**
   - What stage are we entering? What was just completed?
   - What are the goals of the next 1-3 stages?
   - What does the codebase look like right now?

2) **Identify design decisions:**
   - What are the key architectural choices?
   - What dependencies exist between stages or checkpoints?
   - What risks or unknowns need to be addressed first?
   - Are there integration points that require careful ordering?

3) **Make intentional choices:**
   - For each decision, document the choice and one-line rationale.
   - Consider: implementation complexity, testing strategy, rollback safety.
   - Split large stages into smaller stages if they cross natural boundaries.
   - Split large checkpoints if they exceed "one focused loop" scope.
   - It is better to have more small checkpoints than fewer large ones.

4) **Ensure checkpoint quality:**
   Every checkpoint must have:
   - Objective (1 sentence with clear success criteria)
   - Deliverables (concrete files/modules/behaviors, not vague goals)
   - Acceptance (verifiable, testable claims)
   - Demo commands (exact local commands that prove it works)
   - Evidence (specific output to paste into `.vibe/STATE.md`)

   Each checkpoint should be:
   - Implementable in one focused loop (a few hours of work)
   - Independently testable and verifiable
   - Safe to commit and review in isolation

   Complexity budget (hard limits — split if exceeded):
   - Deliverables: ≤ 5 items
   - Acceptance criteria: ≤ 6 items
   - Demo commands: ≤ 4 items
   Run `agentctl validate --strict-complexity` to catch violations automatically.

REQUIRED OUTPUT
- Key design decisions made (3-5 bullet points)
- Stages/checkpoints added, removed, or restructured
- Current stage/checkpoint before and after edits
- Files changed
- Validation command result (pass/fail)

REPORT SCHEMA (required)
- LOOP_RESULT payload must include a `report` object with:
  - `acceptance_matrix`: list of objects (`item`, `status`, `evidence`, `critical`, `confidence`, `evidence_strength`)
  - `top_findings`: max 5 findings sorted by impact (design decisions, risks, dependencies)
  - `state_transition`: `before` + `after` stage/checkpoint/status
  - `loop_result`: mirror of top-level LOOP_RESULT fields

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after updating `.vibe/PLAN.md`, setting STAGE_DESIGNED flag, emitting and recording LOOP_RESULT, and returning control to dispatcher.
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
4) Dependency check: for each deliverable file, run `git log -n 5 --oneline -- <file>`. If recent commits conflict with planned changes (e.g., concurrent modifications by another checkpoint), create an issue and stop rather than overwriting.

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
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED|DECISION_REQUIRED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

Use `Status: DECISION_REQUIRED` when the issue requires an explicit human judgment call
(architecture direction, product scope, security policy, breaking API changes). The
dispatcher will pause and surface these issues to the human rather than routing to
issues_triage. Do NOT use DECISION_REQUIRED for technical blockers an agent can resolve.

REQUIRED COMMANDS
- Run checkpoint demo commands from `.vibe/PLAN.md` (or closest equivalent if paths changed).
- Run `git status --porcelain` before and after commit.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before emitting LOOP_RESULT.

EXECUTION
1) Implement only current checkpoint deliverables.
2) Keep diffs small and scoped.
3) Run verification/demo commands.
4) If verification fails and fix is not strictly in-scope, record issue and stop.
5) Commit at least once using `<checkpoint_id>:` prefix (imperative mood).
6) If unresolved `Impact: MAJOR|BLOCKER` issues remain, do not hand off as ready-for-review; set status to `BLOCKED` and route to triage.
7) Evaluator-Optimizer pass (required):
   - Score `correctness`, `scope_control`, `evidence_quality`, `state_transition_accuracy` from 1-5.
   - If any score < 4, run one targeted repair pass and rescore once.
   - If any score is still < 4, set status to `IN_PROGRESS|BLOCKED` and route to `issues_triage`.

REQUIRED OUTPUT
- Checkpoint ID.
- Files changed.
- Commands run + short results.
- Commit hash(es) + message(s).
- Evidence added to `.vibe/STATE.md`.
- Issues created/updated.
- Evaluator scores + whether a repair pass was required.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` with:
  - `acceptance_matrix`: include one row per acceptance claim with `critical`, `confidence` (0.0-1.0), `evidence_strength` (`LOW|MEDIUM|HIGH`)
  - `top_findings`: max 5 items, ordered by impact
  - `state_transition`: before/after stage-checkpoint-status
  - `loop_result`: exact mirror of top-level LOOP_RESULT fields

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"implement","result":"ready_for_review|blocked","stage":"<id>","checkpoint":"<id>","status":"IN_REVIEW|BLOCKED","next_role_hint":"review|issues_triage","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after commit(s), state updates, LOOP_RESULT output + record, and return control to dispatcher.

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
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED|DECISION_REQUIRED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

REQUIRED COMMANDS
- Re-run demo commands from the active checkpoint (or equivalent).
- Run focused checks needed to verify acceptance claims.
- Run at least 2 adversarial probes (negative-path, boundary, or regression probe).
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before emitting LOOP_RESULT.

EXECUTION
1) Pass A: Verify deliverables and every acceptance criterion with explicit evidence (pass/fail per item).
2) Pass B: Adversarial review:
   - attempt to falsify at least 2 acceptance claims,
   - run targeted negative/boundary checks,
   - document what breaks, what is unverified, and residual risk.
3) Pass C: Code review for improvements:
   - Review the changed/delivered files as a senior code reviewer would.
   - Identify the top 3 improvements NOT already captured in future checkpoints or active issues.
   - Tag each improvement: `[MINOR]`, `[MODERATE]`, or `[MAJOR]`.
     - `[MINOR]`: Style, naming, small refactors, missing comments on tricky logic. Fix these in place during this review pass and note what was fixed.
     - `[MODERATE]`: Missing error handling, incomplete edge cases, suboptimal algorithms, test gaps that weaken confidence. These require dedicated implementation work.
     - `[MAJOR]`: Architectural problems, security concerns, correctness bugs not caught by acceptance criteria, missing abstractions that will cause pain in future stages.
   - `[MODERATE]`/`[MAJOR]` improvements → create issues (using the ACTIVE ISSUE BLOCK format), FAIL the review, and route to implementation.
   - `[MINOR]` improvements → fix in place during this review, still eligible for PASS.
   - If no improvements found, explicitly state "No code review improvements identified" (do not invent improvements for the sake of filling the list).
4) Build a "Top 5 findings by impact" list from all three passes (highest impact first, include evidence line per finding).
5) Evaluator-Optimizer pass (required):
   - Score `correctness`, `scope_control`, `evidence_quality`, `state_transition_accuracy` from 1-5.
   - If any score < 4, run one targeted repair/retest pass and rescore once.
   - If any score remains < 4, force FAIL and route to `issues_triage`.
6) Confidence calibration (required):
   - For each acceptance claim, record `confidence` (0.0-1.0) and `evidence_strength` (`LOW|MEDIUM|HIGH`).
   - If any `critical: true` claim has `confidence < 0.75` or `evidence_strength == LOW`, do not PASS; route to `IN_PROGRESS|BLOCKED` + `issues_triage`.
7) Apply FAIL/PASS mutation rules:
   - FAIL if any acceptance item is unmet,
   - FAIL if any unresolved finding is `Impact: MAJOR|BLOCKER`,
   - FAIL if code review identified any `[MODERATE]` or `[MAJOR]` improvements,
   - PASS only when remaining findings are explicitly accepted as `MINOR|QUESTION` and all code review improvements are `[MINOR]` (and fixed in place).
8) On FAIL, capture precise gaps and exact unblock evidence needed.

REQUIRED OUTPUT
A) Verdict: PASS | FAIL
B) Acceptance evidence matrix (criterion -> command/evidence -> pass/fail)
C) Code review improvements (top 3, each tagged `[MINOR]`/`[MODERATE]`/`[MAJOR]` with description and action taken)
D) Top 5 findings by impact (Impact, finding, evidence, required fix)
E) Issues created/updated
F) State transition applied (including whether auto-advanced)
G) Evaluator scores + confidence/evidence-strength table for critical claims.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` with:
  - `acceptance_matrix`: each row must include `critical`, `confidence`, and `evidence_strength`
  - `top_findings`: max 5 items sorted by impact
  - `state_transition`: before/after stage-checkpoint-status
  - `loop_result`: exact mirror of top-level LOOP_RESULT fields

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"review","result":"pass|fail","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE|IN_PROGRESS|BLOCKED","next_role_hint":"implement|consolidation|issues_triage|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after state updates, LOOP_RESULT output + record, and return control to dispatcher.
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
2) Rank issues using impact-first ordering: `BLOCKER > MAJOR > MINOR > QUESTION`, then by unblock value and blast radius.
3) Produce a "Top 5 issues by impact" list before editing anything.
4) Select only the top 1-2 issues for active resolution in this loop.

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
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED|DECISION_REQUIRED
  - Owner: agent|human
  - Unblock Condition: Specific condition to proceed
  - Evidence Needed: Command/output/link that closes the issue
  - Notes: Optional context

REQUIRED COMMANDS
- Run only commands needed to prove issue resolution (or validate no code change needed).
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before emitting LOOP_RESULT.

EXECUTION
1) Diversity-first candidate generation (required):
   - Generate at least 8 candidate issue actions across at least 3 strategy families (example: risk-first, unblock-first, dependency-first, blast-radius-first).
   - De-duplicate candidates by root cause before ranking.
2) Produce Top 5 by impact with: `Issue ID`, `Impact`, `Why now`, `Unblock condition`, `Evidence needed`.
3) Resolve one issue at a time (top 1-2 only).
4) Prefer docs/plan/config changes over product code changes.
5) Avoid scope expansion; do not silently start implementation work.
6) Confidence calibration (required):
   - For each resolved/updated issue claim, record `confidence` (0.0-1.0) and `evidence_strength` (`LOW|MEDIUM|HIGH`).
   - If any `critical: true` claim has `confidence < 0.75` or `evidence_strength == LOW`, set status to `IN_PROGRESS|BLOCKED` and route to `issues_triage`.
7) Re-rank remaining issues after updates and record the next recommended issue.

REQUIRED OUTPUT
- Top 5 issues by impact (ordered).
- Issues addressed this loop (IDs + impact + resolution status).
- Files changed.
- Commands run + short results.
- Remaining unresolved questions (max 2).
- Candidate strategy families used + dedup summary.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` with:
  - `acceptance_matrix`: include confidence/evidence-strength rows for triage claims
  - `top_findings`: top 5 issue findings, sorted by impact
  - `state_transition`: before/after stage-checkpoint-status
  - `loop_result`: exact mirror of top-level LOOP_RESULT fields

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"issues_triage","result":"resolved|partial|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after top issues are resolved/clarified and LOOP_RESULT is emitted + recorded.
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
2) Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate`.
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
  - Clear stage-scoped workflow flags: set `STAGE_DESIGNED` → `- [ ] STAGE_DESIGNED`, `MAINTENANCE_CYCLE_DONE` → `- [ ] MAINTENANCE_CYCLE_DONE`, `RETROSPECTIVE_DONE` → `- [ ] RETROSPECTIVE_DONE`.

REQUIRED COMMANDS
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --format json` before and after edits.

EXECUTION
1) Archive completed stages into `.vibe/HISTORY.md` with concise stage summaries.
2) Prune `.vibe/STATE.md`:
   - keep at most 10 work log entries (remove oldest first)
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

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` object with:
  - `acceptance_matrix`
  - `top_findings` (max 5, sorted by impact)
  - `state_transition` (before/after)
  - `loop_result` (mirror of top-level LOOP_RESULT fields)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"consolidation","result":"aligned|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"context_capture|implement|issues_triage","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after docs are aligned, validation passes, LOOP_RESULT is emitted + recorded, and control returns to dispatcher.
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

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` object with:
  - `acceptance_matrix`
  - `top_findings` (max 5, sorted by impact)
  - `state_transition` (before/after)
  - `loop_result` (mirror of top-level LOOP_RESULT fields)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"context_capture","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after context update, optional flag clear, and LOOP_RESULT emission + record.
```

---

## prompt.process_improvements — Process Improvements Prompt (system uplift)

This is the "improve the vibecoding system itself" loop. Keep scope bounded, tests objective, and "done" concrete so it doesn't sprawl into product work.

```md
ROLE: Process engineer

GOAL
Implement one bounded improvement to the workflow system with objective validation.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md` (optional), `prompts/template_prompts.md`, `.codex/skills/vibe-loop/scripts/agentctl.py` (if relevant), `README.md` (optional).
2) Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict`.
3) Diagnose at least one concrete process problem before choosing work.

ALLOWED FILES
- `prompts/template_prompts.md`
- `AGENTS.md`
- `.codex/skills/vibe-loop/scripts/agentctl.py` (+ tests)
- `docs/*.md`
- CI config files
- `.gitignore`
- `.vibe/STATE.md` only for workflow-state flag maintenance

REQUIRED STATE MUTATIONS
- If `## Workflow state` has `- [x] RUN_PROCESS_IMPROVEMENTS`, clear it to unchecked (`[ ]`) when the selected improvement is complete.
- Add a work-log note summarizing what was improved and how it was validated.

REQUIRED COMMANDS
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict`
- Additional test/validation commands required by the chosen improvement.

EXECUTION
1) Diversity-first candidate generation:
   - Generate at least 10 candidate process improvements across at least 3 strategy families
     (example: reliability-first, clarity-first, automation-first, validation-first).
   - Tag every candidate with exactly one bracketed idea-impact label:
     `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
   - Cluster/deduplicate by root cause.
2) Produce Top 5 candidate improvements by idea impact, ordered
   `[MAJOR] -> [MODERATE] -> [MINOR]`, each with:
   - Idea impact tag
   - Expected payoff
   - Scope boundary
   - Validation command(s)
3) Choose exactly one improvement that addresses a diagnosed issue.
4) Keep scope bounded to workflow system assets (not product features).
5) Add/adjust tests when behavior changes in scripts.
6) Validate and report pass/fail with concrete command output summaries.

REQUIRED OUTPUT
A) Diagnostic findings
B) Top 5 candidate improvements by idea impact (`[MAJOR]` / `[MODERATE]` / `[MINOR]`)
C) Chosen improvement
D) Files changed
E) Validation commands + results
F) Result summary
G) Remaining workflow issues

RULES
- Every process-improvement idea must include exactly one bracketed tag:
  `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
- Use `MAJOR` for high-leverage system improvements with broad workflow payoff,
  `MODERATE` for meaningful scoped improvements, and `MINOR` for localized cleanup.
- Do not use issue-impact labels (`BLOCKER` / `QUESTION`) for process-improvement idea tagging.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` object with:
  - `acceptance_matrix`
  - `top_findings` (max 5, sorted by impact)
  - `state_transition` (before/after)
  - `loop_result` (mirror of top-level LOOP_RESULT fields)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"improvements","result":"completed|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after one validated improvement and LOOP_RESULT emission + record.
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
- `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --format json`

EXECUTION
1) Move forward by one checkpoint at most.
2) Do not change `.vibe/PLAN.md`.
3) Do not implement product code.

REQUIRED OUTPUT
- Previous pointer and new pointer.
- Validation command result.
- Any exhaustion note added.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` object with:
  - `acceptance_matrix`
  - `top_findings` (max 5, sorted by impact)
  - `state_transition` (before/after)
  - `loop_result` (mirror of top-level LOOP_RESULT fields)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"advance","result":"advanced|exhausted|blocked","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE","next_role_hint":"implement|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after updating `.vibe/STATE.md`, emitting + recording LOOP_RESULT, and returning to dispatcher.
```

---

## prompt.retrospective — Stage Retrospective Prompt

```md
ROLE: Engineering lead (stage retrospective)

GOAL
Analyze the just-completed stage to extract concrete lessons that improve future
checkpoint design. Write findings to `.vibe/CONTEXT.md` and set the RETROSPECTIVE_DONE
flag. Do NOT implement product code or change PLAN.md.

PREFLIGHT
1) Read `AGENTS.md` (optional if already read), `.vibe/STATE.md`, `.vibe/PLAN.md`, `.vibe/HISTORY.md`.
2) Identify the stage that just completed (visible in HISTORY.md or recent work log).
3) If no completed stage exists (first stage ever), write a brief stub and set the flag.

ALLOWED FILES
- `.vibe/CONTEXT.md`
- `.vibe/STATE.md` (only to set RETROSPECTIVE_DONE flag)

REQUIRED STATE MUTATIONS
- Set `RETROSPECTIVE_DONE` workflow flag: `- [x] RETROSPECTIVE_DONE`
- Append a one-line work-log entry noting the retrospective was completed.

REQUIRED COMMANDS
- None required beyond local file reads.

EXECUTION
1) **Gather data** from HISTORY.md and work log:
   - How many loops did the stage take total?
   - Which checkpoints had multiple review cycles (required >1 implement→review)?
   - Were any checkpoints split, skipped, or added mid-stage?
   - Were there any BLOCKER or DECISION_REQUIRED issues? What caused them?

2) **Identify 3-5 concrete lessons** from the above data. Each lesson must be:
   - Specific (cite a checkpoint ID or pattern, not a generic platitude)
   - Actionable (state what to do differently next time)
   - Scoped (not "be more careful" — say what would have prevented the problem)

3) **Write to `.vibe/CONTEXT.md`** under a `## Stage Retrospective Notes` section:
   - One bullet per lesson.
   - Include: which stage the lesson came from, what happened, and what to do next time.
   - Keep total notes under 10 bullets (prune older lessons when adding new ones).

4) **Set RETROSPECTIVE_DONE flag** in `## Workflow state`.

REQUIRED OUTPUT
- Stage retrospected (stage ID).
- Number of lessons extracted.
- Lessons written to CONTEXT.md (brief list).
- Flag set.

REPORT SCHEMA (required)
- LOOP_RESULT payload must include `report` object with:
  - `acceptance_matrix`
  - `top_findings` (max 5, sorted by impact — use lessons as findings)
  - `state_transition` (before/after)
  - `loop_result` (mirror of top-level LOOP_RESULT fields)

LOOP_RESULT (required final line)
Emit exactly one line:
LOOP_RESULT: {"loop":"retrospective","result":"completed|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"design|context_capture|stop","report":<report_json>}
Then record it with:
`python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

STOP CONDITION
Stop after updating CONTEXT.md, setting flag, emitting and recording LOOP_RESULT.
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
D) Record loop completion:
   `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
E) If blocked, add up to 2 questions as issues in `.vibe/STATE.md`, then stop.
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
1) `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next`
2) `python3 tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.
4) Record loop completion:
   `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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
1) `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next`
2) `python3 tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.
4) Record loop completion:
   `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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
1) `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next`
2) `python3 tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>`
3) Execute prompt loop, update `.vibe/STATE.md`, commit changes when tracked files changed.
4) Record loop completion:
   `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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
  - 1-5 checkpoint headings (titles only)

RULES
- Keep stages small and sequential.
- Use consistent numbering (next available stage ID if provided).
- Do not write full checkpoint details here.

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Append a short work-log note + evidence pointer in `.vibe/STATE.md`.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`

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
1) Diversity-first candidate generation:
   - Generate at least 10 candidate refactors across at least 3 strategy families
     (example: maintainability-first, risk-reduction-first, performance-first, testability-first).
   - Tag every candidate with exactly one bracketed idea-impact label:
     `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
   - Cluster/deduplicate by root cause.
2) Top findings by impact (max 5), ordered `[MAJOR] -> [MODERATE] -> [MINOR]`, each with:
   - Idea impact tag (`[MAJOR]` / `[MODERATE]` / `[MINOR]`)
   - Impact type (perf/maintainability/safety)
   - Risk (low/med/high)
   - Effort (S/M/L)
   - Proposed checkpoints (atomic steps)
3) Refactor plan: ordered checkpoints, each with:
   - What I will change
   - How I will prove equivalence
   - Rollback plan
4) Selection recommendation: pick 1-2 best refactors to do first, each with its
   impact tag and one-line expected payoff.

## Results
- Summarize the chosen top recommendations and why they won vs discarded candidates.

## Evidence
- Commands run (if any) and key outputs/paths.

## Next safe step
- Single next action to start execution.

RULES
- Every refactor idea must include exactly one bracketed tag:
  `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
- Use `MAJOR` for high-leverage changes with broad quality payoff, `MODERATE` for
  meaningful scoped improvements, and `MINOR` for localized cleanup.
- Do not use issue-impact labels (`BLOCKER` / `QUESTION`) for refactor idea tagging.
- Do not propose a cross-cutting rewrite unless explicitly requested.
- Identify missing tests as a risk and recommend targeted tests first.
- Scan for: duplication, high cyclomatic complexity, unclear boundaries, hidden global state,
  error-handling inconsistencies, IO mixed with business logic, and missing tests around changed code.
- Prefer refactors that can be proven with existing tests or add minimal tests first.
- Do not create or switch branches.
- If you modify code, run the minimal verification command available.

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with scan findings.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"implement","result":"ready_for_review|blocked","stage":"<id>","checkpoint":"<id>","status":"IN_REVIEW|BLOCKED","next_role_hint":"review|issues_triage","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
```

---

## prompt.refactor_execute — Refactor Execute Prompt

```md
ROLE: Senior engineer (refactor execution)

TASK
Apply a single refactor checkpoint safely.

INPUTS
- One checkpoint from scan output (pasted verbatim, including idea impact tag)
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
- Optional follow-up refactor ideas (max 2), each tagged
  `[MAJOR]` / `[MODERATE]` / `[MINOR]`

## Results
- What changed and whether verification passed.

## Evidence
- Commands run and outputs (or note if none).

## Next safe step
- Single next action to proceed (or stop if blocked).

RULES
- If the checkpoint implies multiple changes, split into smaller sub-checkpoints.
- Preserve the selected checkpoint's impact tag; if scope materially changes, restate
  the new tag and why.
- Do not create or switch branches.
- Stop after completing the checkpoint + verification; do not proceed to the next checkpoint unless asked.

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with file edits and verification outputs.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"implement","result":"ready_for_review|blocked","stage":"<id>","checkpoint":"<id>","status":"IN_REVIEW|BLOCKED","next_role_hint":"review|issues_triage","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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
- Optional follow-up refactor ideas (max 2), each tagged
  `[MAJOR]` / `[MODERATE]` / `[MINOR]`
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
- Any future refactor recommendation must include exactly one bracketed impact tag:
  `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with verification matrix and residual risks.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"review","result":"pass|fail","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE|IN_PROGRESS|BLOCKED","next_role_hint":"implement|consolidation|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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
1) Diversity-first candidate generation:
   - Generate at least 10 candidate test gaps across at least 3 strategy families
     (example: failure-mode-first, boundary-first, integration-risk-first, regression-history-first).
   - Tag every candidate with exactly one bracketed idea-impact label:
     `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
   - Cluster/deduplicate by root cause.
2) Top test gaps by idea impact (max 5), ordered `[MAJOR] -> [MODERATE] -> [MINOR]` (table-like):
  - Idea impact tag (`[MAJOR]` / `[MODERATE]` / `[MINOR]`)
  - Scenario
  - Code location
  - Why it matters (bug class / regression risk)
  - Proposed test type (unit/integration/property)
  - Minimal fixture strategy
3) If coverage tooling exists: include "coverage delta target" (e.g., +X lines / +Y branches).

## Results
- Key gaps and recommended next tests, including why top 5 outrank discarded candidates.

## Evidence
- Commands run and outputs (or note if none).

## Next safe step
- Single next action to start test work.

RULES
- If framework/runner unknown: output a discovery step first, then propose gaps.
- Every test-gap idea must include exactly one bracketed tag:
  `[MAJOR]`, `[MODERATE]`, or `[MINOR]`.
- Use `MAJOR` for high-risk uncovered paths with broad failure potential, `MODERATE`
  for meaningful risk reduction in scoped areas, and `MINOR` for low-risk edge/cleanup coverage.
- Do not use issue-impact labels (`BLOCKER` / `QUESTION`) for test-gap idea tagging.
- Avoid vanity coverage targets.
- Do not create or switch branches.

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with prioritized test gaps.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with generated tests and run output.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"implement","result":"ready_for_review|blocked","stage":"<id>","checkpoint":"<id>","status":"IN_REVIEW|BLOCKED","next_role_hint":"review|issues_triage","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with test quality verdict and top fixes.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"review","result":"pass|fail","stage":"<id>","checkpoint":"<id>","status":"NOT_STARTED|DONE|IN_PROGRESS|BLOCKED","next_role_hint":"implement|consolidation|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with the generated demo script.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"design","result":"updated|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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
  - Impact suggestion
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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with delivered intake form and open questions.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"issues_triage","result":"resolved|partial|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
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
  - Impact (BLOCKER/MAJOR/MINOR/QUESTION)
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

DISPATCHER CONTRACT (when selected by `agentctl` workflow)
- Update `.vibe/STATE.md` work log + evidence with triage decisions and checkpoint proposals.
- Run `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . validate --strict` before handoff.
- Emit exactly one line:
  `LOOP_RESULT: {"loop":"issues_triage","result":"resolved|partial|blocked","stage":"<id>","checkpoint":"<id>","status":"<status>","next_role_hint":"implement|review|issues_triage|stop","report":<report_json>}`
- Record it with:
  `python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...,"report":<report_json>}'`
```

---

## prompt.docs_gap_analysis — Documentation Gap Analysis Prompt

```md
ROLE: Documentation analyst (gap phase)

TASK
Detect missing documentation and missing documentation sections across README,
docs, and embedded guides, then produce deterministic fix recommendations.

INPUTS
- Repository root path
- Severity rubric (`docs/documentation_severity_rubric.md`)
- Scope contract (`docs/continuous_documentation_overview.md`)
- Optional prior gap report for comparison

OUTPUT FORMAT
## Goal
- One-sentence summary of the gap scan scope.

## Findings
- Deterministic list ordered by severity (`MAJOR`, `MODERATE`, `MINOR`) then id.
- Each finding must include:
  - `finding_id`
  - `phase` (`gap`)
  - `category`
  - `severity`
  - `location`
  - `recommendation`

## Recommended Actions
- Action items using only:
  - `edit_section`
  - `create_doc`
  - `create_wiki_page`
- Include target path and one-line summary per action.

## Evidence
- Commands run and key scan outputs (or note if none).

## Next Safe Step
- Single next action: apply gap fixes or triage unresolved blockers.

RULES
- Use deterministic IDs and stable ordering on unchanged repository input.
- Prefer concrete, minimal fixes over broad rewrites.
- `create_doc`/`create_wiki_page` recommendations must include explicit target paths.
- Do not create or switch branches.
```

---

## prompt.docs_gap_fix — Documentation Gap Fix Prompt

```md
ROLE: Documentation engineer (gap remediation)

TASK
Apply scoped fixes for gap findings by editing existing docs and creating
missing docs/wiki targets with explicit traceability back to finding IDs.

INPUTS
- Gap report JSON (findings with recommendations)
- Severity rubric (`docs/documentation_severity_rubric.md`)
- Scope contract (`docs/continuous_documentation_overview.md`)

OUTPUT FORMAT
## Goal
- One-sentence remediation objective tied to selected findings.

## Planned Changes
- Finding-by-finding plan with:
  - `finding_id`
  - action (`edit_section|create_doc|create_wiki_page`)
  - target path

## Applied Changes
- Files created/updated grouped by finding ID.
- Any skipped/no-op findings with reason.

## Validation
- Before/after counts for `MAJOR` and `MODERATE` findings.
- Command outputs for remediation and re-analysis runs.

## Evidence
- Fix log path (`.vibe/docs/gap_fix_log.jsonl`) and representative rows.

## Next Safe Step
- Single next action: move to refactor analysis or triage unresolved blockers.

RULES
- Preserve deterministic ordering from the input report.
- Keep fixes minimal and directly tied to recommendation intent.
- Do not mutate unrelated docs or code.
- Every applied change must map back to one `finding_id`.
- Do not create or switch branches.
```

---

## prompt.docs_refactor_analysis — Documentation Refactor Analysis Prompt

```md
ROLE: Documentation architect (refactor analysis phase)

TASK
Analyze existing documentation quality for `accuracy`, `bloat`, and
`structure`, then emit deterministic findings with refactor recommendations.

INPUTS
- Repository docs corpus (README/docs/embedded guides)
- Severity rubric (`docs/documentation_severity_rubric.md`)
- Optional previous refactor report for diffing

OUTPUT FORMAT
## Goal
- One-sentence refactor analysis scope.

## Findings by Category
- Sections for `accuracy`, `bloat`, and `structure`.
- Each finding includes:
  - `finding_id`
  - `phase` (`refactor`)
  - `category`
  - `severity`
  - `location`
  - `recommendation`

## Recommended Refactors
- Include concrete recommendations with one of:
  - `migrate_to_wiki`
  - `split_to_code_specific_doc`
  - `merge_duplicates`

## Evidence
- Commands run and key indicators used for classification.

## Next Safe Step
- Single next action: apply refactor fixes or triage unresolved blockers.

RULES
- Keep finding IDs and ordering deterministic for unchanged input.
- Prefer evidence-backed quality issues over stylistic preferences.
- Recommendations must include target paths and concise summaries.
- Do not create or switch branches.
```

---

## prompt.docs_refactor_fix — Documentation Refactor Fix Prompt

```md
ROLE: Documentation engineer (refactor remediation phase)

TASK
Execute refactor recommendations from the refactor report to improve
documentation accuracy, reduce bloat, and improve structure.

INPUTS
- Refactor report JSON (`.vibe/docs/refactor_report.json`)
- Severity rubric (`docs/documentation_severity_rubric.md`)
- Optional previous refactor-fix log for idempotence checks

OUTPUT FORMAT
## Goal
- One-sentence remediation target for selected refactor findings.

## Planned Remediations
- Per finding:
  - `finding_id`
  - action (`migrate_to_wiki|split_to_code_specific_doc|merge_duplicates`)
  - target path

## Applied Changes
- Files updated/created grouped by finding ID.
- Any no-op findings with reason.

## Validation
- Re-analysis summary showing before/after `MAJOR|MODERATE` counts.
- Post-fix consistency checks (headings and links) result.

## Migration Artifacts
- Generated `docs/wiki-export/*` paths.
- Mapping manifest updates in `docs/wiki-export/map.json`.

## Evidence
- Refactor fix log path and representative rows.

## Next Safe Step
- Single next action: package workflow skill or triage unresolved blockers.

RULES
- Keep fixes deterministic and idempotent.
- Every file change must map back to one refactor finding.
- Preserve source-to-target mappings for wiki migrations.
- Do not create or switch branches.
```
