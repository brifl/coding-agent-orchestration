#!/usr/bin/env python3
"""
stage_ordering.py

Shared helpers for parsing and ordering stage IDs.
"""

from __future__ import annotations

import re
from typing import Tuple

STAGE_ID_PATTERN = r"\d+[A-Za-z]?"
CHECKPOINT_ID_PATTERN = rf"{STAGE_ID_PATTERN}\.\d+"

_STAGE_ID_RE = re.compile(rf"^(?P<num>\d+)(?P<suffix>[A-Za-z])?$", re.IGNORECASE)
_CHECKPOINT_ID_RE = re.compile(rf"^(?P<stage>{STAGE_ID_PATTERN})\.(?P<minor>\d+)$", re.IGNORECASE)


def is_valid_stage_id(stage_id: str) -> bool:
    return bool(_STAGE_ID_RE.match(stage_id.strip()))


def parse_stage_id(stage_id: str) -> Tuple[int, str | None]:
    """Parse a stage id into (numeric, optional suffix)."""
    raw = stage_id.strip()
    m = _STAGE_ID_RE.match(raw)
    if not m:
        raise ValueError(f"Invalid stage id: {stage_id}")
    num = int(m.group("num"))
    suffix = m.group("suffix")
    if suffix:
        suffix = suffix.upper()
    return num, suffix


def normalize_stage_id(stage_id: str) -> str:
    num, suffix = parse_stage_id(stage_id)
    return f"{num}{suffix or ''}"


def stage_sort_key(stage_id: str) -> Tuple[int, int]:
    """
    Ordering key: numeric first, then suffix (empty suffix sorts before letters).
    """
    num, suffix = parse_stage_id(stage_id)
    if not suffix:
        return (num, 0)
    return (num, ord(suffix) - ord("A") + 1)


def parse_checkpoint_id(checkpoint_id: str) -> Tuple[str, int]:
    raw = checkpoint_id.strip()
    m = _CHECKPOINT_ID_RE.match(raw)
    if not m:
        raise ValueError(f"Invalid checkpoint id: {checkpoint_id}")
    stage = normalize_stage_id(m.group("stage"))
    minor = int(m.group("minor"))
    return stage, minor


def normalize_checkpoint_id(checkpoint_id: str) -> str:
    stage, minor = parse_checkpoint_id(checkpoint_id)
    return f"{stage}.{minor}"
