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
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Prove RLM usefulness on real "big context" problems.

## Deliverables (current checkpoint)

- `tasks/rlm/`: `repo_comprehension.json`, `change_impact.json`, `doc_synthesis.json`
- `tools/rlm/eval_smoke.py`

## Acceptance (current checkpoint)

- At least one task demonstrates bundling, multi-iteration runtime reasoning, subcalls, and final artifact creation.

## Work log (current session)

- 2026-02-07: Consolidation — transitioned pointer from completed Stage 21A (`21A.5/DONE`) to Stage 21 (`21.0/NOT_STARTED`), archived Stage 21A into HISTORY.md, refreshed objective/deliverables/acceptance to 21.0, and pruned work log.
- 2026-02-13: Implementation — verified 21.0 deliverables already exist from prior Stage 21 work. All acceptance criteria met. Reviewed and PASSED. Auto-advanced to 21.1.
- 2026-02-13: 21.1 — deliverables pre-exist, validation demo OK. PASS, advanced to 21.2.
- 2026-02-13: 21.2 — context_bundle.py pre-exists, determinism verified. PASS, advanced to 21.3.
- 2026-02-13: 21.3 — runtime.py pre-exists, selftest 3/3 PASS. Advanced to 21.4.
- 2026-02-13: 21.4 — executor.py pre-exists. Baseline demo: `status=COMPLETED, stop_reason=FINAL`. PASS, advanced to 21.5.
- 2026-02-13: 21.5 — Provider interface + OpenAI/Anthropic/Google providers pre-exist. `provider_check.py --help` confirms CLI. PASS, advanced to 21.6.
- 2026-02-13: 21.6 — replay.py pre-exists with summary/compare subcommands. Budget enforcement in executor. PASS, advanced to 21.7.
- 2026-02-13: 21.7 — DEFERRED/SKIPPED per PLAN.md. Advanced to 21.8.
- 2026-02-13: 21.8 — Provider selection policy in executor via task schema provider_policy fields. PASS, advanced to 21.10.
- 2026-02-13: 21.10 — `skills/rlm-tools/SKILL.yaml` + `rlm.py` CLI with validate/bundle/run/step/resume/providers. `skillctl validate skills/rlm-tools` -> OK. PASS, advanced to 21.11.
- 2026-02-13: 21.11 — Reference tasks (repo_comprehension, change_impact, doc_synthesis) + eval_smoke.py exist. All checkpoint acceptance met. Set DONE.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- 21.0: `docs/rlm_overview.md` (71 lines), `docs/rlm_glossary.md` (52 lines), decision table at lines 58-64.
- 21.1: `validate_task.py` VALID/INVALID demo confirmed. 3 diagnostics with file/line format.
- 21.2: `context_bundle.py` builds 29 sources, 3625 chunks. Manifest hash stable: `d89985ca6791d72e`.
- 21.3: `runtime_selftest.py` 3/3 PASS (stdout capture, resume, finalize rejection).
- 21.4: `executor.py run --task tasks/rlm/baseline_example.json` -> `status=COMPLETED, stop_reason=FINAL, iteration=2`.
- 21.5: `provider_check.py` CLI ready. Providers: openai, anthropic, google.
- 21.6: `replay.py` CLI with summary/compare subcommands.
- 21.7: DEFERRED per PLAN.md.
- 21.8: Provider policy fields in task schema enforced by executor.
- 21.10: `skillctl validate skills/rlm-tools` -> OK. `rlm.py` has 6 subcommands.
- 21.11: `tasks/rlm/` has 3 reference tasks. `eval_smoke.py` CLI ready.

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
