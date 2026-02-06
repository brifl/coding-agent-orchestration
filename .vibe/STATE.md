# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21
- Checkpoint: 21.11
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Prove RLM usefulness on real “big context” problems.

## Deliverables (current checkpoint)

- `tasks/rlm/`:
  - `repo_comprehension.json`
  - `change_impact.json`
  - `doc_synthesis.json`
- `tools/rlm/eval_smoke.py`

## Acceptance (current checkpoint)

- At least one task demonstrates bundling, multi-iteration runtime reasoning, subcalls, and final artifact creation.

## Work log (current session)

- 2026-02-06: Review PASS — 21.10 acceptance met (`skillctl validate skills/rlm-tools` passed) with adversarial probes confirming validation failures for malformed skill manifest and invalid provider selection; auto-advanced to 21.11 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.10 — packaged `rlm-tools` skill with `skills/rlm-tools/SKILL.yaml`, added multi-command wrapper `skills/rlm-tools/rlm.py` for `rlm validate|bundle|run|step|resume|providers`, and documented cross-agent usage in `docs/rlm_agents.md`; `skillctl validate skills/rlm-tools` passes; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.8 acceptance met with deterministic provider-choice reruns (`provider_choice_match=true`) plus adversarial probes (invalid policy schema rejected, disallowed explicit provider blocked at runtime); auto-advanced to 21.10 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.8 — added deterministic provider-policy selection (`primary` + ordered `fallback` + remaining `allowed`) with explicit-provider allowlist enforcement and deterministic provider-fallback behavior; tightened task schema checks (`primary in allowed`, fallback subset), added `tasks/rlm/provider_policy_example.json`, and verified repeat runs yield identical provider-choice sequences; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.6 acceptance met (`readwrite` -> `readonly` replay produced identical response hashes/final artifact), demo command rerun now works without `--fresh`, and adversarial probes confirmed expected failures for missing cache + subcall budget breach; auto-advanced to 21.8 and set status to NOT_STARTED.
- 2026-02-06: Issues triage — resolved ISSUE-014 by resetting run-scoped runtime/trace/output artifacts at `executor.py run` start, so non-fresh reruns no longer load finalized runtime state; reran readonly demo command twice successfully; status set back to IN_REVIEW.
- 2026-02-06: Review FAIL — reran 21.6 demo command exactly (`python3 skills/rlm-tools/executor.py run --task tasks/rlm/subcalls_example.json --cache readonly`) and found non-fresh reruns fail with `Runtime already finalized`; opened ISSUE-014 and moved status to IN_PROGRESS for targeted executor run-reset fix.
- 2026-02-06: Implemented 21.6 — added subcall-mode cache policy enforcement (`readwrite|readonly|off` with mandatory explicit selection), per-iteration/per-run subcall budgets, deterministic retry tracing, and `tools/rlm/replay.py`; verified readonly replay reproduces identical response hashes/final artifact and captured adversarial budget/cache probes; moved status to IN_REVIEW.
- 2026-02-06: Consolidation — pruned STATE work log to the most recent 10 entries and cleared stale 21.5 evidence; stage/checkpoint/status remain aligned at 21.6 / NOT_STARTED.
- 2026-02-06: Review PASS — 21.5 acceptance met with demo rerun plus adversarial probes (invalid provider selection rejects with exit 2, and credential-scrubbed run reports missing env vars); auto-advanced to 21.6 and set status to NOT_STARTED.
- 2026-02-06: Issues triage — loaded API keys from repo `.env` via `provider_check` dotenv support, switched health checks to provider listing endpoints for stable auth/connectivity validation, and resolved ISSUE-013; moved status to IN_REVIEW.
- 2026-02-06: Issues triage — per user direction, deferred Triton support from active Stage 21 scope; updated PLAN/STATE acceptance and blocker criteria to core providers (OpenAI/Anthropic/Google); status remains BLOCKED pending credentials.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- (Pending for checkpoint 21.11; add eval harness and reference-task evidence during implementation/review.)

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
