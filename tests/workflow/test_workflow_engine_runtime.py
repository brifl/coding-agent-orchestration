from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_workflow_engine_includes_documentation_cycle() -> None:
    module = _load_module(REPO_ROOT / "tools" / "workflow_engine.py", "workflow_engine_runtime_test_mod")
    assert module.WORKFLOW_STEP_ORDER["continuous-documentation"] == [
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    ]


def test_workflow_engine_advance_false_does_not_mutate_runtime(tmp_path: Path) -> None:
    module = _load_module(REPO_ROOT / "tools" / "workflow_engine.py", "workflow_engine_runtime_test_mod_2")
    module._repo_root = lambda: tmp_path  # type: ignore[attr-defined]

    state_dir = tmp_path / ".vibe"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "STATE.md").write_text(
        "\n".join(
            [
                "# STATE",
                "## Current focus",
                "- Stage: 35",
                "- Checkpoint: 35.0",
                "- Status: NOT_STARTED",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runtime_path = state_dir / "workflow_runtime.json"
    assert not runtime_path.exists()

    first = module.select_next_prompt("continuous-refactor", advance=False)
    assert first == "prompt.refactor_scan"
    assert not runtime_path.exists()

    second = module.select_next_prompt("continuous-refactor", advance=True)
    assert second == "prompt.refactor_scan"
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    assert runtime_payload["workflows"]["continuous-refactor"]["next_index"] == 1

    third = module.select_next_prompt("continuous-refactor", advance=False)
    assert third == "prompt.refactor_execute"
    runtime_payload_after = json.loads(runtime_path.read_text(encoding="utf-8"))
    assert runtime_payload_after["workflows"]["continuous-refactor"]["next_index"] == 1
