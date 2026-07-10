# CONTEXT

## Architecture

- `tools/agentctl.py` is the editable source dispatcher; bootstrap generates its installed helper bundle under `.codex/skills/vibe-loop/scripts/`.
- `prompts/template_prompts.md` is the editable source catalog; installed consumers receive one generated `vibe-prompts` resource.
- `.vibe/PLAN.md` is the near-term roadmap and `.vibe/STATE.md` is the active checkpoint cockpit.

## Key Decisions

- 2026-07-10: Installed wrappers must execute sibling managed tools/prompts; project overrides require explicit, provenance-visible configuration.
- 2026-07-10: Reinstall will become content-addressed and convergent while preserving project-owned workflow files and skills.
- 2026-07-10: Pure dispatch and removal of automatic meta loops precede broader protocol/context simplification.

## Gotchas

- Current installed wrappers prefer target-repo `tools/`, and prompt resolution prefers target `prompts/template_prompts.md`; stale consumer copies can shadow current installs.
- `_sync_dir` skips newer-mtime destinations and never deletes extras, so current reinstall is not convergent.
- Current `status`/`next` can execute checkpoint demos during review; avoid using them as read-only probes until Stage 34.0.
- `.vibe/` is ignored by pattern but selected workflow files are already tracked; explicit tracked-file staging may emit an ignore warning.

## Hot Files

- `.codex/skills/vibe-run/scripts/vibe_run.py`
- `.codex/skills/vibe-loop/scripts/vibe_next_and_print.py`
- `tools/agentctl.py`
- `tools/prompt_catalog_paths.py`
- `tools/bootstrap.py`
- `tests/workflow/test_vibe_run.py`
- `tests/workflow/test_bootstrap.py`

## Agent Notes

- Active work is Stage 33 checkpoint 33.1: self-first installed execution and provenance.
- Checkpoint 33.2 follows with manifest-based managed reinstall convergence.
