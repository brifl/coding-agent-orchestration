# Manual Template Prompts

These are expected to be copy-pasted using clippy.py.

## guide.create_checkpoints — Design: Create checkpoints (external)

```md
Let's grab the next 1 to 3 stages and break out some checkpoints for imminent work to be done. 
- Crisp up the stages themselves and create 1 to 6 checkpoints within the stages. 
- Do not make any "optional" - either it is in the stage/checkpoint or it isn't. 
- This should be the next 1 to 3 stages and their checkpoints.

Each checkpoint needs:
- Objective (1 sentence)
- Deliverables (concrete files/modules/behaviors)
- Acceptance (verifiable)
- Demo commands (exact, local, minimal)
- Evidence (what to paste into .vibe/STATE.md)

```

---

## prompt.onboarding — Onboarding Prompt (deprecated)

```md
ROLE: New contributor LLM (Claude Code / other)

CONTEXT
You are joining an existing vibecoding workflow that uses:
- Stable execution contract (AGENTS.md)
- Current work pointer (.vibe/STATE.md)
- Near-term plan (.vibe/PLAN.md)
- Templates for the prompt loops (template_prompts.md)
Optional:
- History rollups (.vibe/HISTORY.md)

GOAL
Before you take any action, build an accurate mental model of:
1) how work is selected,
2) how state moves (CURRENT → IN_REVIEW → COMPLETED),
3) what constitutes “done” for a checkpoint,
4) where evidence and issues live,
5) which prompt loop should run next.

SCOPE (this prompt is questions-only)
- Do NOT modify any files.
- Do NOT propose code changes.
- Do NOT start implementing.
- Your job is to ask clarifying questions and report your understanding.

READ FIRST (in order)
1) AGENTS.md (optional if already read this session)
2) .vibe/STATE.md
3) .vibe/PLAN.md
4) README.md (optional, codebase context)
5) .vibe/HISTORY.md (optional; non-authoritative)
6) template_prompts.md (prompt catalog; optional)

OUTPUT FORMAT (must follow)
A) Your current understanding (brief)
- Current stage/checkpoint/status from .vibe/STATE.md
- What the next loop/prompt should be (and why)
- What “done” means for the current checkpoint (from AGENTS.md + .vibe/PLAN.md)
- Where you will record evidence and issues

B) Clarifying questions (max 10; prioritize highest leverage)
Ask only questions that materially change what you would do next. Categorize them:

1) Blocking questions (must be answered before action)
- <question>
- <why it matters in 1 sentence>

2) Non-blocking questions (helpful but not required)
- <question>
- <why it matters in 1 sentence>

C) Assumptions (only if needed)
If you cannot get answers, list up to 5 assumptions you would proceed with.

D) Proposed next prompt loop
Name exactly one loop from template_prompts.md you would run next:
- Stage Design Prompt
- Checkpoint Implementation Prompt
- Checkpoint Review Prompt
- Issues Triage Prompt
- Consolidation Prompt
- Process Improvements Prompt
Provide a 2–4 bullet justification.

STOP CONDITION
Stop after producing the output. Wait for human answers before proceeding.
```
---

## prompt.stage_breakout — Stage Breakout Prompt

```md
Define the next 3 stages in more detail. Break out the checkpoint level details in the following format:

### Checkpoint <S.C>: <Checkpoint name>

**Objective**
- One sentence

**Deliverables**
- Core completion behaviors/functionality, in bulleted form

**Acceptance**
- Verifiable criteria

**Demo commands**
- Local commands to demo/verify

**Evidence**
- What to paste into .vibe/STATE.md
```

---
