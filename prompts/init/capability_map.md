# Agent capability map (internal)

This file is an internal reference for **bootstrap prompt authors**. It mirrors the
capability matrix in `docs/agent_capabilities.md` and should stay in sync.

## Map (compact)

| Agent | Edit files | Run commands | Single-loop | Continuous |
| --- | --- | --- | --- | --- |
| Codex | yes | yes | yes | yes |
| Claude Code | tool-dependent | tool-dependent | yes (manual/tool) | no |
| Gemini | tool-dependent | tool-dependent | yes (manual/tool) | no |
| Copilot | tool-dependent | tool-dependent | yes (manual/tool) | no |

## Usage

- Use this map to decide whether a bootstrap should **run** a loop or **only select** a loop.
- Continuous mode should only be referenced for Codex unless a repo explicitly opts in.
