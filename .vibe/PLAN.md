# PLAN

## Stage 21 — RLM (Recursive Language Model) Tools Skill

**Stage objective:**  
Implement a bounded, auditable Recursive Language Model (RLM) execution harness that allows agents to reason over arbitrarily large contexts by offloading prompt data into a persistent runtime environment and iterating under explicit limits. The system must support real provider-backed subcalls (OpenAI, Anthropic, Google) while remaining deterministic, replayable, and safe.

### Stage invariants (apply to all checkpoints)

- **Prompt offload:** Large context is stored outside the chat window (bundles), not repeatedly injected into prompts.
- **Constant-size loop state:** Each iteration carries only metadata (stdout length, state keys), not full outputs.
- **Explicit bounds:** All recursion and subcalls are governed by declared limits.
- **Explicit stop:** Execution halts only when `FINAL()` is invoked or a limit is breached.
- **Auditability:** Every run emits a trace sufficient to reconstruct what happened and why.
- **No self-looping prompts:** Iteration is owned by the executor, not prompt text.

---

### 21.0 — RLM concept, UX, and capability model

* **Objective:**  
  Define what RLM means in this system, when it should be used, and how it differs from standard prompts and RAG.
* **Deliverables:**
  * `docs/rlm_overview.md` — RLM concepts, lifecycle, and examples
  * `docs/rlm_glossary.md` — terminology (root iteration, bundle, subcall, FINAL, etc.)
  * Decision table: when to use RLM vs RAG vs standard Vibe loops
* **Acceptance:**
  * Documentation explains baseline vs subcall mode and human-assisted providers.
* **Demo commands:**
  * `cat docs/rlm_overview.md`
* **Evidence:**
  * Decision table included and unambiguous.

---

### 21.1 — RLM task schema and validation (fail-fast)

* **Objective:**  
  Define a strict invocation format for RLM runs and validate it before execution.
* **Deliverables:**
  * `docs/rlm_task_schema.md`
  * `tools/rlm/validate_task.py`
  * Example tasks in `tasks/rlm/`
* **Task schema (minimum fields):**
  * `task_id`, `query`
  * `context_sources` (files/dirs/snapshots, include/exclude)
  * `bundle` (chunking strategy, max chars)
  * `mode`: `baseline` | `subcalls`
  * `provider_policy`: primary, allowed[], fallback[]
  * `limits`: max_root_iters, max_depth, max_subcalls_total, max_subcalls_per_iter, timeout_s, max_stdout_chars
  * `outputs`: final_path, artifact_paths[]
  * `trace`: trace_path, redaction_mode
* **Acceptance:**
  * Invalid tasks fail fast with file/line diagnostics.
* **Demo commands:**
  * `python tools/rlm/validate_task.py tasks/rlm/example.json`
* **Evidence:**
  * Validation error shown for malformed task.

---

### 21.2 — Context bundling (build large contexts deterministically)

* **Objective:**  
  Build deterministic “context bundles” that can exceed model context size.
* **Deliverables:**
  * `tools/rlm/context_bundle.py`
  * Bundle output at `.vibe/rlm/bundles/<task_id>/`:
    - `manifest.json` (ordered files, hashes, sizes)
    - `chunks.jsonl` (chunk_id, source, range, char_count, hash, text)
    - `bundle.meta.json`
* **Acceptance:**
  * Same inputs produce identical manifests and chunk hashes.
  * One-line edit only affects related chunks.
* **Demo commands:**
  * `python tools/rlm/context_bundle.py build --task tasks/rlm/example.json`
* **Evidence:**
  * Stable manifest and chunk list.

---

### 21.3 — Runtime sandbox (persistent REPL + state)

* **Objective:**  
  Provide a safe, persistent execution environment for RLM iterations.
* **Deliverables:**
  * `tools/rlm/runtime.py`
  * Injected helpers: `context`, `list_chunks()`, `get_chunk()`, `grep()`, `peek()`, `FINAL()`
  * Deterministic stdout capture and truncation
  * State serialization (`state.json`)
* **Acceptance:**
  * Runtime resumes from saved state without ambiguity.
* **Demo commands:**
  * `python tools/rlm/runtime_selftest.py`
* **Evidence:**
  * Selftest demonstrates resume + truncation.

---

### 21.4 — Core executor loop (baseline mode)

* **Objective:**  
  Implement bounded iteration with constant-size metadata and explicit stop semantics.
* **Deliverables:**
  * `skills/rlm-tools/executor.py`
    - `run`, `step`, `resume`
  * Run directory: `.vibe/rlm/runs/<task_id>/`
    - `state.json`, `trace.jsonl`, final artifacts
* **Acceptance:**
  * Baseline mode completes multi-iteration runs and stops only on `FINAL()` or limits.
* **Demo commands:**
  * `python skills/rlm-tools/executor.py run --task tasks/rlm/baseline_example.json`
* **Evidence:**
  * Trace shows iterations and explicit stop.

---

### 21.5 — Provider-backed `llm_query` (programmatic providers)

* **Objective:**  
  Enable real subcalls to LLM providers with a unified interface.
* **Deliverables:**
  * Provider interface: `tools/rlm/providers/base.py`
  * Providers:
    - OpenAI
    - Anthropic
    - Google (Gemini)
  * Config resolution:
    - repo-local `.vibe/rlm/providers.json`
    - global `~/.vibe/providers.json`
    - secrets via env vars only
  * Health check:
    - `tools/rlm/provider_check.py`
* **Acceptance:**
  * `provider_check` passes for all active providers (OpenAI, Anthropic, Google) on a configured machine.
* **Demo commands:**
  * `python tools/rlm/provider_check.py --provider openai`
* **Evidence:**
  * Successful provider check output.

---

### 21.6 — Determinism backbone: budgets, caching, replay

* **Objective:**  
  Prevent runaway recursion and make subcalls replayable.
* **Deliverables:**
  * Budget enforcement (per run and per iteration)
  * Mandatory caching for subcall mode (`readwrite|readonly|off`)
  * Deterministic retry policy
  * `tools/rlm/replay.py`
* **Acceptance:**
  * Second run with `--cache readonly` reproduces identical response hashes and final output.
* **Demo commands:**
  * `python skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readonly`
* **Evidence:**
  * Trace shows cache hits and identical hashes.

---

### 21.8 — Provider selection policy

* **Objective:**  
  Make provider choice deterministic and explicit.
* **Deliverables:**
  * Task schema fields for provider policy
  * Executor logic honoring primary/allowed/fallback ordering
* **Acceptance:**
  * Same task and config yields same provider choice.
* **Demo commands:**
  * `python skills/rlm-tools/executor.py run --task tasks/rlm/provider_policy_example.json`
* **Evidence:**
  * Trace confirms deterministic selection.

---

### 21.10 — Skill packaging and cross-agent ergonomics

* **Objective:**  
  Package RLM as a first-class skill usable across agents.
* **Deliverables:**
  * `skills/rlm-tools/SKILL.yaml`
  * Entrypoints:
    - `rlm validate`
    - `rlm bundle`
    - `rlm run`
    - `rlm step`
    - `rlm resume`
    - `rlm providers`
  * `docs/rlm_agents.md`
* **Acceptance:**
  * `skillctl validate skills/rlm-tools` passes.
* **Demo commands:**
  * `python tools/skillctl.py validate skills/rlm-tools`
* **Evidence:**
  * CLI help output.

---

### 21.11 — Reference tasks and evaluation harness

* **Objective:**  
  Prove RLM usefulness on real “big context” problems.
* **Deliverables:**
  * `tasks/rlm/`:
    - `repo_comprehension.json`
    - `change_impact.json`
    - `doc_synthesis.json`
  * `tools/rlm/eval_smoke.py`
* **Acceptance:**
  * At least one task demonstrates bundling, multi-iteration runtime reasoning, subcalls, and final artifact creation.
* **Demo commands:**
  * `python tools/rlm/eval_smoke.py --task tasks/rlm/repo_comprehension.json`
* **Evidence:**
  * Example output artifact + trace committed (or redacted).

---

## Stage 22 — Vibe-Run Workflow Improvements

**Stage objective:**
Improve the vibe-run dispatcher to behave more like a senior engineer: design intentionally before each stage, review code quality (not just falsify claims), run periodic maintenance, and catch failures early with a smoke test gate.

### Stage invariants (apply to all checkpoints)

- **Backward-compatible:** Repos without new workflow flags continue to work unchanged.
- **No protocol break:** LOOP_RESULT schema is unchanged.
- **Reuse existing prompts:** Maintenance cycles reuse `prompt.refactor_scan`, `prompt.test_gap_analysis`, `prompt.docs_gap_analysis`.

---

### 22.0 — Stage design trigger and workflow flags

* **Objective:**
  Add `STAGE_DESIGNED` and `MAINTENANCE_CYCLE_DONE` workflow flags and dispatcher logic to route to design/maintenance before implementation.
* **Deliverables:**
  * `_get_stage_number()` helper in `tools/agentctl.py`
  * `_stage_design_trigger_reason()` trigger function
  * `_maintenance_cycle_trigger_reason()` trigger function
  * Updated `_recommend_next()` with new trigger checks
  * Extended return type: `tuple[Role, str, str | None]` for prompt_id override
  * Updated call sites (lines 1884, 2069)
  * New workflow flags in `.vibe/STATE.md`
* **Acceptance:**
  * `agentctl next` returns `design` when `STAGE_DESIGNED` is unset.
  * `agentctl next` returns maintenance prompt when stage%3 triggers and `MAINTENANCE_CYCLE_DONE` is unset.
  * `agentctl next` returns `implement` when both flags are set.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . --format json next`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Dispatcher output shows `design` role with `STAGE_DESIGNED` reason.

---

### 22.1 — Rewrite stage design prompt

* **Objective:**
  Transform `prompt.stage_design` from a formatting pass to a strategic architect.
* **Deliverables:**
  * Rewritten `prompt.stage_design` in `prompts/template_prompts.md`
* **Acceptance:**
  * Prompt focuses on next 1-3 imminent stages only.
  * Prompt requires intentional design decisions.
  * Prompt requires setting `STAGE_DESIGNED` flag.
  * `agentctl validate` passes.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Prompt text includes "STAGE_DESIGNED", "next 1-3 stages", "intentional design decisions".

---

### 22.2 — Enhanced checkpoint review with code-review behavior

* **Objective:**
  Make review identify top 3 improvements like a code reviewer.
* **Deliverables:**
  * Updated `prompt.checkpoint_review` in `prompts/template_prompts.md`
* **Acceptance:**
  * Review includes "Pass C: Code review for improvements".
  * Each improvement tagged `[MINOR]`/`[MODERATE]`/`[MAJOR]`.
  * `[MODERATE]`/`[MAJOR]` → FAIL; `[MINOR]` → fix in place + PASS.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Prompt text includes Pass C, tagging rules, FAIL/PASS criteria.

---

### 22.3 — Smoke test gate before review

* **Objective:**
  Auto-run demo commands before review; fail fast if demos break.
* **Deliverables:**
  * `_extract_demo_commands()` function in `tools/agentctl.py`
  * `_run_smoke_test_gate()` function in `tools/agentctl.py`
  * Updated `_recommend_next()` IN_REVIEW branch
* **Acceptance:**
  * Failing demo commands → `issues_triage` instead of `review`.
  * Passing or absent demo commands → `review` as before.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Unit test with failing demo command dispatches to `issues_triage`.

---

### 22.4 — Implementation preflight, retrospective trigger, consolidation flag cleanup

* **Objective:**
  Add dependency preflight to implementation prompt, extend retrospective to every 5 stages, ensure consolidation clears new flags.
* **Deliverables:**
  * Updated `prompt.checkpoint_implementation` with preflight step
  * Updated `prompt.consolidation` to clear `STAGE_DESIGNED` and `MAINTENANCE_CYCLE_DONE`
  * Updated `_process_improvements_trigger_reason()` with stage%5 check
* **Acceptance:**
  * Implementation prompt includes dependency preflight.
  * Consolidation prompt clears both new flags.
  * Retrospective triggers at stage%5.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Prompt text changes verified. Trigger function tested.

---

### 22.5 — Integration tests and documentation

* **Objective:**
  End-to-end test of improved workflow and documentation.
* **Deliverables:**
  * Tests covering all new triggers and flag lifecycle
  * `docs/workflow_improvements.md`
* **Acceptance:**
  * All tests pass.
  * `agentctl validate --strict` passes.
  * Documentation explains all improvements.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. Documentation file exists.

---

## Stage 23 — Interactive Plan Authoring Pipeline

**Stage objective:**
Implement an `agentctl plan` command that orchestrates the design-side decomposition prompts (ideation → feature_breakdown → architecture → milestones → stages_from_milestones → checkpoints_from_stage) via RLM subcalls to produce a validated `PLAN.md` from a problem statement, eliminating the manual bootstrap burden for new projects.

### Stage invariants (apply to all checkpoints)

- **Dry-run first:** `--dry-run` flag prints the generated plan without writing to disk. Always available.
- **Validate before write:** Generated PLAN.md passes `validate()` (complexity budget, checkpoint structure, stage IDs) before any disk write.
- **Idempotent schema:** Same problem statement + same provider config + same prompt catalog produces the same PLAN.md structure (modulo LLM non-determinism).
- **No silent overwrites:** If `.vibe/PLAN.md` already exists, the command requires `--overwrite` or writes to `--output <path>`.
- **No RLM hard dependency:** If RLM is unavailable, the command fails fast with a clear diagnostic pointing to the missing provider config.

---

### 23.0 — Pipeline schema, CLI skeleton, and config resolution

* **Objective:**
  Define the `PipelineConfig` schema and the `agentctl plan` CLI entry point with argument parsing, config resolution, and dry-run stub.
* **Deliverables:**
  * `tools/plan_pipeline.py` — `PipelineConfig` dataclass (problem_statement, provider, dry_run, output_path, overwrite)
  * `agentctl plan` subcommand wired into `tools/agentctl.py`
  * Config resolution: repo-local `.vibe/plan_pipeline.json` overrides global `~/.vibe/plan_pipeline.json`
  * Fail-fast validation: missing problem statement, output-path conflict (exists + no --overwrite), missing provider config
* **Acceptance:**
  * `agentctl plan --help` shows all flags.
  * Running without `--problem-statement` exits with a clear error.
  * Running with `--dry-run` prints "(dry run — no files written)" without touching disk.
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . plan --help`
  * `python3 tools/agentctl.py --repo-root . plan --dry-run --problem-statement "Build a todo app"`
* **Evidence:**
  * `--help` output and dry-run stub output.

---

### 23.1 — RLM-backed prompt step executor

* **Objective:**
  Implement `_run_pipeline_step(prompt_id, inputs, config)` that calls the RLM provider for one design prompt, validates the output schema before returning, and fails fast with a clear diagnostic on schema mismatch.
* **Deliverables:**
  * `_run_pipeline_step(prompt_id, inputs, config) -> dict` in `tools/plan_pipeline.py`
  * Each step output validated against a minimal required-keys schema before passing to the next step
  * `PipelineStepError` exception with step name, prompt_id, and raw output snippet for diagnosis
  * Unit-testable: step executor accepts a provider stub for offline testing
* **Acceptance:**
  * A stub provider returning well-formed JSON passes step validation and returns structured output.
  * A stub provider returning malformed JSON raises `PipelineStepError` with diagnostic.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/ -k "pipeline_step" -v`
* **Evidence:**
  * Tests pass showing both success and failure paths.

---

### 23.2 — Full pipeline orchestration (ideation → checkpoints)

* **Objective:**
  Wire all six design prompts in sequence, threading each step's structured output as the next step's input, with progress reporting and the ability to resume from a checkpoint directory.
* **Deliverables:**
  * `run_plan_pipeline(config) -> PipelineResult` in `tools/plan_pipeline.py`
  * Prompt sequence: `prompt.ideation` → `prompt.feature_breakdown` → `prompt.architecture` → `prompt.milestones` → `prompt.stages_from_milestones` → `prompt.checkpoints_from_stage`
  * Intermediate outputs saved to `.vibe/plan_pipeline/<run_id>/step_<N>_<prompt_id>.json` for resume
  * `--resume <run_id>` flag skips already-completed steps
  * Progress printed to stderr (Step N/6: running prompt.ideation…)
* **Acceptance:**
  * With stub provider, full 6-step pipeline runs and produces a `PipelineResult` with `stages` and `checkpoints` fields.
  * Resume skips completed steps (verified by deleting step 3 output and re-running).
* **Demo commands:**
  * `python3 -m pytest tests/workflow/ -k "pipeline_orchestration" -v`
* **Evidence:**
  * Test output showing 6-step run and resume behavior.

---

### 23.3 — PLAN.md writer with complexity validation

* **Objective:**
  Convert the `PipelineResult` into a valid PLAN.md document, run it through `validate()` for complexity and structural checks, emit warnings for over-budget checkpoints, and write to disk only when validation passes.
* **Deliverables:**
  * `render_plan_md(result: PipelineResult) -> str` in `tools/plan_pipeline.py`
  * Complexity check: run `check_plan_for_checkpoint()` on each generated checkpoint; warn if budget exceeded
  * Write path: `--dry-run` → print, else write to `--output` (default `.vibe/PLAN.md`) with `--overwrite` guard
  * Human-readable summary: "Generated 3 stages, 11 checkpoints. 1 complexity warning."
* **Acceptance:**
  * A stub pipeline result renders to a PLAN.md that passes `agentctl validate --strict`.
  * A result with an over-budget checkpoint emits a warning but still writes (warns, does not block).
* **Demo commands:**
  * `python3 tools/agentctl.py --repo-root . plan --problem-statement "Build a todo app" --dry-run`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Dry-run output of a generated PLAN.md. Validate passes on the output.

---

### 23.4 — Integration tests and documentation

* **Objective:**
  Full integration test suite for the plan authoring pipeline and end-user documentation.
* **Deliverables:**
  * `tests/workflow/test_plan_pipeline.py` covering: config validation, step executor (stub), full pipeline orchestration, PLAN.md writer, complexity warning, overwrite guard, resume
  * `docs/plan_authoring.md` — user guide with CLI reference, provider config, examples, and resume instructions
* **Acceptance:**
  * All tests pass.
  * `agentctl validate --strict` passes.
  * Docs explain how to run `agentctl plan` from scratch and how to resume an interrupted run.
* **Demo commands:**
  * `python3 -m pytest tests/workflow/test_plan_pipeline.py -v`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. `docs/plan_authoring.md` exists with CLI reference.

---

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
