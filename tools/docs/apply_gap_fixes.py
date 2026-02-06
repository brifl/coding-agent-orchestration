#!/usr/bin/env python3
"""
apply_gap_fixes.py

Apply deterministic documentation fixes from a gap report.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_title(path_str: str) -> str:
    stem = Path(path_str).stem.replace("_", " ").replace("-", " ").strip()
    if not stem:
        stem = "documentation"
    return " ".join(part.capitalize() for part in stem.split())


def _write_text(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return False
    path.write_text(content, encoding="utf-8")
    return True


def _create_doc_content(target_path: str, recommendation: dict[str, Any], location: dict[str, Any]) -> str:
    if target_path == "docs/index.md":
        return (
            "# Documentation Index\n\n"
            "This index maps the primary documentation surfaces in this repository.\n\n"
            "## Core Documents\n\n"
            "- `README.md` - repository overview and workflow entry point.\n"
            "- `docs/continuous_documentation_overview.md` - documentation workflow scope and schema.\n"
            "- `docs/documentation_severity_rubric.md` - deterministic severity classification.\n\n"
            "## Workflow Docs\n\n"
            "- `docs/base_skills.md`\n"
            "- `docs/agent_skill_packs.md`\n"
            "- `docs/skill_lifecycle.md`\n\n"
            "## Maintenance Note\n\n"
            "Update this index whenever new top-level docs are added.\n"
        )
    if target_path == "docs/embedded_guides.md":
        source = location.get("path", "unknown")
        return (
            "# Embedded Guides Index\n\n"
            "This document tracks user-facing guide material embedded in source files.\n\n"
            "## Seeded Source\n\n"
            f"- `{source}`\n\n"
            "## Update Process\n\n"
            "1. Add any source file that contains guide-like usage or troubleshooting blocks.\n"
            "2. Link each source entry to a canonical docs page when available.\n"
            "3. Remove entries once content is migrated to dedicated docs.\n"
        )

    title = _normalize_title(target_path)
    summary = str(recommendation.get("summary", "")).strip()
    body = summary if summary else "Add targeted documentation content for this topic."
    return f"# {title}\n\n{body}\n"


def _apply_create_doc(repo_root: Path, recommendation: dict[str, Any], location: dict[str, Any]) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip()
    if not target:
        return ("invalid_target", [])
    path = repo_root / target
    if path.exists():
        return ("noop_exists", [])
    content = _create_doc_content(target, recommendation, location)
    changed = _write_text(path, content)
    return ("applied" if changed else "noop_exists", [target] if changed else [])


def _append_docs_section(readme_path: Path) -> bool:
    text = readme_path.read_text(encoding="utf-8")
    if re.search(r"(?im)^##\s+(?:documentation map|documentation|docs)\b", text):
        return False
    addition = (
        "\n## Documentation\n\n"
        "- `docs/index.md` - navigation index for core docs.\n"
        "- `docs/continuous_documentation_overview.md` - documentation loop scope and schema.\n"
        "- `docs/documentation_severity_rubric.md` - severity classification guidance.\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    text += addition
    readme_path.write_text(text, encoding="utf-8")
    return True


def _apply_edit_section(repo_root: Path, recommendation: dict[str, Any]) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip()
    if not target:
        return ("invalid_target", [])
    path = repo_root / target
    if not path.exists():
        return ("missing_target", [])

    if target == "README.md":
        changed = _append_docs_section(path)
        return ("applied" if changed else "noop_exists", [target] if changed else [])

    text = path.read_text(encoding="utf-8")
    marker = "<!-- documentation-gap-fix -->"
    if marker in text:
        return ("noop_exists", [])
    if not text.endswith("\n"):
        text += "\n"
    text += f"\n{marker}\n\n{recommendation.get('summary', 'Documentation section update.')}\n"
    path.write_text(text, encoding="utf-8")
    return ("applied", [target])


def _wiki_page_content(target_path: str, location: dict[str, Any], recommendation: dict[str, Any]) -> str:
    title = _normalize_title(target_path)
    source_path = location.get("path", "unknown")
    summary = str(recommendation.get("summary", "")).strip()
    return (
        f"# {title}\n\n"
        "This page is generated as a wiki-export seed from documentation gap remediation.\n\n"
        f"- Source file: `{source_path}`\n"
        f"- Migration intent: {summary or 'Create a focused wiki-friendly version of the source content.'}\n\n"
        "## Suggested Outline\n\n"
        "1. Scope\n"
        "2. Prerequisites\n"
        "3. Procedures\n"
        "4. Troubleshooting\n"
    )


def _apply_create_wiki_page(
    repo_root: Path, recommendation: dict[str, Any], location: dict[str, Any]
) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip()
    if not target:
        return ("invalid_target", [])
    path = repo_root / target
    if path.exists():
        return ("noop_exists", [])
    content = _wiki_page_content(target, location, recommendation)
    changed = _write_text(path, content)
    return ("applied" if changed else "noop_exists", [target] if changed else [])


def apply_fixes(report: dict[str, Any], repo_root: Path, do_apply: bool) -> list[dict[str, Any]]:
    findings = report.get("findings", [])
    log_rows: list[dict[str, Any]] = []

    for finding in findings:
        finding_id = str(finding.get("finding_id", ""))
        recommendation = finding.get("recommendation", {}) or {}
        location = finding.get("location", {}) or {}
        action = str(recommendation.get("action", "")).strip()

        row = {
            "finding_id": finding_id,
            "action": action,
            "source_location": location,
            "target_path": recommendation.get("target_path"),
            "changed_files": [],
            "status": "planned",
        }

        if not do_apply:
            log_rows.append(row)
            continue

        if action == "create_doc":
            status, changed_files = _apply_create_doc(repo_root, recommendation, location)
        elif action == "edit_section":
            status, changed_files = _apply_edit_section(repo_root, recommendation)
        elif action == "create_wiki_page":
            status, changed_files = _apply_create_wiki_page(repo_root, recommendation, location)
        else:
            status, changed_files = ("unsupported_action", [])

        row["status"] = status
        row["changed_files"] = changed_files
        log_rows.append(row)

    return log_rows


def write_log(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply documentation gap fixes from a report.")
    parser.add_argument("--report", required=True, help="Path to gap report JSON.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for applying file edits (default: current directory).",
    )
    parser.add_argument(
        "--log",
        default=".vibe/docs/gap_fix_log.jsonl",
        help="Fix log output path (default: .vibe/docs/gap_fix_log.jsonl).",
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this flag, only plan rows are logged.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    report_path = Path(args.report).expanduser()
    if not report_path.is_absolute():
        report_path = (repo_root / report_path).resolve()

    log_path = Path(args.log).expanduser()
    if not log_path.is_absolute():
        log_path = (repo_root / log_path).resolve()

    report = _load_report(report_path)
    rows = apply_fixes(report, repo_root, do_apply=args.apply)
    write_log(log_path, rows)

    changed_count = sum(1 for row in rows if row.get("changed_files"))
    summary = {
        "applied": bool(args.apply),
        "total_rows": len(rows),
        "changed_rows": changed_count,
        "log_path": str(log_path),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
