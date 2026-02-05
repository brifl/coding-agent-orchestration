#!/usr/bin/env python3
"""
resource_resolver.py

Resolves resources (skills, prompts, etc.) by searching in a defined order of precedence:
1. Repo-Local (`.codex/skills/`, `prompts/`)
2. Global (`~/.codex/skills/` or `$CODEX_HOME/skills`)
3. Built-in (`built_in/skills/`, `built_in/prompts/`)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from path_utils import resolve_codex_home

# Assume 'gemini' for the agent if not specified.
DEFAULT_AGENT = "gemini"

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
            search_paths.append(root / resource_name)

        # Legacy repo layout fallback
        search_paths.append(repo_root / "skills" / resource_name)

        # 2. Global
        if agent_name == "codex":
            search_paths.append(_codex_home() / "skills" / resource_name)
            search_paths.append(Path("/etc/codex/skills") / resource_name)
        else:
            search_paths.append(Path.home() / f".{agent_name}" / "skills" / resource_name)

        # 3. Built-in
        search_paths.append(repo_root / "built_in" / "skills" / resource_name)
    elif resource_type == "prompt":
        # For prompts, we look for the containing file.
        # The resource_name is a key inside the file.
        # 1. Repo-Local
        search_paths.append(repo_root / "prompts" / "template_prompts.md")
        # 2. Global
        search_paths.append(Path.home() / f".{agent_name}" / "prompts" / "template_prompts.md")
        # 3. Built-in
        search_paths.append(repo_root / "built_in" / "prompts" / "template_prompts.md")

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
