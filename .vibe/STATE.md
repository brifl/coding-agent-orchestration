# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.6
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Prevent runaway recursion and make subcalls replayable.

## Deliverables (current checkpoint)

- Budget enforcement (per run and per iteration)
- Mandatory caching for subcall mode (`readwrite|readonly|off`)
- Deterministic retry policy
- `tools/rlm/replay.py`

## Acceptance (current checkpoint)

- Second run with `--cache readonly` reproduces identical response hashes and final output.

## Work log (current session)

- 2026-02-06: Review PASS — 21.5 acceptance met with demo rerun plus adversarial probes (invalid provider selection rejects with exit 2, and credential-scrubbed run reports missing env vars); auto-advanced to 21.6 and set status to NOT_STARTED.
- 2026-02-06: Issues triage — loaded API keys from repo `.env` via `provider_check` dotenv support, switched health checks to provider listing endpoints for stable auth/connectivity validation, and resolved ISSUE-013; moved status to IN_REVIEW.
- 2026-02-06: Issues triage — per user direction, deferred Triton support from active Stage 21 scope; updated PLAN/STATE acceptance and blocker criteria to core providers (OpenAI/Anthropic/Google); status remains BLOCKED pending credentials.
- 2026-02-06: Issues triage — confirmed ISSUE-013 as external prerequisite blocker; clarified exact env vars and concrete unblock evidence command for active providers; status remains BLOCKED.
- 2026-02-06: Implemented 21.5 (blocked) — added provider interface/modules (`openai`, `anthropic`, `google`, `triton`), config resolution overlays (`.vibe/rlm/providers.json`, `~/.vibe/providers.json`), and `tools/rlm/provider_check.py`; health-check command runs and reports structured failures, but acceptance is blocked on missing provider credentials; opened ISSUE-013 and set status to BLOCKED.
- 2026-02-06: Review PASS — 21.4 acceptance met with demo rerun and adversarial probes (max-root-iters limit stop + resume rejection on mutated task hash); auto-advanced to 21.5 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.4 — added `skills/rlm-tools/executor.py` (`run/step/resume`) with bounded baseline iteration, run-state persistence, trace logging, and final artifact writeout; added `tasks/rlm/baseline_example.json` + fixture context; demo run completed multi-iteration execution and stopped on `FINAL`; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.3 acceptance met with selftest + adversarial resume probes (max-stdout mismatch, bundle-fingerprint mismatch); auto-advanced to 21.4 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.3 — added `tools/rlm/runtime.py` with helper injection (`context`, `list_chunks`, `get_chunk`, `grep`, `peek`, `FINAL`), deterministic stdout truncation, and persisted `state.json`; added `tools/rlm/runtime_selftest.py` proving resume semantics and finalized-step rejection; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.2 acceptance met (demo build + malformed-task fail-fast + determinism/locality adversarial probe); auto-advanced to 21.3 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.2 — added `tools/rlm/context_bundle.py` with deterministic file ordering and line-stable chunking; demo build produced bundle artifacts and probes confirmed deterministic reruns plus one-line edit locality; moved status to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- path: tools/rlm/provider_check.py
  - cmd: `python3 tools/rlm/provider_check.py --provider all`
  - result: PASS — `openai`, `anthropic`, and `google` checks return `ok: true` with HTTP 200.
- path: tools/rlm/providers/base.py
  - cmd: `python3 -m py_compile tools/rlm/provider_check.py tools/rlm/providers/*.py`
  - result: PASS — provider modules compile cleanly.

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
