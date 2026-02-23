#!/usr/bin/env python3
"""
resource_resolver.py

Resolves resources (skills, prompts, etc.) by searching in a defined order of precedence:
1. Repo-Local (`.codex/skills/*/resources/`)
2. Global (`~/.codex/skills/*/resources/` or `$CODEX_HOME/skills/*/resources/`)
3. Built-in (`built_in/skills/*/resources/`)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from path_utils import resolve_codex_home

from constants import DEFAULT_AGENT, PROMPT_SKILL_PRIORITY

def _get_repo_root() -> Path:
    """Gets the repository root by searching for the .git directory."""
    # This is a simple implementation. A more robust one would traverse up from cwd.
    # For now, we assume the script is run from within the repo.
    return Path(os.getcwd())


def _codex_home() -> Path:
    return resolve_codex_home()


def _codex_repo_skill_roots(repo_root: Path) -> list[Path]:
    roots: list[Path] = []
    current = repo_root.resolve()
    while True:
        candidate = current / ".codex" / "skills"
        roots.append(candidate)
        if current.parent == current:
            break
        current = current.parent
    return roots


def _append_path_if_new(search_paths: list[Path], path: Path) -> None:
    if path not in search_paths:
        search_paths.append(path)


def _append_prompt_catalog_candidates(
    search_paths: list[Path],
    skills_root: Path,
    resource_name: str,
) -> None:
    for skill_name in PROMPT_SKILL_PRIORITY:
        _append_path_if_new(search_paths, skills_root / skill_name / "resources" / resource_name)

    if skills_root.exists():
        for candidate in sorted(skills_root.glob(f"*/resources/{resource_name}")):
            _append_path_if_new(search_paths, candidate)


def find_resource(resource_type: str, resource_name: str, agent: str | None = None) -> Path | None:
    """
    Finds a resource by searching in the defined order of precedence.

    Args:
        resource_type: The type of resource to find (e.g., "skill", "prompt").
        resource_name: The name of the resource to find.
        agent: The name of the agent, used for the global path.

    Returns:
        The path to the resource, or None if not found.
    """
    repo_root = _get_repo_root()
    agent_name = agent or DEFAULT_AGENT

    search_paths: list[Path] = []

    if resource_type == "skill":
        # 1. Repo-Local (Codex searches .codex/skills from cwd up)
        for root in _codex_repo_skill_roots(repo_root):
            _append_path_if_new(search_paths, root / resource_name)

        # Legacy repo layout fallback
        _append_path_if_new(search_paths, repo_root / "skills" / resource_name)

        # 2. Global
        if agent_name == "codex":
            _append_path_if_new(search_paths, _codex_home() / "skills" / resource_name)
            _append_path_if_new(search_paths, Path("/etc/codex/skills") / resource_name)
        else:
            _append_path_if_new(search_paths, Path.home() / f".{agent_name}" / "skills" / resource_name)

        # 3. Built-in
        _append_path_if_new(search_paths, repo_root / "built_in" / "skills" / resource_name)
    elif resource_type == "prompt":
        # For prompts, search prompt catalogs copied into skill resources first.
        for root in _codex_repo_skill_roots(repo_root):
            _append_prompt_catalog_candidates(search_paths, root, resource_name)

        # Legacy repo-local skills layout fallback.
        _append_prompt_catalog_candidates(search_paths, repo_root / "skills", resource_name)

        # Global locations.
        if agent_name == "codex":
            _append_prompt_catalog_candidates(search_paths, _codex_home() / "skills", resource_name)
            _append_prompt_catalog_candidates(search_paths, Path("/etc/codex/skills"), resource_name)
        else:
            agent_root = Path.home() / f".{agent_name}"
            _append_prompt_catalog_candidates(search_paths, agent_root / "skills", resource_name)

        # Built-in fallback location.
        _append_prompt_catalog_candidates(search_paths, repo_root / "built_in" / "skills", resource_name)

    for path in search_paths:
        if path.exists():
            return path

    return None


def main():
    parser = argparse.ArgumentParser(description="Find resources with precedence.")
    parser.add_argument("resource_type", choices=["skill", "prompt"], help="The type of resource to find.")
    parser.add_argument("resource_name", help="The name of the resource to find.")
    parser.add_argument("--agent", help="The agent name for the global path.")
    parser.add_argument("--show-path", action="store_true", help="Show the path of the found resource.")

    args = parser.parse_args()

    path = find_resource(args.resource_type, args.resource_name, args.agent)

    if path:
        if args.show_path:
            print(path.resolve())
        else:
            print(f"Resource '{args.resource_name}' of type '{args.resource_type}' found at: {path.resolve()}")
    else:
        print(f"Resource '{args.resource_name}' of type '{args.resource_type}' not found.")
        exit(1)


if __name__ == "__main__":
    main()
