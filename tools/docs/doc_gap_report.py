#!/usr/bin/env python3
"""
doc_gap_report.py

Deterministic documentation gap analysis for Stage 21A.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {"MAJOR": 0, "MODERATE": 1, "MINOR": 2}
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
README_DOC_MAP_RE = re.compile(r"(?im)^##\s+(?:documentation map|documentation|docs)\b")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


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


def _slug(value: str) -> str:
    lowered = value.lower().replace("\\", "/")
    normalized = re.sub(r"[^a-z0-9/._-]+", "-", lowered)
    return normalized.strip("-").replace("/", "_") or "root"


def _finding_id(
    phase: str,
    category: str,
    severity: str,
    location: dict[str, Any],
    recommendation: dict[str, Any],
) -> str:
    fingerprint = {
        "phase": phase,
        "category": category,
        "severity": severity,
        "location": location,
        "recommendation": recommendation,
    }
    payload = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:10]
    loc = _slug(str(location.get("path", "unknown")))
    return f"{phase}:{category}:{loc}:{digest}"


def _build_finding(
    *,
    phase: str,
    category: str,
    severity: str,
    location: dict[str, Any],
    recommendation: dict[str, Any],
    rationale: str,
    evidence: str,
) -> dict[str, Any]:
    finding = {
        "phase": phase,
        "category": category,
        "severity": severity,
        "location": location,
        "recommendation": recommendation,
        "rationale": rationale,
        "evidence": evidence,
    }
    finding["finding_id"] = _finding_id(phase, category, severity, location, recommendation)
    return finding


def _detect_embedded_guide_files(repo_root: Path, files: list[Path]) -> list[str]:
    matches: list[str] = []
    for path in files:
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        rel = _rel(path, repo_root)
        if rel.startswith("docs/"):
            continue
        text = _read_text(path)
        if EMBEDDED_GUIDE_RE.search(text):
            matches.append(rel)
    return sorted(matches)


def _largest_docs_markdown(repo_root: Path, files: list[Path]) -> tuple[str, int] | None:
    candidates: list[tuple[str, int]] = []
    for path in files:
        rel = _rel(path, repo_root)
        if not rel.startswith("docs/"):
            continue
        if not rel.endswith(".md"):
            continue
        if rel.startswith("docs/wiki-export/"):
            continue
        line_count = _read_text(path).count("\n") + 1
        candidates.append((rel, line_count))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[1], item[0]))
    return candidates[0]


def build_gap_report(repo_root: Path) -> dict[str, Any]:
    files = _iter_files(repo_root)
    rel_files = {_rel(path, repo_root) for path in files}
    findings: list[dict[str, Any]] = []

    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        findings.append(
            _build_finding(
                phase="gap",
                category="missing_doc",
                severity="MAJOR",
                location={"path": "README.md"},
                recommendation={
                    "action": "create_doc",
                    "target_path": "README.md",
                    "summary": "Create a repository root README with setup and workflow overview.",
                },
                rationale="The root onboarding entry point is missing.",
                evidence="No README.md found at repository root.",
            )
        )
    else:
        readme_text = _read_text(readme_path)
        if not README_DOC_MAP_RE.search(readme_text):
            findings.append(
                _build_finding(
                    phase="gap",
                    category="missing_section",
                    severity="MODERATE",
                    location={"path": "README.md", "section": "Documentation"},
                    recommendation={
                        "action": "edit_section",
                        "target_path": "README.md",
                        "summary": "Add a documentation map section linking core docs and workflows.",
                    },
                    rationale="Readers need a single index to discover repo docs quickly.",
                    evidence="README.md lacks a dedicated docs map/docs section heading.",
                )
            )

    if "docs/index.md" not in rel_files:
        findings.append(
            _build_finding(
                phase="gap",
                category="missing_doc",
                severity="MAJOR",
                location={"path": "docs/"},
                recommendation={
                    "action": "create_doc",
                    "target_path": "docs/index.md",
                    "summary": "Add a docs index with links by topic and workflow.",
                },
                rationale="The docs directory has no explicit entrypoint.",
                evidence="docs/index.md is absent.",
            )
        )

    embedded_guide_files = _detect_embedded_guide_files(repo_root, files)
    if embedded_guide_files and "docs/embedded_guides.md" not in rel_files:
        preview = ", ".join(embedded_guide_files[:3])
        findings.append(
            _build_finding(
                phase="gap",
                category="missing_doc",
                severity="MODERATE",
                location={"path": embedded_guide_files[0]},
                recommendation={
                    "action": "create_doc",
                    "target_path": "docs/embedded_guides.md",
                    "summary": "Create an index for embedded guides and command snippets.",
                },
                rationale="Embedded guide content exists but is not centrally indexed.",
                evidence=f"Detected embedded guide markers in {len(embedded_guide_files)} files: {preview}.",
            )
        )

    largest_doc = _largest_docs_markdown(repo_root, files)
    if largest_doc:
        largest_path, line_count = largest_doc
        stem = Path(largest_path).stem
        wiki_target = f"docs/wiki-export/{stem}.md"
        if line_count >= 150 and wiki_target not in rel_files:
            findings.append(
                _build_finding(
                    phase="gap",
                    category="missing_wiki_target",
                    severity="MINOR",
                    location={"path": largest_path},
                    recommendation={
                        "action": "create_wiki_page",
                        "target_path": wiki_target,
                        "summary": "Seed a wiki export page for long-form cross-cutting guidance.",
                    },
                    rationale="Large docs benefit from a mirrored wiki landing target.",
                    evidence=f"{largest_path} has {line_count} lines and no matching wiki-export page.",
                )
            )

    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["finding_id"]))

    severity_counts = {"MAJOR": 0, "MODERATE": 0, "MINOR": 0}
    action_counts: dict[str, int] = {}
    for finding in findings:
        severity_counts[finding["severity"]] += 1
        action = str(finding.get("recommendation", {}).get("action", ""))
        action_counts[action] = action_counts.get(action, 0) + 1

    report = {
        "schema_version": 1,
        "phase": "gap",
        "coverage": {
            "readme_files": sorted(path for path in rel_files if path.lower().endswith("readme.md")),
            "docs_markdown_files": sorted(path for path in rel_files if path.startswith("docs/") and path.endswith(".md")),
            "embedded_guide_file_count": len(embedded_guide_files),
        },
        "summary": {
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "action_counts": dict(sorted(action_counts.items())),
            "supports_net_new_docs": action_counts.get("create_doc", 0) > 0
            or action_counts.get("create_wiki_page", 0) > 0,
            "ordering_rule": "severity(MAJOR>MODERATE>MINOR),finding_id(asc)",
            "deterministic": True,
        },
        "findings": findings,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic documentation gap report.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to scan (default: current directory).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output JSON report path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    out_path = Path(args.out).expanduser()
    if not out_path.is_absolute():
        out_path = (repo_root / out_path).resolve()

    report = build_gap_report(repo_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(
        json.dumps(
            {
                "total_findings": report["summary"]["total_findings"],
                "severity_counts": report["summary"]["severity_counts"],
                "action_counts": report["summary"]["action_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
