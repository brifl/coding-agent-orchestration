"""Coverage for agentctl workflow selector fallback behavior."""
from __future__ import annotations

import builtins
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import _load_workflow_selector  # type: ignore


def _write_state(repo_root: Path, body: str) -> None:
    state_path = repo_root / ".vibe" / "STATE.md"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(body, encoding="utf-8")


def test_workflow_selector_fallback_uses_builtin_runtime_cycle(
    temp_repo: Path,
    monkeypatch,
) -> None:
    _write_state(
        temp_repo,
        """# STATE

## Current focus
- Stage: 1
- Checkpoint: 1.0
- Status: IN_PROGRESS
""",
    )

    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "workflow_engine":
            raise ImportError("forced failure for fallback coverage")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    selector = _load_workflow_selector(temp_repo)
    runtime_path = temp_repo / ".vibe" / "workflow_runtime.json"

    first = selector("continuous-refactor", None, advance=False)
    assert first == "prompt.refactor_scan"
    assert not runtime_path.exists()

    second = selector("continuous-refactor", None, advance=True)
    assert second == "prompt.refactor_scan"
    assert runtime_path.exists()

    third = selector("continuous-refactor", None, advance=False)
    assert third == "prompt.refactor_execute"
