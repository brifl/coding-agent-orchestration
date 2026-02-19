# PLAN

## Stage 24 — Structured Human Feedback Channel

**Stage objective:**
Implement a validated human feedback protocol: humans write `.vibe/FEEDBACK.md` in a structured schema, `agentctl feedback inject` converts entries to Issue records in STATE.md, the dispatcher routes to issues_triage when unprocessed feedback exists, and `agentctl feedback ack` archives processed entries to HISTORY.md.

### Stage invariants (apply to all checkpoints)

- **Non-destructive injection:** Injecting feedback never overwrites or reorders existing Active issues in STATE.md.
- **Schema-first:** FEEDBACK.md entries are validated before injection; malformed entries fail with line-level diagnostics.
- **Verbatim archival:** Processed entries are appended to HISTORY.md exactly as written (plus timestamps), enabling full audit trail.
- **Backward compatible:** Repos without `.vibe/FEEDBACK.md` are entirely unaffected.
- **Idempotent ack:** Running `agentctl feedback ack` twice produces the same result as running it once.

---

### 24.0 — Feedback schema and validation

* **Objective:**
  Define the `.vibe/FEEDBACK.md` format and implement `agentctl feedback validate` with entry-level parsing and diagnostics.
* **Deliverables:**
  * Feedback entry format in `.vibe/FEEDBACK.md`:
    ```
    - [ ] FEEDBACK-001: <short title>
      - Impact: QUESTION|MINOR|MAJOR|BLOCKER
      - Type: bug|feature|concern|question
      - Description: <what the human observed or wants>
      - Expected: <what should happen instead>
      - Proposed action: <optional — what the human wants the agent to do>
    ```
  * `_parse_feedback_file(text) -> tuple[FeedbackEntry, ...]` in `tools/agentctl.py`
  * `FeedbackEntry` dataclass (feedback_id, impact, type, description, expected, proposed_action, checked, processed)
  * `agentctl feedback validate` subcommand — prints errors/warnings with line numbers
  * Validate: required fields, valid Impact values, valid Type values, no duplicate FEEDBACK-IDs
* **Acceptance:**
  * Valid FEEDBACK.md → exit 0 with "Feedback file OK" message.
  * Missing required field → exit 2 with line number and field name.
  * Duplicate FEEDBACK-ID → exit 2 with diagnostic.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . feedback validate`
* **Evidence:**
  * Validation output for both valid and invalid FEEDBACK.md.

---

### 24.1 — `agentctl feedback inject`

* **Objective:**
  Parse validated FEEDBACK.md entries and inject them as Issue records into the `## Active issues` section of STATE.md, marking injected entries as `[PROCESSED]`.
* **Deliverables:**
  * `agentctl feedback inject` subcommand
  * Conversion logic: `FeedbackEntry → Issue` (Impact → Impact, Type+Description → Notes, Expected → Unblock Condition, Proposed action → Evidence Needed)
  * Issue IDs allocated as `ISSUE-<next-available-id>` (scans existing STATE.md issues to avoid collisions)
  * Injected entries marked with `- [x] FEEDBACK-001: <title>  <!-- processed: ISSUE-123 -->` in FEEDBACK.md
  * `--dry-run` flag: print what would be injected without modifying files
* **Acceptance:**
  * After inject, STATE.md `## Active issues` contains new Issue entries from feedback.
  * FEEDBACK.md entries are marked `[x]` (processed) with the mapped ISSUE-ID in a comment.
  * Running inject twice does not duplicate issues.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . feedback inject --dry-run`
  * `python3 tools/agentctl.py --repo-root . feedback inject`
* **Evidence:**
  * STATE.md diff showing injected Issues. FEEDBACK.md with processed markers.

---

### 24.2 — Dispatcher integration

* **Objective:**
  Extend `_recommend_next()` to route to `issues_triage` when `.vibe/FEEDBACK.md` contains unprocessed entries, surfacing the feedback count and highest-impact entry in the reason string.
* **Deliverables:**
  * `_has_unprocessed_feedback(repo_root) -> tuple[bool, str]` helper in `tools/agentctl.py`
  * `_recommend_next()` check added after hard-stop conditions and before DECISION_REQUIRED gate
  * Reason format: `"Unprocessed human feedback: 2 entries (top impact: MAJOR). Run agentctl feedback inject."`
  * `validate()` warns when FEEDBACK.md exists and has unprocessed entries
* **Acceptance:**
  * `agentctl next` returns `issues_triage` when FEEDBACK.md has `- [ ] FEEDBACK-001:...` entries.
  * `agentctl next` returns normal role when FEEDBACK.md has only `- [x]` (processed) entries.
  * `agentctl validate` emits warning for unprocessed feedback.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . next --format json`
* **Evidence:**
  * `agentctl next` JSON output showing `issues_triage` with feedback reason.

---

### 24.3 — `agentctl feedback ack` and HISTORY.md archival

* **Objective:**
  Archive all processed FEEDBACK.md entries to HISTORY.md and clear them from FEEDBACK.md, with a timestamped summary line per entry.
* **Deliverables:**
  * `agentctl feedback ack` subcommand
  * Appends to `## Feedback archive` section in HISTORY.md (creates section if missing)
  * Archive format: `- YYYY-MM-DD FEEDBACK-001 → ISSUE-123: <title> (Type: concern, Impact: MAJOR)`
  * Removes archived entries from FEEDBACK.md; leaves unprocessed entries untouched
  * Prints summary: "Archived 2 feedback entries to HISTORY.md."
* **Acceptance:**
  * After ack, HISTORY.md contains archived entries with timestamps and ISSUE mappings.
  * FEEDBACK.md retains only unprocessed entries.
  * Idempotent: running ack again on an already-clean FEEDBACK.md prints "Nothing to archive."
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . feedback ack`
* **Evidence:**
  * HISTORY.md diff showing archived entries. FEEDBACK.md showing only remaining unprocessed entries.

---

### 24.4 — Integration tests and documentation

* **Objective:**
  Full test suite for the feedback channel and end-user documentation.
* **Deliverables:**
  * `tests/workflow/test_feedback_channel.py` covering: schema parsing, validation, inject (including duplicate guard), dispatcher routing, ack, idempotency, backward compat (no FEEDBACK.md)
  * `docs/feedback_channel.md` — protocol guide with FEEDBACK.md format reference, inject/ack workflow, and dispatcher integration notes
* **Acceptance:**
  * All tests pass.
  * `agentctl validate --strict` passes.
  * Docs include a full worked example (write feedback → inject → triage → ack).
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_feedback_channel.py -v`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. `docs/feedback_channel.md` exists.

---

## Stage 25 — Checkpoint Dependency Graph

**Stage objective:**
Extend PLAN.md with optional `depends_on: [X.Y, ...]` annotations per checkpoint, build a DAG validator integrated into `agentctl validate`, update the dispatcher to skip checkpoints whose dependencies are not yet (DONE), and implement `agentctl dag` to visualize the dependency graph. Optionally extend `agentctl next --parallel N` to return up to N simultaneously-runnable checkpoints.

### Stage invariants (apply to all checkpoints)

- **Backward compatible:** Existing PLANs without `depends_on:` annotations work identically to today. No defaults change.
- **Validate-integrated:** DAG validation runs inside `agentctl validate` — not a separate command. No extra step required for the common case.
- **Dep resolution is status-based:** A dependency is satisfied iff the referenced checkpoint is marked (DONE) or (SKIP) in PLAN.md. Live STATE.md status is not consulted.
- **No cross-stage restriction:** `depends_on:` may reference checkpoints in any stage; intra-stage and cross-stage deps are treated identically.
- **Additive parallel dispatch:** `--parallel N` is a new optional flag; the default (`agentctl next` with no flag) returns exactly one role as today.

---

### 25.0 — Dependency syntax design and parser

* **Objective:**
  Define the `depends_on:` syntax in PLAN.md checkpoint headers and implement `_parse_checkpoint_dependencies()` with backward-compatible parsing.
* **Deliverables:**
  * Syntax: optional line `depends_on: [1.4, 2.1]` (indented 2 spaces) immediately following the `### N.M — Title` heading
  * `_parse_checkpoint_dependencies(plan_text) -> dict[str, list[str]]` in `tools/agentctl.py` — returns `{checkpoint_id: [dep_id, ...]}` for all checkpoints; checkpoints without `depends_on:` have empty lists
  * Parsing is whitespace-tolerant and order-independent relative to other checkpoint metadata
  * Normalized checkpoint IDs (same `normalize_checkpoint_id()` used elsewhere)
* **Acceptance:**
  * Checkpoints without `depends_on:` → empty dep list (unchanged behavior).
  * Checkpoints with `depends_on: [1.4, 2.1]` → `{"2.0": ["1.4", "2.1"]}`.
  * Malformed `depends_on:` value → parse error captured for validation (not crash).
* **Demo commands:**
  * `python3 -m pytest tests/workflow/ -k "parse_checkpoint_dep" -v`
* **Evidence:**
  * Tests showing parsed deps for checkpoints with and without `depends_on:`.

---

### 25.1 — DAG validation (cycles, dangling deps, self-deps)

* **Objective:**
  Implement `_validate_checkpoint_dag()` with cycle detection, dangling reference detection, and self-dependency detection, integrated into `agentctl validate`.
* **Deliverables:**
  * `_validate_checkpoint_dag(checkpoint_ids, deps) -> list[str]` in `tools/agentctl.py`
  * Cycle detection: DFS with grey/black coloring; error message names the cycle path (e.g., "Cycle: 1.2 → 2.0 → 1.2")
  * Dangling reference: dep ID not present in `checkpoint_ids`
  * Self-dependency: `checkpoint_id` in its own dep list
  * Integration: `validate()` calls `_validate_checkpoint_dag()` and routes errors to `errors` list (strict mode) or `warnings` list (non-strict)
* **Acceptance:**
  * Cycle in deps → error with cycle path.
  * Dep referencing non-existent checkpoint → error with checkpoint ID.
  * Self-dep → error.
  * Valid DAG with no cycles or dangling refs → no errors.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/ -k "checkpoint_dag" -v`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Tests showing all error cases. `agentctl validate` catches a cyclic dep in a test fixture.

---

### 25.2 — Dispatcher integration: dep-aware ready-checkpoint selection

* **Objective:**
  Update `_recommend_next()` so that in the DONE state, it skips checkpoints whose `depends_on` deps are not yet (DONE)/(SKIP), surfaces the first dep-satisfied checkpoint, and emits a dep-blocked reason when all remaining checkpoints are dep-blocked.
* **Deliverables:**
  * `_get_satisfied_deps(plan_text, checkpoint_id) -> bool` helper — returns True iff all deps of `checkpoint_id` are (DONE) or (SKIP) in `plan_text`
  * Updated DONE-state branch in `_recommend_next()`: after skipping (DONE)/(SKIP) checkpoints, also skip dep-blocked checkpoints
  * Dep-blocked stop: if the only remaining checkpoints are dep-blocked, route to `stop` with reason listing the specific unmet deps
* **Acceptance:**
  * Checkpoint with all deps (DONE) → dispatcher routes to it normally.
  * Checkpoint with an unmet dep → dispatcher skips it and finds the next dep-satisfied checkpoint.
  * All remaining checkpoints dep-blocked → dispatcher routes to `stop` with unmet dep list.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/ -k "dep_aware_dispatch" -v`
* **Evidence:**
  * Tests showing all three cases.

---

### 25.3 — `agentctl dag` render command

* **Objective:**
  Implement `agentctl dag` that renders the checkpoint dependency graph as JSON or ASCII, with node status annotations (DONE/SKIP/READY/BLOCKED).
* **Deliverables:**
  * `agentctl dag` subcommand in `tools/agentctl.py`
  * JSON output (`--format json`): `{nodes: [{id, title, status, deps}], edges: [{from, to}]}`
    * `status`: `DONE` | `SKIP` | `READY` (deps satisfied, not yet done) | `DEP_BLOCKED` (unmet deps)
  * ASCII output (`--format ascii`, default): indented tree with status icons
    * `[✓] 1.0 — Title`, `[→] 1.1 — Title (ready)`, `[✗] 2.0 — Title (blocked: 1.2)`
  * Reads both PLAN.md (structure + deps + done markers) and STATE.md (current checkpoint)
* **Acceptance:**
  * `agentctl dag --format json` produces valid JSON with all checkpoints and their statuses.
  * `agentctl dag --format ascii` renders a readable tree.
  * A repo with no `depends_on:` annotations produces a linear graph (no edges in JSON).
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . dag --format json`
  * `python3 tools/agentctl.py --repo-root . dag --format ascii`
* **Evidence:**
  * JSON and ASCII output for a PLAN.md with and without deps.

---

### 25.4 — Parallel dispatch: `agentctl next --parallel N`

* **Objective:**
  Extend `agentctl next` with `--parallel N` that returns up to N simultaneously-runnable checkpoints (dep-satisfied leaves), enabling multiple agents to work in parallel on independent tracks.
* **Deliverables:**
  * `--parallel N` flag on `agentctl next` (N ≥ 1; N=1 is identical to current behavior)
  * `_get_ready_checkpoints(plan_text, state) -> list[str]` — returns all dep-satisfied, not-yet-done checkpoints in document order
  * Parallel output format: `recommended_roles: [{checkpoint, role, prompt_id, reason}, ...]` list instead of single `recommended_role`
  * Single-item list when N=1 or only one ready checkpoint exists (backward compatible JSON shape with both `recommended_role` and `recommended_roles` present)
* **Acceptance:**
  * `--parallel 2` with two independent ready checkpoints returns both.
  * `--parallel 2` with only one ready checkpoint returns one.
  * `--parallel 1` output is structurally identical to `agentctl next` without the flag.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . next --parallel 2 --format json`
* **Evidence:**
  * JSON output showing two recommended roles from a PLAN.md with parallel-ready checkpoints.

---

### 25.5 — Integration tests and documentation

* **Objective:**
  Full test suite for dependency graph features and end-user documentation.
* **Deliverables:**
  * `tests/workflow/test_checkpoint_dag.py` covering: dep parsing, DAG validation (cycles, dangling, self), dispatcher dep-aware skip, dep-blocked stop, `agentctl dag` JSON/ASCII output, parallel dispatch
  * `docs/checkpoint_dependencies.md` — dependency graph guide with syntax reference, validation rules, `agentctl dag` usage, and `--parallel` dispatch guide
  * `docs/concepts.md` updated with DAG concepts
* **Acceptance:**
  * All tests pass.
  * `agentctl validate --strict` passes.
  * Docs include a worked example of a diamond dependency (1.0 → 1.1 and 1.0 → 1.2 → 1.3, where 1.3 depends_on [1.1, 1.2]).
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_checkpoint_dag.py -v`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. `docs/checkpoint_dependencies.md` exists with diamond example.
