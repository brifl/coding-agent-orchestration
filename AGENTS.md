# AGENTS.md — Execution Contract (Repo Baseline)

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Purpose

This file defines the working contract for coding agents and humans collaborating in this repository.

- This repo uses **project-local workflow files** stored under `.vibe/`.
- The agent must follow the **precedence order** and **stop conditions** below.
- This baseline is intended to be copied into target repos and may drift per project.

## Authoritative files and precedence

When instructions conflict, follow this order:

1. **User instructions in the current chat**
2. **This file: `AGENTS.md`**
3. **`.vibe/STATE.md`** (current truth: what we are doing now)
4. **`.vibe/PLAN.md`** (checkpoint backlog and acceptance criteria)
5. **`.vibe/HISTORY.md`** (non-authoritative rollups, context only)
6. Repository source code and tests
7. Anything else (including assumptions)

## Required behavior

### Read order at the start of a session

At the start of any new session (or when context is unclear), the agent must:
1. Read `AGENTS.md`
2. Read `.vibe/STATE.md`
3. Read `.vibe/PLAN.md`
4. Optionally read `.vibe/HISTORY.md` if needed

### Work granularity

- Do **one coherent unit of work** at a time (typically one checkpoint step).
- Prefer **small, reviewable diffs**.
- When ambiguity affects correctness, ask **1–2 clarifying questions max**, then stop.

### Output discipline

- Keep outputs concise and structured.
- Prefer checklists, acceptance evidence, and exact commands over narrative.

## Workflow model

### Checkpoint shape (required fields)

Each checkpoint should define:
- **Objective** (1 sentence)
- **Deliverables** (concrete files/modules/behaviors)
- **Acceptance** (verifiable conditions)
- **Demo commands** (exact local commands)
- **Evidence** (what to paste/link back into `.vibe/STATE.md`)

### Role loops

The agent should operate in one of these loops, as appropriate to `.vibe/STATE.md`:
- **Stage Design**: refine checkpoints in `.vibe/PLAN.md`
- **Implementation**: implement the active checkpoint
- **Review**: verify acceptance; write evidence; identify issues
- **Triage**: classify and resolve issues; adjust plan/state accordingly
- **Consolidation**: move completed content into history; reduce clutter
- **Process Improvement**: improve this orchestration system with minimal churn

## Stop conditions (hard)

Stop and ask for input (as issue) if any of the following occurs:
- Missing required information to meet acceptance criteria
- Conflicting instructions between authoritative sources
- A decision point that changes scope, architecture, or dependencies materially
- The work would require secrets, credentials, destructive actions, or external side effects
- Tests/builds fail and the failure mode isn’t clearly attributable to the change

## Issue handling (lightweight)

- Track current issues in `.vibe/STATE.md` (active list only).
- Keep `.vibe/HISTORY.md` for resolved issues or postmortems.
- Don’t invent new “issue taxonomies” unless the repo explicitly needs it.

## Version control policy (required)

- Work on a feature branch unless explicitly told otherwise.
- Commit as you go:
  - Create at least one commit per completed checkpoint.
  - Additional commits are allowed for discrete sub-steps (e.g., “fix parser”, “tighten prompts”).
- Commit messages:
  - Use imperative mood.
  - Prefix with the checkpoint ID, e.g. "1.2: Fix prompt_catalog fence parsing".
- Do not commit broken builds/tests unless the checkpoint explicitly allows it.
- After setting Status to IN_REVIEW, ensure the branch contains the commits needed to satisfy the checkpoint.

## Definitions

- **Authoritative**: must be followed unless overridden by a higher-precedence source.
- **Checkpoint**: a bounded unit with objective/deliverables/acceptance/demo/evidence.
