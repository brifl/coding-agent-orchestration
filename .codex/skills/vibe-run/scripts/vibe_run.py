#!/usr/bin/env python3
"""
vibe_run.py

Continuous loop helper:
1) Ask agentctl for the next prompt
2) Print the prompt body
3) Repeat until dispatcher returns stop
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _skills_root_from_this_script() -> Path:
    # .../.codex/skills/vibe-run/scripts/vibe_run.py -> .../.codex/skills
    return Path(__file__).resolve().parents[2]


def _run_agentctl_next(repo_root: Path, agentctl_path: Path, workflow: str = "") -> dict:
    cmd = [
        sys.executable,
        str(agentctl_path),
        "--repo-root",
        str(repo_root),
        "--format",
        "json",
        "next",
    ]
    if workflow:
        cmd.extend(["--workflow", workflow])
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"agentctl failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    return json.loads(p.stdout)


def _print_prompt(prompt_catalog_path: Path, catalog_path: Path, prompt_id: str) -> None:
    cmd = [sys.executable, str(prompt_catalog_path), str(catalog_path), "get", prompt_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"prompt_catalog get failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    sys.stdout.write(p.stdout)


def _record_loop_result(agentctl_path: Path, repo_root: Path, loop_result_line: str) -> None:
    cmd = [
        sys.executable,
        str(agentctl_path),
        "--repo-root",
        str(repo_root),
        "--format",
        "json",
        "loop-result",
        "--line",
        loop_result_line,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "loop-result command failed.")


def _extract_loop_result_line(output: str) -> str | None:
    found: str | None = None
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("LOOP_RESULT:"):
            found = line
    return found


def _simulated_loop_result_line(decision: dict) -> str:
    role = str(decision.get("recommended_role") or "").strip()
    stage = str(decision.get("stage") or "").strip()
    checkpoint = str(decision.get("checkpoint") or "").strip()
    status = str(decision.get("status") or "").strip()

    role_map = {
        "design": ("design", "updated", "implement|issues_triage|stop"),
        "implement": ("implement", "ready_for_review", "review|issues_triage"),
        "review": ("review", "pass", "implement|consolidation|issues_triage|stop"),
        "issues_triage": ("issues_triage", "resolved", "implement|review|issues_triage|stop"),
        "advance": ("advance", "advanced", "implement|stop"),
        "consolidation": ("consolidation", "aligned", "context_capture|implement|issues_triage"),
        "context_capture": ("context_capture", "updated", "implement|review|issues_triage|stop"),
        "improvements": ("improvements", "completed", "implement|review|issues_triage|stop"),
    }
    loop_name, result, next_role_hint = role_map.get(
        role,
        ("implement", "blocked", "issues_triage"),
    )

    report = {
        "acceptance_matrix": [
            {
                "item": "Simulated non-interactive loop acknowledgement",
                "status": "N/A",
                "evidence": (
                    "vibe-run used --simulate-loop-result without an executor; "
                    "prompt was emitted but not executed."
                ),
                "critical": False,
                "confidence": 1.0,
                "evidence_strength": "LOW",
            }
        ],
        "top_findings": [
            {
                "impact": "QUESTION",
                "title": "Loop result was simulated",
                "evidence": (
                    "No executor command was provided, so this run only acknowledged "
                    "the loop protocol for non-interactive continuity."
                ),
                "action": "Use --executor or interactive mode for real loop execution.",
            }
        ],
        "state_transition": {
            "before": {"stage": stage, "checkpoint": checkpoint, "status": status},
            "after": {"stage": stage, "checkpoint": checkpoint, "status": status},
        },
        "loop_result": {
            "loop": loop_name,
            "result": result,
            "stage": stage,
            "checkpoint": checkpoint,
            "status": status,
            "next_role_hint": next_role_hint,
        },
    }
    payload = {
        "loop": loop_name,
        "result": result,
        "stage": stage,
        "checkpoint": checkpoint,
        "status": status,
        "next_role_hint": next_role_hint,
        "report": report,
    }
    return "LOOP_RESULT: " + json.dumps(payload, separators=(",", ":"))


def _run_executor(
    executor_cmd: str,
    repo_root: Path,
    decision: dict,
) -> str:
    env = os.environ.copy()
    env.update(
        {
            "VIBE_REPO_ROOT": str(repo_root),
            "VIBE_DECISION_JSON": json.dumps(decision, separators=(",", ":")),
            "VIBE_RECOMMENDED_ROLE": str(decision.get("recommended_role") or ""),
            "VIBE_PROMPT_ID": str(decision.get("recommended_prompt_id") or ""),
            "VIBE_STAGE": str(decision.get("stage") or ""),
            "VIBE_CHECKPOINT": str(decision.get("checkpoint") or ""),
            "VIBE_STATUS": str(decision.get("status") or ""),
        }
    )
    p = subprocess.run(
        executor_cmd,
        shell=True,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.stdout:
        sys.stdout.write(p.stdout)
    if p.stderr:
        sys.stderr.write(p.stderr)
    if p.returncode != 0:
        raise RuntimeError(
            f"executor failed ({p.returncode}). "
            f"stdout={p.stdout.strip()!r} stderr={p.stderr.strip()!r}"
        )

    loop_result_line = _extract_loop_result_line((p.stdout or "") + "\n" + (p.stderr or ""))
    if not loop_result_line:
        raise RuntimeError(
            "executor completed but did not emit LOOP_RESULT line. "
            "Expected output containing: LOOP_RESULT: {...}"
        )
    return loop_result_line


def _prompt_for_loop_result(agentctl_path: Path, repo_root: Path) -> int:
    while True:
        try:
            line = input("Paste LOOP_RESULT line for this loop (or type 'abort' to stop): ").strip()
        except KeyboardInterrupt:
            print("", file=sys.stderr)
            return 130

        if not line:
            print("ERROR: LOOP_RESULT line is required before continuing.", file=sys.stderr)
            continue
        if line.lower() in {"abort", "quit", "exit"}:
            return 130
        try:
            _record_loop_result(agentctl_path, repo_root, line)
            return 0
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)


def _resolve_tool_paths(repo_root: Path) -> tuple[Path, Path]:
    skills_root = _skills_root_from_this_script()
    candidates_agentctl = [
        repo_root / "tools" / "agentctl.py",
        skills_root / "vibe-loop" / "scripts" / "agentctl.py",
    ]
    candidates_prompt_catalog = [
        repo_root / "tools" / "prompt_catalog.py",
        skills_root / "vibe-prompts" / "scripts" / "prompt_catalog.py",
    ]
    agentctl_path = next((p for p in candidates_agentctl if p.exists()), None)
    prompt_catalog_path = next((p for p in candidates_prompt_catalog if p.exists()), None)
    if agentctl_path is None:
        raise RuntimeError("agentctl.py not found in repo tools or installed skills.")
    if prompt_catalog_path is None:
        raise RuntimeError("prompt_catalog.py not found in repo tools or installed skills.")
    return agentctl_path, prompt_catalog_path


def _resolve_catalog_path(repo_root: Path, decision: dict, user_catalog: str) -> Path:
    decision_catalog = decision.get("prompt_catalog_path")
    if isinstance(decision_catalog, str) and decision_catalog:
        return Path(decision_catalog)
    if user_catalog:
        return Path(user_catalog).expanduser().resolve()
    repo_catalog = repo_root / "prompts" / "template_prompts.md"
    if repo_catalog.exists():
        return repo_catalog
    return _skills_root_from_this_script() / "vibe-prompts" / "resources" / "template_prompts.md"


def _record_workflow_approval(
    agentctl_path: Path,
    repo_root: Path,
    workflow: str,
    approved_ids: str,
) -> None:
    cmd = [
        sys.executable,
        str(agentctl_path),
        "--repo-root",
        str(repo_root),
        "--format",
        "json",
        "workflow-approve",
        "--workflow",
        workflow,
        "--ids",
        approved_ids,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "workflow-approve command failed.")


def _try_approval_continue(
    decision: dict,
    *,
    agentctl_path: Path,
    repo_root: Path,
    non_interactive: bool,
    executor_cmd: str,
) -> bool:
    if not decision.get("approval_required"):
        return False
    workflow = str(decision.get("workflow") or "").strip()
    if not workflow:
        return False
    ideas = decision.get("minor_ideas")
    if not isinstance(ideas, list) or not ideas:
        return False

    print("Minor-only threshold reached. Candidate ideas:", file=sys.stderr)
    for item in ideas:
        if not isinstance(item, dict):
            continue
        idea_id = item.get("id")
        impact = str(item.get("impact", "")).strip()
        title = str(item.get("title", "")).strip()
        print(f"  {idea_id}. [{impact}] {title}", file=sys.stderr)

    if non_interactive or executor_cmd:
        print(
            "NOTE: approval-required stop in non-interactive mode; exiting. "
            "Run agentctl workflow-approve manually to continue.",
            file=sys.stderr,
        )
        return False

    while True:
        try:
            approved = input(
                "Approve idea numbers to execute (for example: 1,3,5). Press Enter to stop: "
            ).strip()
        except EOFError:
            return False
        except KeyboardInterrupt:
            print("", file=sys.stderr)
            return False
        if not approved:
            return False
        try:
            _record_workflow_approval(agentctl_path, repo_root, workflow, approved)
            print(f"NOTE: recorded approval for workflow {workflow}: {approved}", file=sys.stderr)
            return True
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(prog="vibe_run.py")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: current directory)")
    ap.add_argument("--catalog", default="", help="Optional path to template_prompts.md")
    ap.add_argument("--workflow", default="", help="Optional workflow name passed to agentctl next")
    ap.add_argument("--max-loops", type=int, default=0, help="Loop cap for safety (0 = until stop)")
    ap.add_argument("--show-decision", action="store_true", help="Print agentctl decision JSON to stderr each loop")
    ap.add_argument(
        "--executor",
        default="",
        help=(
            "Optional shell command run after each emitted prompt. "
            "Command must print a LOOP_RESULT line that this runner records automatically."
        ),
    )
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not pause between loops. Use only when another process updates state.",
    )
    ap.add_argument(
        "--simulate-loop-result",
        action="store_true",
        help=(
            "Auto-record a synthetic LOOP_RESULT after each emitted prompt. "
            "Use for non-interactive dry-runs without an executor."
        ),
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    try:
        agentctl_path, prompt_catalog_path = _resolve_tool_paths(repo_root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    loop_count = 0
    while True:
        if args.max_loops > 0 and loop_count >= args.max_loops:
            return 0

        try:
            decision = _run_agentctl_next(repo_root, agentctl_path, args.workflow)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        if args.show_decision:
            print(json.dumps(decision, indent=2, sort_keys=True), file=sys.stderr)

        if decision.get("requires_loop_result"):
            print(f"NOTICE: {decision.get('reason', 'LOOP_RESULT acknowledgement required.')}", file=sys.stderr)
            if decision.get("recommended_role") == "stop":
                return 2

        prompt_id = decision.get("recommended_prompt_id")
        if decision.get("recommended_role") == "stop" or prompt_id == "stop":
            should_continue = _try_approval_continue(
                decision,
                agentctl_path=agentctl_path,
                repo_root=repo_root,
                non_interactive=bool(args.non_interactive),
                executor_cmd=str(args.executor or ""),
            )
            if should_continue:
                continue
            return 0
        if not isinstance(prompt_id, str) or not prompt_id:
            print(f"ERROR: missing recommended_prompt_id in decision: {decision}", file=sys.stderr)
            return 2

        catalog_path = _resolve_catalog_path(repo_root, decision, args.catalog)
        if not catalog_path.exists():
            print(f"ERROR: prompt catalog not found: {catalog_path}", file=sys.stderr)
            return 2

        try:
            _print_prompt(prompt_catalog_path, catalog_path, prompt_id)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        loop_count += 1
        if args.executor:
            try:
                loop_result_line = _run_executor(args.executor, repo_root, decision)
                _record_loop_result(agentctl_path, repo_root, loop_result_line)
            except RuntimeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 2
            continue

        if args.simulate_loop_result:
            try:
                simulated_line = _simulated_loop_result_line(decision)
                _record_loop_result(agentctl_path, repo_root, simulated_line)
            except RuntimeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 2
            print(
                "NOTE: recorded simulated LOOP_RESULT (--simulate-loop-result).",
                file=sys.stderr,
            )
            continue

        if args.non_interactive:
            print(
                "ERROR: --non-interactive requires --executor or --simulate-loop-result "
                "to acknowledge LOOP_RESULT.",
                file=sys.stderr,
            )
            return 2
        if not sys.stdin.isatty():
            print("NOTE: stdin is not interactive; stopping after one loop.", file=sys.stderr)
            return 0
        try:
            input("Press Enter after completing this loop to continue (Ctrl+C to stop): ")
        except KeyboardInterrupt:
            print("", file=sys.stderr)
            return 130

        result = _prompt_for_loop_result(agentctl_path, repo_root)
        if result != 0:
            return result


if __name__ == "__main__":
    raise SystemExit(main())
