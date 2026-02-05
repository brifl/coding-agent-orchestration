# Base Vibe skills

This document defines the **base skill surface** that is considered stable and core.
All future skills must layer on top of this foundation without breaking it.

## Core skills

- **vibe-prompts**: provides prompt catalog access and prompt lookup.
- **vibe-loop**: runs a single workflow loop using `agentctl` to select the next prompt.
- **vibe-one-loop**: compatibility alias for single-loop execution in Codex instruction packs.
- **vibe-run**: continuous loop runner (Codex reference implementation); it keeps looping
  until the dispatcher returns `recommended_role == "stop"`.
- **agentctl semantics**: deterministic `next`, `status`, and validation behaviors that
  drive loop selection and state transitions.

## Compatibility guarantees

| Agent | vibe-prompts | vibe-loop | vibe-one-loop | vibe-run | Notes |
| --- | --- | --- | --- | --- | --- |
| Codex | Full | Full | Full | Full | Reference implementation for continuous mode. |
| Claude Code | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Not supported | Use single-loop prompts or manual instructions. |
| Gemini | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Not supported | Use single-loop prompts or manual instructions. |
| Copilot | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Not supported | Use single-loop prompts or manual instructions. |
| Kilo | Full | Full | Full | See agent_capabilities.md | Self-hosted; full capabilities when tool-enabled. |

## Non-goals

- Base skills do **not** promise product-specific automation.
- Base skills do **not** include repo-local overlays (those are opt-in extensions).
