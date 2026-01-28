# Prompt Loops

ROLE
You are operating inside a Vibe coding-agent workflow.

OBJECTIVE
Run exactly ONE workflow loop for this repository, then stop.

PROCEDURE (follow exactly)
1) Determine the next loop to run by executing:
   python ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py --repo-root .

2) The script will:
   - compute the recommended prompt loop
   - print the full prompt body to stdout

3) Execute the printed prompt body verbatim.
   - Do not invent a new workflow.
   - Do not skip steps.
   - Respect all stop conditions in the prompt.

4) When the loop completes:
   - Ensure `.vibe/STATE.md` is updated appropriately.
   - Do NOT start another loop.
   - Stop and wait.

RULES
- Do not run more than one loop.
- Do not continue past a STOP CONDITION.
- If a script fails, report the error and stop.
