#!/usr/bin/env python3
"""
skillctl.py

Unified CLI for skill management.
Commands: list, info, install, uninstall, update, validate
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from resource_resolver import find_resource
from skill_registry import DEFAULT_AGENT, discover_skills


REQUIRED_FIELDS = ["name", "version", "description", "agents", "dependencies", "entry_points"]


def _repo_root() -> Path:
    return Path.cwd()


def _agent_global_dir(agent: str) -> Path:
    return Path.home() / f".{agent}" / "skills"


def _repo_skill_source(name: str) -> Path:
    return _repo_root() / "skills" / "repo" / name


def _repo_skill_dest(name: str) -> Path:
    return _repo_root() / ".vibe" / "skills" / name


def _find_manifest(skill_dir: Path) -> Path | None:
    for name in ("SKILL.yaml", "SKILL.yml", "SKILL.json"):
        path = skill_dir / name
        if path.exists():
            return path
    return None


def _parse_yaml_minimal(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and ":" in line and not line.startswith("-"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_key = key
            else:
                data[key] = value.strip("\"'")
                current_key = None
            continue

        if current_key and indent > 0 and line.startswith("-"):
            item = line[1:].strip()
            if item.startswith("name:"):
                item = item.split(":", 1)[1].strip()
            data[current_key].append(item.strip("\"'"))

    return data


def _load_manifest(path: Path) -> dict[str, Any] | None:
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in {".yaml", ".yml"}:
            return _parse_yaml_minimal(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _sync_dir(src: Path, dst: Path, *, force: bool) -> None:
    if dst.exists() and force:
        shutil.rmtree(dst)
    if dst.exists():
        return
    shutil.copytree(src, dst)


def cmd_list(fmt: str, agent: str) -> int:
    records = discover_skills(_repo_root(), agent)
    if fmt == "json":
        out = [
            {
                "name": r.name,
                "version": r.version,
                "description": r.description,
                "agents": r.agents,
                "source": r.source,
                "path": str(r.path),
                "manifest_path": str(r.manifest_path) if r.manifest_path else None,
            }
            for r in records
        ]
        print(json.dumps(out, indent=2))
        return 0
    for r in records:
        print(f"{r.name}\t{r.version or '-'}\t{r.source}\t{r.description or ''}")
    return 0


def cmd_info(name: str, fmt: str, agent: str) -> int:
    records = discover_skills(_repo_root(), agent)
    record = next((r for r in records if r.name == name), None)
    if not record:
        print(f"Skill '{name}' not found.")
        return 1
    if fmt == "json":
        print(
            json.dumps(
                {
                    "name": record.name,
                    "version": record.version,
                    "description": record.description,
                    "agents": record.agents,
                    "source": record.source,
                    "path": str(record.path),
                    "manifest_path": str(record.manifest_path) if record.manifest_path else None,
                },
                indent=2,
            )
        )
        return 0
    print(f"Name: {record.name}")
    print(f"Version: {record.version or '-'}")
    print(f"Description: {record.description or '-'}")
    print(f"Agents: {', '.join(record.agents) if record.agents else '-'}")
    print(f"Source: {record.source}")
    print(f"Path: {record.path}")
    print(f"Manifest: {record.manifest_path or '-'}")
    return 0


def cmd_install(name: str, *, agent: str, global_install: bool, repo_install: bool, force: bool) -> int:
    if global_install == repo_install:
        print("Choose exactly one of --global or --repo for install.")
        return 2

    if repo_install:
        src = _repo_skill_source(name)
        dst = _repo_skill_dest(name)
    else:
        src = find_resource("skill", name, agent=agent)
        if not src:
            print(f"Skill '{name}' not found.")
            return 1
        dst = _agent_global_dir(agent) / name

    if not src.exists():
        print(f"Source skill folder missing: {src}")
        return 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    _sync_dir(src, dst, force=force)
    print(f"Installed {name} to {dst}")
    return 0


def cmd_uninstall(name: str, *, agent: str, global_install: bool, repo_install: bool) -> int:
    if global_install == repo_install:
        print("Choose exactly one of --global or --repo for uninstall.")
        return 2

    dst = _repo_skill_dest(name) if repo_install else _agent_global_dir(agent) / name
    if not dst.exists():
        print(f"Skill '{name}' is not installed at {dst}")
        return 1
    shutil.rmtree(dst)
    print(f"Removed {name} from {dst}")
    return 0


def cmd_update(name: str, *, agent: str, global_install: bool, repo_install: bool) -> int:
    return cmd_install(name, agent=agent, global_install=global_install, repo_install=repo_install, force=True)


def cmd_validate(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        print(f"Skill path not found: {path}")
        return 1

    manifest_path = _find_manifest(path)
    if not manifest_path:
        print(f"Missing SKILL manifest in {path}")
        return 1

    manifest = _load_manifest(manifest_path)
    if not manifest:
        print(f"Failed to parse manifest: {manifest_path}")
        return 1

    missing = [field for field in REQUIRED_FIELDS if field not in manifest]
    if missing:
        print(f"Missing required fields: {', '.join(missing)}")
        return 1

    print(f"OK: {path}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="skillctl.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    listp = sub.add_parser("list", help="List available skills")
    listp.add_argument("--format", choices=["json", "text"], default="text")
    listp.add_argument("--agent", default=DEFAULT_AGENT)

    infop = sub.add_parser("info", help="Show skill metadata")
    infop.add_argument("name")
    infop.add_argument("--format", choices=["json", "text"], default="text")
    infop.add_argument("--agent", default=DEFAULT_AGENT)

    instp = sub.add_parser("install", help="Install a skill")
    instp.add_argument("name")
    instp.add_argument("--global", dest="global_install", action="store_true")
    instp.add_argument("--repo", dest="repo_install", action="store_true")
    instp.add_argument("--agent", default=DEFAULT_AGENT)
    instp.add_argument("--force", action="store_true")

    uninstp = sub.add_parser("uninstall", help="Remove a skill")
    uninstp.add_argument("name")
    uninstp.add_argument("--global", dest="global_install", action="store_true")
    uninstp.add_argument("--repo", dest="repo_install", action="store_true")
    uninstp.add_argument("--agent", default=DEFAULT_AGENT)

    updp = sub.add_parser("update", help="Reinstall a skill")
    updp.add_argument("name")
    updp.add_argument("--global", dest="global_install", action="store_true")
    updp.add_argument("--repo", dest="repo_install", action="store_true")
    updp.add_argument("--agent", default=DEFAULT_AGENT)

    valp = sub.add_parser("validate", help="Validate a skill manifest")
    valp.add_argument("path")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        return cmd_list(args.format, args.agent)
    if args.cmd == "info":
        return cmd_info(args.name, args.format, args.agent)
    if args.cmd == "install":
        return cmd_install(args.name, agent=args.agent, global_install=args.global_install, repo_install=args.repo_install, force=args.force)
    if args.cmd == "uninstall":
        return cmd_uninstall(args.name, agent=args.agent, global_install=args.global_install, repo_install=args.repo_install)
    if args.cmd == "update":
        return cmd_update(args.name, agent=args.agent, global_install=args.global_install, repo_install=args.repo_install)
    if args.cmd == "validate":
        return cmd_validate(Path(args.path))

    return 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
