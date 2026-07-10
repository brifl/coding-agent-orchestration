# STATE

## Current focus

- Stage: 33
- Checkpoint: 33.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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
- Current `_copy_file` trusts destination mtimes and `_sync_dir` never deletes extras.
- Existing consumer installs have no ownership manifest; retired `vibe-one-loop`, caches, bytecode, and stale managed files can survive reinstall.
- Global installation can resolve skill source from an older destination via `find_resource`; all install paths need one framework-source reconciler.

## Workflow state

- [x] STAGE_DESIGNED

## Work log (current session)

- 2026-07-10: Split the Stage 33 review gap into self-first execution (33.1) and convergent managed reinstall (33.2), then replaced the near-term roadmap with the audited correctness, context, and protocol work.
- 2026-07-10: Implemented self-first runtime/catalog resolution, fail-closed incomplete bundles, provenance digests/modes, and adversarial consumer fixtures.
- 2026-07-10: Review PASS; all checkpoint acceptance items have direct fixture evidence. Dispatcher smoke timeout is deferred to checkpoint 34.0.
- 2026-07-10: Advanced to 33.2 to replace incremental copying with a deterministic managed-tree reconciliation contract.

## Evidence

- Commits `654aa05` and `6926529`: managed runtime/catalog precedence, workflow-engine packaging, provenance, and fail-closed overrides.
- `45 passed` across wrapper/bootstrap/prompt/workflow suites; Ruff and strict validation passed.
- Adversarial fixture honored project workflow YAML while stale target Python/catalog markers remained untouched; missing managed runtime/catalog failed closed.
- Full workflow baseline: `288 passed, 2 failed`; both failures predate this diff and omit an existing `_DecisionContext` field in feedback tests.
- Review note: dispatcher timed out the passing 48-second bootstrap/skill suite at its hard-coded 30-second smoke limit; checkpoint 34.0 removes that implicit gate.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
