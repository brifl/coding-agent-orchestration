"""Tests for headless executor support in vibe_run.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _setup_fake_repo(repo_root: Path, *, executor_body: str) -> None:
    (repo_root / ".vibe").mkdir(parents=True)
    (repo_root / "tools").mkdir(parents=True)
    (repo_root / "prompts").mkdir(parents=True)
    (repo_root / "prompts" / "template_prompts.md").write_text(
        "# template prompts\n",
        encoding="utf-8",
    )

    _write_executable(
        repo_root / "tools" / "agentctl.py",
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv
repo_root = Path(args[args.index("--repo-root") + 1])
next_count_path = repo_root / ".vibe" / "next_count.txt"
if "next" in args:
    count = int(next_count_path.read_text(encoding="utf-8")) if next_count_path.exists() else 0
    count += 1
    next_count_path.write_text(str(count), encoding="utf-8")
    if count == 1:
        payload = {
            "recommended_role": "implement",
            "recommended_prompt_id": "prompt.checkpoint_implementation",
            "prompt_catalog_path": str(repo_root / "prompts" / "template_prompts.md"),
            "stage": "1",
            "checkpoint": "1.0",
            "status": "NOT_STARTED",
        }
    else:
        payload = {
            "recommended_role": "stop",
            "recommended_prompt_id": "stop",
            "stage": "1",
            "checkpoint": "1.0",
            "status": "NOT_STARTED",
        }
    print(json.dumps(payload))
    raise SystemExit(0)

if "loop-result" in args:
    line = args[args.index("--line") + 1]
    (repo_root / ".vibe" / "recorded_loop_result.txt").write_text(line, encoding="utf-8")
    print(json.dumps({"ok": True}))
    raise SystemExit(0)

raise SystemExit(2)
""",
    )

    _write_executable(
        repo_root / "tools" / "prompt_catalog.py",
        """#!/usr/bin/env python3
import sys

if len(sys.argv) >= 4 and sys.argv[2] == "get":
    print(f"PROMPT BODY FOR: {sys.argv[3]}")
    raise SystemExit(0)

raise SystemExit(2)
""",
    )

    _write_executable(repo_root / "executor.py", executor_body)


def test_vibe_run_executor_records_loop_result(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _setup_fake_repo(
        repo_root,
        executor_body=(
            "#!/usr/bin/env python3\n"
            "print('LOOP_RESULT: {\"loop\":\"implement\",\"result\":\"pass\",\"stage\":\"1\",\"checkpoint\":\"1.0\","
            "\"status\":\"NOT_STARTED\",\"next_role_hint\":\"implement\"}')\n"
        ),
    )

    runner = Path(__file__).resolve().parents[2] / ".codex" / "skills" / "vibe-run" / "scripts" / "vibe_run.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--repo-root",
            str(repo_root),
            "--executor",
            f"{sys.executable} {repo_root / 'executor.py'}",
            "--max-loops",
            "10",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.returncode == 0
    recorded = (repo_root / ".vibe" / "recorded_loop_result.txt")
    assert recorded.exists()
    assert recorded.read_text(encoding="utf-8").startswith("LOOP_RESULT:")


def test_vibe_run_executor_requires_loop_result_line(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _setup_fake_repo(
        repo_root,
        executor_body=(
            "#!/usr/bin/env python3\n"
            "print('executor ran without loop result')\n"
        ),
    )

    runner = Path(__file__).resolve().parents[2] / ".codex" / "skills" / "vibe-run" / "scripts" / "vibe_run.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--repo-root",
            str(repo_root),
            "--executor",
            f"{sys.executable} {repo_root / 'executor.py'}",
            "--max-loops",
            "10",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.returncode == 2
    assert "did not emit LOOP_RESULT line" in proc.stderr
