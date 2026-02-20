# Documentation Index

This index maps all documentation surfaces in this repository.

## Workflow and Orchestration

- `README.md` - repository overview, mental model, and workflow entry point.
- `docs/concepts.md` - continuous mode semantics, skill sets, checkpoint DAG, manual fallback.
- `docs/conventions.md` - coding and doc conventions used across the repo.
- `docs/workflow_schema.md` - schema for workflow YAML definitions.
- `docs/workflow_improvements.md` - Stage 22 dispatcher improvements: design/retrospective/maintenance loops, smoke gate, review pass C.
- `docs/plan_authoring.md` - how to write and maintain PLAN.md checkpoints.
- `docs/stage_ordering.md` - stage numbering and ordering rules.
- `docs/checkpoint_templates.md` - available checkpoint templates and usage.
- `docs/checkpoint_dependencies.md` - dependency DAG syntax, commands, and examples.
- `docs/quality_gates.md` - configuring and running deterministic quality gates.
- `docs/feedback_channel.md` - how to submit feedback and issues.

## Skills

- `docs/skill_reference.md` - navigation index for all skill topic docs.
- `docs/skill_manifest.md` - SKILL.md front matter format and required fields.
- `docs/skill_sets.md` - named skill bundle schema and inheritance.
- `docs/skill_sources.md` - git/github/local skill sources and trust levels.
- `docs/skill_lifecycle.md` - versioning, deprecation, governance, and compatibility policy.
- `docs/base_skills.md` - base skill surface and agent compatibility matrix.
- `docs/agent_skill_packs.md` - agent-specific invocation patterns for all supported agents.
- `docs/agent_capabilities.md` - capability matrix (file editing, command execution, continuous mode) per agent.

## Schemas and Configuration

- `docs/config_schema.md` - `.vibe/config.json` schema reference.
- `docs/context_schema.md` - `.vibe/CONTEXT.md` schema reference.
- `docs/resource_model.md` - resource model for workflow state files.

## RLM (Recursive Language Model)

- `docs/rlm_overview.md` - what RLM is, when to use it, execution modes.
- `docs/rlm_glossary.md` - RLM terminology and definitions.
- `docs/rlm_agents.md` - RLM agent roles and responsibilities.
- `docs/rlm_task_schema.md` - task schema for RLM executions.

## Continuous Documentation Workflow

- `docs/continuous_documentation_overview.md` - documentation workflow scope, phases, and finding schema.
- `docs/documentation_severity_rubric.md` - deterministic MAJOR/MODERATE/MINOR classification.

## Embedded Guides and Wiki Export

- `docs/embedded_guides.md` - index of user-facing guide material embedded in source files.
- `docs/embedded-guides/index.md` - per-source embedded guide mapping.
- `docs/wiki-export/config_schema.md` - wiki-exported config schema page.
- `docs/wiki-export/map.json` - wiki export mapping manifest.

## Refactoring

- `docs/refactoring-guide.md` - project-local refactoring smell table, concepts, and strategies.

## Maintenance Note

Update this index whenever new top-level docs are added to `docs/`.
