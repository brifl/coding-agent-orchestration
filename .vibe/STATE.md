# STATE

## Current focus

- Stage: 33
- Checkpoint: 33.1
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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
- Real consumer evidence showed Tartu still executes older copied tools/prompts because installed wrappers prefer target-repo files.
- Tartu's local `agentctl.py` contains no project-only behavior; its useful fixes already exist upstream.
- Reinstall convergence remains separate checkpoint 33.2 work after resolution precedence is corrected.

## Workflow state

- [x] STAGE_DESIGNED

## Work log (current session)

- 2026-07-10: Split the Stage 33 review gap into self-first execution (33.1) and convergent managed reinstall (33.2), then replaced the near-term roadmap with the audited correctness, context, and protocol work.

## Evidence

- Tartu override audit: local `agentctl.py` is an older upstream snapshot; local prompt-path delta only retains removed `vibe-one-loop`.
- Runtime audit: installed wrappers prefer target `tools/`, prompt lookup prefers target `prompts/`, and `_sync_dir` neither deletes extras nor refreshes newer-mtime destinations.
- Token/lifecycle audit: dispatch runs hidden verification; automatic maintenance cannot close its flag contract; current CONTEXT is stale.

## Active issues

- None.

## Decisions

- 2026-07-10: Treat generated runtime and prompt assets as framework-managed; require explicit, provenance-visible project overrides.
- 2026-07-10: Prefer deletion of automatic meta loops and duplicated protocol over repairing their existing ceremony.
