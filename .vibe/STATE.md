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
- Status: BLOCKED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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

- 2026-02-06: Issues triage — confirmed ISSUE-013 as external prerequisite blocker; clarified exact env vars/endpoints and concrete unblock evidence command (`provider_check --all` must return all `ok: true`); status remains BLOCKED.
- 2026-02-06: Implemented 21.5 (blocked) — added provider interface/modules (`openai`, `anthropic`, `google`, `triton`), config resolution overlays (`.vibe/rlm/providers.json`, `~/.vibe/providers.json`), and `tools/rlm/provider_check.py`; health-check command runs and reports structured failures, but acceptance is blocked on missing provider credentials and unavailable Triton endpoint; opened ISSUE-013 and set status to BLOCKED.
- 2026-02-06: Review PASS — 21.4 acceptance met with demo rerun and adversarial probes (max-root-iters limit stop + resume rejection on mutated task hash); auto-advanced to 21.5 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.4 — added `skills/rlm-tools/executor.py` (`run/step/resume`) with bounded baseline iteration, run-state persistence, trace logging, and final artifact writeout; added `tasks/rlm/baseline_example.json` + fixture context; demo run completed multi-iteration execution and stopped on `FINAL`; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.3 acceptance met with selftest + adversarial resume probes (max-stdout mismatch, bundle-fingerprint mismatch); auto-advanced to 21.4 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.3 — added `tools/rlm/runtime.py` with helper injection (`context`, `list_chunks`, `get_chunk`, `grep`, `peek`, `FINAL`), deterministic stdout truncation, and persisted `state.json`; added `tools/rlm/runtime_selftest.py` proving resume semantics and finalized-step rejection; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.2 acceptance met (demo build + malformed-task fail-fast + determinism/locality adversarial probe); auto-advanced to 21.3 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.2 — added `tools/rlm/context_bundle.py` with deterministic file ordering and line-stable chunking; demo build produced bundle artifacts and probes confirmed deterministic reruns plus one-line edit locality; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.1 acceptance met with demo + adversarial probes (semantic invalid schema and malformed JSON); auto-advanced to 21.2 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.1 — added `docs/rlm_task_schema.md`, `tools/rlm/validate_task.py`, and example tasks under `tasks/rlm/`; validated pass path on `tasks/rlm/example.json` and fail-fast diagnostics on malformed input; moved status to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- path: tools/rlm/provider_check.py
  - cmd: `python3 tools/rlm/provider_check.py --provider openai`
  - result: FAIL (expected in current environment) — reports missing `OPENAI_API_KEY` and exits non-zero.
- path: tools/rlm/provider_check.py
  - cmd: `python3 tools/rlm/provider_check.py --provider all`
  - result: FAIL (expected in current environment) — reports missing `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, and Triton connection refusal.
- path: tools/rlm/providers/base.py
  - cmd: `python3 -m py_compile tools/rlm/provider_check.py tools/rlm/providers/*.py`
  - result: PASS — provider modules compile cleanly.

## Active issues

- [ ] ISSUE-013: Provider credentials/endpoints unavailable for 21.5 acceptance
  - Impact: BLOCKER
  - Status: BLOCKED
  - Owner: human
  - Unblock Condition: Configure required provider credentials and a reachable Triton HTTP endpoint on this machine.
  - Evidence Needed: `python3 tools/rlm/provider_check.py --provider all` returns exit code 0 with all provider checks `ok: true`.
  - Notes: Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY`; start/configure Triton at configured `base_url` (default `http://localhost:8000`) with expected model name; rerun provider checks.

## Decisions

(No decisions)
