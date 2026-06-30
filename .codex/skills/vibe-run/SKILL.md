---
name: vibe-run
description: Continuously assess and execute a repository's Vibe backlog. Use when the user invokes $vibe-run or asks Codex to inspect a repo, bootstrap or replenish .vibe/PLAN.md, and keep implementing and reviewing checkpoints until a real blocker or explicit stop.
---

# Vibe Run

Run the Vibe workflow as an agent loop. Treat `.vibe/PLAN.md` as a durable
execution backlog, not as a substitute for inspecting the repository.

## Operating posture

`$vibe-run` is high-throughput scaffolding for complex work. It should keep Codex
moving through design, implementation, review, and handoff without letting process
become the product.

- Use evidence as lightweight trust-but-verify receipts, not comprehensive proof.
- Prefer one or two high-signal checks over broad verification when risk is low.
- Let non-building loops earn their cost: they should reduce rework, backsliding,
  rediscovery, or shaky handoffs.
- Keep moving when the next capability is safe; record useful non-blocking checks
  as concise backlog items instead of making them gate every loop.
- If an issue, checkpoint, or stage is blocked but later independent work can
  safely proceed, mark it `[DEFERRED]`, add a short reason plus unblock/revisit
  condition, and move on. Waiting on human feedback is a valid deferral reason.
- Revisit `[DEFERRED]` items during design and consolidation; reactivate them
  when the unblock condition is true, otherwise keep the note compact.

## Start

1. Read `AGENTS.md`, `.vibe/STATE.md`, and `.vibe/PLAN.md` in that order.
2. From the repository root, dispatch with the explicit `vibe-run` workflow:

   ```bash
   python3 .codex/skills/vibe-loop/scripts/agentctl.py --repo-root . --format json next --workflow vibe-run
   ```

   In this orchestration source repo, use `python3 tools/agentctl.py ...` instead;
   the `.codex` dispatcher script is generated during install.

3. Fetch `recommended_prompt_id` from the returned `prompt_catalog_path`:

   ```bash
   python3 .codex/skills/vibe-prompts/scripts/prompt_catalog.py <prompt_catalog_path> get <recommended_prompt_id>
   ```

   In this orchestration source repo, use `python3 tools/prompt_catalog.py ...` instead.

4. Follow the fetched prompt as the current loop. Inspect and edit the repository
   yourself; `scripts/vibe_run.py` is a terminal/headless helper, not a replacement
   for Codex executing the work.
5. Emit and record the prompt's `LOOP_RESULT`, then dispatch again.

## Planning behavior

- On a fresh template, let the initial `design` loop inspect source, tests,
  manifests, docs, and the existing plan before authoring executable checkpoints.
- On an exhausted plan, explicit `--workflow vibe-run` dispatches `design` again
  so the backlog can be replenished from current repository evidence.
- Preserve substantive unfinished checkpoints. Replace placeholders, repair stale
  assumptions, and extend exhausted plans; never overwrite useful work merely to
  regenerate formatting.
- Preserve `[DEFERRED]` work only while it has a real owner/outcome and a useful
  revisit condition. Do not treat deferral as satisfying dependencies.
- Use another installed skill only when its description clearly matches a
  specialized part of the current loop. Read that skill before following it.
- Ask at most two questions only when missing information materially changes
  scope, architecture, dependencies, or acceptance.

## Continue until a terminal condition

Continue through `design`, `implement`, `review`, `issues_triage`, `advance`,
`consolidation`, and `context_capture`. A completed checkpoint, review pass, or
auto-advance is not a stopping condition.

Stop only when:

- the dispatcher returns `recommended_role: stop` for a real blocker or explicit
  workflow terminal condition;
- a required human decision is recorded in `.vibe/STATE.md`; or
- the user cancels or narrows the run.

Do not accept placeholder behavior or shallow test success as completion.

Evidence should stay short: command + result, commit hash, file/path changed,
manual observation, or pointer to a bounded artifact. Avoid pasting long logs into
STATE unless the log is the thing a future agent will need.

## Terminal and headless helper

```bash
# Interactive
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --show-decision

# Headless executor; the executor must emit LOOP_RESULT
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --executor "python3 ./scripts/run_one_loop.py" --show-decision

# Protocol dry-run only
python3 .codex/skills/vibe-run/scripts/vibe_run.py --repo-root . --non-interactive --simulate-loop-result --max-loops 10 --show-decision
```
