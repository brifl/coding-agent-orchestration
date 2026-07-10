# STATE

## Current focus

- Stage: 33
- Checkpoint: 33.2
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Make repeated installs converge framework-owned files by content while preserving project-owned work.

## Deliverables (current checkpoint)

- Deterministic manifest of managed skill files and digests
- Content-based managed refresh and removal of retired managed artifacts
- Preservation of unrelated project skills and substantive workflow files
- Legacy-upgrade and local-modification regression fixtures

## Acceptance (current checkpoint)

- Fresh install and legacy upgrade produce the same managed tree.
- Retired skills, caches, bytecode, and obsolete managed resources are removed.
- Project skills plus customized STATE/PLAN/AGENTS remain byte-identical.
- Locally changed managed files are repaired by content and reported clearly.

## Current truth

- Stage 33.1 completed self-first managed execution and provenance through `cc2c99c`.
- Repo and global installs now share one framework-source, manifest-driven reconciler.
- Managed skill directories converge by content, remove extras/retired artifacts, and roll back swaps if manifest commit fails.
- Ownership is by managed skill name; sibling project skills and substantive repository workflow files remain outside that boundary.

## Workflow state

- [x] STAGE_DESIGNED

## Work log (current session)

- 2026-07-10: Split the Stage 33 review gap into self-first execution (33.1) and convergent managed reinstall (33.2), then replaced the near-term roadmap with the audited correctness, context, and protocol work.
- 2026-07-10: Implemented self-first runtime/catalog resolution, fail-closed incomplete bundles, provenance digests/modes, and adversarial consumer fixtures.
- 2026-07-10: Review PASS; all checkpoint acceptance items have direct fixture evidence. Dispatcher smoke timeout is deferred to checkpoint 34.0.
- 2026-07-10: Advanced to 33.2 to replace incremental copying with a deterministic managed-tree reconciliation contract.
- 2026-07-10: Implemented deterministic manifests, staged digest validation, rollback-safe swaps, content repair reporting, and legacy/fresh convergence fixtures.
- 2026-07-10: Review PASS; managed ownership, convergence, cleanup, preservation, and rollback acceptance all have direct fixture evidence.

## Evidence

- Commit `cd62633`: manifest-driven reconciler, unified install paths, ownership docs, and upgrade/rollback fixtures.
- `18 passed` bootstrap suite; `44 passed` combined bootstrap/skill/prompt suites; Ruff and strict validation passed.
- Fresh/global/legacy manifests and managed trees match; future-mtime edits are repaired and reported; second reinstall is a no-op.
- Project skill plus customized AGENTS/STATE/PLAN stayed byte-identical; retired alias, caches, bytecode, and obsolete catalog were removed.
- Full workflow suite: `295 passed, 2 failed`; the same pre-existing feedback tests omit `_DecisionContext.recent_resolved_triage_for_current_state`.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
