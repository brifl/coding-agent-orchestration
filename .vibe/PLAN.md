# PLAN

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## How to use this file

- This is the **checkpoint backlog**.
- Each checkpoint must have: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Keep checkpoints small enough to complete in one focused iteration.
- Completed stages are archived to `.vibe/HISTORY.md`.

---

## Stage 21 — RLM (Recursive Language Model) Tools Skill

**Stage objective:**  
Implement a bounded, auditable Recursive Language Model (RLM) execution harness that allows agents to reason over arbitrarily large contexts by offloading prompt data into a persistent runtime environment and iterating under explicit limits. The system must support real provider-backed subcalls (OpenAI, Anthropic, Google, Triton HTTP) and a human-assisted Kilo provider, while remaining deterministic, replayable, and safe.

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
    - Triton HTTP (TensorRT-LLM)
  * Config resolution:
    - repo-local `.vibe/rlm/providers.json`
    - global `~/.vibe/providers.json`
    - secrets via env vars only
  * Health check:
    - `tools/rlm/provider_check.py`
* **Acceptance:**
  * `provider_check` passes for all four providers on a configured machine.
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

### 21.7 — Kilo provider (human-assisted via external queue)

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

### 21.9 — Triton HTTP codec contract

* **Objective:**  
  Support TensorRT-LLM via HTTP with extensible input/output codecs.
* **Deliverables:**
  * Codec interface (`encode` / `decode`)
  * v1 `raw_text` codec
  * Docs: `docs/rlm_triton.md`
* **Acceptance:**
  * `provider_check --provider triton` succeeds using raw_text codec.
* **Demo commands:**
  * `python tools/rlm/provider_check.py --provider triton`
* **Evidence:**
  * Successful completion output.

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
