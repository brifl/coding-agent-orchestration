# Vibe-Run Workflow Improvements (Stage 22)

Stage 22 added five improvements to the vibe-run dispatcher and review loop.
This document describes each feature, the dispatch logic that triggers it, and
how to observe or test it.

---

## 1. Stage Design Loop (`STAGE_DESIGNED` flag)

**What it does:**
Before any implementation work begins on a new stage, the dispatcher routes to
the `design` role to let the agent review the stage's PLAN.md entries, make
architectural decisions, and record those decisions in STATE.md and CONTEXT.md.

**Dispatch trigger (`_stage_design_trigger_reason`):**
Fires when:
- `STAGE_DESIGNED` key is present in the `## Workflow state` section of STATE.md, AND
- Its value is unchecked (`[ ]`).

The backward-compat guard (`if "STAGE_DESIGNED" not in workflow_flags: return None`)
ensures repositories that predate the flag are unaffected.

**Lifecycle:**
1. Consolidation clears `STAGE_DESIGNED` (unchecks it) when advancing to a new stage.
2. The stage-design loop sets `STAGE_DESIGNED` (checks it) when complete.
3. On the next dispatcher call, the flag is set → trigger skips → implementation proceeds.

**STATE.md section example:**
```markdown
## Workflow state
- [ ] STAGE_DESIGNED
```

---

## 2. Retrospective Loop (`RETROSPECTIVE_DONE` flag)

**What it does:**
After a stage transition, the dispatcher routes to the `retrospective` role to
capture lessons learned from the completed stage before starting the next one.
Lessons are written to `CONTEXT.md` under `## Stage Retrospective Notes`.

**Dispatch trigger (`_retrospective_trigger_reason`):**
Fires when:
- `RETROSPECTIVE_DONE` key is present in `## Workflow state`, AND
- Its value is unchecked (`[ ]`).

Retrospective runs *before* stage design in the dispatch priority order:
`retrospective → design → maintenance → implement`.

**Lifecycle:**
1. Consolidation clears `RETROSPECTIVE_DONE` on stage transition.
2. The retrospective loop sets `RETROSPECTIVE_DONE` when complete.
3. Subsequent dispatcher call skips the trigger → stage design can fire next.

---

## 3. Periodic Maintenance Cycle (`MAINTENANCE_CYCLE_DONE` flag)

**What it does:**
Once per stage (before implementation begins), the dispatcher routes to the
`implement` role with a maintenance-specific prompt to address either
code-quality gaps, test coverage gaps, or documentation gaps depending on the
stage number.

**Cycle type selection (`_maintenance_cycle_trigger_reason`):**
The cycle type is determined by `stage_number % 3`:

| `stage % 3` | Cycle type | Prompt ID |
|-------------|------------|-----------|
| 0           | refactor   | `prompt.refactor_scan` |
| 1           | test       | `prompt.test_gap_analysis` |
| 2           | docs       | `prompt.docs_gap_analysis` |

**Dispatch trigger:**
Fires when:
- `MAINTENANCE_CYCLE_DONE` key is present in `## Workflow state`, AND
- Its value is unchecked (`[ ]`), AND
- The stage ID is a valid integer (not `None` or non-numeric).

**Lifecycle:**
1. Consolidation clears `MAINTENANCE_CYCLE_DONE` on stage transition.
2. The maintenance loop sets `MAINTENANCE_CYCLE_DONE` when complete.
3. Subsequent dispatcher call skips the trigger → normal implementation proceeds.

---

## 4. Smoke Test Gate

**What it does:**
Before routing to the `review` role, the dispatcher runs the demo commands
defined in PLAN.md for the current checkpoint. If any command fails, the
dispatcher routes to `issues_triage` instead of `review`, surfacing the failure
as a blocking issue.

**Implementation (`_run_smoke_test_gate`):**
1. Calls `_extract_demo_commands(plan_text, checkpoint_id)` to find `* **Demo commands:**` lines under the current checkpoint heading.
2. For each command, runs `subprocess.run(cmd, shell=True, cwd=repo_root, timeout=30)`.
3. Returns `(False, reason)` on non-zero exit, timeout, or OSError.
4. Returns `(True, None)` if all commands pass or none are defined.

**Dispatch integration:**
Inside the `IN_REVIEW` branch of `_recommend_next`:
```python
passed, gate_reason = _run_smoke_test_gate(repo_root, state, plan_text)
if not passed:
    return ("issues_triage", f"Smoke test gate failed: {gate_reason}", None)
```

**Demo commands format in PLAN.md:**
```markdown
### 1.0 — My checkpoint

* **Demo commands:**
  * `python3 -m pytest tests/ -q`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
```

**Edge cases handled:**
- No checkpoint set → gate skips (returns `True`).
- No demo commands defined → gate passes (returns `True`).
- `TimeoutExpired` → gate fails with "timed out" message.
- `OSError` → gate fails with "could not run" message.

---

## 5. Checkpoint Review Pass C (Code Improvement)

**What it does:**
The `checkpoint_review` prompt now includes a third review pass (Pass C) that
scans the implementation for opportunities to improve code clarity, remove
dead code, or simplify logic. Each finding is tagged `[MINOR]`, `[MODERATE]`,
or `[MAJOR]`. A finding tagged `[MODERATE]` or higher causes the review to
FAIL, routing back to implementation.

**Tagging rules:**
- `[MINOR]` — style or cosmetic; note for future, do not block.
- `[MODERATE]` — correctness concern or tech-debt risk; blocks the review.
- `[MAJOR]` — functional bug or security issue; blocks the review.

---

## Dispatch Priority Order

When checkpoint status is `NOT_STARTED`, the dispatcher evaluates triggers in
this order (first match wins):

1. **BLOCKER issues** — all human-owned → `stop`; otherwise → `issues_triage`
2. **MAJOR+ issues** → `issues_triage`
3. **Work log consolidation** (>10 entries) → `consolidation`
4. **Retrospective** (`RETROSPECTIVE_DONE` unset) → `retrospective`
5. **Stage design** (`STAGE_DESIGNED` unset) → `design`
6. **Maintenance cycle** (`MAINTENANCE_CYCLE_DONE` unset) → `implement` (with maintenance prompt)
7. **Context capture** (CONTEXT.md missing or stale) → `context_capture`
8. **Process improvements** (`RUN_PROCESS_IMPROVEMENTS` set) → `improvements`
9. **Normal implementation** → `implement`

---

## Additional Dispatcher Hardening (22.4)

Four smaller improvements were made to the dispatcher in checkpoint 22.4:

### Human-owned BLOCKERs route to stop
If all BLOCKER-impact issues in `## Active issues` have `owner: human`, the
dispatcher returns `stop` instead of `issues_triage`. The agent cannot resolve
human-owned blockers unilaterally. The stop reason lists the blocking issue IDs.

### Resolved issues warning
If an issue in `## Active issues` has `status: RESOLVED` and is checked (`[x]`),
`agentctl validate` emits a warning (error in `--strict` mode) advising that the
issue should be moved to HISTORY.md.

### Stop decisions recorded in LOOP_RESULT.json
When the dispatcher returns `stop`, it now writes a sentinel
`LOOP_RESULT.json` with `"loop": "stop"`, `"result": "stop"`, and the
stop reason. This allows the vibe-run runner to detect the stop decision
programmatically without parsing dispatcher text output.

### Checkpoint minor ID ordering validation
`agentctl validate` now warns if checkpoint minor IDs within a stage are not in
non-decreasing numeric order (e.g., `1.2` followed by `1.1`). This catches
copy-paste ordering mistakes in PLAN.md early.

---

## Testing

All features described above are covered by tests in:

- `tests/workflow/test_agentctl_routing.py` — routing and smoke gate tests
- `tests/workflow/test_issue_schema_validation.py` — validation warning tests

Key test groups added in Stage 22:

| Feature | Test functions |
|---------|---------------|
| Stage design trigger | `test_stage_design_flag_*` |
| Retrospective trigger | `test_retrospective_trigger_*` |
| Maintenance cycle dispatch | `test_maintenance_cycle_*` |
| Smoke gate | `test_smoke_gate_*` |
| `_extract_demo_commands` | `test_extract_demo_commands_*` |
| Flag lifecycle integration | `test_flag_lifecycle_*` |
| Human BLOCKER → stop | `test_all_human_owned_blockers_route_to_stop` |
| Stop writes LOOP_RESULT | `test_stop_route_writes_loop_result_json` |
| Resolved issue warning | `test_resolved_checked_issue_*` |
| Minor ID ordering | `test_checkpoint_minor_ids_*` |

Run the full suite:
```
python3 -m pytest tests/workflow/ -q
```
