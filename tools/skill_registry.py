#!/usr/bin/env python3
"""
skill_registry.py

Discover and query available skills across:
1) Repo-local (.codex/skills/)
2) Global (~/.codex/skills/ or $CODEX_HOME/skills)
3) Built-in (built_in/skills/)

Provides:
- list: enumerate skills with metadata
- info: show detailed metadata for a single skill
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from path_utils import resolve_codex_home
from skillset_utils import find_manifest, load_manifest

DEFAULT_AGENT = "gemini"


@dataclass(frozen=True)
class SkillRecord:
    name: str
    version: str | None
    description: str | None
    agents: list[str]
    source: str
    path: Path
    manifest_path: Path | None


_CACHE: dict[tuple[Path, str], list[SkillRecord]] = {}


def _repo_root() -> Path:
    return Path.cwd()


def _repo_skill_roots(repo_root: Path) -> list[Path]:
    roots: list[Path] = []
    current = repo_root.resolve()
    while True:
        roots.append(current / ".codex" / "skills")
        if current.parent == current:
            break
        current = current.parent

    legacy = repo_root / "skills"
    if legacy.exists():
        roots.append(legacy)
    return roots


def _skill_paths(repo_root: Path, agent: str) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for root in _repo_skill_roots(repo_root):
        paths.append(("repo", root))

    if agent == "codex":
        paths.append(("global", resolve_codex_home() / "skills"))
        paths.append(("system", Path("/etc/codex/skills")))
    else:
        paths.append(("global", Path.home() / f".{agent}" / "skills"))

    paths.append(("built_in", repo_root / "built_in" / "skills"))
    return paths


def _record_from_dir(skill_dir: Path, source: str) -> SkillRecord:
    manifest_path = find_manifest(skill_dir)
    manifest = load_manifest(manifest_path) if manifest_path else None

    name = (manifest or {}).get("name") or skill_dir.name
    version = (manifest or {}).get("version")
    description = (manifest or {}).get("description")
    agents = (manifest or {}).get("agents") or []

    if isinstance(agents, str):
        agents = [agents]

    return SkillRecord(
        name=str(name),
        version=str(version) if version else None,
        description=str(description) if description else None,
        agents=[str(a) for a in agents],
        source=source,
        path=skill_dir,
        manifest_path=manifest_path,
    )


def discover_skills(repo_root: Path, agent: str) -> list[SkillRecord]:
    cache_key = (repo_root, agent)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    records: list[SkillRecord] = []
    seen: set[str] = set()

    for source, base in _skill_paths(repo_root, agent):
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            rec = _record_from_dir(entry, source)
            if rec.name in seen:
                continue
            seen.add(rec.name)
            records.append(rec)

    _CACHE[cache_key] = records
    return records


def _to_dict(record: SkillRecord) -> dict[str, Any]:
    return {
        "name": record.name,
        "version": record.version,
        "description": record.description,
        "agents": record.agents,
        "source": record.source,
        "path": str(record.path),
        "manifest_path": str(record.manifest_path) if record.manifest_path else None,
    }


def cmd_list(repo_root: Path, agent: str, fmt: str) -> int:
    records = discover_skills(repo_root, agent)
    if fmt == "json":
        print(json.dumps([_to_dict(r) for r in records], indent=2))
        return 0
    for r in records:
        print(f"{r.name}\t{r.version or '-'}\t{r.source}\t{r.description or ''}")
    return 0


def cmd_info(repo_root: Path, agent: str, name: str, fmt: str) -> int:
    records = discover_skills(repo_root, agent)
    record = next((r for r in records if r.name == name), None)
    if not record:
        print(f"Skill '{name}' not found.")
        return 1
    if fmt == "json":
        print(json.dumps(_to_dict(record), indent=2))
        return 0
    print(f"Name: {record.name}")
    print(f"Version: {record.version or '-'}")
    print(f"Description: {record.description or '-'}")
    print(f"Agents: {', '.join(record.agents) if record.agents else '-'}")
    print(f"Source: {record.source}")
    print(f"Path: {record.path}")
    print(f"Manifest: {record.manifest_path or '-'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover and query skills.")
    parser.add_argument("command", choices=["list", "info"], help="Command to run.")
    parser.add_argument("name", nargs="?", help="Skill name for info.")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--agent", default=DEFAULT_AGENT, help="Agent name for global path.")

    args = parser.parse_args()
    repo_root = _repo_root()

    if args.command == "list":
        return cmd_list(repo_root, args.agent, args.format)
    if args.command == "info":
        if not args.name:
            print("Skill name required for info.")
            return 2
        return cmd_info(repo_root, args.agent, args.name, args.format)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
