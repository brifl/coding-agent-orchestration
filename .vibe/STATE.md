# STATE

## Current focus

- Stage: 33
- Checkpoint: 33.1
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Ensure installed Vibe entrypoints execute their sibling managed runtime and prompt catalog instead of stale target-repo framework copies.

## Deliverables (current checkpoint)

- Self-first installed wrapper/runtime/catalog resolution
- No implicit target-repo workflow-engine shadowing
- Compact runtime and prompt provenance in dispatcher output
- Regression coverage for stale consumer copies and source mode

## Acceptance (current checkpoint)

- Stale target tools/catalogs do not shadow an installed bundle.
- Source-repo tools/prompts remain canonical during source development.
- Dispatcher decisions identify active runtime/catalog path, digest, and mode.
- Focused wrapper, prompt, selector, and strict-validation checks pass.

## Current truth

- Stage 33.0 delivered the fresh install and repository-aware backlog path through `ed17740`.
- Installed wrappers now execute only their sibling runtime/catalog by default and label explicit overrides in decision provenance.
- The managed helper bundle now includes `workflow_engine.py`, preserving project YAML behavior without importing target Python.
- Reinstall convergence remains separate checkpoint 33.2 work after resolution precedence is corrected.

## Workflow state

- [x] STAGE_DESIGNED

## Work log (current session)

- 2026-07-10: Split the Stage 33 review gap into self-first execution (33.1) and convergent managed reinstall (33.2), then replaced the near-term roadmap with the audited correctness, context, and protocol work.
- 2026-07-10: Implemented self-first runtime/catalog resolution, fail-closed incomplete bundles, provenance digests/modes, and adversarial consumer fixtures.
- 2026-07-10: Review PASS; all checkpoint acceptance items have direct fixture evidence. Dispatcher smoke timeout is deferred to checkpoint 34.0.

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
