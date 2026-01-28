# Agent capabilities

This document captures the **capability matrix** for supported agents so workflow prompts
and scripts do not assume abilities that an agent cannot reliably provide.

## Capability matrix

| Agent | File editing | Command execution | Single-loop mode | Continuous mode | Notes |
| --- | --- | --- | --- | --- | --- |
| Codex | Yes | Yes | Yes | Yes | Reference implementation for loop execution. |
| Claude Code | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |
| Gemini | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |
| Copilot | Tool-dependent | Tool-dependent | Yes (manual or tool-assisted) | No (manual re-invocation only) | Default to advisory/review unless tools are explicitly available. |

## Definitions

- **Tool-dependent**: Capability is available only when the host environment exposes editor and/or
  command tools to the agent. When unavailable, assume the agent cannot edit or run commands.
- **Single-loop mode**: Execute exactly one loop and stop. Manual execution is acceptable.
- **Continuous mode**: Looping without manual re-invocation (supported only by Codex for now).

## Guidance

- If tools are unavailable, the agent should produce instructions or propose diffs instead of editing.
- Prompts should avoid requiring command execution unless Codex (or a tool-enabled agent) is in use.
- Continuous mode should be offered only to Codex unless a repo explicitly opts in for other agents.
