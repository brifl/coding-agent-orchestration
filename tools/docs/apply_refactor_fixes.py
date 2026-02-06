#!/usr/bin/env python3
"""
apply_refactor_fixes.py

Apply deterministic documentation refactor fixes from a refactor report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git",
    ".vibe",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}
SOURCE_EXTENSIONS = {
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
}
EMBEDDED_GUIDE_RE = re.compile(
    r"(?im)^(?:\s*(?:#|//|--|/\*|\*)\s*)?(?:usage|quickstart|how to|troubleshooting)\b"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _write_text(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return False
    path.write_text(content, encoding="utf-8")
    return True


def _iter_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(names):
            full = Path(root) / name
            if full.is_file():
                files.append(full)
    return files


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _detect_embedded_guides(repo_root: Path) -> list[str]:
    matches: list[str] = []
    for path in _iter_files(repo_root):
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        rel = _rel(path, repo_root)
        if rel.startswith("docs/"):
            continue
        text = _read_text(path)
        if EMBEDDED_GUIDE_RE.search(text):
            matches.append(rel)
    return sorted(matches)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> bool:
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return _write_text(path, data)


def _apply_split_to_code_specific_doc(repo_root: Path, recommendation: dict[str, Any]) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip() or "docs/embedded-guides/"
    target_dir = repo_root / target
    if target_dir.suffix:
        target_dir = target_dir.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    embedded_sources = _detect_embedded_guides(repo_root)
    changed_files: list[str] = []

    # Rewrite the top-level index with a deterministic full list.
    embedded_index_path = repo_root / "docs" / "embedded_guides.md"
    lines = [
        "# Embedded Guides Index",
        "",
        "This document tracks user-facing guide material embedded in source files.",
        "",
        "## Source Inventory",
        "",
    ]
    if embedded_sources:
        lines.extend(f"- `{src}`" for src in embedded_sources)
    else:
        lines.append("- (No embedded guides detected)")
    lines.extend(
        [
            "",
            "## Detailed Split Docs",
            "",
            "- `docs/embedded-guides/index.md`",
            "",
            "## Update Process",
            "",
            "1. Add newly detected source files to this index.",
            "2. Keep split docs aligned with source ownership boundaries.",
            "3. Remove entries once guidance is migrated to canonical docs.",
        ]
    )
    if _write_text(embedded_index_path, "\n".join(lines) + "\n"):
        changed_files.append("docs/embedded_guides.md")

    split_index_path = target_dir / "index.md"
    split_lines = [
        "# Embedded Guides (Split)",
        "",
        "Per-source embedded guide mapping for refactor remediation.",
        "",
    ]
    if embedded_sources:
        split_lines.extend(f"- `{src}`" for src in embedded_sources)
    else:
        split_lines.append("- (No embedded guides detected)")
    if _write_text(split_index_path, "\n".join(split_lines) + "\n"):
        changed_files.append(_rel(split_index_path, repo_root))

    return ("applied" if changed_files else "noop_exists", sorted(changed_files))


def _append_doc_link(index_path: Path, link_line: str) -> bool:
    if not index_path.exists():
        return False
    text = index_path.read_text(encoding="utf-8")
    if link_line in text:
        return False
    if not text.endswith("\n"):
        text += "\n"
    text += f"\n{link_line}\n"
    index_path.write_text(text, encoding="utf-8")
    return True


def _apply_merge_duplicates(repo_root: Path, recommendation: dict[str, Any]) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip() or "docs/skill_reference.md"
    target_path = repo_root / target
    skill_docs = sorted(
        _rel(path, repo_root)
        for path in _iter_files(repo_root)
        if _rel(path, repo_root).startswith("docs/skill_") and _rel(path, repo_root).endswith(".md")
    )

    lines = [
        "# Skill Reference",
        "",
        "This file consolidates overlapping skill-oriented documentation.",
        "",
        "## Source Documents",
        "",
    ]
    if skill_docs:
        lines.extend(f"- `{doc}`" for doc in skill_docs)
    else:
        lines.append("- (No skill-specific docs detected)")
    lines.extend(
        [
            "",
            "## Consolidation Plan",
            "",
            "1. Keep canonical definitions in this file.",
            "2. Convert repeated sections in source docs to short pointers.",
            "3. Preserve source docs for specialized details only.",
        ]
    )

    changed_files: list[str] = []
    if _write_text(target_path, "\n".join(lines) + "\n"):
        changed_files.append(target)

    # Keep index discoverable.
    if _append_doc_link(repo_root / "docs" / "index.md", "- `docs/skill_reference.md`"):
        changed_files.append("docs/index.md")

    return ("applied" if changed_files else "noop_exists", sorted(changed_files))


def _update_wiki_map(repo_root: Path, source_path: str, target_path: str, finding_id: str) -> bool:
    map_path = repo_root / "docs" / "wiki-export" / "map.json"
    if map_path.exists():
        payload = _load_json(map_path)
    else:
        payload = {"schema_version": 1, "entries": []}

    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        entries = []

    replacement = {"source": source_path, "target": target_path, "finding_id": finding_id}
    entries = [entry for entry in entries if not (entry.get("source") == source_path and entry.get("target") == target_path)]
    entries.append(replacement)
    entries.sort(key=lambda item: (str(item.get("source", "")), str(item.get("target", "")), str(item.get("finding_id", ""))))
    payload = {"schema_version": 1, "entries": entries}
    return _write_json(map_path, payload)


def _apply_migrate_to_wiki(
    repo_root: Path, finding: dict[str, Any], recommendation: dict[str, Any]
) -> tuple[str, list[str]]:
    target = str(recommendation.get("target_path", "")).strip()
    location = finding.get("location", {}) or {}
    source_path = str(location.get("path", "docs/unknown.md"))
    if not target:
        return ("invalid_target", [])

    target_path = repo_root / target
    title = Path(target).stem.replace("_", " ").replace("-", " ").title()
    summary = str(recommendation.get("summary", "Create wiki-friendly structure.")).strip()
    content = (
        f"# {title}\n\n"
        "This page is maintained as a deterministic wiki-export artifact.\n\n"
        f"- Source: `{source_path}`\n"
        f"- Refactor intent: {summary}\n\n"
        "## Suggested Navigation\n\n"
        "1. Overview\n"
        "2. Procedures\n"
        "3. Troubleshooting\n"
    )

    changed_files: list[str] = []
    if _write_text(target_path, content):
        changed_files.append(target)
    if _update_wiki_map(repo_root, source_path, target, str(finding.get("finding_id", ""))):
        changed_files.append("docs/wiki-export/map.json")

    return ("applied" if changed_files else "noop_exists", sorted(set(changed_files)))


def _validate_markdown_consistency(repo_root: Path, changed_files: list[str]) -> list[str]:
    errors: list[str] = []
    for rel in sorted(set(changed_files)):
        if not rel.endswith(".md"):
            continue
        path = repo_root / rel
        if not path.exists():
            errors.append(f"{rel}: missing file")
            continue
        text = path.read_text(encoding="utf-8")
        first_non_empty = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not first_non_empty.startswith("#"):
            errors.append(f"{rel}: missing top-level heading")

        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or "://" in target or target.startswith("#"):
                continue
            if target.startswith("mailto:"):
                continue
            linked = (path.parent / target).resolve()
            if linked.suffix != ".md":
                continue
            if not linked.exists():
                errors.append(f"{rel}: broken markdown link -> {target}")
    return errors


def apply_fixes(report: dict[str, Any], repo_root: Path, do_apply: bool) -> tuple[list[dict[str, Any]], list[str]]:
    findings = report.get("findings", [])
    rows: list[dict[str, Any]] = []
    all_changed_files: list[str] = []

    for finding in findings:
        recommendation = finding.get("recommendation", {}) or {}
        action = str(recommendation.get("action", "")).strip()
        row = {
            "finding_id": str(finding.get("finding_id", "")),
            "action": action,
            "target_path": recommendation.get("target_path"),
            "changed_files": [],
            "status": "planned",
        }

        if not do_apply:
            rows.append(row)
            continue

        if action == "split_to_code_specific_doc":
            status, changed = _apply_split_to_code_specific_doc(repo_root, recommendation)
        elif action == "merge_duplicates":
            status, changed = _apply_merge_duplicates(repo_root, recommendation)
        elif action == "migrate_to_wiki":
            status, changed = _apply_migrate_to_wiki(repo_root, finding, recommendation)
        else:
            status, changed = ("unsupported_action", [])

        row["status"] = status
        row["changed_files"] = changed
        rows.append(row)
        all_changed_files.extend(changed)

    validation_errors = _validate_markdown_consistency(repo_root, all_changed_files) if do_apply else []
    return rows, validation_errors


def write_log(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply documentation refactor fixes from a report.")
    parser.add_argument("--report", required=True, help="Path to refactor report JSON.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for applying edits (default: current directory).",
    )
    parser.add_argument(
        "--log",
        default=".vibe/docs/refactor_fix_log.jsonl",
        help="Fix log output path (default: .vibe/docs/refactor_fix_log.jsonl).",
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

    report = _load_json(report_path)
    rows, validation_errors = apply_fixes(report, repo_root, do_apply=args.apply)
    write_log(log_path, rows)

    changed_rows = sum(1 for row in rows if row.get("changed_files"))
    summary = {
        "applied": bool(args.apply),
        "total_rows": len(rows),
        "changed_rows": changed_rows,
        "validation_errors": validation_errors,
        "log_path": str(log_path),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
