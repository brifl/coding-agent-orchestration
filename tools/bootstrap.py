#!/usr/bin/env python3
"""
bootstrap.py

Repo bootstrapper for the coding-agent-orchestration kit.

Commands:
  init-repo <path>
    - Ensures <path> exists and is a directory.
    - Creates <path>/.vibe/ and installs STATE/PLAN/HISTORY templates (only if missing).
    - Adds ".vibe/" to <path>/.gitignore (idempotent).
    - Installs a baseline <path>/AGENTS.md (only if missing).
    - Optionally installs <path>/VIBE.md (only if missing) if a template exists.

  install-skills --global --agent <agent_name>
    - Installs/updates skills for the specified agent into ~/.<agent_name>/skills
    - Syncs prompts/template_prompts.md into the vibe-prompts skill resources.
    - Copies supporting scripts (agentctl.py, prompt_catalog.py) into skill scripts as needed.

Design:
  - Safe, idempotent operations.
  - Never overwrites existing repo-specific files by default.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable


def _repo_root_from_this_file() -> Path:
    # tools/bootstrap.py -> <repo_root>/tools/bootstrap.py
    return Path(__file__).resolve().parents[1]


def _template_path(repo_root: Path, relative: str) -> Path:
    return repo_root / relative


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _copy_if_missing(src: Path, dst: Path) -> bool:
    """
    Returns True if created, False if skipped (already exists).
    """
    if dst.exists():
        return False
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")
    _write_text(dst, _read_text(src))
    return True


def _ensure_gitignore_contains(repo_path: Path, lines: Iterable[str]) -> bool:
    """
    Ensure each line exists (exact match) in .gitignore.
    Returns True if modified, False otherwise.
    """
    gi = repo_path / ".gitignore"
    existing: list[str] = []
    if gi.exists():
        existing = _read_text(gi).splitlines()

    normalized_existing = set(existing)
    to_add = [ln for ln in lines if ln not in normalized_existing]

    if not to_add:
        return False

    new_lines = existing[:]
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")  # blank line separator

    new_lines.extend(to_add)
    _write_text(gi, "\n".join(new_lines).rstrip("\n") + "\n")
    return True


def init_repo(target_repo: Path, skillset: str | None = None) -> int:
    repo_root = _repo_root_from_this_file()

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo path does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"Target repo path is not a directory: {target_repo}")

    # 1) .vibe folder + templates (never overwrite)
    vibe_dir = target_repo / ".vibe"
    vibe_dir.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []

    for name in ("STATE.md", "PLAN.md", "HISTORY.md"):
        src = _template_path(repo_root, f"templates/vibe_folder/{name}")
        dst = vibe_dir / name
        (created if _copy_if_missing(src, dst) else skipped).append(str(dst))

    # 2) .gitignore contains .vibe/
    gi_modified = _ensure_gitignore_contains(target_repo, [".vibe/"])

    # 3) baseline AGENTS.md at repo root (never overwrite)
    agents_src = _template_path(repo_root, "templates/repo_root/AGENTS.md")
    agents_dst = target_repo / "AGENTS.md"
    if _copy_if_missing(agents_src, agents_dst):
        created.append(str(agents_dst))
    else:
        skipped.append(str(agents_dst))

    # 4) optional VIBE.md pointer doc (never overwrite)
    vibe_md_src = _template_path(repo_root, "templates/repo_root/VIBE.md")
    vibe_md_dst = target_repo / "VIBE.md"
    if vibe_md_src.exists():
        if _copy_if_missing(vibe_md_src, vibe_md_dst):
            created.append(str(vibe_md_dst))
        else:
            skipped.append(str(vibe_md_dst))

    # 5) Optional skillset config (never overwrite)
    if skillset:
        config_path = vibe_dir / "config.json"
        if config_path.exists():
            skipped.append(str(config_path))
        else:
            config_payload = {
                "name": skillset,
                "skill_folders": [],
                "prompt_catalogs": [],
            }
            _write_text(config_path, json.dumps(config_payload, indent=2) + "\n")
            created.append(str(config_path))

    # Summary
    print("init-repo summary")
    print(f"- Repo: {target_repo}")
    print(f"- .vibe dir: {vibe_dir}")
    print(f"- .gitignore updated: {'yes' if gi_modified else 'no'}")
    if created:
        print("- Created:")
        for p in created:
            print(f"  - {p}")
    if skipped:
        print("- Skipped (already exists):")
        for p in skipped:
            print(f"  - {p}")

    return 0


def _default_agent_global_dir(agent: str) -> Path:
    """
    Agent global skills directory. Default: ~/.<agent>/skills

    Note: Some installations use AGENT_HOME. If set, use $AGENT_HOME/skills.
    """
    agent_home = os.environ.get("AGENT_HOME")
    if agent_home:
        return Path(agent_home).expanduser().resolve() / "skills"
    return Path.home() / f".{agent}" / "skills"


def _copy_file(src: Path, dst: Path, *, force: bool = False, preserve_mtime: bool = True) -> bool:
    """
    Copy file src -> dst.
    Returns True if copied/updated, False if skipped.
    """
    if not src.exists():
        raise FileNotFoundError(f"Missing source file: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() and not force:
        # Skip if destination is newer or same mtime
        try:
            if dst.stat().st_mtime >= src.stat().st_mtime:
                return False
        except OSError:
            pass

    shutil.copy2(src, dst) if preserve_mtime else shutil.copyfile(src, dst)
    return True


def _sync_dir(src_dir: Path, dst_dir: Path, *, force: bool = False) -> list[str]:
    """
    Sync a directory recursively (copy files). Returns list of updated files (dst paths).
    Does not delete extra files in dst.
    """
    updated: list[str] = []
    if not src_dir.exists():
        raise FileNotFoundError(f"Missing source directory: {src_dir}")

    for src in src_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel
        if _copy_file(src, dst, force=force):
            updated.append(str(dst))
    return updated


def install_skills_agent_global(agent: str, force: bool) -> int:
    repo_root = _repo_root_from_this_file()
    dst_root = _default_agent_global_dir(agent)
    dst_root.mkdir(parents=True, exist_ok=True)

    # Generic skills are in skills/
    src_skills_root = repo_root / "skills"

    # Expected skill folders (we install only these by name)
    skill_names = ["vibe-prompts", "vibe-loop"]

    updated: list[str] = []
    skipped: list[str] = []

    # 1) Sync skill folders
    for name in skill_names:
        src_dir = src_skills_root / name
        dst_dir = dst_root / name
        if not src_dir.exists():
            raise FileNotFoundError(f"Skill folder missing: {src_dir}")
        u = _sync_dir(src_dir, dst_dir, force=force)
        if u:
            updated.extend(u)
        else:
            skipped.append(str(dst_dir))

    # 2) Force-refresh runtime scripts every install (prevents stale behavior)
    updated.extend(
        _sync_dir(
            src_skills_root / "vibe-prompts" / "scripts",
            dst_root / "vibe-prompts" / "scripts",
            force=True,
        )
    )
    updated.extend(
        _sync_dir(
            src_skills_root / "vibe-loop" / "scripts",
            dst_root / "vibe-loop" / "scripts",
            force=True,
        )
    )

    # 3) Canonical catalog location
    canonical_catalog = repo_root / "prompts" / "template_prompts.md"
    if not canonical_catalog.exists():
        raise FileNotFoundError(f"Canonical catalog missing: {canonical_catalog}")

    # 4) Validate the catalog BEFORE installing it (no package imports; use subprocess)
    import subprocess

    p = subprocess.run(
        [sys.executable, str(repo_root / "tools" / "prompt_catalog.py"), str(canonical_catalog), "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"Prompt catalog validation failed:\n{p.stderr or p.stdout}")

    # 5) Sync catalog into installed vibe-prompts resources (always refresh)
    dst_catalog = dst_root / "vibe-prompts" / "resources" / "template_prompts.md"
    if _copy_file(canonical_catalog, dst_catalog, force=True):
        updated.append(str(dst_catalog))

    # 6) Ensure key helper scripts are present inside skills (force refresh)
    helper_pairs = [
        (repo_root / "tools" / "agentctl.py", dst_root / "vibe-loop" / "scripts" / "agentctl.py"),
        (repo_root / "tools" / "prompt_catalog.py", dst_root / "vibe-prompts" / "scripts" / "prompt_catalog.py"),
    ]
    for src, dst in helper_pairs:
        if _copy_file(src, dst, force=True):
            updated.append(str(dst))

    print(f"install-skills summary ({agent} global)")
    print(f"- Destination: {dst_root}")
    print(f"- Skills: {', '.join(skill_names)}")
    if updated:
        print("- Updated:")
        for pth in updated:
            print(f"  - {pth}")
    if skipped:
        print("- No changes:")
        for pth in skipped:
            print(f"  - {pth}")

    return 0


def install_skills_agent_repo(agent: str, target_repo: Path, force: bool) -> int:
    repo_root = _repo_root_from_this_file()
    src_skills_root = repo_root / "skills" / "repo"

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo path does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"Target repo path is not a directory: {target_repo}")

    vibe_dir = target_repo / ".vibe"
    if not vibe_dir.exists():
        raise FileNotFoundError(f"Missing .vibe directory in target repo: {vibe_dir}")

    if not src_skills_root.exists():
        raise FileNotFoundError(f"Repo-local skills folder missing: {src_skills_root}")

    dst_root = vibe_dir / "skills"
    dst_root.mkdir(parents=True, exist_ok=True)

    updated: list[str] = []
    skipped: list[str] = []
    skill_names: list[str] = []

    for src_dir in sorted(p for p in src_skills_root.iterdir() if p.is_dir()):
        skill_names.append(src_dir.name)
        dst_dir = dst_root / src_dir.name
        u = _sync_dir(src_dir, dst_dir, force=force)
        if u:
            updated.extend(u)
        else:
            skipped.append(str(dst_dir))

    if not skill_names:
        raise RuntimeError(f"No repo-local skills found in: {src_skills_root}")

    print(f"install-skills summary ({agent} repo-local)")
    print(f"- Repo: {target_repo}")
    print(f"- Destination: {dst_root}")
    print(f"- Skills: {', '.join(skill_names)}")
    if updated:
        print("- Updated:")
        for pth in updated:
            print(f"  - {pth}")
    if skipped:
        print("- No changes:")
        for pth in skipped:
            print(f"  - {pth}")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bootstrap.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    initp = sub.add_parser("init-repo", help="Bootstrap a target repo with AGENTS.md and .vibe templates")
    initp.add_argument("path", type=str, help="Path to the target repo root")
    initp.add_argument("--skillset", type=str, help="Optional skillset name to seed .vibe/config.json")

    isp = sub.add_parser("install-skills", help="Install skills for a given agent/tool")
    isp.add_argument("--global", dest="global_install", action="store_true", help="Install to user/global location")
    isp.add_argument("--repo", dest="repo_install", action="store_true", help="Install into .vibe/skills in the repo")
    isp.add_argument("--agent", choices=("codex", "gemini"), required=True, help="Which agent to install for")
    isp.add_argument("--force", action="store_true", help="Force overwrite of SKILL.md and other files")
    return p


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "init-repo":
            return init_repo(Path(args.path).expanduser().resolve(), skillset=args.skillset)

        if args.cmd == "install-skills":
            if args.global_install == args.repo_install:
                raise ValueError("Choose exactly one of --global or --repo for install-skills.")
            
            if args.global_install:
                return install_skills_agent_global(agent=args.agent, force=args.force)
            return install_skills_agent_repo(agent=args.agent, target_repo=Path.cwd().resolve(), force=args.force)

        raise ValueError(f"Unknown command: {args.cmd}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
