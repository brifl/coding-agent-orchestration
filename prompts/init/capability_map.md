# Agent capability map (internal)

This file is an internal reference for bootstrap prompt authors. It mirrors
`docs/agent_capabilities.md` and should stay in sync.

## Map (compact)

| Agent | Edit files | Run commands | Single-loop | Continuous |
| --- | --- | --- | --- | --- |
| Codex (GPT 5.2) | yes | yes | yes | yes |
| Claude Code | yes | yes | yes | yes |

## Usage

- Use this map to decide whether a bootstrap should run a loop or only select a loop.
- Only Codex and Claude Code are supported workflow platforms.
- Both supported agents can invoke `agentctl next` in a loop for continuous execution.
