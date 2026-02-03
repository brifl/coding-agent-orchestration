# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 14
- Checkpoint: 14.1
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Define how skill sets are structured and stored.

## Deliverables (current checkpoint)

- `docs/skill_sets.md` — schema and usage documentation
- `skillsets/` directory for set definitions
- Set format: name, description, skills list, version constraints

## Acceptance (current checkpoint)

- Sets can reference skills by name with optional version pins
- Sets can extend other sets (inheritance)

## Work log (current session)
- 2026-02-02: Advanced checkpoint 14.0 → 14.1; status set to NOT_STARTED.
- 2026-02-02: Review PASS — 14.0 acceptance met; status set to DONE.
- 2026-02-02: Added skill set docs and examples; ran demo command; status set to IN_REVIEW.
- 2026-02-02: Consolidated Stage 13A; advanced stage pointer to 14.0; cleared evidence.
- 2026-02-02: Review PASS — 13A.2 acceptance met; status set to DONE.
- 2026-02-02: Updated stage ordering docs with (SKIP) semantics; ran demo command; status set to IN_REVIEW.
- 2026-02-02: Advanced checkpoint 13A.1 → 13A.2; status set to NOT_STARTED.
- 2026-02-02: Review PASS — 13A.1 acceptance met; status set to DONE.
- 2026-02-02: Re-ran pytest with --capture=sys; tests pass; status set to IN_REVIEW.
- 2026-02-02: Implemented 13A.1 tests; pytest -v capture fails (FileNotFoundError); status set to BLOCKED.
- 2026-02-02: Advanced checkpoint 13A.0 → 13A.1; status set to NOT_STARTED.
- 2026-02-02: Review PASS — 13A.0 acceptance met; status set to DONE.
- 2026-02-02: Added consolidation prompt rule to preserve (SKIP) items; ran demo commands + skip behavior check; status set to IN_REVIEW.

## Evidence

- Added `docs/skill_sets.md` describing schema, version pins, and inheritance.
- Added `skillsets/` with `vibe-base.yaml` and `vibe-core.yaml`.
- `cat skillsets/vibe-core.yaml` output:\n  `name: vibe-core`\n  `description: Default bundle for repo workflows.`\n  `extends:`\n  `  - vibe-base`\n  `skills:`\n  `  - name: vibe-review-pass`\n  `    version: \">=1.0.0\"`

## Active issues

- [MAJOR] ISSUE-005: Agents not working from current branch
  - Severity: MAJOR
  - Owner: agent
  - Notes: Agents running vibe-loop or other skills should not create branches. They should always work from the current branch and commit to the current branch. This is documented in prompts, but it is not followed consistently. This creates drift, branch clutter, and merge issues when these branches are created.

## Decisions

(No decisions)
