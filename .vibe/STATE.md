# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.5
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Enable real subcalls to LLM providers with a unified interface.

## Deliverables (current checkpoint)

- Add provider interface: `tools/rlm/providers/base.py`
- Add providers:
  - OpenAI
  - Anthropic
  - Google (Gemini)
  - Triton HTTP (TensorRT-LLM)
- Add provider config resolution:
  - repo-local `.vibe/rlm/providers.json`
  - global `~/.vibe/providers.json`
  - env-var-only secrets
- Add `tools/rlm/provider_check.py`

## Acceptance (current checkpoint)

- `provider_check` passes for all four providers on a configured machine.

## Work log (current session)

- 2026-02-06: Review PASS — 21.4 acceptance met with demo rerun and adversarial probes (max-root-iters limit stop + resume rejection on mutated task hash); auto-advanced to 21.5 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.4 — added `skills/rlm-tools/executor.py` (`run/step/resume`) with bounded baseline iteration, run-state persistence, trace logging, and final artifact writeout; added `tasks/rlm/baseline_example.json` + fixture context; demo run completed multi-iteration execution and stopped on `FINAL`; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.3 acceptance met with selftest + adversarial resume probes (max-stdout mismatch, bundle-fingerprint mismatch); auto-advanced to 21.4 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.3 — added `tools/rlm/runtime.py` with helper injection (`context`, `list_chunks`, `get_chunk`, `grep`, `peek`, `FINAL`), deterministic stdout truncation, and persisted `state.json`; added `tools/rlm/runtime_selftest.py` proving resume semantics and finalized-step rejection; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.2 acceptance met (demo build + malformed-task fail-fast + determinism/locality adversarial probe); auto-advanced to 21.3 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.2 — added `tools/rlm/context_bundle.py` with deterministic file ordering and line-stable chunking; demo build produced bundle artifacts and probes confirmed deterministic reruns plus one-line edit locality; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.1 acceptance met with demo + adversarial probes (semantic invalid schema and malformed JSON); auto-advanced to 21.2 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.1 — added `docs/rlm_task_schema.md`, `tools/rlm/validate_task.py`, and example tasks under `tasks/rlm/`; validated pass path on `tasks/rlm/example.json` and fail-fast diagnostics on malformed input; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.0 acceptance met (`rlm_overview` + `rlm_glossary` + decision table) with adversarial probes for required sections/terms; auto-advanced to 21.1 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.0 — added `docs/rlm_overview.md` and `docs/rlm_glossary.md`, including decision table (`RLM vs RAG vs standard loops`) and baseline/subcall + human-assisted provider explanations; moved status to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

(Checkpoint 21.5 — not yet started)

## Active issues

(None)

## Decisions

(No decisions)
