#!/usr/bin/env python3
"""
vibe_next_and_print.py

Compute the recommended next prompt for a target repo (via agentctl.py),
then print the corresponding prompt body from the prompt catalog.

This is intentionally deterministic:
- agentctl decides the next prompt id
- prompt catalog prints the exact body
- no LLM judgment required

Usage (from inside a target repo):
  python3 ~/.codex/skills/vibe-loop/scripts/vibe_next_and_print.py \
    --repo-root . \
    --catalog ~/.codex/skills/vibe-prompts/resources/template_prompts.md

Tip: add --format json to see the decision payload.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# These files are expected to exist within the installed skill folder:
# - agentctl.py in the same scripts/ directory
# - prompt_catalog.py in the vibe-prompts skill; we call it via subprocess for isolation.


def _run_agentctl(repo_root: Path) -> dict:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "agentctl.py"),
        "--repo-root",
        str(repo_root),
        "--format",
        "json",
        "next",
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"agentctl failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    return json.loads(p.stdout)


def _print_prompt(catalog: Path, prompt_id: str) -> None:
    # Use vibe-prompts' prompt_catalog.py directly (it prints the body).
    # We do not import across skill folders to keep installs simple.
    cmd = [
        sys.executable,
        str(Path.home() / ".codex" / "skills" / "vibe-prompts" / "scripts" / "prompt_catalog.py"),
        str(catalog),
        "get",
        prompt_id,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"prompt_catalog get failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    sys.stdout.write(p.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(prog="vibe_next_and_print.py")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: .)")
    ap.add_argument(
        "--catalog",
        default=str(Path.home() / ".codex" / "skills" / "vibe-prompts" / "resources" / "template_prompts.md"),
        help="Path to the prompt catalog to use (default: global vibe-prompts catalog).",
    )
    ap.add_argument(
        "--show-decision",
        action="store_true",
        help="Print the decision JSON to stderr before printing the prompt body.",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    catalog = Path(args.catalog).expanduser().resolve()

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2
    if not catalog.exists():
        print(f"ERROR: catalog not found: {catalog}", file=sys.stderr)
        return 2

    decision = _run_agentctl(repo_root)
    prompt_id = decision.get("recommended_prompt_id")
    if not prompt_id:
        print(f"ERROR: agentctl decision missing recommended_prompt_id: {decision}", file=sys.stderr)
        return 2

    if args.show_decision:
        print(json.dumps(decision, indent=2, sort_keys=True), file=sys.stderr)

    _print_prompt(catalog, prompt_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
