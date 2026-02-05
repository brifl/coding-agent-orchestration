#!/usr/bin/env python3
"""
vibe_one_loop.py

Compatibility wrapper for one-shot loop execution.
Delegates to vibe-loop's vibe_next_and_print.py.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_local_loop_script(repo_root: Path) -> Path:
    return repo_root / ".codex" / "skills" / "vibe-loop" / "scripts" / "vibe_next_and_print.py"


def _sibling_loop_script() -> Path:
    # .../.codex/skills/vibe-one-loop/scripts/vibe_one_loop.py -> .../.codex/skills/vibe-loop/scripts/...
    return Path(__file__).resolve().parents[2] / "vibe-loop" / "scripts" / "vibe_next_and_print.py"


def _find_loop_script(repo_root: Path) -> Path | None:
    candidates = [_sibling_loop_script(), _repo_local_loop_script(repo_root)]
    return next((p for p in candidates if p.exists()), None)


def main() -> int:
    ap = argparse.ArgumentParser(prog="vibe_one_loop.py")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: current directory)")
    ap.add_argument("--catalog", default="", help="Optional path to template_prompts.md")
    ap.add_argument("--show-decision", action="store_true", help="Print decision JSON to stderr")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    loop_script = _find_loop_script(repo_root)
    if loop_script is None:
        print("ERROR: could not locate vibe-loop/scripts/vibe_next_and_print.py", file=sys.stderr)
        return 2

    cmd = [sys.executable, str(loop_script), "--repo-root", str(repo_root)]
    if args.catalog:
        cmd.extend(["--catalog", str(Path(args.catalog).expanduser().resolve())])
    if args.show_decision:
        cmd.append("--show-decision")

    p = subprocess.run(cmd)
    return int(p.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
