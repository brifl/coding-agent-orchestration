#!/usr/bin/env python3
"""
vibe_next_and_print.py

Compute the recommended next prompt for a target repo (via agentctl.py),
then print the corresponding prompt body from the prompt catalog.

Deterministic:
- agentctl decides the next prompt id
- prompt catalog prints the exact body

Robust install:
- Locates the skills root from this script's path.
- Locates vibe-prompts as a sibling skill folder.
- Also supports CODEX_HOME if needed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _skills_root_from_this_script() -> Path:
    """
    .../skills/vibe-loop/scripts/vibe_next_and_print.py
    -> .../skills
    """
    p = Path(__file__).resolve()
    # parents: [0]=scripts, [1]=vibe-loop, [2]=skills
    return p.parents[2]


def _codex_skills_root_env_fallback() -> Path | None:
    """
    If CODEX_HOME is set, Codex uses $CODEX_HOME/skills.
    """
    codex_home = os.environ.get("CODEX_HOME")
    if not codex_home:
        return None
    return Path(codex_home).expanduser().resolve() / "skills"


def _looks_like_skills_root(root: Path) -> bool:
    """
    Simple heuristics to ensure the candidate folder contains the required skills.
    """
    return (root / "vibe-loop").exists() and (root / "vibe-prompts").exists()


def _locate_skills_root() -> Path:
    """
    Prefer the CODEX_HOME-aware install root but fall back to whichever root contains the skills layout.
    """
    candidates: list[Path] = []
    env_root = _codex_skills_root_env_fallback()
    if env_root and env_root.exists():
        candidates.append(env_root)

    script_root = _skills_root_from_this_script()
    candidates.append(script_root)

    for candidate in candidates:
        if _looks_like_skills_root(candidate):
            return candidate

    # Nothing matched the heuristic; fall back to the script-derived location.
    return script_root


def _run_agentctl(repo_root: Path, agentctl_path: Path) -> dict:
    cmd = [
        sys.executable,
        str(agentctl_path),
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


def _print_prompt(prompt_catalog_path: Path, catalog_path: Path, prompt_id: str) -> None:
    cmd = [
        sys.executable,
        str(prompt_catalog_path),
        str(catalog_path),
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
        default="",
        help="Optional path to template_prompts.md. If omitted, uses sibling vibe-prompts resources.",
    )
    ap.add_argument(
        "--show-decision",
        action="store_true",
        help="Print the decision JSON to stderr before printing the prompt body.",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    # Locate skill install layout (prefers CODEX_HOME when present).
    skills_root = _locate_skills_root()

    agentctl_path = skills_root / "vibe-loop" / "scripts" / "agentctl.py"
    if not agentctl_path.exists():
        print(f"ERROR: agentctl.py not found at: {agentctl_path}", file=sys.stderr)
        return 2

    prompt_catalog_path = skills_root / "vibe-prompts" / "scripts" / "prompt_catalog.py"
    if not prompt_catalog_path.exists():
        print(f"ERROR: prompt_catalog.py not found at: {prompt_catalog_path}", file=sys.stderr)
        return 2

    if args.catalog:
        catalog_path = Path(args.catalog).expanduser().resolve()
    else:
        catalog_path = skills_root / "vibe-prompts" / "resources" / "template_prompts.md"

    if not catalog_path.exists():
        print(f"ERROR: catalog not found at: {catalog_path}", file=sys.stderr)
        print("Hint: reinstall skills to refresh resources:", file=sys.stderr)
        print("  python3 tools/bootstrap.py install-skills --global --agent codex", file=sys.stderr)
        return 2

    decision = _run_agentctl(repo_root, agentctl_path)
    prompt_id = decision.get("recommended_prompt_id")
    if not prompt_id:
        print(f"ERROR: agentctl decision missing recommended_prompt_id: {decision}", file=sys.stderr)
        return 2

    if args.show_decision:
        print(json.dumps(decision, indent=2, sort_keys=True), file=sys.stderr)

    _print_prompt(prompt_catalog_path, catalog_path, prompt_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
