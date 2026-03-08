#!/usr/bin/env python3
"""
Prompt catalog path helpers for repo-local and installed skill layouts.
"""

from __future__ import annotations

from pathlib import Path

try:
    from constants import PROMPT_CATALOG_FILENAME
except ModuleNotFoundError as exc:
    if exc.name != "constants":
        raise
    PROMPT_CATALOG_FILENAME = "template_prompts.md"

from resource_resolver import find_resource


PROMPT_SKILL_NAME = "vibe-prompts"


def canonical_repo_prompt_catalog_path(repo_root: Path) -> Path:
    return (repo_root / "prompts" / PROMPT_CATALOG_FILENAME).resolve()


def resolve_installed_prompt_catalog_path(*, agent: str | None = None) -> Path | None:
    skill_dir = find_resource("skill", PROMPT_SKILL_NAME, agent=agent)
    if skill_dir is None:
        return None
    candidate = (skill_dir / "resources" / PROMPT_CATALOG_FILENAME).resolve()
    if candidate.exists():
        return candidate
    return None


def resolve_prompt_catalog_path(repo_root: Path) -> Path | None:
    repo_catalog = canonical_repo_prompt_catalog_path(repo_root)
    if repo_catalog.exists():
        return repo_catalog
    return resolve_installed_prompt_catalog_path()


def is_repo_canonical_prompt_catalog(repo_root: Path, catalog_path: Path) -> bool:
    return catalog_path.resolve() == canonical_repo_prompt_catalog_path(repo_root)


def prompt_catalog_contract_description() -> str:
    return (
        "prompts/template_prompts.md in repo mode or "
        "vibe-prompts/resources/template_prompts.md in installed-skill mode"
    )
