#!/usr/bin/env python3
"""
continuous_documentation.py

Compatibility wrapper that runs vibe-run with the continuous-documentation workflow.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_local_vibe_run(repo_root: Path) -> Path:
    return repo_root / ".codex" / "skills" / "vibe-run" / "scripts" / "vibe_run.py"


def _sibling_vibe_run() -> Path:
    # .../.codex/skills/continuous-documentation/scripts/continuous_documentation.py
    # -> .../.codex/skills/vibe-run/scripts/vibe_run.py
    return Path(__file__).resolve().parents[2] / "vibe-run" / "scripts" / "vibe_run.py"


def _find_vibe_run_script(repo_root: Path) -> Path | None:
    candidates = [_sibling_vibe_run(), _repo_local_vibe_run(repo_root)]
    return next((path for path in candidates if path.exists()), None)


def main() -> int:
    ap = argparse.ArgumentParser(prog="continuous_documentation.py")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: current directory)")
    ap.add_argument("--catalog", default="", help="Optional path to template_prompts.md")
    ap.add_argument("--max-loops", type=int, default=0, help="Loop cap for safety (0 = until stop)")
    ap.add_argument("--show-decision", action="store_true", help="Print agentctl decision JSON to stderr each loop")
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not pause between loops. Use only when another process updates state.",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    vibe_run_script = _find_vibe_run_script(repo_root)
    if vibe_run_script is None:
        print("ERROR: could not locate vibe-run/scripts/vibe_run.py", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        str(vibe_run_script),
        "--repo-root",
        str(repo_root),
        "--workflow",
        "continuous-documentation",
    ]
    if args.catalog:
        cmd.extend(["--catalog", str(Path(args.catalog).expanduser().resolve())])
    if args.max_loops > 0:
        cmd.extend(["--max-loops", str(args.max_loops)])
    if args.show_decision:
        cmd.append("--show-decision")
    if args.non_interactive:
        cmd.append("--non-interactive")

    result = subprocess.run(cmd)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
