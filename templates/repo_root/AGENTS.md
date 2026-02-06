# AGENTS.md — Execution Contract (Repo Baseline)

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
1. Read `AGENTS.md` (optional if already read this session)
2. Read `.vibe/STATE.md`
3. Read `.vibe/PLAN.md`
4. Optionally read `.vibe/HISTORY.md` if needed

### Work granularity

- Do **one coherent unit of work** at a time (typically one checkpoint step).
- Prefer **small, reviewable diffs**.
- When ambiguity affects correctness, ask **1–2 clarifying questions max** as issues in `.vibe/STATE.md`, then stop.

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

The agent should operate in one of these loops, as appropriate to `.vibe/STATE.md`.
This registry is canonical and must stay aligned with `tools/agentctl.py` role mapping.

| Role key | Loop name | Intent | Typical transition |
| --- | --- | --- | --- |
| `design` | Stage Design | refine checkpoints in `.vibe/PLAN.md` | unclear/invalid status -> `design` |
| `implement` | Implementation | implement active checkpoint deliverables | `NOT_STARTED`/`IN_PROGRESS` -> `implement` |
| `review` | Review | verify acceptance and decide PASS/FAIL | `IN_REVIEW` -> `review` |
| `issues_triage` | Triage | resolve/clarify active issues with minimal scope | issues or blocked state -> `issues_triage` |
| `advance` | Advance | move pointer to next checkpoint (fallback/manual) | `DONE` + same-stage next checkpoint |
| `consolidation` | Consolidation | archive completed stage and sync docs/state | `DONE` + stage transition |
| `context_capture` | Context Capture | refresh `.vibe/CONTEXT.md` and clear context flags | post-consolidation or stale context |
| `improvements` | Process Improvement | improve orchestration system itself | workflow debt or explicit flag |
| `stop` | Stop | end loop when plan is exhausted | no remaining active checkpoints |

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

### Required active issue schema

Each active issue in `.vibe/STATE.md` should use this format:

```
- [ ] ISSUE-123: Short title
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: <what must be true to proceed>
  - Evidence Needed: <command/output/link proving resolution>
  - Notes: <optional context>
```

- `ISSUE-<id>` must be stable across updates.
- `Impact` drives triage priority.
- `Status` reflects current resolution state.
- `Unblock Condition` and `Evidence Needed` should be concrete and testable.
- `python tools/agentctl.py --repo-root . validate --strict` should fail if required fields are missing.

## Version control policy (required)

### Branch discipline (hard rule)

- Work on the **current branch**.
- **Do not create, switch, or delete branches** unless the user explicitly instructs you to.
  - Forbidden without explicit instruction: `git checkout -b`, `git switch -c`, `git switch <branch>`, `git checkout <branch>`, `git branch -d`, `git rebase`, `git cherry-pick`, `git merge`.
- If you discover the current branch is unsuitable for committing (e.g., protected branch policy, detached HEAD, or missing upstream),
  - record a **BLOCKER** issue in `.vibe/STATE.md` describing what you found and what instruction you need,
  - then stop.

### Commit discipline (hard rule)

- If you change tracked files, you must produce commits.
- **Before setting Status to `IN_REVIEW`**, ensure:
  - at least one commit exists that implements the checkpoint deliverables, and
  - files touched by the active checkpoint are clean in the working tree.
- Unrelated pre-existing changes in other files are allowed:
  - do not revert them unless explicitly instructed,
  - keep your checkpoint diff scoped and reviewable,
  - document any relevant constraints in `.vibe/STATE.md` work log.
- If unrelated changes make a scoped commit impossible, record a **BLOCKER** issue and stop.
- Minimum standard: **≥ 1 commit per completed checkpoint** (more is fine if each commit is a coherent step).

### Commit messages

- Use imperative mood.
- Prefix with the checkpoint ID, e.g. `11.1: Add fix-bug checkpoint template`.
- Avoid “WIP” commits unless explicitly asked; prefer small, complete commits.

### Safety

- Do not push, open PRs, or change remotes unless explicitly instructed.
- Do not commit knowingly broken builds/tests unless the checkpoint explicitly allows it and `.vibe/STATE.md` records the rationale.

## Definitions

- **Authoritative**: must be followed unless overridden by a higher-precedence source.
- **Checkpoint**: a bounded unit with objective/deliverables/acceptance/demo/evidence.
