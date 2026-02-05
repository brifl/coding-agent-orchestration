#!/usr/bin/env python3
"""Recursive directory scanner for multi-directory RAG indexing.

Scans one or more directories, respects .gitignore and custom exclusions,
and outputs a file manifest with metadata (path, size, mtime, type).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


# Common extension -> language mapping (~20 common extensions)
_EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".sql": "sql",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
}


def _infer_language(path: Path) -> str | None:
    """Infer language from file extension. Returns None if unknown."""
    ext = path.suffix.lower()
    return _EXTENSION_TO_LANGUAGE.get(ext)


def _parse_gitignore(gitignore_path: Path) -> list[str]:
    """Parse a .gitignore (or .ignore) file and return glob patterns."""
    patterns: list[str] = []
    if not gitignore_path.is_file():
        return patterns
    for line in gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def _collect_gitignore_patterns(directory: Path) -> list[str]:
    """Collect gitignore patterns from .gitignore and .ignore in a directory."""
    patterns: list[str] = []
    for name in (".gitignore", ".ignore"):
        patterns.extend(_parse_gitignore(directory / name))
    return patterns


def _matches_any(rel_path: str, patterns: list[str]) -> str | None:
    """Return the first matching pattern if rel_path matches any, else None.

    Supports simple gitignore-style matching:
    - Patterns ending with '/' match directories only (checked by caller)
    - Leading '/' anchors to the root
    - Otherwise matched against any path component or the full relative path
    """
    name = os.path.basename(rel_path)
    for pat in patterns:
        anchor = pat.startswith("/")
        check = pat.lstrip("/").rstrip("/")
        # Match against basename
        if fnmatch(name, check):
            return pat
        # Match against full relative path
        if fnmatch(rel_path, check):
            return pat
        if anchor and fnmatch(rel_path, check):
            return pat
        # Match directory components
        for part in Path(rel_path).parts:
            if fnmatch(part, check):
                return pat
    return None


def _guess_type(path: Path) -> str:
    """Guess MIME type for a file path."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def _compute_content_hash(path: Path) -> str:
    """Compute SHA-256 hash of file content."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


class ScanStats:
    """Track exclusion statistics during scanning."""

    def __init__(self) -> None:
        self.by_gitignore = 0
        self.by_exclude = 0
        self.by_file_types = 0
        self.by_include = 0
        self.by_hidden = 0
        self.total_included = 0

    def summary(self) -> str:
        parts = []
        if self.by_gitignore:
            parts.append(f"{self.by_gitignore} by gitignore")
        if self.by_exclude:
            parts.append(f"{self.by_exclude} by --exclude")
        if self.by_file_types:
            parts.append(f"{self.by_file_types} by --file-types")
        if self.by_include:
            parts.append(f"{self.by_include} by --include")
        if self.by_hidden:
            parts.append(f"{self.by_hidden} by hidden")
        excluded_total = (
            self.by_gitignore + self.by_exclude + self.by_file_types
            + self.by_include + self.by_hidden
        )
        return f"Included: {self.total_included}, Excluded: {excluded_total} ({', '.join(parts) if parts else 'none'})"


def scan_directories(
    directories: list[str],
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    file_types: list[str] | None = None,
    max_depth: int | None = None,
    respect_gitignore: bool = True,
    stats: ScanStats | None = None,
) -> list[dict[str, Any]]:
    """Scan multiple directories and return a file manifest.

    Args:
        directories: List of directory paths to scan.
        include_patterns: If set, only files matching at least one pattern are included.
        exclude_patterns: Additional exclusion glob patterns.
        file_types: If set, only files with these extensions are included (e.g. [".py", ".md"]).
        max_depth: Maximum directory depth to recurse (0 = root only).
        respect_gitignore: Whether to respect .gitignore / .ignore files.
        stats: Optional ScanStats object to track exclusion reasons.

    Returns:
        List of file metadata dicts, sorted by (root, rel_path) for determinism.
    """
    manifest: list[dict[str, Any]] = []
    exclude_patterns = list(exclude_patterns or [])
    gitignore_patterns_set: set[str] = set()  # Track which patterns are from gitignore

    for dir_path_str in directories:
        root = Path(dir_path_str).resolve()
        if not root.is_dir():
            print(f"WARNING: {root} is not a directory, skipping.", file=sys.stderr)
            continue

        # Gather gitignore patterns from root
        gitignore_patterns: list[str] = []
        if respect_gitignore:
            gitignore_patterns = _collect_gitignore_patterns(root)
            gitignore_patterns_set.update(gitignore_patterns)

        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            depth = len(current.relative_to(root).parts)

            if max_depth is not None and depth > max_depth:
                dirnames.clear()
                continue

            # Per-directory gitignore
            local_patterns: list[str] = []
            if respect_gitignore and current != root:
                local_patterns = _collect_gitignore_patterns(current)
                gitignore_patterns_set.update(local_patterns)

            all_ignore = gitignore_patterns + local_patterns + exclude_patterns

            # Filter directories in-place so os.walk skips them
            filtered_dirs: list[str] = []
            for d in dirnames:
                rel = str(Path(dirpath, d).relative_to(root))
                if d.startswith("."):
                    if stats:
                        stats.by_hidden += 1
                    continue
                matched = _matches_any(rel, all_ignore)
                if matched:
                    if stats:
                        if matched in gitignore_patterns_set:
                            stats.by_gitignore += 1
                        else:
                            stats.by_exclude += 1
                    continue
                filtered_dirs.append(d)
            dirnames[:] = sorted(filtered_dirs)

            for fname in sorted(filenames):
                fpath = Path(dirpath) / fname
                rel = str(fpath.relative_to(root))

                # Gitignore / exclude check
                matched_pattern = _matches_any(rel, all_ignore)
                if matched_pattern:
                    if stats:
                        if matched_pattern in gitignore_patterns_set:
                            stats.by_gitignore += 1
                        else:
                            stats.by_exclude += 1
                    continue

                # Include pattern filter
                if include_patterns:
                    if not any(fnmatch(fname, p) for p in include_patterns):
                        if stats:
                            stats.by_include += 1
                        continue

                # File type filter
                if file_types:
                    ext = fpath.suffix.lower()
                    if ext not in file_types:
                        if stats:
                            stats.by_file_types += 1
                        continue

                try:
                    stat_info = fpath.stat()
                except OSError:
                    continue

                content_hash = _compute_content_hash(fpath)
                language = _infer_language(fpath)

                manifest.append({
                    "path": str(fpath),
                    "rel_path": rel,
                    "root": str(root),
                    "size": stat_info.st_size,
                    "mtime": stat_info.st_mtime,
                    "type": _guess_type(fpath),
                    "content_hash": content_hash,
                    "language": language,
                })

    # Sort by (root, rel_path) for deterministic output
    manifest.sort(key=lambda e: (e["root"], e["rel_path"]))

    if stats:
        stats.total_included = len(manifest)

    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scan directories and output a file manifest."
    )
    parser.add_argument(
        "directories",
        nargs="+",
        help="One or more directories to scan.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: stdout).",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="Include only files matching these glob patterns (e.g. '*.py' '*.md').",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Exclude files matching these glob patterns.",
    )
    parser.add_argument(
        "--file-types",
        nargs="*",
        default=None,
        help="Include only files with these extensions (e.g. .py .md).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum recursion depth (0 = top-level files only).",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore and .ignore files.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print exclusion statistics to stderr.",
    )

    args = parser.parse_args(argv)

    # Normalize file_types to include leading dot
    file_types = None
    if args.file_types:
        file_types = [t if t.startswith(".") else f".{t}" for t in args.file_types]

    scan_stats = ScanStats() if args.stats else None

    manifest = scan_directories(
        args.directories,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        file_types=file_types,
        max_depth=args.max_depth,
        respect_gitignore=not args.no_gitignore,
        stats=scan_stats,
    )

    output = json.dumps(manifest, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {len(manifest)} entries to {args.output}")
    else:
        print(output)

    if scan_stats:
        print(scan_stats.summary(), file=sys.stderr)


if __name__ == "__main__":
    main()
