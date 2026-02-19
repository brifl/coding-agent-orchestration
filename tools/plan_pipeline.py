#!/usr/bin/env python3
"""
plan_pipeline.py

PipelineConfig schema and config resolution for `agentctl plan`.

Config resolution order (highest priority first):
  1. CLI flags
  2. Repo-local  .vibe/plan_pipeline.json
  3. Global      ~/.vibe/plan_pipeline.json
  4. Defaults
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineConfig:
    """Resolved configuration for one plan-pipeline run."""

    problem_statement: str
    provider: str
    dry_run: bool = False
    output_path: str = ".vibe/PLAN.md"
    overwrite: bool = False

    # Provider-specific options forwarded verbatim to the provider layer.
    provider_options: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config file resolution
# ---------------------------------------------------------------------------

_CONFIG_FILENAME = "plan_pipeline.json"


def _load_json_config(path: Path) -> dict[str, Any]:
    """Load a JSON config file; return {} on missing or parse error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _global_config_path() -> Path:
    return Path.home() / ".vibe" / _CONFIG_FILENAME


def _repo_config_path(repo_root: Path) -> Path:
    return repo_root / ".vibe" / _CONFIG_FILENAME


def _merge_config(
    repo_root: Path,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Merge config sources (lowest → highest priority): global → repo-local → overrides."""
    merged: dict[str, Any] = {}
    for source in (
        _load_json_config(_global_config_path()),
        _load_json_config(_repo_config_path(repo_root)),
        overrides,
    ):
        merged.update({k: v for k, v in source.items() if v is not None})
    return merged


# ---------------------------------------------------------------------------
# Validation / fail-fast
# ---------------------------------------------------------------------------

class PipelineConfigError(ValueError):
    """Raised when PipelineConfig cannot be resolved or is invalid."""


def resolve_config(
    repo_root: Path,
    *,
    problem_statement: str | None = None,
    provider: str | None = None,
    dry_run: bool = False,
    output_path: str | None = None,
    overwrite: bool = False,
) -> PipelineConfig:
    """Resolve CLI flags against config files and return a validated PipelineConfig.

    Raises PipelineConfigError on missing required fields or output-path conflicts.
    """
    cli_overrides: dict[str, Any] = {
        k: v
        for k, v in {
            "problem_statement": problem_statement,
            "provider": provider,
            "output_path": output_path,
        }.items()
        if v is not None
    }
    # dry_run and overwrite are flags (bool), always take them from CLI
    merged = _merge_config(repo_root, cli_overrides)

    resolved_problem = merged.get("problem_statement")
    resolved_provider = merged.get("provider")
    resolved_output = merged.get("output_path", ".vibe/PLAN.md")
    resolved_dry_run = dry_run
    resolved_overwrite = overwrite
    provider_options: dict[str, Any] = merged.get("provider_options") or {}

    # Fail-fast: problem statement is mandatory
    if not resolved_problem or not str(resolved_problem).strip():
        raise PipelineConfigError(
            "Missing --problem-statement. "
            "Provide it via CLI or set 'problem_statement' in "
            ".vibe/plan_pipeline.json or ~/.vibe/plan_pipeline.json."
        )

    # Fail-fast: provider is mandatory unless dry-run (no LLM calls in dry-run)
    if not resolved_dry_run and (not resolved_provider or not str(resolved_provider).strip()):
        raise PipelineConfigError(
            "Missing provider. "
            "Provide it via --provider or set 'provider' in "
            ".vibe/plan_pipeline.json or ~/.vibe/plan_pipeline.json."
        )

    # Fail-fast: output path conflict (exists + no --overwrite) — only in non-dry-run
    if not resolved_dry_run:
        out = Path(resolved_output)
        if not out.is_absolute():
            out = repo_root / out
        if out.exists() and not resolved_overwrite:
            raise PipelineConfigError(
                f"Output file already exists: {out}. "
                "Use --overwrite to replace it, or choose a different --output path."
            )

    return PipelineConfig(
        problem_statement=str(resolved_problem).strip(),
        provider=str(resolved_provider).strip() if resolved_provider else "",
        dry_run=resolved_dry_run,
        output_path=resolved_output,
        overwrite=resolved_overwrite,
        provider_options=provider_options,
    )
