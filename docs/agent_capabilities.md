# Agent capabilities

This document captures the **capability matrix** for supported agents so workflow prompts
and scripts do not assume abilities that an agent cannot reliably provide.

## Capability matrix

| Agent | File editing | Command execution | Single-loop mode | Continuous mode | Notes |
| --- | --- | --- | --- | --- | --- |
| Codex (GPT 5.2) | Yes | Yes | Yes | Yes | Reference implementation; native skill support via `$skill`. |
| Claude Code CLI | Yes | Yes | Yes | Yes | Full capabilities via Read/Write/Edit/Bash tools. Invoke agentctl directly. |
| Gemini Code | Yes | Yes | Yes | Yes | Full capabilities in code assistant mode. |
| Copilot | Yes | Yes | Yes | Partial | VS Code/CLI mode has full edit/exec; continuous requires manual re-invocation. |
| Kimi 2.5 | Yes | Yes | Yes | Yes | Self-hosted; full capabilities when tool-enabled. |
| Claude (web chat) | No | No | Yes (advisory) | No | No file/command access; produces instructions only. |
| Gemini (web chat) | No | No | Yes (advisory) | No | No file/command access; produces instructions only. |

## Definitions

- **Yes**: Capability is natively available in the standard deployment.
- **Partial**: Capability works but may require manual intervention or re-invocation.
- **No**: Capability is not available; agent produces instructions instead.
- **Single-loop mode**: Execute exactly one loop and stop.
- **Continuous mode**: Looping without manual re-invocation until stop condition.

## Agent-specific notes

### Claude Code CLI

- Uses Read/Write/Edit/Bash tools for full file and command access
- Can invoke `python tools/agentctl.py` directly to get next prompt
- Continuous mode: invoke agentctl in a loop, execute returned prompts
- No native skill system; uses direct tool invocation

### Gemini Code

- Full file editing and command execution in code assistant deployments
- Continuous mode supported via tool-enabled loop execution
- Web chat version has no tool access (advisory only)

### Copilot

- VS Code integration provides full edit/exec capabilities
- CLI mode (GitHub Copilot CLI) has command execution
- Continuous mode requires manual re-invocation between loops

#### Copilot Continuous Mode Workaround

Copilot cannot natively loop without user intervention. To achieve pseudo-continuous execution:

**Option 1: Manual Re-invocation (recommended)**

```bash
# 1. Get next action
python tools/agentctl.py --repo-root . --format json next

# 2. Get the prompt body
python tools/prompt_catalog.py prompts/template_prompts.md get <prompt_id>

# 3. Paste the prompt to Copilot, let it execute
# 4. Repeat from step 1 until agentctl returns "stop"
```

**Option 2: VS Code Task Automation**

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [{
    "label": "vibe-next",
    "type": "shell",
    "command": "python tools/agentctl.py --repo-root . --format json next"
  }]
}
```
Then trigger the task between loops with `Ctrl+Shift+P` → "Run Task" → "vibe-next".

**What works with Copilot:**
- Single-loop execution (full file editing, command execution)
- STATE.md updates within a loop
- Review, implementation, and triage loops

**What requires manual intervention:**
- Advancing to next loop (must re-invoke agentctl)
- Crossing stage boundaries (must run consolidation manually)
- Context continuity (re-read AGENTS.md/STATE.md each session)

### Kimi 2.5 / IQuest Coder / Other self-hosted

- Capabilities depend on tool configuration
- When tool-enabled: full file/command/continuous support
- Can run overnight on long tasks if properly configured

#### Self-Hosted Agent Configuration Guide

To use a self-hosted agent with the Vibe workflow:

**1. Tool Requirements**

Your agent must have access to:
- **File operations**: Read, write, edit files (especially `.vibe/STATE.md`)
- **Command execution**: Run Python scripts (`agentctl.py`, `prompt_catalog.py`)
- **UTF-8 handling**: All workflow files are UTF-8 encoded

**2. Bootstrap Setup**

Use the generic bootstrap prompt:
```bash
cat prompts/init/generic_bootstrap.md
```

Paste this into your agent at the start of each session.

**3. Skill Installation (optional)**

If your agent supports a skill/plugin system:
```bash
python tools/bootstrap.py install-skills --global --agent kimi
# or: --agent <your-agent-name>
```

This installs to `~/.<agent>/skills/`.

**4. Continuous Mode**

For overnight or long-running execution:
```bash
# Your agent should loop:
while true:
    result = run("python tools/agentctl.py --repo-root . --format json next")
    if result.recommended_role == "stop":
        break
    prompt = run(f"python tools/prompt_catalog.py prompts/template_prompts.md get {result.recommended_prompt_id}")
    execute(prompt)
```

**5. Error Handling**

Configure your agent to:
- Stop on BLOCKED status or BLOCKER issues
- Commit changes after each checkpoint (optional)
- Log progress to a file for later review

**6. Resource Limits**

Consider setting:
- Maximum loops per session (e.g., 20)
- Context window management (re-read STATE.md periodically)
- Timeout per loop (e.g., 30 minutes)

## Guidance

- CLI/IDE versions of agents generally have full capabilities
- Web chat versions are advisory-only (no file/command access)
- Continuous mode is now supported by multiple agents, not just Codex
- Use `python tools/agentctl.py next` to get the next prompt for any agent
