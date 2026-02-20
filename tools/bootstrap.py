#!/usr/bin/env python3
"""
bootstrap.py

Repo bootstrapper for the coding-agent-orchestration kit.

Commands:
  init-repo <path>
    - Ensures <path> exists and is a directory.
    - Creates <path>/.vibe/ and installs STATE/PLAN/HISTORY templates (only if missing).
    - Adds ".vibe/" to <path>/.gitignore (idempotent).
    - Installs a baseline <path>/AGENTS.md (only if missing unless --overwrite).
    - Optionally installs <path>/VIBE.md (only if missing unless --overwrite) if a template exists.
    - Installs repo-local skills from the selected skillset into <path>/.codex/skills
      (defaults to "vibe-base", which includes continuous workflow runners).

  install-skills --global --agent <agent_name>
    - Installs/updates skills for the specified agent into ~/.codex/skills (Codex) or ~/.<agent>/skills
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
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

# Add parent dir to path to allow sibling imports
_tools_dir = Path(__file__).parent.resolve()
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from path_utils import normalize_home_path, resolve_codex_home
from resource_resolver import find_resource
from cli_error_utils import format_cli_error
from skillset_utils import find_skillset, load_skillset, parse_skillset_yaml  # noqa: F401

# All supported agents for bulk installation
ALL_AGENTS = ["codex", "claude", "gemini", "copilot"]


# Canonical doc templates for init-repo
CANONICAL_AGENTS_TEMPLATE = Path("templates/repo_root/AGENTS.md")
CANONICAL_VIBE_TEMPLATE = Path("templates/repo_root/VIBE.md")
DEFAULT_INIT_SKILLSET = "vibe-base"


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


def _copy_if_missing(src: Path, dst: Path, *, force: bool = False) -> str:
    """
    Returns one of: "created", "overwritten", "skipped".
    """
    existed = dst.exists()
    if existed and not force:
        return "skipped"
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return "overwritten" if existed else "created"


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


def init_repo(target_repo: Path, skillset: str | None = None, overwrite: bool = False) -> int:
    repo_root = _repo_root_from_this_file()

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo path does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"Target repo path is not a directory: {target_repo}")

    # 1) .vibe folder + templates
    vibe_dir = target_repo / ".vibe"
    vibe_dir.mkdir(parents=True, exist_ok=True)

    created = []
    overwritten = []
    skipped = []
    effective_skillset = (skillset or DEFAULT_INIT_SKILLSET).strip()
    if not effective_skillset:
        raise ValueError("Skillset name cannot be empty.")

    for name in ("STATE.md", "PLAN.md", "HISTORY.md"):
        src = _template_path(repo_root, f"templates/vibe_folder/{name}")
        dst = vibe_dir / name
        # Never overwrite workflow files - they contain important project state
        result = _copy_if_missing(src, dst, force=False)
        if result == "created":
            created.append(str(dst))
        else:
            skipped.append(str(dst))

    # 2) .gitignore contains .vibe/
    gi_modified = _ensure_gitignore_contains(target_repo, [".vibe/"])

    # 3) baseline AGENTS.md at repo root
    agents_src = _template_path(repo_root, str(CANONICAL_AGENTS_TEMPLATE))
    agents_dst = target_repo / "AGENTS.md"
    result = _copy_if_missing(agents_src, agents_dst, force=overwrite)
    if result == "created":
        created.append(str(agents_dst))
    elif result == "overwritten":
        overwritten.append(str(agents_dst))
    else:
        skipped.append(str(agents_dst))

    # 4) optional VIBE.md pointer doc
    vibe_md_src = _template_path(repo_root, str(CANONICAL_VIBE_TEMPLATE))
    vibe_md_dst = target_repo / "VIBE.md"
    if vibe_md_src.exists():
        result = _copy_if_missing(vibe_md_src, vibe_md_dst, force=overwrite)
        if result == "created":
            created.append(str(vibe_md_dst))
        elif result == "overwritten":
            overwritten.append(str(vibe_md_dst))
        else:
            skipped.append(str(vibe_md_dst))

    # 5) Optional skillset config (never overwrite)
    if skillset:
        config_path = vibe_dir / "config.json"
        if config_path.exists():
            skipped.append(str(config_path))
        else:
            config_payload = {
                "skillset": {"name": effective_skillset},
                "skill_folders": [],
                "prompt_catalogs": [],
            }
            _write_text(config_path, json.dumps(config_payload, indent=2) + "\n")
            created.append(str(config_path))

    # Auto-install skills from the selected set into .codex/skills.
    skill_defs = _resolve_skillset(repo_root, effective_skillset)
    dst_root = target_repo / ".codex" / "skills"
    dst_root.mkdir(parents=True, exist_ok=True)
    for skill in skill_defs:
        name = skill["name"]
        src_dir = repo_root / ".codex" / "skills" / name
        if not src_dir.exists():
            src_dir = repo_root / "skills" / name
        if not src_dir.exists():
            raise FileNotFoundError(f"Skill folder not found for '{name}'.")
        dst_dir = dst_root / name
        u = _sync_dir(src_dir, dst_dir, force=False)
        if u:
            created.extend(u)
        else:
            skipped.append(str(dst_dir))

    # Summary
    print("init-repo summary")
    print(f"- Repo: {target_repo}")
    print(f"- .vibe dir: {vibe_dir}")
    print(f"- .gitignore updated: {'yes' if gi_modified else 'no'}")
    print(f"- Skillset installed: {effective_skillset}")
    if created:
        print("- Created:")
        for p in created:
            print(f"  - {p}")
    if overwritten:
        print("- Overwritten:")
        for p in overwritten:
            print(f"  - {p}")
    if skipped:
        print("- Skipped (already exists):")
        for p in skipped:
            print(f"  - {p}")

    return 0


def _default_agent_global_dir(agent: str) -> Path:
    """
    Agent global skills directory. Default:
    - Codex: $CODEX_HOME/skills (fallback: ~/.codex/skills)
    - Others: ~/.<agent>/skills

    Note: Some non-Codex installations use AGENT_HOME. If set, use $AGENT_HOME/skills.
    """
    if agent == "codex":
        return resolve_codex_home() / "skills"

    agent_home = os.environ.get("AGENT_HOME")
    if agent_home:
        return normalize_home_path(agent_home) / "skills"
    return Path.home() / f".{agent}" / "skills"


def _resolve_skillset(repo_root: Path, name: str) -> list[dict[str, Any]]:
    visited: set[str] = set()
    resolving: set[str] = set()
    resolved: dict[str, str | None] = {}

    def load_set(set_name: str) -> dict[str, Any]:
        path = find_skillset(repo_root / "skillsets", set_name)
        if not path:
            raise FileNotFoundError(f"Skillset '{set_name}' not found.")
        data = load_skillset(path)
        if not data:
            raise ValueError(f"Failed to parse skillset: {path}")
        return data

    def visit_set(set_name: str) -> None:
        if set_name in resolving:
            raise ValueError(f"Circular skillset dependency detected: {set_name}")
        if set_name in visited:
            return
        resolving.add(set_name)
        data = load_set(set_name)
        for parent in data.get("extends", []):
            visit_set(str(parent))
        for skill in data.get("skills", []):
            skill_name = str(skill.get("name"))
            version = skill.get("version")
            if skill_name in resolved and version and resolved[skill_name] and resolved[skill_name] != version:
                raise ValueError(f"Version conflict for {skill_name}: {resolved[skill_name]} vs {version}")
            resolved[skill_name] = resolved.get(skill_name) or version
        visited.add(set_name)
        resolving.remove(set_name)

    visit_set(name)
    return [{"name": k, "version": v} for k, v in resolved.items()]


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

    # Expected skill folders (we install only these by name)
    skill_names = [
        "vibe-prompts",
        "vibe-loop",
        "vibe-one-loop",
        "vibe-run",
        "continuous-refactor",
        "continuous-test-generation",
        "continuous-documentation",
    ]

    updated: list[str] = []
    skipped: list[str] = []

    # 1) Install skill folders via skillctl
    for name in skill_names:
        cmd = [
            sys.executable,
            str(repo_root / "tools" / "skillctl.py"),
            "install",
            name,
            "--global",
            "--agent",
            agent,
        ]
        if force:
            cmd.append("--force")
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"skillctl install failed for '{name}':\n{p.stderr or p.stdout}")
        updated.append(str(dst_root / name))

    # 2) Force-refresh skill contents (including manifests) every install.
    for name in skill_names:
        src_dir = find_resource("skill", name, agent=agent)
        if src_dir is None:
            raise RuntimeError(f"Could not resolve installed source for skill '{name}'.")
        updated.extend(_sync_dir(src_dir, dst_root / name, force=True))

    # 3) Canonical catalog location
    canonical_catalog = repo_root / "prompts" / "template_prompts.md"
    if not canonical_catalog.exists():
        raise FileNotFoundError(f"Canonical catalog missing: {canonical_catalog}")

    # 4) Validate the catalog BEFORE installing it (no package imports; use subprocess)
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
        (repo_root / "tools" / "checkpoint_templates.py", dst_root / "vibe-loop" / "scripts" / "checkpoint_templates.py"),
        (repo_root / "tools" / "resource_resolver.py", dst_root / "vibe-loop" / "scripts" / "resource_resolver.py"),
        (repo_root / "tools" / "stage_ordering.py", dst_root / "vibe-loop" / "scripts" / "stage_ordering.py"),
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
    src_skills_root = repo_root / ".codex" / "skills"

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo path does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"Target repo path is not a directory: {target_repo}")

    if not src_skills_root.exists():
        raise FileNotFoundError(f"Repo-local skills folder missing: {src_skills_root}")

    dst_root = target_repo / ".codex" / "skills"
    dst_root.mkdir(parents=True, exist_ok=True)

    updated: list[str] = []
    skipped: list[str] = []
    skill_names: list[str] = []

    for src_dir in sorted(p for p in src_skills_root.iterdir() if p.is_dir()):
        skill_names.append(src_dir.name)
        dst_dir = dst_root / src_dir.name
        updated.extend(_sync_dir(src_dir, dst_dir, force=force))

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
    initp.add_argument(
        "--skillset",
        type=str,
        default=None,
        help=(
            "Skillset name to install into .codex/skills (default: vibe-base). "
            "When explicitly provided, also seeds .vibe/config.json if missing."
        ),
    )
    initp.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing AGENTS.md and VIBE.md (does NOT overwrite STATE.md, PLAN.md, or HISTORY.md)",
    )

    isp = sub.add_parser("install-skills", help="Install skills for a given agent/tool")
    isp.add_argument("--global", dest="global_install", action="store_true", help="Install to user/global location")
    isp.add_argument("--repo", dest="repo_install", action="store_true", help="Install into .codex/skills in the repo")
    isp.add_argument("--agent", choices=("all", "codex", "claude", "gemini", "copilot"), required=True, help="Which agent to install for (use 'all' to install for all agents)")
    isp.add_argument("--force", action="store_true", help="Force overwrite of SKILL.md and other files")
    return p


def _install_skills_all(global_install: bool, repo_install: bool, force: bool) -> int:
    """Install skills for all agents. Returns 0 if all succeeded, 1 if any failed."""
    errors: list[tuple[str, str]] = []
    
    for agent in ALL_AGENTS:
        print(f"\n{'='*60}")
        print(f"Installing skills for: {agent}")
        print(f"{'='*60}")
        try:
            if global_install:
                result = install_skills_agent_global(agent=agent, force=force)
            else:
                result = install_skills_agent_repo(agent=agent, target_repo=Path.cwd().resolve(), force=force)
            if result != 0:
                errors.append((agent, f"Return code: {result}"))
        except Exception as exc:
            errors.append((agent, format_cli_error(exc)))
    
    print(f"\n{'='*60}")
    print("Bulk installation complete")
    print(f"{'='*60}")
    
    if errors:
        print(f"\nFailed installations ({len(errors)}/{len(ALL_AGENTS)}):")
        for agent, error in errors:
            print(f"  - {agent}: {error}")
        return 1
    
    print(f"\nAll {len(ALL_AGENTS)} agents installed successfully.")
    return 0


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "init-repo":
            return init_repo(Path(args.path).expanduser().resolve(), skillset=args.skillset, overwrite=args.overwrite)

        if args.cmd == "install-skills":
            if args.global_install == args.repo_install:
                raise ValueError("Choose exactly one of --global or --repo for install-skills.")
            
            if args.agent == "all":
                return _install_skills_all(global_install=args.global_install, repo_install=args.repo_install, force=args.force)
            
            if args.global_install:
                return install_skills_agent_global(agent=args.agent, force=args.force)
            return install_skills_agent_repo(agent=args.agent, target_repo=Path.cwd().resolve(), force=args.force)

        raise ValueError(f"Unknown command: {args.cmd}")
    except Exception as exc:
        print(f"ERROR: {format_cli_error(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
