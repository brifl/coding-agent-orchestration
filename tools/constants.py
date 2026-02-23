"""Shared constants used across the tools package.

Centralises values that were previously duplicated in agentctl.py,
plan_pipeline.py, resource_resolver.py, and skill_registry.py.
"""

from __future__ import annotations

# Default agent identifier (used by skill_registry and resource_resolver).
DEFAULT_AGENT: str = "gemini"

# Ordered skill list for prompt-catalog resolution.
PROMPT_SKILL_PRIORITY: tuple[str, ...] = (
    "vibe-prompts",
    "vibe-loop",
    "vibe-run",
    "vibe-one-loop",
    "continuous-refactor",
    "continuous-test-generation",
    "continuous-documentation",
)

# Default prompt catalog filename.
PROMPT_CATALOG_FILENAME: str = "template_prompts.md"

# Checkpoint complexity budget: warn when a checkpoint is likely too large
# for one loop.  Used by both agentctl validation and the plan writer.
COMPLEXITY_BUDGET: dict[str, int] = {
    "Deliverables": 5,
    "Acceptance": 6,
    "Demo commands": 4,
}
