# RLM Glossary

## Core Terms

- **RLM (Recursive Language Model):** Executor-managed iterative reasoning
  system with explicit limits, persistent state, and explicit stop semantics.
- **Task:** Declarative run request (query, context sources, mode, limits,
  provider policy, outputs, trace config).
- **Root iteration:** One top-level executor step in the main loop.
- **FINAL():** Explicit termination call that marks successful completion.
- **Limit breach:** Forced stop when configured budgets/limits are exceeded.

## Context and Data

- **Context bundle:** Deterministic, disk-backed representation of large task
  context.
- **Manifest (`manifest.json`):** Ordered input file list with hashes/sizes.
- **Chunk (`chunks.jsonl` row):** Addressable piece of source text with source
  range, hash, and metadata.
- **Bundle metadata (`bundle.meta.json`):** Build parameters and summary stats.

## Runtime and Execution

- **Runtime sandbox:** Persistent execution environment exposing safe helpers
  (for example `list_chunks()`, `get_chunk()`, `grep()`, `peek()`).
- **State snapshot (`state.json`):** Serializable run state used for resume.
- **Trace (`trace.jsonl`):** Append-only audit log of iteration decisions,
  subcalls, limits, and transitions.
- **Constant-size loop state:** Iteration handoff contains metadata pointers,
  not full context payloads.

## Modes and Providers

- **Baseline mode:** RLM run without provider subcalls.
- **Subcall mode:** RLM run that allows `llm_query(...)` calls to configured
  providers.
- **Provider policy:** Deterministic rule set for provider selection
  (`primary`, `allowed`, `fallback`).
- **Human-assisted provider:** Provider path that requires external human/tool
  response handling before runtime can continue.
- **AWAITING_EXTERNAL:** Runtime status when execution pauses pending imported
  external response.

## Control and Reproducibility

- **Budget:** Declared resource bounds (iterations, depth, subcalls, timeout,
  output size).
- **Cache mode:** Subcall cache policy (`readwrite`, `readonly`, `off`).
- **Replay:** Deterministic re-execution using trace + cached subcall artifacts
  to verify output stability.
