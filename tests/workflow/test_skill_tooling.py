"""Tests for skill manifests, skillset resolution, and path normalization."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from path_utils import normalize_home_path, resolve_codex_home  # type: ignore
from skillctl import cmd_validate, resolve_skillset  # type: ignore


def test_core_vibe_skill_manifests_validate() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    skills_root = repo_root / ".codex" / "skills"
    for name in (
        "vibe-prompts",
        "vibe-loop",
        "vibe-one-loop",
        "vibe-run",
        "continuous-refactor",
        "continuous-test-generation",
    ):
        assert cmd_validate(skills_root / name) == 0


def test_vibe_base_skillset_includes_loop_run_aliases() -> None:
    payload = resolve_skillset("vibe-base", "codex")
    names = {entry["name"] for entry in payload["skills"]}
    assert "vibe-prompts" in names
    assert "vibe-loop" in names
    assert "vibe-one-loop" in names
    assert "vibe-run" in names
    assert "continuous-refactor" in names
    assert "continuous-test-generation" in names


def test_bootstrap_global_skill_list_includes_continuous_refactor() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    bootstrap_text = (repo_root / "tools" / "bootstrap.py").read_text(encoding="utf-8")
    assert "continuous-refactor" in bootstrap_text
    assert "continuous-test-generation" in bootstrap_text


@pytest.mark.skipif(os.name == "nt", reason="WSL/Windows path normalization is POSIX-specific")
def test_normalize_home_path_converts_wsl_unc() -> None:
    raw = r"\\wsl.localhost\Ubuntu\home\alice\.codex"
    assert normalize_home_path(raw) == Path("/home/alice/.codex")


@pytest.mark.skipif(os.name == "nt", reason="Drive-letter normalization targets POSIX hosts")
def test_normalize_home_path_converts_windows_drive() -> None:
    raw = r"C:\Users\alice\.codex"
    assert normalize_home_path(raw) == Path("/mnt/c/Users/alice/.codex")


@pytest.mark.skipif(os.name == "nt", reason="WSL/Windows path normalization is POSIX-specific")
def test_resolve_codex_home_uses_normalized_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_HOME", r"\\wsl.localhost\Ubuntu\home\brifl\.codex")
    assert resolve_codex_home() == Path("/home/brifl/.codex")
