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
- Status: IN_PROGRESS  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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

- 2026-02-06: Review FAIL — reran 21.6 demo command exactly (`python3 skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readonly`) and found non-fresh reruns fail with `Runtime already finalized`; opened ISSUE-014 and moved status to IN_PROGRESS for targeted executor run-reset fix.
- 2026-02-06: Implemented 21.6 — added subcall-mode cache policy enforcement (`readwrite|readonly|off` with mandatory explicit selection), per-iteration/per-run subcall budgets, deterministic retry tracing, and `tools/rlm/replay.py`; verified readonly replay reproduces identical response hashes/final artifact and captured adversarial budget/cache probes; moved status to IN_REVIEW.
- 2026-02-06: Consolidation — pruned STATE work log to the most recent 10 entries and cleared stale 21.5 evidence; stage/checkpoint/status remain aligned at 21.6 / NOT_STARTED.
- 2026-02-06: Review PASS — 21.5 acceptance met with demo rerun plus adversarial probes (invalid provider selection rejects with exit 2, and credential-scrubbed run reports missing env vars); auto-advanced to 21.6 and set status to NOT_STARTED.
- 2026-02-06: Issues triage — loaded API keys from repo `.env` via `provider_check` dotenv support, switched health checks to provider listing endpoints for stable auth/connectivity validation, and resolved ISSUE-013; moved status to IN_REVIEW.
- 2026-02-06: Issues triage — per user direction, deferred Triton support from active Stage 21 scope; updated PLAN/STATE acceptance and blocker criteria to core providers (OpenAI/Anthropic/Google); status remains BLOCKED pending credentials.
- 2026-02-06: Issues triage — confirmed ISSUE-013 as external prerequisite blocker; clarified exact env vars and concrete unblock evidence command for active providers; status remains BLOCKED.
- 2026-02-06: Implemented 21.5 (blocked) — added provider interface/modules (`openai`, `anthropic`, `google`, `triton`), config resolution overlays (`.vibe/rlm/providers.json`, `~/.vibe/providers.json`), and `tools/rlm/provider_check.py`; health-check command runs and reports structured failures, but acceptance is blocked on missing provider credentials; opened ISSUE-013 and set status to BLOCKED.
- 2026-02-06: Review PASS — 21.4 acceptance met with demo rerun and adversarial probes (max-root-iters limit stop + resume rejection on mutated task hash); auto-advanced to 21.5 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.4 — added `skills/rlm-tools/executor.py` (`run/step/resume`) with bounded baseline iteration, run-state persistence, trace logging, and final artifact writeout; added `tasks/rlm/baseline_example.json` + fixture context; demo run completed multi-iteration execution and stopped on `FINAL`; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.3 acceptance met with selftest + adversarial resume probes (max-stdout mismatch, bundle-fingerprint mismatch); auto-advanced to 21.4 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.3 — added `tools/rlm/runtime.py` with helper injection (`context`, `list_chunks`, `get_chunk`, `grep`, `peek`, `FINAL`), deterministic stdout truncation, and persisted `state.json`; added `tools/rlm/runtime_selftest.py` proving resume semantics and finalized-step rejection; moved status to IN_REVIEW.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- `python3 skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readwrite --fresh` and `python3 skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readonly --fresh` both completed with identical `response_hashes` and final artifact hash.
- Replay summaries: `.vibe/rlm/runs/subcalls_example.readwrite.summary.json` and `.vibe/rlm/runs/subcalls_example.readonly.summary.json`; comparison artifact: `.vibe/rlm/runs/subcalls_example.compare.json` (`response_hashes_match=true`, `final_artifact_sha256_match=true`).
- Readonly cache-hit trace evidence: `.vibe/rlm/runs/subcalls_example/trace.jsonl` contains `event=subcall`, `cache_status=hit`, `attempts=0`.
- Mandatory cache enforcement probe: `.vibe/rlm/evidence/21.6/probe_missing_cache.log` shows `Subcall mode requires explicit --cache`.
- Readonly cache-miss probe: `.vibe/rlm/runs/probe_cache_miss/trace.jsonl` records `Readonly cache miss ...` and run stops `STEP_ERROR`.
- Per-iteration budget probe: `.vibe/rlm/runs/probe_per_iter_limit/trace.jsonl` records `Subcall budget exceeded for iteration 1`.
- Per-run budget probe: `.vibe/rlm/runs/probe_total_limit/trace.jsonl` records `Subcall budget exceeded for run: max_subcalls_total=1`.
- Deterministic retry probe: `.vibe/rlm/runs/probe_retry/trace.jsonl` subcall event shows `attempts=2` on first-call transient failure scenario.

## Active issues

- [ ] ISSUE-014: Non-fresh executor rerun fails after finalized state
  - Impact: MAJOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: `executor.py run` resets runtime state for new runs (or safely replaces stale run-state artifacts) so the checkpoint demo command works repeatedly without requiring `--fresh`.
  - Evidence Needed: `python3 skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readonly` succeeds twice in a row and preserves replay consistency.
  - Notes: Current behavior raises `Runtime already finalized; additional steps are not allowed.`

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
