# PLAN

## Stage 21 — RLM (Recursive Language Model) Tools Skill

**Stage objective:**  
Implement a bounded, auditable Recursive Language Model (RLM) execution harness that allows agents to reason over arbitrarily large contexts by offloading prompt data into a persistent runtime environment and iterating under explicit limits. The system must support real provider-backed subcalls (OpenAI, Anthropic, Google) and a human-assisted Kilo provider, while remaining deterministic, replayable, and safe.

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
  * `provider_policy`: primary, allowed[], fallback[], `kilo_requires_human`
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

### (DEFERRED) 21.7 — Kilo provider (human-assisted via external queue)
* **Important:**  This is deferred. Mark it as complete/skipped for now. We are not going to support Kilo until much later on.
* **Objective:**  
  Support Kilo (VS Code extension) as a human-assisted provider with full auditability.
* **Deliverables:**
  * `tools/rlm/providers/kilo_provider.py` (mode: external_queue)
  * Queue directories:
    - `.vibe/rlm/queue/<run_id>/requests.jsonl`
    - `.vibe/rlm/queue/<run_id>/responses.jsonl`
  * Queue CLI helpers:
    - `queue status`
    - `queue export`
    - `queue import`
  * Docs: `docs/rlm_kilo.md`
* **Acceptance:**
  * Executor pauses with `AWAITING_EXTERNAL`, resumes after response import, and completes run.
* **Demo commands:**
  * `python skills/rlm-tools/executor.py queue status --run <run_dir>`
* **Evidence:**
  * Trace shows external request/response hashes.

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
  * `python3 -m pytest tools/ -k "stage_22" -v`
  * `python3 tools/agentctl.py --repo-root . validate --strict`
* **Evidence:**
  * Test output showing all pass. Documentation file exists.
---
