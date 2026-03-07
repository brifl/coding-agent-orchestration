# Agent capabilities

This document captures the capability matrix for the supported workflow agents so prompts
and scripts do not assume abilities that the agent cannot reliably provide.

## Capability matrix

| Agent | File editing | Command execution | Single-loop mode | Continuous mode | Notes |
| --- | --- | --- | --- | --- | --- |
| Codex (GPT 5.2) | Yes | Yes | Yes | Yes | Reference implementation; native skill support via `$skill`. |
| Claude Code | Yes | Yes | Yes | Yes | Full capabilities via Read/Write/Edit/Bash tools. Invoke agentctl directly or via installed skills. |

## Definitions

- **Yes**: Capability is natively available in the standard deployment.
- **Single-loop mode**: Execute exactly one loop and stop.
- **Continuous mode**: Looping without manual re-invocation until stop condition.

## Agent-specific notes

### Claude Code

- Uses Read/Write/Edit/Bash tools for full file and command access
- Can invoke `python tools/agentctl.py` directly to get next prompt
- Continuous mode: invoke agentctl in a loop, execute returned prompts
- Supports installed skills via the `Skill` tool (e.g., `/continuous-documentation`, `/continuous-refactor`, `/vibe-run`); skill scripts under `~/.claude/skills/<name>/` or `.codex/skills/<name>/` are invoked by name

## Guidance

- Only Codex and Claude Code are supported workflow agents.
- Both supported agents can execute the full loop stack with file and command access.
- Use `python tools/agentctl.py next` to get the next prompt for either supported agent.
