# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 11
- Checkpoint: 11.2
- Status: BLOCKED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Allow templates to be inserted directly into PLAN.md.

## Deliverables (current checkpoint)

- `agentctl add-checkpoint --template <name> --params ...` command
- Automatic stage detection (add to current stage or create new)
- Validation that inserted checkpoint follows schema

## Acceptance (current checkpoint)

- Templates can be added without manual editing
- Inserted checkpoints pass `agentctl validate`

## Work log (current session)

- 2026-01-29: Resolved ISSUE-002 (dispatcher mismatch) by preferring repo-local tools in vibe_next_and_print.
- 2026-01-29: Reviewed 11.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 11.2 - Added agentctl add-checkpoint command and stage insertion logic.
- 2026-01-29: Advanced to checkpoint 11.2.
- 2026-01-29: Reviewed 11.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 11.1 - Added core checkpoint templates and instantiate command.
- 2026-01-29: Advanced to checkpoint 11.1.
- 2026-01-29: Reviewed 11.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 11.0 - Added checkpoint template schema, catalog tool, and example template.
- 2026-01-29: Consolidation: archived Stage 10 to HISTORY, pruned PLAN/STATE for Stage 11.
- 2026-01-29: Reviewed 10.2 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.2 - Added context-aware bootstrap reads and status output.
- 2026-01-29: Reviewed 10.1 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.1 - Added prompt.context_capture and consolidation guidance.
- 2026-01-29: Reviewed 10.0 - PASS. Deliverables and acceptance criteria met.
- 2026-01-29: Implemented 10.0 - Added context schema and example CONTEXT.md with persistent vs ephemeral guidance.

## Evidence

- `python tools/agentctl.py --repo-root <temp> add-checkpoint --template add-feature --name "user-auth"`
  - Inserts a templated checkpoint and reports the new id (demo run on a temp repo copy).
- `python tools/agentctl.py --repo-root <temp> validate`
  - Inserted checkpoint passes validation checks.
- `python /home/brifl/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`
  - Decision JSON now matches repo agentctl (no consolidation mismatch).

## Active issues

- [BLOCKER] ISSUE-002: Bootstrap `--overwrite` does not reliably replace AGENTS.md and VIBE.md
  - Severity: BLOCKER
  - Owner: agent
  - Notes:
    - `bootstrap.py --overwrite` should deterministically overwrite repo-canonical docs (`AGENTS.md`, `VIBE.md`) but currently skips or partially updates.
    - Need: define canonical source path(s) for these docs
    - implement true overwrite (byte-for-byte or explicitly defined transform)
    - log what was overwritten
    - add a regression test that fails when overwrite does not occur

- [BLOCKER] ISSUE-003: Duplicate `template_prompts.md` sources cause drift; enforce single canonical catalog in `prompts/`
  - Severity: BLOCKER
  - Owner: agent
  - Notes:
    - There should be exactly one maintained prompt catalog (canonical) under `prompts/` and all tools/skills must resolve/read that copy only
    - Need: remove/stop-reading the non-canonical copy
    - update resolver/installer/skills to consume `prompts/template_prompts.md` exclusively
    - add validation that fails if a second catalog is present or referenced

- [BLOCKER] ISSUE-004: Replace Kimi with Kilo in all agent references and parity groupings
  - Severity: BLOCKER
  - Owner: agent|human
  - Notes:
    - Kilo was intended to supersede/encapsulate Kimi
    - Need: remove Kimi references across docs/config/bootstrap/verification notes
    - ensure Kilo appears wherever Codex/Copilot/Claude/Gemini are enumerated
    - make capability/parity language consistent so the support matrix is unambiguous

## Decisions

- 2026-01-28: Skipped checkpoints 7.1/7.2 (Kimi/IQuest verification) — no access to these agents; generic bootstrap is sufficient.
- 2026-01-28: Stage pointer in STATE.md must match the stage containing the checkpoint in PLAN.md. agentctl.py now validates this.
- 2026-01-28: Evidence should be cleared when advancing to a new stage (consolidation prompt updated).
- 2026-01-28: All CLI agents (Claude Code, Gemini Code, Copilot) now documented as having full capabilities.
- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
