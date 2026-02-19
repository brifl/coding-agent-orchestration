# RLM Overview

## What RLM Means Here

RLM (Recursive Language Model) is an executor-managed loop for tasks that exceed
normal prompt context. The system keeps loop state small and stable while
offloading large inputs to disk as deterministic context bundles.

RLM is not "self-looping prompt text." Iteration is owned by the runtime, with
explicit limits, stop conditions, and audit traces.

## Why It Exists

Standard single-prompt workflows break down when a task needs:
- Repository-scale context that cannot fit in one prompt.
- Multi-step reasoning that must be resumable and auditable.
- Optional provider-backed subcalls under explicit budgets.

RLM addresses those cases with bounded execution and replayable traces.

## Lifecycle

1. Validate task schema before execution.
2. Build deterministic context bundle (`manifest.json`, `chunks.jsonl`).
3. Start runtime with persistent state and helper functions.
4. Execute root iterations under configured limits.
5. Optionally perform provider-backed subcalls (`subcalls` mode).
6. Stop only on `FINAL()` or limit breach.
7. Emit trace and final artifacts for audit/replay.

## Execution Modes

### Baseline mode (`mode: baseline`)

- No provider subcalls.
- Root loop reasons over bundled context directly.
- Best for deterministic, low-complexity multi-step tasks.
- Lower integration surface and lower operational risk.

### Subcall mode (`mode: subcalls`)

- Root loop may call `llm_query(...)` via provider interface.
- Provider selection follows explicit policy (primary/allowed/fallback).
- Requires strict budgets and caching for reproducibility.
- Best for tasks requiring targeted deep reasoning or specialization.

## Human-Assisted Providers

Some providers are human-assisted, not fully programmatic. A human-assisted
provider runs via an external queue:
- Executor writes request records.
- Human-assisted system returns response records.
- Runtime pauses as `AWAITING_EXTERNAL` and resumes after import.

Human-assisted providers are valid in subcall mode when auditability and
handoff semantics are preserved.

## Decision Table: Standard Loop vs RAG vs RLM

| Choose | Best when | Core mechanism | State profile | Typical output |
| --- | --- | --- | --- | --- |
| Standard Vibe loop | Scope is small and local; one checkpoint can be completed with direct file edits/tests | Agent reads needed files directly in session context | Ephemeral chat context; no formal bundle | Code/docs change + normal loop evidence |
| RAG (`rag-index`) | Need retrieval over larger corpus, but task is still single-pass answering or drafting | Indexed lexical/semantic retrieval returns top snippets for one generation pass | Index + retrieval context; no iterative runtime state | Retrieved context block + one response/artifact |
| RLM | Need bounded multi-iteration reasoning over large context with resumability/audit and optional subcalls | Deterministic bundle + persistent runtime + executor-managed recursion | Constant-size loop metadata + persisted runtime state/trace | Multi-iteration trace + explicit `FINAL()` artifact |

## Quick Selection Rules

- Use standard loops first when the checkpoint is narrow and directly actionable.
- Use RAG when retrieval quality is the bottleneck, not iterative reasoning.
- Use RLM when both context size and iterative reasoning depth are bottlenecks.
