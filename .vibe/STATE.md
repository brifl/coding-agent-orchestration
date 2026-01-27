# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 1
- Checkpoint: 1.2
- Status: IN_PROGRESS  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Ship a usable Codex global skill MVP that can (a) recommend the next loop, and (b) print the corresponding prompt body deterministically.

## Deliverables (current checkpoint)

- `skills/codex/vibe-prompts/` includes:
  - `SKILL.md`
  - `scripts/vibe_get_prompt.py`
  - `resources/template_prompts.md` synced from `prompts/template_prompts.md`
- `skills/codex/vibe-loop/` includes:
  - `SKILL.md`
  - `scripts/vibe_next_and_print.py` that respects `CODEX_HOME` when set
- `tools/bootstrap.py install-skills --global --agent codex` is reliable + idempotent
- End-to-end demo works from a bootstrapped target repo

## Acceptance (current checkpoint)

- [ ] `python3 tools/bootstrap.py install-skills --global --agent codex` installs/updates into the correct global Codex skills folder (supports `CODEX_HOME`)
- [ ] From a bootstrapped target repo, `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root .` prints a valid loop prompt body to stdout
- [ ] `agentctl next --format json` returns a `recommended_prompt_id` that exists in the prompt catalog
- [ ] Scripts fail with clear errors when `.vibe/STATE.md` or prompt catalog is missing

## Work log (current session)

- 2026-01-27: Bootstrapped this repo as a “real” example repo; populated plan/state.

## Evidence

- (pending) Paste command output for:
  - `python3 tools/bootstrap.py install-skills --global --agent codex`
  - `python3 tools/agentctl.py status`
  - `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`

## Active issues

- [ ] ISSUE-001: `vibe_next_and_print.py` assumes `~/.codex/skills` instead of honoring `CODEX_HOME`
  - Severity: MINOR
  - Owner: agent
  - Notes: Patch script to use the same global dir resolution as `bootstrap.py`.

## Decisions

- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
