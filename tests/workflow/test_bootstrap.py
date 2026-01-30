"""Tests for bootstrap init-repo behavior."""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from bootstrap import init_repo  # type: ignore


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
