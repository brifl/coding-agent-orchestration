"""Tests for skill manifests, skillset resolution, and path normalization."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from constants import DEFAULT_AGENT, SUPPORTED_AGENTS  # type: ignore
from path_utils import normalize_home_path, resolve_claude_home, resolve_codex_home  # type: ignore
from resource_resolver import find_resource  # type: ignore
from skill_registry import discover_skills  # type: ignore
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


def test_supported_agent_defaults_are_codex_and_claude_only() -> None:
    assert DEFAULT_AGENT == "codex"
    assert SUPPORTED_AGENTS == ("codex", "claude")


def test_continuous_skill_manifests_only_list_supported_agents() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for path in (
        repo_root / ".codex" / "skills" / "continuous-refactor" / "SKILL.md",
        repo_root / ".codex" / "skills" / "continuous-test-generation" / "SKILL.md",
        repo_root / ".codex" / "skills" / "continuous-documentation" / "SKILL.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "gemini" not in text
        assert "copilot" not in text


def test_discover_skills_rejects_unsupported_agents() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match="Unsupported agent 'gemini'"):
        discover_skills(repo_root, "gemini")


def test_find_resource_rejects_unsupported_agents() -> None:
    with pytest.raises(ValueError, match="Unsupported agent 'copilot'"):
        find_resource("skill", "vibe-loop", agent="copilot")


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


@pytest.mark.skipif(os.name == "nt", reason="WSL/Windows path normalization is POSIX-specific")
def test_resolve_claude_home_uses_normalized_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_HOME", r"\\wsl.localhost\Ubuntu\home\brifl\.claude")
    assert resolve_claude_home() == Path("/home/brifl/.claude")
