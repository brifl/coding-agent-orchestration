# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 16
- Checkpoint: 16.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define how external skill sources are specified and trusted.

## Deliverables (current checkpoint)

- `docs/skill_sources.md` — source configuration and trust model
- Source format: git URL, branch/tag, subdirectory path
- Trust levels: verified, community, untrusted

## Acceptance (current checkpoint)

- Sources can be GitHub repos, git URLs, or local paths
- Trust level affects installation warnings

## Work log (current session)
- 2026-02-03: Advanced checkpoint 16.1 → 16.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 16.1 acceptance met; status set to DONE.
- 2026-02-03: Ran subscription demo for 16.1; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 16.0 → 16.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 16.0 acceptance met; status set to DONE.
- 2026-02-03: Verified skill source docs for 16.0; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 15; advanced to checkpoint 16.0; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 15.2 acceptance met; status set to DONE.
- 2026-02-03: Implemented sync + upgrade flow; ran demo commands; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 15.1 → 15.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 15.1 acceptance met; status set to DONE.
- 2026-02-03: Implemented skill subscription + lock file; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 15.0 → 15.1; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 15.0 acceptance met; status set to DONE.
- 2026-02-03: Added skill source docs; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Consolidated Stage 14; advanced to checkpoint 15.0; status set to NOT_STARTED.

## Evidence

- `python3 tools/skillctl.py subscribe https://github.com/anthropics/skills claude-memory --pin v1.0.0` updates `.vibe/skill-lock.json`.

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
