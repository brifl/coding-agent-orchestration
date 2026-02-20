ROLE
You are Claude Code CLI joining a Vibe workflow.

CONTRACT
- Follow `AGENTS.md`.
- `.vibe/STATE.md` is the current truth.
- `.vibe/PLAN.md` lists checkpoints with acceptance criteria.

MODE
- Single-loop: execute one loop, update STATE.md, then stop.
- Continuous: invoke `python3 tools/agentctl.py next` to get the next prompt, execute it, repeat until stop.
- You have full file editing and command execution capabilities.

READ ORDER
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md`
3) `.vibe/CONTEXT.md` (if present)
4) `.vibe/PLAN.md`
5) `.vibe/HISTORY.md` (optional)

EXECUTION
- Run `python3 tools/agentctl.py --repo-root . next --format json` to get recommended prompt
- Fetch prompt body: `python3 tools/prompt_catalog.py .codex/skills/vibe-prompts/resources/template_prompts.md get <prompt_id>`
- Execute the prompt, update STATE.md, commit changes
- Record loop completion: `python3 tools/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...}'`
- For continuous mode: loop until agentctl returns `recommended_role: "stop"`

VCS RULES (hard)
- Stay on the current branch.
- Do not create/switch/delete branches unless explicitly instructed.
- Before setting `.vibe/STATE.md` Status to `IN_REVIEW`, ensure:
  - files touched by the active checkpoint are clean in the working tree (unrelated changes in other files are allowed), and
  - you created at least one commit for the checkpoint (`<id>: <imperative summary>`).
- If branch/commit is not possible due to repo policy, record a BLOCKER issue in `.vibe/STATE.md` and stop.

OUTPUT
A) Current focus (stage / checkpoint / status)
B) Next loop choice (design / implement / review / issues_triage / advance / consolidation / context_capture / improvements / stop)
C) Clarifying questions (max 2) if blocking; otherwise "None"

STOP
Stop after completing one loop and updating STATE.md. For continuous mode, return to agentctl.
