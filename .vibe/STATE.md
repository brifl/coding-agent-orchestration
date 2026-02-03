# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 14
- Checkpoint: 14.2
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Enable bootstrapping with a skill set reference.

## Deliverables (current checkpoint)

- `bootstrap.py` enhancement: `--skillset <name>` flag
- Auto-install all skills in set
- Record set reference in `.vibe/config.json`

## Acceptance (current checkpoint)

- `bootstrap.py init-repo . --skillset vibe-core` installs all vibe-core skills
- Config records which set was used

## Work log (current session)
- 2026-02-03: Review PASS — 14.2 acceptance met; status set to DONE.
- 2026-02-03: Added skillset auto-install in bootstrap; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 14.1 → 14.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 14.1 acceptance met; status set to DONE.
- 2026-02-03: Implemented resolve-set in skillctl; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 13; advanced to checkpoint 14.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 13.2 acceptance met; status set to DONE.
- 2026-02-03: Implemented skillctl CLI and bootstrap integration; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 13.1 → 13.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 13.1 acceptance met; status set to DONE.
- 2026-02-03: Implemented skill registry CLI and parsing; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 13.0 → 13.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 13.0 acceptance met; status set to DONE.
- 2026-02-03: Added skill manifest schema and sample; ran demo command; status set to IN_REVIEW.
- 2026-02-03: JIT injected Stage 13 before Stage 14; advanced to checkpoint 13.0; status set to NOT_STARTED.

## Evidence

- `python3 tools/bootstrap.py init-repo /tmp/test --skillset vibe-core` installs set skills into `/tmp/test/.vibe/skills`.
- `/tmp/test/.vibe/config.json` includes `"skillset": {"name": "vibe-core"}`.

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
