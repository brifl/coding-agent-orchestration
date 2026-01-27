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

  install-skills --global codex
    - Installs/updates Codex skills into ~/.codex/skills
    - Syncs prompts/template_prompts.md into the vibe-prompts skill resources.
    - Copies supporting scripts (agentctl.py, prompt_catalog.py) into skill scripts as needed.

Design:
  - Safe, idempotent operations.
  - Never overwrites existing repo-specific files by default.
"""

from __future__ import annotations

import argparse
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


def init_repo(target_repo: Path) -> int:
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


def _default_codex_global_dir() -> Path:
    """
    Codex global skills directory. Default: ~/.codex/skills

    Note: Some installations use CODEX_HOME. If set, use $CODEX_HOME/skills.
    """
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser().resolve() / "skills"
    return Path.home() / ".codex" / "skills"


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


def install_skills_codex_global(force: bool) -> int:
    repo_root = _repo_root_from_this_file()
    dst_root = _default_codex_global_dir()
    dst_root.mkdir(parents=True, exist_ok=True)

    # Skills are authored in skills/codex/* in this repo.
    src_skills_root = repo_root / "skills" / "codex"

    # Expected skill folders (we install only these by name)
    skill_names = ["vibe-prompts", "vibe-loop"]

    updated: list[str] = []
    skipped: list[str] = []

    # 1) Sync skill folders (excluding prompt catalog sync which we do explicitly)
    for name in skill_names:
        src_dir = src_skills_root / name
        dst_dir = dst_root / name
        if not src_dir.exists():
            raise FileNotFoundError(f"Skill folder missing: {src_dir}")
        # Copy everything under the skill folder (SKILL.md, scripts, etc.)
        # Resource sync is handled below for vibe-prompts to ensure it matches prompts/template_prompts.md
        u = _sync_dir(src_dir, dst_dir, force=force)
        if u:
            updated.extend(u)
        else:
            skipped.append(str(dst_dir))

    # 2) Ensure vibe-prompts/resources/template_prompts.md is synced from canonical prompts/template_prompts.md
    canonical_catalog = repo_root / "prompts" / "template_prompts.md"
    if not canonical_catalog.exists():
        raise FileNotFoundError(f"Canonical catalog missing: {canonical_catalog}")

    dst_catalog = dst_root / "vibe-prompts" / "resources" / "template_prompts.md"
    if _copy_file(canonical_catalog, dst_catalog, force=True):  # always refresh
        updated.append(str(dst_catalog))

    # 3) Ensure key helper scripts are present inside skills (so skills don't depend on your repo layout)
    # (These files can be referenced by SKILL.md later.)
    helper_pairs = [
        (repo_root / "tools" / "agentctl.py", dst_root / "vibe-loop" / "scripts" / "agentctl.py"),
        (repo_root / "tools" / "prompt_catalog.py", dst_root / "vibe-prompts" / "scripts" / "prompt_catalog.py"),
    ]
    for src, dst in helper_pairs:
        if _copy_file(src, dst, force=True):
            updated.append(str(dst))

    print("install-skills summary (codex global)")
    print(f"- Destination: {dst_root}")
    print(f"- Skills: {', '.join(skill_names)}")
    if updated:
        print("- Updated:")
        for p in updated:
            print(f"  - {p}")
    if skipped:
        print("- No changes:")
        for p in skipped:
            print(f"  - {p}")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bootstrap.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    initp = sub.add_parser("init-repo", help="Bootstrap a target repo with AGENTS.md and .vibe templates")
    initp.add_argument("path", type=str, help="Path to the target repo root")

    isp = sub.add_parser("install-skills", help="Install skills for a given agent/tool")
    isp.add_argument("--global", dest="global_install", action="store_true", help="Install to user/global location")
    isp.add_argument("--agent", choices=("codex",), required=True, help="Which agent to install for (codex)")
    isp.add_argument("--force", action="store_true", help="Force overwrite of SKILL.md and other files")
    return p


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "init-repo":
            return init_repo(Path(args.path).expanduser().resolve())

        if args.cmd == "install-skills":
            if not args.global_install:
                raise ValueError("Only --global installs are supported currently.")
            if args.agent == "codex":
                return install_skills_codex_global(force=args.force)

        raise ValueError(f"Unknown command: {args.cmd}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
