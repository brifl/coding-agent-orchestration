#!/usr/bin/env python3
"""Prompt catalog path helpers for canonical and repo-local skill layouts."""

from __future__ import annotations

from pathlib import Path

try:
    from constants import PROMPT_CATALOG_FILENAME, PROMPT_SKILL_PRIORITY
except ModuleNotFoundError as exc:
    if exc.name != "constants":
        raise
    PROMPT_CATALOG_FILENAME = "template_prompts.md"
    PROMPT_SKILL_PRIORITY = (
        "vibe-prompts",
        "vibe-loop",
        "vibe-run",
        "vibe-one-loop",
        "continuous-refactor",
        "continuous-test-generation",
        "continuous-documentation",
    )

from resource_resolver import find_resource


PROMPT_SKILL_NAME = "vibe-prompts"


def canonical_repo_prompt_catalog_path(repo_root: Path) -> Path:
    return (repo_root / "prompts" / PROMPT_CATALOG_FILENAME).resolve()


def _iter_prompt_catalog_candidates_in_skills(skills_root: Path) -> list[Path]:
    seen: set[Path] = set()
    candidates: list[Path] = []
    for skill_name in PROMPT_SKILL_PRIORITY:
        candidate = skills_root / skill_name / "resources" / PROMPT_CATALOG_FILENAME
        if candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)
    if skills_root.exists():
        for candidate in sorted(skills_root.glob(f"*/resources/{PROMPT_CATALOG_FILENAME}")):
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
    return candidates


def iter_repo_local_prompt_catalog_candidates(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for root in (
        repo_root / ".codex" / "skills",
        repo_root / "skills",
        repo_root / "built_in" / "skills",
    ):
        candidates.extend(_iter_prompt_catalog_candidates_in_skills(root))
    return candidates


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
    for candidate in iter_repo_local_prompt_catalog_candidates(repo_root):
        if candidate.exists():
            return candidate
    return resolve_installed_prompt_catalog_path()


def is_repo_canonical_prompt_catalog(repo_root: Path, catalog_path: Path) -> bool:
    return catalog_path.resolve() == canonical_repo_prompt_catalog_path(repo_root)


def is_repo_local_prompt_catalog(repo_root: Path, catalog_path: Path) -> bool:
    resolved = catalog_path.resolve()
    if is_repo_canonical_prompt_catalog(repo_root, resolved):
        return True
    for candidate in iter_repo_local_prompt_catalog_candidates(repo_root):
        if resolved == candidate.resolve():
            return True
    return False


def prompt_catalog_contract_description() -> str:
    return (
        "prompts/template_prompts.md in canonical repo mode, "
        ".codex/skills/vibe-prompts/resources/template_prompts.md in consumer repo mode, or "
        "vibe-prompts/resources/template_prompts.md in installed-skill mode"
    )
