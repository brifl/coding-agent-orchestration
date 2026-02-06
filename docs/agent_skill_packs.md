# Agent skill packs

This document describes the **base skill equivalents** for agents that do not use Codex
skills directly. Each pack provides instructions, prompt locations, and invocation patterns.

## Shared prompt pack

All agents use the same prompt catalog and bootstraps:
- Bootstraps: `prompts/init/*.md`
- Loop catalog: `prompts/template_prompts.md`

## Codex (reference)

- **Instructions**: use `$vibe-one-loop` or `$vibe-run` skills.
- **Prompt pack**: bundled into the Codex skill resources.
- **Invocation pattern**:
  1) Run `$vibe-one-loop` for single-loop execution.
  2) Run `$vibe-run` for continuous execution (do not stop after one loop;
     it repeats until the dispatcher returns `recommended_role == "stop"`).
  3) Run `$continuous-refactor` for continuous refactor-only execution
     (workflow pinned to `continuous-refactor`).

## Claude Code

- **Instructions**: paste `prompts/init/claude_bootstrap.md` into a new chat.
- **Prompt pack**: `prompts/template_prompts.md` (loop prompts).
- **Invocation pattern**:
  1) Use the bootstrap to select the next loop.
  2) Execute exactly one loop manually.
  3) Re-run the bootstrap for pseudo-continuous progress.

## Gemini

- **Instructions**: paste `prompts/init/gemini_bootstrap.md` into a new chat.
- **Prompt pack**: `prompts/template_prompts.md` (loop prompts).
- **Invocation pattern**:
  1) Use the bootstrap to select the next loop.
  2) Execute exactly one loop manually.
  3) Re-run the bootstrap for pseudo-continuous progress.

## Copilot

- **Instructions**: paste `prompts/init/copilot_bootstrap.md` into a new chat.
- **Prompt pack**: `prompts/template_prompts.md` (loop prompts).
- **Invocation pattern**:
  1) Use the bootstrap to select the next loop.
  2) Execute exactly one loop manually.
  3) Re-run the bootstrap for pseudo-continuous progress.

## Kilo

- **Instructions**: paste `prompts/init/kilo_bootstrap.md` into a new chat.
- **Prompt pack**: `prompts/template_prompts.md` (loop prompts).
- **Invocation pattern**:
  1) Use the bootstrap to select the next loop.
  2) Execute exactly one loop manually.
  3) Re-run the bootstrap for pseudo-continuous progress.

## Differences (explicit)

- Codex supports continuous mode with `$vibe-run` and `$continuous-refactor`.
- Other agents can use installed skill scripts in a tool-enabled environment,
  or fall back to manual prompt execution.
