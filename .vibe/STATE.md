# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 21A
- Checkpoint: 21A.1
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Build deterministic gap analysis that identifies missing or incomplete documentation and proposes edits or net-new docs.

## Deliverables (current checkpoint)

- `prompt.docs_gap_analysis` in `prompts/template_prompts.md`
- `tools/docs/doc_gap_report.py`
- `.vibe/docs/gap_report.json` with candidate actions (`edit_section|create_doc|create_wiki_page`)

## Acceptance (current checkpoint)

- Re-running on an unchanged repo snapshot produces stable finding IDs/severity ordering.
- Report includes actionable recommendations and supports net-new document proposals.

## Work log (current session)

- 2026-02-06: Review PASS — 21A.0 acceptance met by rerunning demo (`cat docs/documentation_severity_rubric.md`) plus adversarial probes validating required schema fields and full severity-example coverage; no blocking findings, so checkpoint auto-advanced to 21A.1 and status set to NOT_STARTED.
- 2026-02-06: Implemented 21A.0 — added `docs/continuous_documentation_overview.md` (scope + wiki migration rules + finding schema) and `docs/documentation_severity_rubric.md` (deterministic `MAJOR|MODERATE|MINOR` criteria with concrete examples); ran checkpoint demo command and prepared review evidence; moved status to IN_REVIEW.
- 2026-02-06: Consolidation — transitioned pointer from completed Stage 21 (`21.11/DONE`) to Stage 21A (`21A.0/NOT_STARTED`), refreshed objective/deliverables/acceptance to 21A.0, and pruned work log to latest 10 entries.
- 2026-02-06: Review PASS — 21.11 acceptance met (`eval_smoke` passed on `repo_comprehension`) with adversarial probes confirming expected failures for invalid task schema and readonly cache miss; no remaining same-stage checkpoints, so checkpoint set to DONE (plan exhausted for Stage 21).
- 2026-02-06: Implemented 21.11 — added reference tasks (`repo_comprehension`, `change_impact`, `doc_synthesis`) and `tools/rlm/eval_smoke.py`; smoke eval confirms one task exercises bundling + multi-iteration reasoning + subcalls + final artifact creation; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.10 acceptance met (`skillctl validate skills/rlm-tools` passed) with adversarial probes confirming validation failures for malformed skill manifest and invalid provider selection; auto-advanced to 21.11 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.10 — packaged `rlm-tools` skill with `skills/rlm-tools/SKILL.yaml`, added multi-command wrapper `skills/rlm-tools/rlm.py` for `rlm validate|bundle|run|step|resume|providers`, and documented cross-agent usage in `docs/rlm_agents.md`; `skillctl validate skills/rlm-tools` passes; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.8 acceptance met with deterministic provider-choice reruns (`provider_choice_match=true`) plus adversarial probes (invalid policy schema rejected, disallowed explicit provider blocked at runtime); auto-advanced to 21.10 and set status to NOT_STARTED.
- 2026-02-06: Implemented 21.8 — added deterministic provider-policy selection (`primary` + ordered `fallback` + remaining `allowed`) with explicit-provider allowlist enforcement and deterministic provider-fallback behavior; tightened task schema checks (`primary in allowed`, fallback subset), added `tasks/rlm/provider_policy_example.json`, and verified repeat runs yield identical provider-choice sequences; moved status to IN_REVIEW.
- 2026-02-06: Review PASS — 21.6 acceptance met (`readwrite` -> `readonly` replay produced identical response hashes/final artifact), demo command rerun now works without `--fresh`, and adversarial probes confirmed expected failures for missing cache + subcall budget breach; auto-advanced to 21.8 and set status to NOT_STARTED.

## Workflow state

- [ ] RUN_CONTEXT_CAPTURE

## Evidence

- (Pending for checkpoint 21A.1; 21A.0 review evidence captured in work-log entry.)

## Active issues

(None)

## Decisions

- 2026-02-06: Deferred Triton provider support from active Stage 21 backlog; implement later in a future stage/checkpoint.
