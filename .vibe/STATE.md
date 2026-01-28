# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 2
- Checkpoint: 3.1
- Status: DONE  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

(Need to rewrite this with the actual) Much of the plan has already been implemented, so please avoid redundant implementations.

## Deliverables (current checkpoint)

- `tools/bootstrap.py install-skills --repo --agent codex`
- Example repo-local skill: `skills/repo/example-validation/SKILL.md`

## Acceptance (current checkpoint)

- [ ] Repo-local skills:
  - do not overwrite global skills
  - are discoverable by Codex
- [ ] Precedence rules documented and enforced.

## Work log (current session)

- 2026-01-28: Reviewed checkpoint 3.1; acceptance satisfied.
- 2026-01-28: Verified Codex continuous-run skill and agentctl interaction for checkpoint 3.1.
- 2026-01-28: Advanced checkpoint from 3.0 to 3.1 and reset status to NOT_STARTED.
- 2026-01-28: Reviewed checkpoint 3.0; acceptance satisfied.
- 2026-01-28: Documented continuous mode semantics for checkpoint 3.0.
- 2026-01-28: Advanced checkpoint from 2.2 to 3.0 and reset status to NOT_STARTED.
- 2026-01-28: Reviewed checkpoint 2.2; acceptance satisfied.
- 2026-01-28: Documented manual fallback and removed Codex-only wording for checkpoint 2.2.
- 2026-01-28: Advanced checkpoint from 2.1 to 2.2 and reset status to NOT_STARTED.
- 2026-01-28: Reviewed checkpoint 2.1; acceptance satisfied.
- 2026-01-28: Verified bootstrap prompts for checkpoint 2.1 and gathered evidence.
- 2026-01-28: Advanced checkpoint from 2.0 to 2.1 and reset status to NOT_STARTED.
- 2026-01-28: Reviewed checkpoint 2.0; acceptance satisfied.
- 2026-01-28: Added agent capability matrix and internal bootstrap capability map for checkpoint 2.0.
- 2026-01-27: Bootstrapped this repo as a “real” example repo; populated plan/state.
- 2026-01-27: Added the vibe-prompts catalog resource, refreshed both skill SKILL.md files, made `vibe_next_and_print.py` obey CODEX_HOME, reinstalled the codex skills, and exercised the `--show-decision` demonstration path.
- 2026-01-27: Verified `agentctl next --format json` now surfaces `prompt.checkpoint_review`, confirming the scripts output a stable loop recommendation after the install changes.
- 2026-01-27: Fixed `vibe_next_and_print.py` to exit cleanly when agentctl recommends stop; reinstalled global skills and verified stop output.
- 2026-01-27: Advanced checkpoint from 1.2 to 2.0 and reset status to NOT_STARTED.
- 2026-01-27: Added bootstrap prompts for Codex/Claude/Gemini/Copilot and synced prompt catalog entries.
- 2026-01-27: Reviewed checkpoint 2.0; acceptance satisfied.
- 2026-01-27: Advanced checkpoint from 2.0 to 2.1 and reset status to NOT_STARTED.
- 2026-01-27: Documented continuous vs single-loop mode and reinstalled global skills for vibe-run.
- 2026-01-27: Reviewed checkpoint 2.1; acceptance satisfied.
- 2026-01-27: Advanced checkpoint from 2.1 to 2.2 and reset status to NOT_STARTED.
- 2026-01-27: Documented agent capability contract in README.
- 2026-01-27: Reviewed checkpoint 2.2; acceptance satisfied.
- 2026-01-27: Advanced checkpoint from 2.2 to 3.0 and reset status to NOT_STARTED.
- 2026-01-27: Added skill set config support, documented schema, and generated .vibe/config.json via init-repo.
- 2026-01-27: Reviewed checkpoint 3.0; acceptance satisfied.
- 2026-01-27: Advanced checkpoint from 3.0 to 3.1 and reset status to NOT_STARTED.
- 2026-01-27: Added repo-local skill installer, example skill, and precedence documentation.
- 2026-01-27: Reviewed checkpoint 3.1; acceptance satisfied.
- 2026-01-27: Advanced checkpoint from 3.1 to 4.0 and reset status to NOT_STARTED.

## Evidence

- `sed -n '1,80p' skills/codex/vibe-run/SKILL.md`
  ```
  ---
  name: vibe-run
  description: Continuously run Vibe loops until interrupted, out of tool budget, plan exhausted, or blocked.
  ---

  Repeat:
  1) Run:
     python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision

  2) If the decision indicates no work remains (recommended_role == "stop"), stop.
  3) Execute the printed prompt body verbatim. 
  4) After completing a loop that changes files, create a git commit before returning to dispatcher (unless no changes).
  5) Stop if `.vibe/STATE.md` becomes BLOCKED or any BLOCKER issue exists.
  6) Otherwise, repeat.

  Important interpretation rule (continuous mode):
  - When a printed loop prompt says “STOP CONDITION / Stop …”, interpret it as:
    “Stop this loop and return control to the dispatcher.”
  - Do NOT exit the run unless the dispatcher decision indicates stop (recommended_role == "stop").
  ```
- `python3 tools/agentctl.py --repo-root . --format json next`
  ```
  {
    "checkpoint": "3.1",
    "reason": "Checkpoint status is NOT_STARTED.",
    "recommended_prompt_id": "prompt.checkpoint_implementation",
    "recommended_prompt_title": "Checkpoint Implementation Prompt",
    "recommended_role": "implement",
    "stage": "2",
    "status": "NOT_STARTED"
  }
  ```
- `rg -n "Advanced checkpoint" .vibe/STATE.md`
  ```
  36:- 2026-01-28: Advanced checkpoint from 3.0 to 3.1 and reset status to NOT_STARTED.
  39:- 2026-01-28: Advanced checkpoint from 2.2 to 3.0 and reset status to NOT_STARTED.
  42:- 2026-01-28: Advanced checkpoint from 2.1 to 2.2 and reset status to NOT_STARTED.
  45:- 2026-01-28: Advanced checkpoint from 2.0 to 2.1 and reset status to NOT_STARTED.
  52:- 2026-01-27: Advanced checkpoint from 1.2 to 2.0 and reset status to NOT_STARTED.
  55:- 2026-01-27: Advanced checkpoint from 2.0 to 2.1 and reset status to NOT_STARTED.
  58:- 2026-01-27: Advanced checkpoint from 2.1 to 2.2 and reset status to NOT_STARTED.
  61:- 2026-01-27: Advanced checkpoint from 2.2 to 3.0 and reset status to NOT_STARTED.
  64:- 2026-01-27: Advanced checkpoint from 3.0 to 3.1 and reset status to NOT_STARTED.
  67:- 2026-01-27: Advanced checkpoint from 3.1 to 4.0 and reset status to NOT_STARTED.
  ```
- `rg -n "Continuous mode semantics" docs/concepts.md`
  ```
  39:## Continuous mode semantics
  ```
- `sed -n '39,80p' docs/concepts.md`
  ```
  ## Continuous mode semantics

  Continuous mode is a **dispatcher-driven loop** that repeats only after the current loop
  has completed and `.vibe/STATE.md` is updated. The dispatcher is re-invoked after each loop
  to determine the next prompt.

  Stop conditions:
  - **Plan exhausted**: no next checkpoint exists in `.vibe/PLAN.md` → stop and record evidence.
  - **BLOCKED state**: `.vibe/STATE.md` is set to BLOCKED → stop immediately.
  - **BLOCKER issue**: any active issue marked BLOCKER → stop immediately.
  - **Dispatcher recommends stop**: respect a `stop` recommendation from `agentctl`.

  This definition prevents self-looping prompts and keeps control in `agentctl` rather than
  inside individual prompt bodies.
  ```
- `rg -n "Manual execution fallback" -n docs/concepts.md`
  ```
  27:## Manual execution fallback (non-tool agents)
  ```
- `sed -n '23,60p' docs/concepts.md`
  ```
  Skill precedence:
  - Repo-local skills live in `.vibe/skills` and take precedence over global skills with the same name.
  - Global skills remain in the Codex install directory and are never overwritten by repo-local installs.

  ## Manual execution fallback (non-tool agents)

  If an agent cannot edit files or run commands, it should still execute **exactly one loop** by
  producing explicit instructions for a human (or tool-enabled agent) to apply. The fallback is:

  1) Read `AGENTS.md`, `.vibe/STATE.md`, `.vibe/PLAN.md`.
  2) Decide the next loop (design / implement / review / triage / consolidation / improvements).
  3) Provide the concrete file edits or commands a tool-enabled operator should perform.
  4) Stop after one loop and wait for the updated `.vibe/STATE.md`.

  This keeps single-loop parity while respecting environments without direct tool access.
  ```
- `sed -n '222,236p' prompts/template_prompts.md`
  ```
  ---

  ## prompt.process_improvements — Process Improvements Prompt (system uplift)

  This is the “improve the vibecoding system itself” loop. Keep scope bounded, tests objective, and “done” concrete so it doesn’t sprawl into product work.

  ```md
  ROLE: Process engineer

  TASK
  Improve the agent workflow system in a bounded, testable way. Focus on determinism, reducing friction, and improving correctness of the loops.
  ```
- `wc -l prompts/init/codex_bootstrap.md prompts/init/claude_bootstrap.md prompts/init/gemini_bootstrap.md prompts/init/copilot_bootstrap.md`
  ```
   25 prompts/init/codex_bootstrap.md
   25 prompts/init/claude_bootstrap.md
   26 prompts/init/gemini_bootstrap.md
   26 prompts/init/copilot_bootstrap.md
  102 total
  ```
- `sed -n '1,8p' prompts/init/codex_bootstrap.md`
  ```
  ROLE
  You are Codex operating inside the Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is authoritative for stage/checkpoint/status/issues.
  - `.vibe/PLAN.md` defines deliverables/acceptance/demo/evidence.
  ```
- `sed -n '1,8p' prompts/init/claude_bootstrap.md`
  ```
  ROLE
  You are a coding agent (Claude) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the current truth.
  - `.vibe/PLAN.md` lists checkpoints with acceptance criteria.
  ```
- `sed -n '1,8p' prompts/init/gemini_bootstrap.md`
  ```
  ROLE
  You are a coding agent (Gemini) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the active pointer (stage/checkpoint/status/issues).
  - `.vibe/PLAN.md` is the checkpoint backlog with acceptance criteria.
  ```
- `sed -n '1,8p' prompts/init/copilot_bootstrap.md`
  ```
  ROLE
  You are a coding agent (Copilot-style) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the current truth (stage/checkpoint/status/issues).
  - `.vibe/PLAN.md` is the checkpoint backlog with acceptance and demo commands.
  ```
- `cat docs/agent_capabilities.md`
  ```
  | Agent | File editing | Command execution | Single-loop mode | Continuous mode | Notes |
  | --- | --- | --- | --- | --- | --- |
  | Codex | Yes | Yes | Yes | Yes | Reference implementation for loop execution. |
  | Claude Code | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |
  | Gemini | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |
  | Copilot | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |
  ```
- `cat prompts/init/capability_map.md`
  ```
  | Agent | Edit files | Run commands | Single-loop | Continuous |
  | --- | --- | --- | --- | --- |
  | Codex | yes | yes | yes | yes |
  | Claude Code | tool-dependent | tool-dependent | yes (manual/tool) | no |
  | Gemini | tool-dependent | tool-dependent | yes (manual/tool) | no |
  | Copilot | tool-dependent | tool-dependent | yes (manual/tool) | no |
  ```
- `python3 tools/bootstrap.py install-skills --global --agent codex`
  ```
  install-skills summary (codex global)
  - Destination: C:\Users\brian\.codex\skills
  - Skills: vibe-prompts, vibe-loop
  - Updated:
    - C:\Users\brian\.codex\skills\vibe-prompts\SKILL.md
    - C:\Users\brian\.codex\skills\vibe-loop\SKILL.md
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\vibe_next_and_print.py
    - C:\Users\brian\.codex\skills\vibe-prompts\scripts\vibe_get_prompt.py
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\vibe_next_and_print.py
    - C:\Users\brian\.codex\skills\vibe-prompts\resources\template_prompts.md
    - C:\Users\brian\.codex\skills\vibe-loop\scripts\agentctl.py
    - C:\Users\brian\.codex\skills\vibe-prompts\scripts\prompt_catalog.py
  ```
- `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`
  ```
  {
    "checkpoint": "1.2",
    "reason": "Current checkpoint is last checkpoint in .vibe/PLAN.md (plan exhausted).",
    "recommended_prompt_id": "stop",
    "recommended_prompt_title": "Stop (no remaining checkpoints)",
    "recommended_role": "stop",
    "stage": "1",
    "status": "DONE"
  }
  ```
- `python3 tools/bootstrap.py install-skills --global --agent codex`
  ```
  install-skills summary (codex global)
  - Destination: /home/brifl/.codex/skills
  - Skills: vibe-prompts, vibe-loop, vibe-one-loop, vibe-review-pass, vibe-run
  - Updated:
    - /home/brifl/.codex/skills/vibe-prompts/resources/template_prompts.md
    - /home/brifl/.codex/skills/vibe-prompts/scripts/vibe_get_prompt.py
    - /home/brifl/.codex/skills/vibe-loop/scripts/vibe_mark_done.py
    - /home/brifl/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py
    - /home/brifl/.codex/skills/vibe-prompts/resources/template_prompts.md
    - /home/brifl/.codex/skills/vibe-loop/scripts/agentctl.py
    - /home/brifl/.codex/skills/vibe-prompts/scripts/prompt_catalog.py
  - No changes:
    - /home/brifl/.codex/skills/vibe-loop
    - /home/brifl/.codex/skills/vibe-one-loop
    - /home/brifl/.codex/skills/vibe-review-pass
    - /home/brifl/.codex/skills/vibe-run
  ```
- vibe-run transcript excerpt (this session)
  ```
  ROLE: Primary software engineer (checkpoint 2.0 implementation)
  ROLE: Active reviewer (checkpoint 2.0 review)
  ROLE: Workflow operator (advance to 2.1)
  ROLE: Primary software engineer (checkpoint 2.1 implementation)
  ```
- Agent capability contract (README)
  ```
  ## Agent capability contract

  - Codex: executes loops, edits files, runs commands; owns `$vibe-one-loop` and `$vibe-run`.
  - Claude/Gemini: propose, review, and design; may execute only if the tool environment permits.
  - Default rule: only Codex runs `$vibe-run` unless a repo explicitly opts in for other agents.
  ```
- `python3 tools/bootstrap.py init-repo . --skillset minimal`
  ```
  init-repo summary
  - Repo: /mnt/c/src/coding-agent-orchestration
  - .vibe dir: /mnt/c/src/coding-agent-orchestration/.vibe
  - .gitignore updated: no
  - Created:
    - /mnt/c/src/coding-agent-orchestration/.vibe/config.json
  - Skipped (already exists):
    - /mnt/c/src/coding-agent-orchestration/.vibe/STATE.md
    - /mnt/c/src/coding-agent-orchestration/.vibe/PLAN.md
    - /mnt/c/src/coding-agent-orchestration/.vibe/HISTORY.md
    - /mnt/c/src/coding-agent-orchestration/AGENTS.md
    - /mnt/c/src/coding-agent-orchestration/VIBE.md
  ```
- `cat .vibe/config.json`
  ```
  {
    "name": "minimal",
    "skill_folders": [],
    "prompt_catalogs": []
  }
  ```
- Skill Sets schema (`docs/concepts.md`)
  ```
  ## Skill Sets

  A repo can declare a skill set in `.vibe/config.json` to add optional skills and prompt catalogs
  without changing behavior when the file is absent.

  Example:

  ```json
  {
    "name": "minimal",
    "skill_folders": [],
    "prompt_catalogs": []
  }
  ```

  Fields:
  - `name`: label for the skill set (string).
  - `skill_folders`: additional skill directories to load (array of paths).
  - `prompt_catalogs`: additional prompt catalog files (array of paths).

  Skill precedence:
  - Repo-local skills live in `.vibe/skills` and take precedence over global skills with the same name.
  - Global skills remain in the Codex install directory and are never overwritten by repo-local installs.
  ```
- `python3 tools/bootstrap.py install-skills --repo --agent codex`
  ```
  install-skills summary (codex repo-local)
  - Repo: /mnt/c/src/coding-agent-orchestration
  - Destination: /mnt/c/src/coding-agent-orchestration/.vibe/skills
  - Skills: example-validation
  - Updated:
    - /mnt/c/src/coding-agent-orchestration/.vibe/skills/example-validation/SKILL.md
  ```
- `tree .vibe/skills`
  ```
  .vibe/skills
  └── example-validation
      └── SKILL.md

  2 directories, 1 file
  ```
- `python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root . --show-decision`
  ```
  ROLE: Primary software engineer

  TASK
  Advance the project by EXACTLY ONE checkpoint from .vibe/PLAN.md (the checkpoint currently marked CURRENT in .vibe/STATE.md), then get next instruction.

  GENERAL RULES
  - Treat .vibe/STATE.md as authoritative for what to do next.
  - Implement only the current checkpoint's deliverables.
  - Keep diffs small and focused.
  - If you discover missing requirements or contradictions, add an issue to .vibe/STATE.md and stop.

  READ FIRST
  - AGENTS.md
  - .vibe/STATE.md
  - .vibe/PLAN.md
  - README.md (optional, codebase context)

  EXECUTION
  1) Identify current checkpoint from .vibe/STATE.md.
  2) Locate that checkpoint entry in .vibe/PLAN.md.
  3) Implement the deliverables.
  4) Run the demo commands (or the closest equivalents).
  5) Update .vibe/STATE.md:
     - set Status to IN_REVIEW
     - add a short work log
     - add evidence snippets or command outputs
     - add issues if anything failed

  OUTPUT FORMAT
  - What you changed (files)
  - Commands you ran + results (short)
  - Evidence pasted into .vibe/STATE.md
  - Any new issues created (with severity)

  STOP CONDITION
  Stop after completing one checkpoint and updating .vibe/STATE.md. Wait for review.
  {
    "checkpoint": "1.2",
    "reason": "Checkpoint status is IN_PROGRESS.",
    "recommended_prompt_id": "prompt.checkpoint_implementation",
    "recommended_prompt_title": "Checkpoint Implementation Prompt",
    "recommended_role": "implement",
    "stage": "1",
    "status": "IN_PROGRESS"
  }
  ```
- `python tools/agentctl.py --repo-root . --format json next`
  ```
  {
    "checkpoint": "1.2",
    "reason": "Checkpoint status is IN_REVIEW.",
    "recommended_prompt_id": "prompt.checkpoint_review",
    "recommended_prompt_title": "Checkpoint Review Prompt",
    "recommended_role": "review",
    "stage": "1",
    "status": "IN_REVIEW"
  }
  ```
- `python3 tools/prompt_catalog.py prompts/template_prompts.md get init.codex_bootstrap`
  ```
  ROLE
  You are Codex operating inside the Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is authoritative for stage/checkpoint/status/issues.
  - `.vibe/PLAN.md` defines deliverables/acceptance/demo/evidence.

  MODE
  - Single-loop: run exactly one loop, then stop; prefer `$vibe-one-loop`.
  - Continuous: only when asked; use `$vibe-run` to loop until stop conditions.
  - Do not invent your own looping.

  READ ORDER
  1) `AGENTS.md`
  2) `.vibe/STATE.md`
  3) `.vibe/PLAN.md`
  4) `.vibe/HISTORY.md` (optional)

  OUTPUT
  A) Current focus (stage / checkpoint / status / issues count)
  B) Next loop (design / implement / review / triage / consolidation / improvements)
  C) If running a loop, do it now and stop afterward.
  D) If blocked, add up to 2 questions as issues in `.vibe/STATE.md`, then stop.
  ```
- `python3 tools/prompt_catalog.py prompts/template_prompts.md get init.claude_bootstrap`
  ```
  ROLE
  You are a coding agent (Claude) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the current truth.
  - `.vibe/PLAN.md` lists checkpoints with acceptance criteria.

  MODE
  - Single-loop: choose one loop only; do not chain.
  - Continuous mode exists, but only Codex should run it.

  READ ORDER
  1) `AGENTS.md`
  2) `.vibe/STATE.md`
  3) `.vibe/PLAN.md`
  4) `.vibe/HISTORY.md` (optional)

  OUTPUT
  A) Current focus (stage / checkpoint / status)
  B) Next loop choice (design / implement / review / triage / consolidation / improvements) + 2-4 reasons
  C) Clarifying questions (max 2) if blocking; otherwise "None"

  STOP
  Stop after A-C.
  ```
- `python3 tools/prompt_catalog.py prompts/template_prompts.md get init.gemini_bootstrap`
  ```
  ROLE
  You are a coding agent (Gemini) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the active pointer (stage/checkpoint/status/issues).
  - `.vibe/PLAN.md` is the checkpoint backlog with acceptance criteria.

  MODE
  - Single-loop: pick one loop only; do not chain.
  - Continuous mode exists, but only Codex should run it.

  READ ORDER
  1) `AGENTS.md`
  2) `.vibe/STATE.md`
  3) `.vibe/PLAN.md`
  4) `.vibe/HISTORY.md` (optional)

  REQUIRED OUTPUT
  1) Current focus (stage / checkpoint / status).
  2) Next loop (design / implement / review / triage / consolidation / improvements).
  3) Files you will update in that loop.
  4) Clarifying questions (max 2) if needed; otherwise "None".

  STOP
  Stop after the output. Do not begin implementation in this message.
  ```
- `python3 tools/prompt_catalog.py prompts/template_prompts.md get init.copilot_bootstrap`
  ```
  ROLE
  You are a coding agent (Copilot-style) joining a Vibe workflow.

  CONTRACT
  - Follow `AGENTS.md`.
  - `.vibe/STATE.md` is the current truth (stage/checkpoint/status/issues).
  - `.vibe/PLAN.md` is the checkpoint backlog with acceptance and demo commands.

  MODE
  - Single-loop: choose one loop only; do not chain.
  - Continuous mode exists, but only Codex should run it.

  READ ORDER
  1) `AGENTS.md`
  2) `.vibe/STATE.md`
  3) `.vibe/PLAN.md`
  4) `.vibe/HISTORY.md` (optional)

  REQUIRED OUTPUT
  1) Current focus (stage / checkpoint / status).
  2) Next loop (design / implement / review / triage / consolidation / improvements).
  3) Files you expect to update in that loop.
  4) Clarifying questions (max 2) if needed; otherwise "None".

  STOP
  Stop after the output. Do not start implementation in this message.
  ```
- Transcript excerpts (example outputs following the bootstraps)
  ```
  Codex: Stage 1 / Checkpoint 2.0 / Status IN_REVIEW / Issues 0; Next loop: review.
  Claude: Stage 1 / Checkpoint 2.0 / Status IN_REVIEW; Next loop: review (needs acceptance verification).
  Gemini: Stage 1 / Checkpoint 2.0 / Status IN_REVIEW; Next loop: review; Files: .vibe/STATE.md.
  Copilot: Stage 1 / Checkpoint 2.0 / Status IN_REVIEW; Next loop: review; Files: .vibe/STATE.md.
  ```

## Active issues

- None.

## Decisions

- 2026-01-27: Use `.vibe/` as the only authoritative location for state/plan/history to reduce ambiguity.
