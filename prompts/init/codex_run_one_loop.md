# Prompt Loops

ROLE
You are operating inside a Vibe coding-agent workflow.

OBJECTIVE
Run exactly ONE workflow loop for this repository, then stop.

PROCEDURE (follow exactly)
1) Determine the next loop to run by executing:
   python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root .
   (If you set `CODEX_HOME`, use `$CODEX_HOME/skills/...` instead.)

2) The script will:
   - compute the recommended prompt loop
   - print the full prompt body to stdout

3) Execute the printed prompt body verbatim.
   - Do not invent a new workflow.
   - Do not skip steps.
   - Respect all stop conditions in the prompt.

4) When the loop completes:
   - Ensure `.vibe/STATE.md` is updated appropriately.
   - Record loop completion:
     `python3 tools/agentctl.py --repo-root . --format json loop-result --line 'LOOP_RESULT: {...}'`
   - Do NOT start another loop.
   - Stop and wait.

VCS RULES (hard)
- Stay on the current branch.
- Do not create/switch/delete branches unless explicitly instructed.
- Before setting `.vibe/STATE.md` Status to `IN_REVIEW`, ensure:
  - `git status --porcelain` is clean, and
  - you created at least one commit for the checkpoint (`<id>: <imperative summary>`).
- If branch/commit is not possible due to repo policy, record a BLOCKER issue in `.vibe/STATE.md` and stop.

RULES
- Do not run more than one loop.
- Do not continue past a STOP CONDITION.
- If a script fails, report the error and stop.
