#!/usr/bin/env python3
"""
vibe_get_prompt.py

Convenience wrapper around prompt_catalog.py for the Codex vibe-prompts skill.
Prints a prompt body by stable ID or title.

Usage:
  python3 scripts/vibe_get_prompt.py resources/template_prompts.md prompt.onboarding
"""

from __future__ import annotations

import sys
from pathlib import Path

# prompt_catalog.py is expected to be in the same scripts/ folder after install
from prompt_catalog import load_catalog, find_entry  # type: ignore


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
