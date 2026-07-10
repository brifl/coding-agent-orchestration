#!/usr/bin/env python3
"""
vibe_next_and_print.py

Compute the recommended next prompt for a target repo (via agentctl.py),
then print the corresponding prompt body from the prompt catalog.

Deterministic:
- agentctl decides the next prompt id
- prompt catalog prints the exact body

Robust install:
- Uses the managed skills bundle that contains this script.
- Locates vibe-prompts as a sibling skill folder.
- Falls back to CODEX_HOME (or AGENT_HOME) only for incomplete legacy copies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


_WSL_UNC_RE = re.compile(r"^//wsl(?:\.localhost)?/[^/]+/(.+)$", re.IGNORECASE)
_WIN_DRIVE_RE = re.compile(r"^([A-Za-z]):/(.+)$")


def _normalize_home_path(raw: str) -> Path:
    value = raw.strip().strip('"').strip("'")
    if os.name != "nt":
        value = value.replace("\\", "/")
        unc_match = _WSL_UNC_RE.match(value)
        if unc_match:
            value = "/" + unc_match.group(1).lstrip("/")
        else:
            drive_match = _WIN_DRIVE_RE.match(value)
            if drive_match:
                drive = drive_match.group(1).lower()
                tail = drive_match.group(2)
                value = f"/mnt/{drive}/{tail}"
    return Path(value).expanduser().resolve()


def _skills_root_from_this_script() -> Path:
    """
    .../.codex/skills/vibe-loop/scripts/vibe_next_and_print.py
    -> .../.codex/skills
    """
    p = Path(__file__).resolve()
    # parents: [0]=scripts, [1]=vibe-loop, [2]=skills
    return p.parents[2]


def _skills_root_env_fallback() -> Path | None:
    """
    If CODEX_HOME or AGENT_HOME is set, use $CODEX_HOME/skills or $AGENT_HOME/skills.
    """
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return _normalize_home_path(codex_home) / "skills"
    agent_home = os.environ.get("AGENT_HOME")
    if not agent_home:
        return None
    return _normalize_home_path(agent_home) / "skills"


def _looks_like_skills_root(root: Path) -> bool:
    """
    Simple heuristics to ensure the candidate folder contains the required skills.
    """
    return any(root.glob("**/vibe-loop")) and any(root.glob("**/vibe-prompts"))


def _locate_skills_root() -> Path:
    """
    Prefer this wrapper's managed bundle; use an environment install only as a legacy fallback.
    """
    script_root = _skills_root_from_this_script()
    candidates = [script_root]
    env_root = _skills_root_env_fallback()
    if env_root and env_root.exists():
        candidates.append(env_root)

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
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if p.returncode != 0:
        raise RuntimeError(f"prompt_catalog get failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    sys.stdout.write(p.stdout)


def _default_catalog_candidates(repo_root: Path, skills_root: Path) -> list[Path]:
    return [
        skills_root / "vibe-prompts" / "resources" / "template_prompts.md",
        repo_root / ".codex" / "skills" / "vibe-prompts" / "resources" / "template_prompts.md",
        repo_root / "skills" / "vibe-prompts" / "resources" / "template_prompts.md",
        repo_root / "prompts" / "template_prompts.md",
    ]


def _resolve_tool_paths(repo_root: Path, skills_root: Path) -> tuple[Path | None, Path | None]:
    installed_tools_dir = skills_root / "vibe-loop" / "scripts"
    installed_prompt_dir = skills_root / "vibe-prompts" / "scripts"
    agentctl_candidates = [
        installed_tools_dir / "agentctl.py",
        repo_root / "tools" / "agentctl.py",
    ]
    prompt_candidates = [
        installed_prompt_dir / "prompt_catalog.py",
        repo_root / "tools" / "prompt_catalog.py",
    ]
    return (
        next((path for path in agentctl_candidates if path.exists()), None),
        next((path for path in prompt_candidates if path.exists()), None),
    )


def _with_explicit_catalog_provenance(decision: dict, catalog_path: Path) -> dict:
    updated = dict(decision)
    try:
        digest = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    except OSError:
        digest = None
    updated.update(
        {
            "prompt_catalog_path": str(catalog_path),
            "prompt_catalog_sha256": digest,
            "prompt_catalog_mode": "explicit",
        }
    )
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(prog="vibe_next_and_print.py")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: .)")
    ap.add_argument(
        "--catalog",
        default="",
        help="Optional explicit template_prompts.md override. If omitted, uses the active runtime's catalog.",
    )
    ap.add_argument(
        "--show-decision",
        action="store_true",
        help="Print the decision JSON to stderr before printing the prompt body.",
    )
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    # Locate the managed bundle that owns this wrapper.
    skills_root = _locate_skills_root()
    agentctl_path, prompt_catalog_path = _resolve_tool_paths(repo_root, skills_root)

    if agentctl_path is None:
        print("ERROR: agentctl.py not found in repo or skills tools.", file=sys.stderr)
        return 2

    if prompt_catalog_path is None:
        print("ERROR: prompt_catalog.py not found in repo or skills tools.", file=sys.stderr)
        return 2

    decision = _run_agentctl(repo_root, agentctl_path)
    if args.catalog:
        explicit_catalog = Path(args.catalog).expanduser().resolve()
        decision = _with_explicit_catalog_provenance(decision, explicit_catalog)
    prompt_id = decision.get("recommended_prompt_id")
    if not prompt_id:
        print(f"ERROR: agentctl decision missing recommended_prompt_id: {decision}", file=sys.stderr)
        return 2

    if args.show_decision:
        print(json.dumps(decision, indent=2, sort_keys=True), file=sys.stderr)

    if decision.get("requires_loop_result"):
        print(f"NOTICE: {decision.get('reason', 'LOOP_RESULT acknowledgement required.')}", file=sys.stderr)
        if decision.get("recommended_role") == "stop":
            return 2

    if args.catalog:
        catalog_path = Path(args.catalog).expanduser().resolve()
    elif decision.get("prompt_catalog_path"):
        catalog_path = Path(decision["prompt_catalog_path"]).expanduser().resolve()
    else:
        catalog_candidates = _default_catalog_candidates(repo_root, skills_root)
        catalog_path = next((path for path in catalog_candidates if path.exists()), catalog_candidates[0])

    if not catalog_path.exists():
        print(f"ERROR: catalog not found at: {catalog_path}", file=sys.stderr)
        print("Hint: reinstall skills to refresh resources:", file=sys.stderr)
        print("  python3 tools/bootstrap.py install-skills --global --agent <your_agent>", file=sys.stderr)
        return 2

    if decision.get("recommended_role") == "stop" or prompt_id == "stop":
        return 0

    _print_prompt(prompt_catalog_path, catalog_path, prompt_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
