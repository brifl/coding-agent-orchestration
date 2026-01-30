"""Tests for prompt catalog location validation."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from prompt_catalog import load_catalog  # type: ignore


def _write_catalog(path: Path) -> None:
    path.write_text(
        "## prompt.one - One\n"
        "```md\n"
        "hello\n"
        "```\n",
        encoding="utf-8",
    )


def test_rejects_noncanonical_prompt_catalog(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    manual = prompts_dir / "manual_template_prompts.md"
    _write_catalog(manual)

    with pytest.raises(ValueError, match="Non-canonical prompt catalog path"):
        load_catalog(manual)


def test_rejects_duplicate_prompt_catalogs(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    canonical = prompts_dir / "template_prompts.md"
    duplicate = prompts_dir / "manual_template_prompts.md"
    _write_catalog(canonical)
    _write_catalog(duplicate)

    with pytest.raises(ValueError, match="Multiple prompt catalogs detected"):
        load_catalog(canonical)
