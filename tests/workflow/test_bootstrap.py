"""Tests for bootstrap init-repo behavior."""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from bootstrap import _build_parser, init_repo  # type: ignore


def test_init_repo_overwrite_replaces_canonical_docs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    agents_template = repo_root / "templates" / "repo_root" / "AGENTS.md"
    vibe_template = repo_root / "templates" / "repo_root" / "VIBE.md"

    (tmp_path / "AGENTS.md").write_text("old agents", encoding="utf-8")
    (tmp_path / "VIBE.md").write_text("old vibe", encoding="utf-8")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = init_repo(tmp_path, overwrite=True)
    assert exit_code == 0

    assert (tmp_path / "AGENTS.md").read_bytes() == agents_template.read_bytes()
    if vibe_template.exists():
        assert (tmp_path / "VIBE.md").read_bytes() == vibe_template.read_bytes()

    out = buffer.getvalue()
    assert "Overwritten:" in out
    assert str(tmp_path / "AGENTS.md") in out


def test_init_repo_installs_vibe_base_skills_by_default(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = init_repo(tmp_path)
    assert exit_code == 0

    skills_root = tmp_path / ".codex" / "skills"
    assert (skills_root / "vibe-run" / "SKILL.md").exists()
    assert (skills_root / "continuous-refactor" / "SKILL.md").exists()
    assert (skills_root / "continuous-test-generation" / "SKILL.md").exists()
    assert (skills_root / "vibe-loop" / "scripts" / "agentctl.py").read_bytes() == (
        repo_root / "tools" / "agentctl.py"
    ).read_bytes()
    assert (skills_root / "vibe-loop" / "scripts" / "resource_resolver.py").read_bytes() == (
        repo_root / "tools" / "resource_resolver.py"
    ).read_bytes()
    assert (skills_root / "vibe-loop" / "scripts" / "constants.py").read_bytes() == (
        repo_root / "tools" / "constants.py"
    ).read_bytes()
    assert (skills_root / "vibe-loop" / "scripts" / "path_utils.py").read_bytes() == (
        repo_root / "tools" / "path_utils.py"
    ).read_bytes()

    out = buffer.getvalue()
    assert "- Skillset installed: vibe-base" in out


def test_standalone_agentctl_imports_without_repo_constants(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    for name in ("agentctl.py", "resource_resolver.py", "checkpoint_templates.py", "stage_ordering.py"):
        shutil.copyfile(repo_root / "tools" / name, runtime_dir / name)

    proc = subprocess.run(
        [sys.executable, str(runtime_dir / "agentctl.py"), "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "agentctl" in proc.stdout


@pytest.mark.parametrize("agent", ["gemini", "copilot"])
def test_install_skills_parser_rejects_removed_agents(agent: str) -> None:
    parser = _build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["install-skills", "--global", "--agent", agent])

    assert exc_info.value.code == 2
