#!/usr/bin/env python3
"""
Path normalization helpers used by skill tooling.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


_WSL_UNC_RE = re.compile(r"^//wsl(?:\.localhost)?/[^/]+/(.+)$", re.IGNORECASE)
_WIN_DRIVE_RE = re.compile(r"^([A-Za-z]):/(.+)$")


def normalize_home_path(raw: str) -> Path:
    """
    Normalize user-provided home-like paths across Windows/WSL variants.

    Examples on POSIX:
    - \\\\wsl.localhost\\Ubuntu\\home\\user\\.codex -> /home/user/.codex
    - C:\\Users\\user\\.codex -> /mnt/c/Users/user/.codex
    """
    value = raw.strip().strip('"').strip("'")
    if os.name != "nt":
        value = value.replace("\\", "/")
        unc_match = _WSL_UNC_RE.match(value)
        if unc_match:
            value = "/" + unc_match.group(1).lstrip("/")
        else:
            drive_match = _WIN_DRIVE_RE.match(value)
            if drive_match:
                drive = drive_match.group(1).lower()
                tail = drive_match.group(2)
                value = f"/mnt/{drive}/{tail}"
    return Path(value).expanduser().resolve()


def resolve_codex_home() -> Path:
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return normalize_home_path(env_home)
    return Path.home() / ".codex"
