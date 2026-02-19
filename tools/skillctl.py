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

from path_utils import resolve_codex_home
from resource_resolver import find_resource
from skill_registry import DEFAULT_AGENT, discover_skills
from skillset_utils import (
    find_manifest,
    find_skillset,
    load_manifest,
    load_skillset,
    parse_skillset_yaml,  # noqa: F401
)


REQUIRED_FIELDS = ["name", "description"]


def _repo_root() -> Path:
    return Path.cwd()


def _skillsets_root() -> Path:
    return _repo_root() / "skillsets"


def _lock_path() -> Path:
    return _repo_root() / ".vibe" / "skill-lock.json"


def _load_lock() -> dict[str, Any]:
    path = _lock_path()
    if not path.exists():
        return {"subscriptions": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_lock(payload: dict[str, Any]) -> None:
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _agent_global_dir(agent: str) -> Path:
    if agent == "codex":
        return resolve_codex_home() / "skills"
    return Path.home() / f".{agent}" / "skills"


def _repo_skill_source(name: str) -> Path:
    primary = _repo_root() / ".codex" / "skills" / name
    if primary.exists():
        return primary
    legacy = _repo_root() / "skills" / name
    if legacy.exists():
        return legacy
    return primary


def _repo_skill_dest(name: str) -> Path:
    return _repo_root() / ".codex" / "skills" / name


def _manifest_dependencies(skill_name: str, agent: str) -> list[str]:
    skill_dir = find_resource("skill", skill_name, agent=agent)
    if not skill_dir or not skill_dir.exists():
        return []
    manifest_path = find_manifest(Path(skill_dir))
    if not manifest_path:
        return []
    manifest = load_manifest(manifest_path)
    if not manifest:
        return []
    deps = manifest.get("dependencies") or []
    if isinstance(deps, list):
        return [str(d) for d in deps]
    return []


def resolve_skillset(name: str, agent: str) -> dict[str, Any]:
    visited: set[str] = set()
    resolving: set[str] = set()
    resolved: dict[str, str | None] = {}
    tree: dict[str, list[str]] = {}

    def load_set(set_name: str) -> dict[str, Any]:
        path = find_skillset(_skillsets_root(), set_name)
        if not path:
            raise FileNotFoundError(f"Skillset '{set_name}' not found.")
        data = load_skillset(path)
        if not data:
            raise ValueError(f"Failed to parse skillset: {path}")
        return data

    def visit_set(set_name: str) -> None:
        if set_name in resolving:
            raise ValueError(f"Circular skillset dependency detected: {set_name}")
        if set_name in visited:
            return
        resolving.add(set_name)
        data = load_set(set_name)
        for parent in data.get("extends", []):
            visit_set(str(parent))

        for skill in data.get("skills", []):
            name = str(skill.get("name"))
            version = skill.get("version")
            if name in resolved and version and resolved[name] and resolved[name] != version:
                raise ValueError(f"Version conflict for {name}: {resolved[name]} vs {version}")
            resolved[name] = resolved.get(name) or version
        visited.add(set_name)
        resolving.remove(set_name)

    visit_set(name)

    # Expand dependencies from manifests
    for skill_name in list(resolved.keys()):
        deps = _manifest_dependencies(skill_name, agent)
        tree[skill_name] = deps
        for dep in deps:
            if dep not in resolved:
                resolved[dep] = None

    resolved_list = [
        {"name": skill, "version": resolved[skill]} for skill in sorted(resolved.keys())
    ]

    return {"name": name, "skills": resolved_list, "dependency_tree": tree}


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

    manifest_path = find_manifest(path)
    if not manifest_path:
        print(f"Missing SKILL manifest in {path}")
        return 1

    manifest = load_manifest(manifest_path)
    if not manifest:
        print(f"Failed to parse manifest: {manifest_path}")
        return 1

    missing = [field for field in REQUIRED_FIELDS if field not in manifest]
    if missing:
        print(f"Missing required fields: {', '.join(missing)}")
        return 1

    print(f"OK: {path}")
    return 0


def cmd_resolve_set(name: str, fmt: str, agent: str) -> int:
    try:
        payload = resolve_skillset(name, agent)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    if fmt == "json":
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Skillset: {payload['name']}")
    print("Skills:")
    for skill in payload["skills"]:
        version = skill["version"] or "-"
        print(f"- {skill['name']} ({version})")
    print("Dependency tree:")
    for key, deps in payload["dependency_tree"].items():
        print(f"- {key}: {', '.join(deps) if deps else '-'}")
    return 0


def cmd_subscribe(source: str, name: str, pin: str | None) -> int:
    lock = _load_lock()
    subs = lock.get("subscriptions", [])
    # Update existing subscription if present.
    existing = next((s for s in subs if s.get("name") == name and s.get("source") == source), None)
    entry = {
        "name": name,
        "source": source,
        "pin": pin or "HEAD",
    }
    if existing:
        existing.update(entry)
    else:
        subs.append(entry)
    lock["subscriptions"] = subs
    _write_lock(lock)
    print(f"Subscribed {name} from {source} (pin: {entry['pin']})")
    return 0


def _parse_major(pin: str) -> int | None:
    raw = pin.lstrip("vV")
    if not raw or not raw[0].isdigit():
        return None
    num = ""
    for ch in raw:
        if ch.isdigit():
            num += ch
        else:
            break
    return int(num) if num else None


def cmd_sync(upgrade: bool) -> int:
    lock = _load_lock()
    subs = lock.get("subscriptions", [])
    updated = False
    for sub in subs:
        pin = sub.get("pin") or "HEAD"
        major = _parse_major(pin)
        if major is None:
            print(f"{sub.get('name')}: synced ({pin})")
            continue
        if upgrade:
            new_pin = f"v{major + 1}.0.0"
            if new_pin != pin:
                sub["pin"] = new_pin
                updated = True
                print(f"{sub.get('name')}: upgraded {pin} -> {new_pin}")
        else:
            print(f"{sub.get('name')}: major update available; run --upgrade to bump (current {pin})")

    if updated:
        _write_lock(lock)
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
    instp.add_argument("--repo", dest="repo_install", action="store_true", help="Install into .codex/skills in the repo")
    instp.add_argument("--agent", default=DEFAULT_AGENT)
    instp.add_argument("--force", action="store_true")

    uninstp = sub.add_parser("uninstall", help="Remove a skill")
    uninstp.add_argument("name")
    uninstp.add_argument("--global", dest="global_install", action="store_true")
    uninstp.add_argument("--repo", dest="repo_install", action="store_true", help="Remove from .codex/skills in the repo")
    uninstp.add_argument("--agent", default=DEFAULT_AGENT)

    updp = sub.add_parser("update", help="Reinstall a skill")
    updp.add_argument("name")
    updp.add_argument("--global", dest="global_install", action="store_true")
    updp.add_argument("--repo", dest="repo_install", action="store_true", help="Reinstall into .codex/skills in the repo")
    updp.add_argument("--agent", default=DEFAULT_AGENT)

    valp = sub.add_parser("validate", help="Validate a skill manifest")
    valp.add_argument("path")

    rsvp = sub.add_parser("resolve-set", help="Resolve a skill set")
    rsvp.add_argument("name")
    rsvp.add_argument("--format", choices=["json", "text"], default="text")
    rsvp.add_argument("--agent", default=DEFAULT_AGENT)

    subp = sub.add_parser("subscribe", help="Subscribe to an external skill")
    subp.add_argument("source")
    subp.add_argument("name")
    subp.add_argument("--pin", type=str)

    syncp = sub.add_parser("sync", help="Sync subscribed skills")
    syncp.add_argument("--upgrade", action="store_true")

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
    if args.cmd == "resolve-set":
        return cmd_resolve_set(args.name, args.format, args.agent)
    if args.cmd == "subscribe":
        return cmd_subscribe(args.source, args.name, args.pin)
    if args.cmd == "sync":
        return cmd_sync(args.upgrade)

    return 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
