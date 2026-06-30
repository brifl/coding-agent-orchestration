# Skill Lifecycle Policy

Skills are maintained product surfaces, not append-only compatibility layers.

## Principles

1. **Small stable surface:** Keep one clear default path and remove redundant entrypoints.
2. **Evidence-based compatibility:** Preserve a compatibility path only for a demonstrated consumer or explicit requirement.
3. **Ownership over wrappers:** Improve the nearest existing skill when that is clearer than adding a wrapper, flag, or extension.
4. **Bounded migration cost:** Update in-repo consumers, tests, and docs atomically. Write migration guidance only when external users actually need it.

## Skill categories

### Maintained core

The core surface is defined in `docs/base_skills.md`. Core skills may evolve when
the change fixes behavior or reduces complexity.

Change rules:

- Prefer replacing or removing a weak interface over retaining old and new paths.
- Add a flag or command only for a real recurring variation.
- Protect stable behavior with focused tests; do not freeze accidental implementation details.
- Test affected supported agents in proportion to the change.

### Extension skills

An extension skill is appropriate only when it owns a distinct workflow that the
core surface should not absorb. Use semantic versions when external consumers need
release coordination:

- **MAJOR:** breaking interface or behavior change
- **MINOR:** new capability or bounded interface simplification
- **PATCH:** compatible bug fix

Skill locations:

- `.codex/skills/<skill-name>/` — repository-local source
- `$CODEX_HOME/skills/<skill-name>/` — Codex user install
- `$AGENT_HOME/skills/<skill-name>/` — Claude Code user install

## Adding a skill

Add a skill only when all of these are true:

- It solves a demonstrated repeated problem.
- The nearest core skill would become less coherent by absorbing it.
- Its name and description define one clear trigger boundary.
- It has a concrete demo or regression check that reduces future debugging time.
- It does not introduce a parallel route to behavior already owned elsewhere.

Review the resulting surface, not just the new directory:

- Remove displaced commands, docs, flags, and compatibility branches.
- Update the relevant skill set and agent-facing docs.
- Verify supported agents that actually consume the skill.

## Changing or removing a skill

Before preserving an old path, identify its consumer. If no consumer exists,
remove it with the replacement change.

When consumers do exist:

1. Define the replacement and why it is simpler.
2. Update known in-repo consumers in the same change.
3. Add a time-bounded migration note only for external consumers.
4. Remove the old path when the stated migration window ends.

A core skill may be consolidated or removed when another supported path fully
owns its behavior. Removal requires scoped review and regression verification,
not an indefinite deprecation ceremony.

## Metadata

Codex skill frontmatter contains `name` and `description`. Put UI metadata in
`agents/openai.yaml`; keep version coordination in release/skill-set metadata
when it is genuinely needed.
