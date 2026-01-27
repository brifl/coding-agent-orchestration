#!/usr/bin/env python3
"""
prompt_catalog.py

Shared parser for prompts/template_prompts.md.

Catalog conventions:
- A prompt section begins at a line: "## <id> — <title>" OR "## <title>" (legacy)
- The payload is the first fenced code block that follows the header.
  - Supported fences: ```md ... ``` or ``` ... ```
- Extraction returns the payload text (without the fences).

This module is intended to be used by:
- tools/clipper.py (UI / clipboard)
- future agent skills scripts (prompt fetch)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_HEADER_RE = re.compile(r"^##\s+(?P<hdr>.+?)\s*$")
_STABLE_ID_RE = re.compile(r"^(?P<id>[a-z0-9_.-]+)\s+—\s+(?P<title>.+)$")
_FENCE_START_RE = re.compile(r"^```(?P<lang>[A-Za-z0-9_-]+)?\s*$")
_FENCE_END_RE = re.compile(r"^```\s*$")


@dataclass(frozen=True)
class CatalogEntry:
    key: str          # stable id if present, else derived from title
    title: str        # human title
    body: str         # fenced block content (without fences)
    start_line: int   # 1-based line number where header appears


def _derive_key_from_title(title: str) -> str:
    # Conservative slug; stable IDs are preferred.
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    return slug or "untitled"


def parse_catalog(text: str) -> List[CatalogEntry]:
    lines = text.splitlines()
    entries: List[CatalogEntry] = []

    i = 0
    while i < len(lines):
        m = _HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue

        hdr = m.group("hdr").strip()
        stable = _STABLE_ID_RE.match(hdr)
        if stable:
            key = stable.group("id").strip()
            title = stable.group("title").strip()
        else:
            title = hdr
            key = _derive_key_from_title(title)

        header_line_no = i + 1

        # Find first fenced code block after header.
        j = i + 1
        while j < len(lines) and not _FENCE_START_RE.match(lines[j]):
            # stop early if another header starts (no payload)
            if _HEADER_RE.match(lines[j]):
                break
            j += 1

        if j >= len(lines) or not _FENCE_START_RE.match(lines[j]):
            # No payload found; skip this header.
            i += 1
            continue

        # Capture until closing fence.
        j += 1
        body_lines: List[str] = []
        while j < len(lines) and not _FENCE_END_RE.match(lines[j]):
            body_lines.append(lines[j])
            j += 1

        if j >= len(lines):
            raise ValueError(f"Unterminated fenced block after header at line {header_line_no}")

        body = "\n".join(body_lines).rstrip("\n")
        entries.append(CatalogEntry(key=key, title=title, body=body, start_line=header_line_no))

        i = j + 1  # continue after closing fence

    # Enforce unique keys.
    seen: Dict[str, CatalogEntry] = {}
    for e in entries:
        if e.key in seen:
            prev = seen[e.key]
            raise ValueError(
                f"Duplicate catalog key '{e.key}': line {prev.start_line} and line {e.start_line}. "
                f"Use stable IDs to disambiguate."
            )
        seen[e.key] = e

    return entries


def load_catalog(path: Path) -> List[CatalogEntry]:
    return parse_catalog(path.read_text(encoding="utf-8"))


def index_catalog(entries: List[CatalogEntry]) -> Dict[str, CatalogEntry]:
    return {e.key: e for e in entries}


def find_entry(entries: List[CatalogEntry], key_or_title: str) -> Optional[CatalogEntry]:
    """
    Lookup priority:
    1) exact key match (stable ID)
    2) exact title match (case-insensitive)
    3) derived-key match from title
    """
    q = key_or_title.strip()
    if not q:
        return None

    by_key = index_catalog(entries)
    if q in by_key:
        return by_key[q]

    # title case-insensitive
    q_lower = q.lower()
    for e in entries:
        if e.title.lower() == q_lower:
            return e

    derived = _derive_key_from_title(q)
    return by_key.get(derived)


def list_entries(path: Path) -> List[Tuple[str, str]]:
    entries = load_catalog(path)
    return [(e.key, e.title) for e in entries]


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(prog="prompt_catalog.py")
    p.add_argument("catalog", type=str, help="Path to prompts/template_prompts.md")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_list = sub.add_parser("list", help="List prompt keys and titles")
    sp_get = sub.add_parser("get", help="Print prompt body by key or title")
    sp_get.add_argument("name", type=str, help="Stable key or exact title")

    args = p.parse_args()
    catalog_path = Path(args.catalog).expanduser().resolve()
    entries = load_catalog(catalog_path)

    if args.cmd == "list":
        for k, t in [(e.key, e.title) for e in entries]:
            print(f"{k}\t{t}")
        return 0

    if args.cmd == "get":
        e = find_entry(entries, args.name)
        if not e:
            print(f"ERROR: prompt not found: {args.name}")
            return 2
        print(e.body)
        return 0

    raise ValueError(f"Unknown cmd: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
