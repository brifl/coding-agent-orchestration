#!/usr/bin/env python3
"""Recursive directory scanner for multi-directory RAG indexing.

Scans one or more directories, respects .gitignore and custom exclusions,
and outputs a file manifest with metadata (path, size, mtime, type).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


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


def scan_directories(
    directories: list[str],
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    file_types: list[str] | None = None,
    max_depth: int | None = None,
    respect_gitignore: bool = True,
) -> list[dict[str, Any]]:
    """Scan multiple directories and return a file manifest.

    Args:
        directories: List of directory paths to scan.
        include_patterns: If set, only files matching at least one pattern are included.
        exclude_patterns: Additional exclusion glob patterns.
        file_types: If set, only files with these extensions are included (e.g. [".py", ".md"]).
        max_depth: Maximum directory depth to recurse (0 = root only).
        respect_gitignore: Whether to respect .gitignore / .ignore files.

    Returns:
        List of file metadata dicts.
    """
    manifest: list[dict[str, Any]] = []
    exclude_patterns = list(exclude_patterns or [])

    for dir_path_str in directories:
        root = Path(dir_path_str).resolve()
        if not root.is_dir():
            print(f"WARNING: {root} is not a directory, skipping.", file=sys.stderr)
            continue

        # Gather gitignore patterns from root
        gitignore_patterns: list[str] = []
        if respect_gitignore:
            gitignore_patterns = _collect_gitignore_patterns(root)

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

            all_ignore = gitignore_patterns + local_patterns + exclude_patterns

            # Filter directories in-place so os.walk skips them
            filtered_dirs: list[str] = []
            for d in dirnames:
                rel = str(Path(dirpath, d).relative_to(root))
                if d.startswith("."):
                    continue
                if _matches_any(rel, all_ignore):
                    continue
                filtered_dirs.append(d)
            dirnames[:] = sorted(filtered_dirs)

            for fname in sorted(filenames):
                fpath = Path(dirpath) / fname
                rel = str(fpath.relative_to(root))

                # Gitignore / exclude check
                matched_pattern = _matches_any(rel, all_ignore)
                if matched_pattern:
                    continue

                # Include pattern filter
                if include_patterns:
                    if not any(fnmatch(fname, p) for p in include_patterns):
                        continue

                # File type filter
                if file_types:
                    ext = fpath.suffix.lower()
                    if ext not in file_types:
                        continue

                try:
                    stat = fpath.stat()
                except OSError:
                    continue

                manifest.append({
                    "path": str(fpath),
                    "rel_path": rel,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "type": _guess_type(fpath),
                    "root": str(root),
                })

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

    args = parser.parse_args(argv)

    # Normalize file_types to include leading dot
    file_types = None
    if args.file_types:
        file_types = [t if t.startswith(".") else f".{t}" for t in args.file_types]

    manifest = scan_directories(
        args.directories,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        file_types=file_types,
        max_depth=args.max_depth,
        respect_gitignore=not args.no_gitignore,
    )

    output = json.dumps(manifest, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {len(manifest)} entries to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
