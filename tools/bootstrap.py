#!/usr/bin/env python3
"""
bootstrap.py

Repo bootstrapper for the coding-agent-orchestration kit.

Commands:
  <path>
    - Ensures <path> exists and is a directory.
    - Creates <path>/.vibe/ and installs STATE/PLAN/HISTORY templates (only if missing).
    - Adds ".vibe/" to <path>/.gitignore (idempotent).
    - Installs a baseline <path>/AGENTS.md (only if missing unless --overwrite).
    - Optionally installs <path>/VIBE.md (only if missing unless --overwrite) if a template exists.
    - Installs repo-local skills from the selected skillset into <path>/.codex/skills
      (defaults to "vibe-base", which includes continuous workflow runners).

  install-skills --global --agent <agent_name>
    - Installs/updates skills for the specified agent into ~/.codex/skills (Codex) or ~/.claude/skills (Claude Code)
    - Syncs the canonical prompt catalog into installed skill resource directories.
    - Copies supporting scripts (agentctl.py, prompt_catalog.py) into skill scripts as needed.

Design:
  - Safe, idempotent operations.
  - Never overwrites existing repo-specific files by default.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from cli_error_utils import format_cli_error
from constants import PROMPT_CATALOG_FILENAME, SUPPORTED_AGENTS, validate_agent_name
from managed_install import (
    PRE_MANIFEST_RETIRED_SKILLS,
    ManagedInstallReport,
    reconcile_managed_skills,
)
from path_utils import resolve_claude_home, resolve_codex_home
from prompt_catalog_paths import canonical_repo_prompt_catalog_path
from skillset_utils import find_skillset, load_skillset

# All supported agents for bulk installation
ALL_AGENTS = list(SUPPORTED_AGENTS)


# Canonical repo-install templates
CANONICAL_AGENTS_TEMPLATE = Path("templates/repo_root/AGENTS.md")
CANONICAL_VIBE_TEMPLATE = Path("templates/repo_root/VIBE.md")
DEFAULT_REPO_SKILLSET = "vibe-base"
DEFAULT_MANAGED_SKILLS = (
    "vibe-prompts",
    "vibe-loop",
    "vibe-run",
    "continuous-refactor",
    "continuous-test-generation",
    "continuous-documentation",
)


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


def _resolve_canonical_prompt_catalog(repo_root: Path) -> Path:
    catalog_path = canonical_repo_prompt_catalog_path(repo_root)
    if catalog_path.exists():
        return catalog_path
    raise FileNotFoundError(
        "Canonical catalog missing (expected prompts/template_prompts.md)."
    )


def _validate_prompt_catalog(repo_root: Path, catalog_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(repo_root / "tools" / "prompt_catalog.py"), str(catalog_path), "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Prompt catalog validation failed:\n{proc.stderr or proc.stdout}")


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


def install_repo(target_repo: Path, skillset: str | None = None, overwrite: bool = False) -> int:
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
    effective_skillset = (skillset or DEFAULT_REPO_SKILLSET).strip()
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

    # Reconcile framework-managed skills from the selected set.
    skill_defs = _resolve_skillset(repo_root, effective_skillset)
    dst_root = target_repo / ".codex" / "skills"
    managed_report = _reconcile_managed_install(
        repo_root,
        dst_root,
        [str(skill["name"]) for skill in skill_defs],
    )
    created.extend(str(dst_root / relative) for relative in managed_report.changed_files)

    # Summary
    print("repo install summary")
    print(f"- Repo: {target_repo}")
    print(f"- .vibe dir: {vibe_dir}")
    print(f"- .gitignore updated: {'yes' if gi_modified else 'no'}")
    print(f"- Skillset installed: {effective_skillset}")
    print(f"- Files created/updated: {len(created)}")
    print(f"- Files overwritten: {len(overwritten)}")
    print(f"- Existing files preserved: {len(skipped)}")
    _print_managed_report(managed_report)
    print("- Next:")
    print(f"  1. Open Codex in {target_repo}")
    print("  2. Invoke $vibe-run")

    return 0


def _default_agent_global_dir(agent: str) -> Path:
    """
    Agent global skills directory. Default:
    - Codex: $CODEX_HOME/skills (fallback: ~/.codex/skills)
    - Claude Code: $AGENT_HOME/skills when set, otherwise ~/.claude/skills
    """
    normalized_agent = validate_agent_name(agent)
    if normalized_agent == "codex":
        return resolve_codex_home() / "skills"
    return resolve_claude_home() / "skills"


def _resolve_skillset(repo_root: Path, name: str) -> list[dict[str, Any]]:
    visited: set[str] = set()
    resolving: set[str] = set()
    resolved: dict[str, None] = {}

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
            resolved[skill_name] = None
        visited.add(set_name)
        resolving.remove(set_name)

    visit_set(name)
    return [{"name": skill_name} for skill_name in resolved]


def _resolve_skill_source(repo_root: Path, skill_name: str) -> Path:
    for root in (repo_root / ".codex" / "skills", repo_root / "skills"):
        candidate = root / skill_name
        if (candidate / "SKILL.md").is_file():
            return candidate
    raise FileNotFoundError(f"Skill folder not found for '{skill_name}'.")


def _managed_overlay_sources(repo_root: Path, skill_names: set[str]) -> dict[str, Path]:
    overlays: dict[str, Path] = {}
    if "vibe-prompts" in skill_names:
        overlays[f"vibe-prompts/resources/{PROMPT_CATALOG_FILENAME}"] = (
            _resolve_canonical_prompt_catalog(repo_root)
        )
        overlays["vibe-prompts/scripts/prompt_catalog.py"] = repo_root / "tools" / "prompt_catalog.py"
    if "vibe-loop" in skill_names:
        for filename in (
            "agentctl.py",
            "checkpoint_templates.py",
            "constants.py",
            "path_utils.py",
            "prompt_catalog_paths.py",
            "resource_resolver.py",
            "stage_ordering.py",
            "workflow_engine.py",
        ):
            overlays[f"vibe-loop/scripts/{filename}"] = repo_root / "tools" / filename
    return overlays


def _reconcile_managed_install(
    repo_root: Path,
    skills_root: Path,
    skill_names: Iterable[str],
) -> ManagedInstallReport:
    names = tuple(sorted({str(name).strip() for name in skill_names if str(name).strip()}))
    catalog_path = _resolve_canonical_prompt_catalog(repo_root)
    _validate_prompt_catalog(repo_root, catalog_path)
    sources = {name: _resolve_skill_source(repo_root, name) for name in names}
    overlays = _managed_overlay_sources(repo_root, set(names))
    return reconcile_managed_skills(skills_root, sources, overlays)


def _path_summary(paths: Iterable[str], *, limit: int = 5) -> str:
    values = list(paths)
    if not values:
        return "none"
    shown = ", ".join(values[:limit])
    if len(values) > limit:
        shown += f", ... (+{len(values) - limit})"
    return shown


def _print_managed_report(report: ManagedInstallReport) -> None:
    print(f"- Managed skills: {', '.join(report.managed_skills)}")
    print(f"- Managed bundle SHA-256: {report.bundle_sha256}")
    print(f"- Managed files changed: {len(report.changed_files)}")
    print(
        f"- Managed local changes repaired: {len(report.repaired_files)} "
        f"({_path_summary(report.repaired_files)})"
    )
    print(
        f"- Managed extras removed: {len(report.removed_extras)} "
        f"({_path_summary(report.removed_extras)})"
    )
    print(
        f"- Retired managed skills removed: {len(report.retired_skills)} "
        f"({_path_summary(report.retired_skills)})"
    )
    print(f"- Managed manifest: {report.manifest_path}")


def install_skills_agent_global(agent: str, force: bool) -> int:
    agent = validate_agent_name(agent)
    repo_root = _repo_root_from_this_file()
    dst_root = _default_agent_global_dir(agent)
    del force  # Managed files always converge by content; force is retained for CLI compatibility.
    report = _reconcile_managed_install(repo_root, dst_root, DEFAULT_MANAGED_SKILLS)

    print(f"install-skills summary ({agent} global)")
    print(f"- Destination: {dst_root}")
    _print_managed_report(report)
    return 0


def install_skills_agent_repo(agent: str, target_repo: Path, force: bool) -> int:
    agent = validate_agent_name(agent)
    repo_root = _repo_root_from_this_file()
    src_skills_root = repo_root / ".codex" / "skills"

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo path does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"Target repo path is not a directory: {target_repo}")

    if not src_skills_root.exists():
        raise FileNotFoundError(f"Repo-local skills folder missing: {src_skills_root}")

    del force  # Managed files always converge by content; force is retained for CLI compatibility.
    dst_root = target_repo / ".codex" / "skills"
    skill_names = [
        src_dir.name
        for src_dir in sorted(src_skills_root.iterdir())
        if src_dir.is_dir()
        and (src_dir / "SKILL.md").exists()
        and src_dir.name not in PRE_MANIFEST_RETIRED_SKILLS
    ]

    if not skill_names:
        raise RuntimeError(f"No repo-local skills found in: {src_skills_root}")
    report = _reconcile_managed_install(repo_root, dst_root, skill_names)

    print(f"install-skills summary ({agent} repo-local)")
    print(f"- Repo: {target_repo}")
    print(f"- Destination: {dst_root}")
    _print_managed_report(report)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="Install Vibe into a target repository.",
    )
    parser.add_argument("path", type=str, help="Path to the target repo root")
    parser.add_argument(
        "--skillset",
        type=str,
        default=None,
        help=(
            "Skillset name to install into .codex/skills (default: vibe-base). "
            "When explicitly provided, also seeds .vibe/config.json if missing."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing AGENTS.md and VIBE.md (does NOT overwrite STATE.md, PLAN.md, or HISTORY.md)",
    )

    return parser


def _build_install_skills_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bootstrap.py install-skills",
        description="Install Vibe skills for an agent.",
    )
    parser.add_argument("--global", dest="global_install", action="store_true", help="Install to user/global location")
    parser.add_argument("--repo", dest="repo_install", action="store_true", help="Install into .codex/skills in the repo")
    parser.add_argument("--agent", choices=("all", *SUPPORTED_AGENTS), required=True, help="Which agent to install for (use 'all' to install for all supported agents)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Compatibility flag; framework-managed skill files always converge by content.",
    )
    return parser


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
    try:
        if argv and argv[0] == "install-skills":
            args = _build_install_skills_parser().parse_args(argv[1:])
            if args.global_install == args.repo_install:
                raise ValueError("Choose exactly one of --global or --repo for install-skills.")
            
            if args.agent == "all":
                return _install_skills_all(global_install=args.global_install, repo_install=args.repo_install, force=args.force)
            
            if args.global_install:
                return install_skills_agent_global(agent=args.agent, force=args.force)
            return install_skills_agent_repo(agent=args.agent, target_repo=Path.cwd().resolve(), force=args.force)

        args = _build_parser().parse_args(argv)
        return install_repo(Path(args.path).expanduser().resolve(), skillset=args.skillset, overwrite=args.overwrite)
    except Exception as exc:
        print(f"ERROR: {format_cli_error(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
