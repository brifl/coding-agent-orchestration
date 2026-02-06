#!/usr/bin/env python3
"""
doc_refactor_report.py

Deterministic documentation refactor analysis for accuracy, bloat, and structure.
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
DOC_LINK_RE = re.compile(r"(?m)^\s*-\s*`([^`]+)`")


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
    category: str,
    severity: str,
    location: dict[str, Any],
    recommendation: dict[str, Any],
    rationale: str,
    evidence: str,
) -> dict[str, Any]:
    finding = {
        "phase": "refactor",
        "category": category,
        "severity": severity,
        "location": location,
        "recommendation": recommendation,
        "rationale": rationale,
        "evidence": evidence,
    }
    finding["finding_id"] = _finding_id("refactor", category, severity, location, recommendation)
    return finding


def _detect_embedded_guides(repo_root: Path, files: list[Path]) -> list[str]:
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


def _parse_embedded_guide_index(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = _read_text(path)
    links = [match.group(1).strip() for match in DOC_LINK_RE.finditer(text)]
    return sorted(set(link for link in links if link and not link.startswith("docs/")))


def _largest_docs_file(repo_root: Path, files: list[Path]) -> tuple[str, int] | None:
    docs_files: list[tuple[str, int]] = []
    for path in files:
        rel = _rel(path, repo_root)
        if not rel.startswith("docs/") or not rel.endswith(".md"):
            continue
        if rel.startswith("docs/wiki-export/"):
            continue
        lines = _read_text(path).count("\n") + 1
        docs_files.append((rel, lines))
    if not docs_files:
        return None
    docs_files.sort(key=lambda item: (-item[1], item[0]))
    return docs_files[0]


def build_refactor_report(repo_root: Path) -> dict[str, Any]:
    files = _iter_files(repo_root)
    rel_files = {_rel(path, repo_root) for path in files}
    findings: list[dict[str, Any]] = []

    # Accuracy: embedded guide index drift.
    detected_embedded = _detect_embedded_guides(repo_root, files)
    indexed_embedded = _parse_embedded_guide_index(repo_root / "docs" / "embedded_guides.md")
    detected_set = set(detected_embedded)
    indexed_set = set(indexed_embedded)
    missing_from_index = sorted(detected_set - indexed_set)
    if missing_from_index:
        findings.append(
            _build_finding(
                category="accuracy",
                severity="MAJOR",
                location={"path": "docs/embedded_guides.md"},
                recommendation={
                    "action": "split_to_code_specific_doc",
                    "target_path": "docs/embedded-guides/",
                    "summary": "Split embedded guide inventory by subsystem and sync index generation.",
                },
                rationale="Embedded guide index is incomplete relative to detected guide-bearing files.",
                evidence=(
                    f"Detected {len(detected_embedded)} embedded-guide files but index lists "
                    f"{len(indexed_embedded)}. Missing entries include: {', '.join(missing_from_index[:3])}."
                ),
            )
        )
    else:
        findings.append(
            _build_finding(
                category="accuracy",
                severity="MINOR",
                location={"path": "docs/embedded_guides.md"},
                recommendation={
                    "action": "split_to_code_specific_doc",
                    "target_path": "docs/embedded-guides/",
                    "summary": "Move to per-subsystem embedded guide docs before index scale grows.",
                },
                rationale="No mismatch detected now, but single-file indexing will not scale.",
                evidence="Embedded guide index and detected sources currently match.",
            )
        )

    # Bloat: parallel skill docs likely overlap.
    skill_docs = sorted(path for path in rel_files if path.startswith("docs/skill_") and path.endswith(".md"))
    if len(skill_docs) >= 3:
        findings.append(
            _build_finding(
                category="bloat",
                severity="MODERATE",
                location={"path": skill_docs[0]},
                recommendation={
                    "action": "merge_duplicates",
                    "target_path": "docs/skill_reference.md",
                    "summary": "Consolidate repeated lifecycle/manifest/source guidance into one canonical reference.",
                },
                rationale="Multiple skill-focused docs increase duplication risk and maintenance overhead.",
                evidence=f"Found {len(skill_docs)} skill-related docs: {', '.join(skill_docs[:4])}.",
            )
        )
    else:
        findings.append(
            _build_finding(
                category="bloat",
                severity="MINOR",
                location={"path": "docs/"},
                recommendation={
                    "action": "merge_duplicates",
                    "target_path": "docs/index.md",
                    "summary": "Add deduplication notes as docs surface area grows.",
                },
                rationale="Current bloat risk is low but should be monitored.",
                evidence="Fewer than three skill-focused docs were detected.",
            )
        )

    # Structure: long-form docs can be split into wiki-oriented navigation.
    largest = _largest_docs_file(repo_root, files)
    if largest:
        largest_path, line_count = largest
        findings.append(
            _build_finding(
                category="structure",
                severity="MODERATE" if line_count >= 140 else "MINOR",
                location={"path": largest_path},
                recommendation={
                    "action": "migrate_to_wiki",
                    "target_path": f"docs/wiki-export/{Path(largest_path).stem}.md",
                    "summary": "Create a navigable wiki mirror and leave concise repo-local doc pointers.",
                },
                rationale="Large documents are harder to navigate and version as a single page.",
                evidence=f"Largest documentation file is {largest_path} with {line_count} lines.",
            )
        )
    else:
        findings.append(
            _build_finding(
                category="structure",
                severity="MINOR",
                location={"path": "docs/"},
                recommendation={
                    "action": "migrate_to_wiki",
                    "target_path": "docs/wiki-export/README.md",
                    "summary": "Seed wiki-export structure for future growth.",
                },
                rationale="No long docs found, but migration scaffolding is still useful.",
                evidence="No markdown files found in docs/ scope.",
            )
        )

    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["category"], item["finding_id"]))

    severity_counts = {"MAJOR": 0, "MODERATE": 0, "MINOR": 0}
    category_counts: dict[str, int] = {"accuracy": 0, "bloat": 0, "structure": 0}
    recommendation_counts: dict[str, int] = {}
    for finding in findings:
        severity_counts[finding["severity"]] += 1
        category_counts[finding["category"]] += 1
        action = str(finding.get("recommendation", {}).get("action", ""))
        recommendation_counts[action] = recommendation_counts.get(action, 0) + 1

    report = {
        "schema_version": 1,
        "phase": "refactor",
        "summary": {
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "recommendation_counts": dict(sorted(recommendation_counts.items())),
            "ordering_rule": "severity(MAJOR>MODERATE>MINOR),category,finding_id",
            "deterministic": True,
        },
        "findings": findings,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic documentation refactor report.")
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

    report = build_refactor_report(repo_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(
        json.dumps(
            {
                "total_findings": report["summary"]["total_findings"],
                "severity_counts": report["summary"]["severity_counts"],
                "category_counts": report["summary"]["category_counts"],
                "recommendation_counts": report["summary"]["recommendation_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
