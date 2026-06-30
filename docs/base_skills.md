# Base Vibe skills

This document defines the intentionally small core skill surface. Improve this
surface directly when that is clearer than layering on another alias or wrapper.

## Core skills

- **vibe-prompts**: provides prompt catalog access and prompt lookup.
- **vibe-loop**: runs a single workflow loop using `agentctl` to select the next prompt.
- **vibe-run**: continuous loop runner (Codex reference implementation); it keeps looping
  until the dispatcher returns `recommended_role == "stop"`, and explicit invocation
  replenishes fresh or exhausted backlogs through repository-aware stage design.
- **continuous-refactor**: continuous runner pinned to the `continuous-refactor` workflow.
- **continuous-test-generation**: continuous runner pinned to the `continuous-test-generation` workflow.
- **continuous-documentation**: continuous runner pinned to the `continuous-documentation` workflow.
- **agentctl semantics**: deterministic `next`, `status`, and validation behaviors that
  drive loop selection and state transitions.

## Supported surfaces

| Agent | vibe-prompts | vibe-loop | vibe-run | continuous-refactor | continuous-test-generation | continuous-documentation | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | Full | Full | Full | Full | Full | Full | Reference implementation for continuous mode. |
| Claude Code | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Manual/Tool-dependent | Use installed skill scripts or manual prompts. |

## Non-goals

- Base skills do **not** promise product-specific automation.
- Base skills do **not** include repo-local overlays (those are opt-in extensions).
