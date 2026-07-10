# CONTEXT

## Architecture

- `tools/agentctl.py` is the editable source dispatcher; bootstrap generates its installed helper bundle under `.codex/skills/vibe-loop/scripts/`.
- `prompts/template_prompts.md` is the editable source catalog; installed consumers receive one generated `vibe-prompts` resource.
- `tools/managed_install.py` owns deterministic managed-skill manifests, staged swaps, and rollback; sibling skill names remain project-owned.
- `.vibe/PLAN.md` is the near-term roadmap and `.vibe/STATE.md` is the active checkpoint cockpit.

## Key Decisions

- 2026-07-10: Installed wrappers must execute sibling managed tools/prompts; project overrides require explicit, provenance-visible configuration.
- 2026-07-10: Reinstall is content-addressed and convergent while preserving project-owned workflow files and skills.
- 2026-07-10: Pure dispatch and removal of automatic meta loops precede broader protocol/context simplification.

## Gotchas

- Current `status`/`next` can execute checkpoint demos during review; avoid using them as read-only probes until Stage 34.0.
- Successful `next --run-gates` currently runs configured gates twice; keep gate invocation counting in the 34.0 regression surface.
- `.vibe/` is ignored by pattern but selected workflow files are already tracked; explicit tracked-file staging may emit an ignore warning.

## Hot Files

- `tools/agentctl.py`
- `tests/workflow/test_agentctl_routing.py`
- `tests/workflow/test_agentctl.py`

## Agent Notes

- Active work is Stage 34 checkpoint 34.0: remove implicit verification from routing and deduplicate explicit gates.

## Stage Retrospective Notes

- Stage 33 added checkpoints 33.1/33.2 after real Tartu and Story Engine evidence contradicted the original completion surface; future packaging stages should begin with an adversarial existing-consumer upgrade fixture.
- Checkpoint 33.1 needed a review correction because “prefer sibling” still allowed silent stale-local fallback; encode ownership as fail-closed plus explicit provenance at design time.
- Both Stage 33 reviews were misrouted when passing verification exceeded the dispatcher’s hidden 30-second timeout; checkpoint 34.0 must make role queries subprocess-free and leave verification explicitly requested.
- Checkpoint 33.2 stayed bounded by defining ownership at the managed skill-name boundary; reuse explicit ownership boundaries when preserving project extensions during framework upgrades.
