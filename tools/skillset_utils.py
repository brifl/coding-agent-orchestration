#!/usr/bin/env python3
"""
skillset_utils.py

Shared helpers for parsing, locating, and loading skill manifests and skillset
definition files. Used by bootstrap.py, skillctl.py, and skill_registry.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_MANIFEST_LOAD_EXCEPTIONS = (
    json.JSONDecodeError,
    OSError,
    UnicodeDecodeError,
    ValueError,
)


def parse_skillset_yaml(text: str) -> dict[str, Any]:
    """Parse a skillset YAML definition (name/description/extends/skills) without PyYAML."""
    data: dict[str, Any] = {"extends": [], "skills": []}
    current_section: str | None = None
    last_skill: dict[str, Any] | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.startswith("name:"):
            data["name"] = line.split(":", 1)[1].strip().strip("\"'")
            current_section = None
            continue
        if indent == 0 and line.startswith("description:"):
            data["description"] = line.split(":", 1)[1].strip().strip("\"'")
            current_section = None
            continue
        if indent == 0 and line.startswith("extends:"):
            current_section = "extends"
            continue
        if indent == 0 and line.startswith("skills:"):
            current_section = "skills"
            continue

        if current_section == "extends" and line.startswith("-"):
            item = line[1:].strip().strip("\"'")
            data["extends"].append(item)
            continue

        if current_section == "skills" and line.startswith("-"):
            item = line[1:].strip()
            skill: dict[str, Any] = {}
            if item.startswith("name:"):
                skill["name"] = item.split(":", 1)[1].strip().strip("\"'")
            data["skills"].append(skill)
            last_skill = skill
            continue

        if current_section == "skills" and indent > 0 and ":" in line and last_skill is not None:
            key, value = line.split(":", 1)
            last_skill[key.strip()] = value.strip().strip("\"'")

    return data


def load_skillset(path: Path) -> dict[str, Any] | None:
    """Load a skillset definition from a JSON or YAML file. Returns None on error."""
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in {".yaml", ".yml"}:
            return parse_skillset_yaml(path.read_text(encoding="utf-8"))
    except _MANIFEST_LOAD_EXCEPTIONS as exc:
        import sys
        print(f"[skillset_utils] warning: failed to load skillset {path}: {exc}", file=sys.stderr)
        return None
    return None


def find_skillset(skillsets_root: Path, name: str) -> Path | None:
    """Find a skillset file by name under *skillsets_root*. Returns None if not found."""
    for ext in (".yaml", ".yml", ".json"):
        path = skillsets_root / f"{name}{ext}"
        if path.exists():
            return path
    return None


def parse_yaml_minimal(text: str) -> dict[str, Any]:
    """Parse a simple flat YAML document (key: value / list items) without PyYAML."""
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


def front_matter(text: str) -> str | None:
    """Extract YAML front matter delimited by ``---`` lines. Returns None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def find_manifest(skill_dir: Path) -> Path | None:
    """Locate the manifest file (SKILL.md/.yaml/.yml/.json) inside *skill_dir*."""
    for name in ("SKILL.md", "SKILL.yaml", "SKILL.yml", "SKILL.json"):
        path = skill_dir / name
        if path.exists():
            return path
    return None


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load a skill manifest from JSON, YAML, or Markdown front matter. Returns None on error."""
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in {".yaml", ".yml"}:
            return parse_yaml_minimal(path.read_text(encoding="utf-8"))
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            fm = front_matter(text)
            if fm is None:
                return None
            return parse_yaml_minimal(fm)
    except _MANIFEST_LOAD_EXCEPTIONS:
        return None
    return None
