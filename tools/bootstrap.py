#!/usr/bin/env python3
"""
bootstrap.py

Repo bootstrapper for the coding-agent-orchestration kit.

Command:
  init-repo <path>
    - Ensures <path> exists and is a directory.
    - Creates <path>/.vibe/ and installs STATE/PLAN/HISTORY templates (only if missing).
    - Adds ".vibe/" to <path>/.gitignore (idempotent).
    - Installs a baseline <path>/AGENTS.md (only if missing).
    - Optionally installs <path>/VIBE.md (only if missing) if a template exists.

Design:
  - Safe, idempotent operations.
  - Never overwrites existing repo-specific files by default.
"""

from __future__ import annotations

import argparse
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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bootstrap.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    initp = sub.add_parser("init-repo", help="Bootstrap a target repo with AGENTS.md and .vibe templates")
    initp.add_argument("path", type=str, help="Path to the target repo root")

    return p


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "init-repo":
            return init_repo(Path(args.path).expanduser().resolve())
        raise ValueError(f"Unknown command: {args.cmd}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
