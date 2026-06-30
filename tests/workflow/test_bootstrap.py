"""Tests for repository bootstrap behavior."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from bootstrap import _build_install_skills_parser, install_repo  # type: ignore


def test_install_repo_overwrite_replaces_canonical_docs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    agents_template = repo_root / "templates" / "repo_root" / "AGENTS.md"
    vibe_template = repo_root / "templates" / "repo_root" / "VIBE.md"

    (tmp_path / "AGENTS.md").write_text("old agents", encoding="utf-8")
    (tmp_path / "VIBE.md").write_text("old vibe", encoding="utf-8")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = install_repo(tmp_path, overwrite=True)
    assert exit_code == 0

    assert (tmp_path / "AGENTS.md").read_bytes() == agents_template.read_bytes()
    if vibe_template.exists():
        assert (tmp_path / "VIBE.md").read_bytes() == vibe_template.read_bytes()

    out = buffer.getvalue()
    assert "- Files overwritten: 2" in out


def test_install_repo_installs_vibe_base_skills_by_default(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    canonical_catalog = repo_root / "prompts" / "template_prompts.md"
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = install_repo(tmp_path)
    assert exit_code == 0

    skills_root = tmp_path / ".codex" / "skills"
    assert (skills_root / "vibe-run" / "SKILL.md").exists()
    assert not (skills_root / "vibe-one-loop").exists()
    assert (skills_root / "vibe-run" / "agents" / "openai.yaml").exists()
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
    assert (skills_root / "vibe-loop" / "scripts" / "prompt_catalog_paths.py").read_bytes() == (
        repo_root / "tools" / "prompt_catalog_paths.py"
    ).read_bytes()
    assert (skills_root / "vibe-loop" / "scripts" / "path_utils.py").read_bytes() == (
        repo_root / "tools" / "path_utils.py"
    ).read_bytes()
    installed_catalog = skills_root / "vibe-prompts" / "resources" / "template_prompts.md"
    assert installed_catalog.read_bytes() == canonical_catalog.read_bytes()
    assert not (skills_root / "vibe-run" / "resources" / "template_prompts.md").exists()
    assert not (skills_root / "continuous-refactor" / "resources" / "template_prompts.md").exists()
    assert not any(path.name == "__pycache__" for path in skills_root.rglob("__pycache__"))
    assert not any(path.suffix in {".pyc", ".pyo"} for path in skills_root.rglob("*"))

    out = buffer.getvalue()
    assert "- Skillset installed: vibe-base" in out
    assert "Invoke $vibe-run" in out


def test_direct_repo_path_install_routes_first_vibe_run_step_to_design(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target = tmp_path / "target"
    target.mkdir()

    install = subprocess.run(
        [sys.executable, str(repo_root / "tools" / "bootstrap.py"), str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert install.returncode == 0, install.stderr
    assert f"- Repo: {target}" in install.stdout
    assert "Invoke $vibe-run" in install.stdout

    decision = subprocess.run(
        [
            sys.executable,
            str(target / ".codex" / "skills" / "vibe-loop" / "scripts" / "agentctl.py"),
            "--repo-root",
            str(target),
            "--format",
            "json",
            "next",
            "--workflow",
            "vibe-run",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert decision.returncode == 0, decision.stderr
    payload = json.loads(decision.stdout)
    assert payload["recommended_role"] == "design"
    assert payload["recommended_prompt_id"] == "prompt.stage_design"
    assert payload["recommended_roles"] == [
        {
            "checkpoint": "0.0",
            "prompt_id": "prompt.stage_design",
            "reason": "New stage entered without design; STAGE_DESIGNED flag not set.",
            "role": "design",
        }
    ]


def test_legacy_init_repo_subcommand_is_not_supported(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    proc = subprocess.run(
        [sys.executable, str(repo_root / "tools" / "bootstrap.py"), "init-repo", str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 2
    assert "unrecognized arguments" in proc.stderr


def test_reinstall_preserves_substantive_workflow_files(tmp_path: Path) -> None:
    assert install_repo(tmp_path) == 0
    state_path = tmp_path / ".vibe" / "STATE.md"
    plan_path = tmp_path / ".vibe" / "PLAN.md"
    state_path.write_text("# STATE\n\ncustom state\n", encoding="utf-8")
    plan_path.write_text("# PLAN\n\n## Stage 7 — Keep me\n", encoding="utf-8")

    assert install_repo(tmp_path) == 0

    assert state_path.read_text(encoding="utf-8") == "# STATE\n\ncustom state\n"
    assert plan_path.read_text(encoding="utf-8") == "# PLAN\n\n## Stage 7 — Keep me\n"


def test_standalone_agentctl_imports_without_repo_constants(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    for name in (
        "agentctl.py",
        "resource_resolver.py",
        "prompt_catalog_paths.py",
        "checkpoint_templates.py",
        "stage_ordering.py",
    ):
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
    parser = _build_install_skills_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--global", "--agent", agent])

    assert exc_info.value.code == 2
