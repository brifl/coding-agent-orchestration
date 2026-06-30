#!/usr/bin/env python3
"""
vibe_get_prompt.py

Convenience wrapper around prompt_catalog.py for the Codex vibe-prompts skill.
Prints a prompt body by stable ID or title.

Usage:
  python3 scripts/vibe_get_prompt.py resources/template_prompts.md prompt.stage_design
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    # Installed skills generate prompt_catalog.py into this same scripts folder.
    from prompt_catalog import find_entry, load_catalog  # type: ignore
except ModuleNotFoundError as exc:
    if exc.name != "prompt_catalog":
        raise
    source_tools = Path(__file__).resolve().parents[4] / "tools"
    if str(source_tools) not in sys.path:
        sys.path.insert(0, str(source_tools))
    from prompt_catalog import find_entry, load_catalog  # type: ignore


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python3 scripts/vibe_get_prompt.py <catalog_path> <prompt_id_or_title>", file=sys.stderr)
        return 2

    catalog_path = Path(argv[1]).expanduser().resolve()
    query = argv[2].strip()
    if not catalog_path.exists():
        print(f"ERROR: catalog not found: {catalog_path}", file=sys.stderr)
        return 2

    entries = load_catalog(catalog_path)
    e = find_entry(entries, query)
    if not e:
        print(f"ERROR: prompt not found: {query}", file=sys.stderr)
        print("Hint: list available prompts with:", file=sys.stderr)
        print("  python3 scripts/prompt_catalog.py resources/template_prompts.md list", file=sys.stderr)
        return 2

    print(e.body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
