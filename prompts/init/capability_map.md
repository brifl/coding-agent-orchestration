# Agent capability map (internal)

This file is an internal reference for **bootstrap prompt authors**. It mirrors the
capability matrix in `docs/agent_capabilities.md` and should stay in sync.

## Map (compact)

| Agent | Edit files | Run commands | Single-loop | Continuous |
| --- | --- | --- | --- | --- |
| Codex (GPT 5.2) | yes | yes | yes | yes |
| Claude Code CLI | yes | yes | yes | yes |
| Gemini Code | yes | yes | yes | yes |
| Copilot | yes | yes | yes | partial |
| Claude (web) | no | no | advisory | no |
| Gemini (web) | no | no | advisory | no |

## Usage

- Use this map to decide whether a bootstrap should **run** a loop or **only select** a loop.
- CLI/IDE versions (Claude Code CLI, Gemini Code, Copilot) have full capabilities.
- Web chat versions are advisory-only and produce instructions instead of executing.
- Continuous mode is supported by most CLI agents; invoke `agentctl next` in a loop.
