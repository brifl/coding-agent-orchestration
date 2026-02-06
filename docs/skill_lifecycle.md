# Skill Lifecycle and Compatibility Policy

This document defines how skills are added, versioned, and deprecated in the Vibe workflow system.

## Core Principles

1. **Stability over features** — Base skills must remain stable; new features go in extension skills
2. **No breaking changes to base skills** — Once a skill is in `docs/base_skills.md`, its interface is frozen
3. **Explicit compatibility** — Skills should note which agents they support when relevant
4. **Graceful degradation** — Skills should work in reduced-capability environments when possible

## Skill Categories

### Base Skills (frozen)

These skills are defined in `docs/base_skills.md` and are **immutable**:

| Skill | Purpose | Breaking changes allowed? |
|-------|---------|---------------------------|
| vibe-prompts | Prompt catalog access | No |
| vibe-loop | Single loop execution | No |
| vibe-one-loop | Single loop alias for compatibility | No |
| vibe-run | Continuous execution | No |
| continuous-refactor | Continuous refactor workflow execution | No |
| continuous-test-generation | Continuous test workflow execution | No |
| agentctl | Dispatcher and validation | No (interface only) |

**What "no breaking changes" means:**
- Existing commands/flags must continue to work
- Output formats must remain backward-compatible
- New features are additive only (new flags, new commands)
- Bug fixes are allowed even if they change behavior

### Extension Skills (versioned)

Skills not in the base set follow semantic versioning:

- **MAJOR** — Breaking changes (rename, remove, change interface)
- **MINOR** — New features, backward-compatible
- **PATCH** — Bug fixes only

Extension skills live in:
- `.codex/skills/<skill-name>/` — Repo-local Codex skills
- `~/.codex/skills/<skill-name>/` or `$CODEX_HOME/skills/<skill-name>/` — User/global installs

## Adding a New Skill

### Go/No-Go Criteria

Before adding a skill, it must pass ALL of these criteria:

| Criterion | Requirement | Verified by |
|-----------|-------------|-------------|
| **Need** | Solves a real problem not covered by base skills | Review discussion |
| **Scope** | Does one thing well; not a catch-all | Code review |
| **Compatibility** | Works with at least 2 supported agents | Test transcript |
| **Documentation** | Has SKILL.md with usage instructions | File check |
| **No base conflicts** | Does not override or shadow base skill names | Name check |
| **Testable** | Has demo commands that verify it works | Manual test |

### Review Checklist

Use this checklist when reviewing a new skill PR:

```markdown
## New Skill Review Checklist

### Metadata
- [ ] SKILL.md exists with name and description
- [ ] Skill name does not conflict with base skills
- [ ] Agent compatibility is documented

### Functionality
- [ ] Does one thing well (single responsibility)
- [ ] Does not duplicate base skill functionality
- [ ] Works without requiring base skill modifications

### Compatibility
- [ ] Tested with Codex
- [ ] Tested with at least one other agent (Claude/Gemini/Copilot)
- [ ] Fails gracefully on unsupported agents

### Documentation
- [ ] Usage instructions are clear
- [ ] Demo commands are provided
- [ ] Error cases are documented

### Integration
- [ ] Does not modify files outside skill directory
- [ ] Does not require changes to agentctl.py
- [ ] Does not require changes to template_prompts.md
```

## Deprecating a Skill

Extension skills may be deprecated following this process:

1. **Announce** — Add deprecation notice to SKILL.md
2. **Grace period** — Minimum 2 releases or 30 days
3. **Remove** — Delete skill directory and update docs

Base skills **cannot be deprecated** — they can only be extended.

## Versioning Scheme

### Skill Version Format

```
<skill-name>@<major>.<minor>.<patch>
```

Example: `my-validator@1.2.0`

### Version Storage

Version is declared in SKILL.md frontmatter:

```yaml
---
name: my-validator
version: 1.2.0
description: Validates widget configurations
---
```

### Compatibility Matrix Updates

When adding or modifying skills, update:
- `docs/agent_capabilities.md` — If agent support changes
- `docs/base_skills.md` — Only if adding to base set (requires RFC)
- `docs/agent_skill_packs.md` — If agent-specific instructions change

## Repo-Local Skills

Repos can override global skills by placing them in `.codex/skills/<skill-name>/`.

**Precedence order:**
1. `.codex/skills/<skill-name>/` (repo-local, highest priority)
2. `$CODEX_HOME/skills/<skill-name>/` (global user, defaults to `~/.codex/skills`)
3. `/etc/codex/skills/<skill-name>/` (system)

**Rules for repo-local skills:**
- May shadow global skills (use same name to override)
- Must be self-contained (no external dependencies)
- Are not subject to base skill freeze (repo can customize anything)
- Should be documented in repo README

## Breaking Change Process (Extension Skills Only)

If an extension skill must make a breaking change:

1. **Bump MAJOR version** — `1.x.x` → `2.0.0`
2. **Document migration** — Add MIGRATION.md to skill directory
3. **Announce in changelog** — Note breaking changes prominently
4. **Update dependent repos** — Coordinate with known users

## Exceptions

The following changes are NOT considered breaking:

- Fixing bugs that caused incorrect behavior
- Adding new optional parameters with sensible defaults
- Improving error messages
- Performance improvements
- Adding new output fields (existing fields unchanged)

## Governance

- **Base skill changes** — Require RFC and multi-agent verification
- **Extension skill additions** — Require review checklist completion
- **Deprecations** — Require 30-day notice minimum
- **Emergency fixes** — May bypass process for security issues
