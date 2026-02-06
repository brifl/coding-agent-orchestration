#!/usr/bin/env python3
"""Self-test for RLM runtime resume and stdout truncation behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from runtime import RLMRuntime, RuntimeErrorState


def _write_fixture_bundle(bundle_dir: Path) -> None:
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "chunking_strategy": "by_chars",
        "max_chars": 200,
        "sources": [
            {
                "path": "fixtures/example.txt",
                "sha256": "fixture",
                "size_bytes": 22,
            }
        ],
        "task_id": "runtime_selftest",
    }
    (bundle_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    chunks = [
        {
            "char_count": 11,
            "chunk_id": "00000001",
            "hash": "chunk1",
            "range": {"line_start": 1, "line_end": 1},
            "source": "fixtures/example.txt",
            "text": "alpha line\n",
        },
        {
            "char_count": 11,
            "chunk_id": "00000002",
            "hash": "chunk2",
            "range": {"line_start": 2, "line_end": 2},
            "source": "fixtures/example.txt",
            "text": "beta line\n",
        },
    ]
    with (bundle_dir / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for row in chunks:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    meta = {
        "chunk_count": 2,
        "manifest_sha256": "fixture",
        "source_count": 1,
        "task_id": "runtime_selftest",
        "total_chars": 22,
    }
    (bundle_dir / "bundle.meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    temp_root = repo_root / ".tmp_runtime_selftest"
    if temp_root.exists():
        shutil.rmtree(temp_root)

    bundle_dir = temp_root / "bundle"
    run_dir = temp_root / "run"
    _write_fixture_bundle(bundle_dir)

    runtime = RLMRuntime(bundle_dir=bundle_dir, run_dir=run_dir, max_stdout_chars=40)
    step1 = runtime.step(
        "print('X' * 120)\n"
        "first = list_chunks(limit=1)[0]['chunk_id']\n"
        "memory['first_chunk'] = first\n"
    )
    assert step1["stdout_truncated"], "Expected stdout truncation in step 1"
    assert step1["iteration"] == 1, "Expected step 1 iteration == 1"

    resumed = RLMRuntime(bundle_dir=bundle_dir, run_dir=run_dir, max_stdout_chars=40)
    assert resumed.iteration == 1, "Expected resumed runtime to keep prior iteration count"
    assert resumed.memory.get("first_chunk") == "00000001", "Expected persisted memory across resume"

    step2 = resumed.step(
        "print(peek(memory['first_chunk'], max_chars=5))\n"
        "FINAL('done')\n"
    )
    assert not step2["stdout_truncated"], "Unexpected truncation in step 2"
    assert step2["finalized"], "Expected runtime finalization in step 2"
    assert step2["final_payload"] == "done", "Unexpected FINAL payload"

    resumed_final = RLMRuntime(bundle_dir=bundle_dir, run_dir=run_dir, max_stdout_chars=40)
    assert resumed_final.iteration == 2, "Expected two persisted iterations"
    assert resumed_final.finalized is True, "Expected finalized state on resume"
    assert resumed_final.final_payload == "done", "Expected persisted final payload"

    try:
        resumed_final.step("print('should not run')")
        raise AssertionError("Expected finalized runtime to reject additional steps")
    except RuntimeErrorState:
        pass

    state_payload = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state_payload.get("iteration") == 2, "Expected state.json iteration == 2"

    print("PASS: runtime captured deterministic stdout with truncation.")
    print("PASS: runtime resumed from state.json without ambiguity.")
    print("PASS: finalized runtime rejected additional steps.")

    shutil.rmtree(temp_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
