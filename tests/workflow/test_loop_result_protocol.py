"""Tests for LOOP_RESULT acknowledgement protocol."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import cmd_loop_result, cmd_next  # type: ignore


def _next_args(repo_root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=str(repo_root),
        format="json",
        run_gates=False,
        workflow=None,
    )


def _loop_result_args(repo_root: Path, line: str) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=str(repo_root),
        format="json",
        line=line,
        json_payload=None,
        stdin=False,
    )


def _set_state_status(repo_root: Path, status: str) -> None:
    path = repo_root / ".vibe" / "STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("- Status: NOT_STARTED", f"- Status: {status}")
    text = text.replace("- Status: IN_PROGRESS", f"- Status: {status}")
    text = text.replace("- Status: IN_REVIEW", f"- Status: {status}")
    path.write_text(text, encoding="utf-8")


def _loop_result_line(
    *,
    loop: str,
    result: str,
    stage: str,
    checkpoint: str,
    status: str,
    next_role_hint: str,
    confidence: float = 0.95,
    evidence_strength: str = "HIGH",
    include_report: bool = True,
) -> str:
    payload: dict[str, object] = {
        "loop": loop,
        "result": result,
        "stage": stage,
        "checkpoint": checkpoint,
        "status": status,
        "next_role_hint": next_role_hint,
    }
    report = {
        "acceptance_matrix": [
            {
                "item": "checkpoint acceptance",
                "status": "PASS",
                "evidence": "demo command output",
                "critical": True,
                "confidence": confidence,
                "evidence_strength": evidence_strength,
            }
        ],
        "top_findings": [
            {
                "impact": "MINOR",
                "title": "No blocking findings",
                "evidence": "All checks passed",
                "action": "Proceed",
            }
        ],
        "state_transition": {
            "before": {"stage": stage, "checkpoint": checkpoint, "status": "NOT_STARTED"},
            "after": {"stage": stage, "checkpoint": checkpoint, "status": status},
        },
        "loop_result": {
            "loop": loop,
            "result": result,
            "stage": stage,
            "checkpoint": checkpoint,
            "status": status,
            "next_role_hint": next_role_hint,
        },
    }
    if include_report:
        payload["report"] = report
    return "LOOP_RESULT: " + json.dumps(payload, separators=(",", ":"))


def test_next_bootstraps_loop_result_file(vibe_state: Path, vibe_plan: Path, capsys) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan

    rc = cmd_next(_next_args(repo_root))
    assert rc == 0
    _ = capsys.readouterr()

    loop_result_path = repo_root / ".vibe" / "LOOP_RESULT.json"
    assert loop_result_path.exists()
    payload = json.loads(loop_result_path.read_text(encoding="utf-8"))
    assert payload["protocol_version"] == 1
    assert isinstance(payload["state_sha256"], str)
    assert payload["state_sha256"]


def test_next_blocks_when_state_changes_without_loop_result_ack(
    vibe_state: Path, vibe_plan: Path, capsys
) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan

    first = cmd_next(_next_args(repo_root))
    assert first == 0
    _ = capsys.readouterr()

    _set_state_status(repo_root, "IN_PROGRESS")
    second = cmd_next(_next_args(repo_root))
    assert second == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["recommended_role"] == "stop"
    assert payload["requires_loop_result"] is True


def test_loop_result_ack_unblocks_next(vibe_state: Path, vibe_plan: Path, capsys) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan

    first = cmd_next(_next_args(repo_root))
    assert first == 0
    _ = capsys.readouterr()

    _set_state_status(repo_root, "IN_PROGRESS")
    blocked = cmd_next(_next_args(repo_root))
    assert blocked == 0
    blocked_payload = json.loads(capsys.readouterr().out)
    assert blocked_payload["requires_loop_result"] is True

    rc = cmd_loop_result(
        _loop_result_args(
            repo_root,
            _loop_result_line(
                loop="implement",
                result="ready",
                stage="1",
                checkpoint="1.0",
                status="IN_PROGRESS",
                next_role_hint="review",
            ),
        )
    )
    assert rc == 0
    _ = capsys.readouterr()

    after = cmd_next(_next_args(repo_root))
    assert after == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload.get("requires_loop_result") is not True
    assert payload["recommended_role"] == "implement"


def test_loop_result_rejects_missing_report(vibe_state: Path, vibe_plan: Path, capsys) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan
    _set_state_status(repo_root, "IN_PROGRESS")

    rc = cmd_loop_result(
        _loop_result_args(
            repo_root,
            _loop_result_line(
                loop="implement",
                result="ready",
                stage="1",
                checkpoint="1.0",
                status="IN_PROGRESS",
                next_role_hint="review",
                include_report=False,
            ),
        )
    )
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert any("report" in error for error in payload["errors"])


def test_loop_result_rejects_low_confidence_without_triage_route(
    vibe_state: Path, vibe_plan: Path, capsys
) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan
    _set_state_status(repo_root, "IN_PROGRESS")

    rc = cmd_loop_result(
        _loop_result_args(
            repo_root,
            _loop_result_line(
                loop="review",
                result="pass",
                stage="1",
                checkpoint="1.0",
                status="IN_PROGRESS",
                next_role_hint="implement|review",
                confidence=0.40,
                evidence_strength="LOW",
            ),
        )
    )
    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert any("issues_triage" in error for error in payload["errors"])


def test_loop_result_accepts_low_confidence_with_triage_route(
    vibe_state: Path, vibe_plan: Path, capsys
) -> None:
    repo_root = vibe_state.parent.parent
    _ = vibe_plan
    _set_state_status(repo_root, "BLOCKED")

    rc = cmd_loop_result(
        _loop_result_args(
            repo_root,
            _loop_result_line(
                loop="review",
                result="fail",
                stage="1",
                checkpoint="1.0",
                status="BLOCKED",
                next_role_hint="issues_triage|implement",
                confidence=0.40,
                evidence_strength="LOW",
            ),
        )
    )
    assert rc == 0
    _ = capsys.readouterr()
