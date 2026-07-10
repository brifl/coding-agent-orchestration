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
- Fails closed when the sibling bundle is incomplete unless an override is explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def _skills_root_from_this_script() -> Path:
    """
    .../.codex/skills/vibe-loop/scripts/vibe_next_and_print.py
    -> .../.codex/skills
    """
    p = Path(__file__).resolve()
    # parents: [0]=scripts, [1]=vibe-loop, [2]=skills
    return p.parents[2]


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


def _resolve_tool_paths(skills_root: Path, runtime_tools_dir: str) -> tuple[Path, Path]:
    if runtime_tools_dir:
        tools_dir = Path(runtime_tools_dir).expanduser().resolve()
        source_label = f"explicit runtime tools directory {tools_dir}"
        agentctl_path = tools_dir / "agentctl.py"
        prompt_catalog_path = tools_dir / "prompt_catalog.py"
    else:
        source_label = f"managed Vibe bundle {skills_root}"
        agentctl_path = skills_root / "vibe-loop" / "scripts" / "agentctl.py"
        prompt_catalog_path = skills_root / "vibe-prompts" / "scripts" / "prompt_catalog.py"
    missing = [
        path.name
        for path in (agentctl_path, prompt_catalog_path)
        if not path.exists()
    ]
    if missing:
        raise RuntimeError(
            f"{source_label} is incomplete (missing: {', '.join(missing)}). "
            "Reinstall Vibe skills or pass --runtime-tools-dir as an explicit override."
        )
    return agentctl_path, prompt_catalog_path


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


def _with_explicit_runtime_provenance(decision: dict, runtime_path: Path) -> dict:
    updated = dict(decision)
    try:
        digest = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
    except OSError:
        digest = None
    updated.update(
        {
            "runtime_path": str(runtime_path),
            "runtime_sha256": digest,
            "runtime_mode": "explicit",
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
        "--runtime-tools-dir",
        default="",
        help="Explicit directory containing agentctl.py and prompt_catalog.py; managed sibling tools are the default.",
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

    skills_root = _skills_root_from_this_script()
    try:
        agentctl_path, prompt_catalog_path = _resolve_tool_paths(
            skills_root,
            args.runtime_tools_dir,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    decision = _run_agentctl(repo_root, agentctl_path)
    if args.catalog:
        explicit_catalog = Path(args.catalog).expanduser().resolve()
        decision = _with_explicit_catalog_provenance(decision, explicit_catalog)
    if args.runtime_tools_dir:
        decision = _with_explicit_runtime_provenance(decision, agentctl_path)
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
        catalog_path = skills_root / "vibe-prompts" / "resources" / "template_prompts.md"

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
