#!/usr/bin/env python3
"""
workflow_engine.py

Minimal workflow engine for running configured prompt sequences.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKFLOW_RUNTIME_STATE = Path(".vibe/workflow_runtime.json")
ROTATING_WORKFLOWS = {
    "continuous-refactor",
    "continuous-test-generation",
    "continuous-documentation",
    "refactor-cycle",
}

WORKFLOW_STEP_ORDER: dict[str, list[str]] = {
    "continuous-refactor": [
        "prompt.refactor_scan",
        "prompt.refactor_execute",
        "prompt.refactor_verify",
    ],
    "continuous-test-generation": [
        "prompt.test_gap_analysis",
        "prompt.test_generation",
        "prompt.test_review",
    ],
    "continuous-documentation": [
        "prompt.docs_gap_analysis",
        "prompt.docs_gap_fix",
        "prompt.docs_refactor_analysis",
        "prompt.docs_refactor_fix",
    ],
}
# Backward-compatible alias used by older callers/tests.
BUILTIN_WORKFLOW_STEPS = WORKFLOW_STEP_ORDER


@dataclass(frozen=True)
class WorkflowStep:
    prompt_id: str
    condition: str | None
    every: int | None


@dataclass(frozen=True)
class Workflow:
    name: str
    description: str
    triggers: list[dict[str, str]]
    steps: list[WorkflowStep]
    path: Path


def _repo_root() -> Path:
    return Path.cwd()


def _workflows_root() -> Path:
    return _repo_root() / "workflows"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_yaml_workflow(text: str, path: Path) -> Workflow:
    name = ""
    description = ""
    triggers: list[dict[str, str]] = []
    steps: list[WorkflowStep] = []

    section: str | None = None
    current: dict[str, Any] | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("\"'")
            continue
        if indent == 0 and line.startswith("description:"):
            description = line.split(":", 1)[1].strip().strip("\"'")
            continue
        if indent == 0 and line.startswith("triggers:"):
            section = "triggers"
            current = None
            continue
        if indent == 0 and line.startswith("steps:"):
            section = "steps"
            current = None
            continue

        if section in {"triggers", "steps"} and line.startswith("-"):
            current = {}
            if section == "triggers":
                triggers.append(current)
            else:
                # steps handled later
                pass
            # inline key after dash
            item = line[1:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current[key.strip()] = value.strip().strip("\"'")
            if section == "steps":
                # create a placeholder step to populate later
                steps.append(WorkflowStep(prompt_id=str(current.get("prompt_id", "")), condition=None, every=None))
            continue

        if section == "triggers" and current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip().strip("\"'")
            continue

        if section == "steps" and ":" in line:
            key, value = line.split(":", 1)
            if not steps:
                continue
            last = steps[-1]
            data = {
                "prompt_id": last.prompt_id,
                "condition": last.condition,
                "every": last.every,
            }
            if key.strip() == "prompt_id":
                data["prompt_id"] = value.strip().strip("\"'")
            elif key.strip() == "condition":
                data["condition"] = value.strip().strip("\"'")
            elif key.strip() == "every":
                raw_val = value.strip().strip("\"'")
                data["every"] = int(raw_val) if raw_val.isdigit() else None
            steps[-1] = WorkflowStep(**data)

    if not name:
        raise ValueError(f"Workflow missing name: {path}")

    return Workflow(name=name, description=description, triggers=triggers, steps=steps, path=path)


def _load_workflow(name: str) -> Workflow:
    root = _workflows_root()
    for ext in (".yaml", ".yml", ".json"):
        path = root / f"{name}{ext}"
        if not path.exists():
            continue
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            steps = [
                WorkflowStep(
                    prompt_id=str(step.get("prompt_id")),
                    condition=step.get("condition"),
                    every=int(step["every"]) if str(step.get("every", "")).isdigit() else None,
                )
                for step in payload.get("steps", [])
            ]
            return Workflow(
                name=payload.get("name", name),
                description=payload.get("description", ""),
                triggers=payload.get("triggers", []),
                steps=steps,
                path=path,
            )
        return _parse_yaml_workflow(path.read_text(encoding="utf-8"), path)
    builtin_steps = WORKFLOW_STEP_ORDER.get(name)
    if builtin_steps:
        return Workflow(
            name=name,
            description=f"Built-in fallback workflow for {name}",
            triggers=[{"type": "manual"}],
            steps=[WorkflowStep(prompt_id=prompt_id, condition=None, every=None) for prompt_id in builtin_steps],
            path=root / f"<builtin:{name}>",
        )
    raise FileNotFoundError(f"Workflow '{name}' not found in {root}.")


def _parse_state() -> dict[str, Any]:
    state_path = _repo_root() / ".vibe" / "STATE.md"
    text = state_path.read_text(encoding="utf-8")
    kv = {}
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*(Stage|Checkpoint|Status)\s*:\s*(.+)$", line)
        if m:
            kv[m.group(1).lower()] = m.group(2).strip().split()[0]
    issues = []
    in_issues = False
    for line in text.splitlines():
        if line.strip().lower() == "## active issues":
            in_issues = True
            continue
        if in_issues and line.startswith("## "):
            break
        if in_issues:
            sm = re.match(r"^\s*-\s*\[(\w+)\]\s*(.+)$", line)
            if sm:
                issues.append(sm.group(1))
            sm2 = re.match(r"^\s*-\s*Impact\s*:\s*(\w+)", line, re.IGNORECASE)
            if sm2:
                issues.append(sm2.group(1).upper())
    return {"stage": kv.get("stage"), "checkpoint": kv.get("checkpoint"), "status": kv.get("status"), "issues": issues}


def _workflow_runtime_path() -> Path:
    return _repo_root() / WORKFLOW_RUNTIME_STATE


def _load_workflow_runtime() -> dict[str, Any]:
    path = _workflow_runtime_path()
    if not path.exists():
        return {"workflows": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"workflows": {}}
    if not isinstance(payload, dict):
        return {"workflows": {}}
    workflows = payload.get("workflows")
    if not isinstance(workflows, dict):
        payload["workflows"] = {}
    return payload


def _save_workflow_runtime(payload: dict[str, Any]) -> None:
    path = _workflow_runtime_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _trigger_matches(trigger: dict[str, str], state: dict[str, Any]) -> bool:
    ttype = trigger.get("type")
    value = trigger.get("value")
    if ttype in {"manual", "scheduled"}:
        return True
    if ttype == "on-status":
        return value == state.get("status")
    if ttype == "on-issue":
        return value in state.get("issues", [])
    return False


def _condition_matches(condition: str | None, state: dict[str, Any]) -> bool:
    if not condition or condition == "always":
        return True
    if condition.startswith("status:"):
        return condition.split(":", 1)[1] == state.get("status")
    if condition.startswith("issue:"):
        return condition.split(":", 1)[1] in state.get("issues", [])
    return False


def _every_matches(every: int | None, checkpoint: str | None) -> bool:
    if not every or not checkpoint:
        return True
    if "." not in checkpoint:
        return True
    try:
        minor = int(checkpoint.split(".", 1)[1])
    except ValueError:
        return True
    return minor % every == 0


def _eligible_prompt_ids(
    workflow: Workflow,
    state: dict[str, Any],
    allowed_prompt_ids: set[str] | None,
) -> list[str]:
    prompt_ids: list[str] = []
    for step in workflow.steps:
        if not step.prompt_id:
            continue
        if not _condition_matches(step.condition, state):
            continue
        if not _every_matches(step.every, state.get("checkpoint")):
            continue
        if allowed_prompt_ids is not None and step.prompt_id not in allowed_prompt_ids:
            continue
        prompt_ids.append(step.prompt_id)
    return prompt_ids


def _select_rotating_prompt(
    workflow: Workflow,
    state: dict[str, Any],
    allowed_prompt_ids: set[str] | None,
    *,
    advance: bool,
) -> str | None:
    prompt_ids = _eligible_prompt_ids(workflow, state, allowed_prompt_ids)
    if not prompt_ids:
        return None

    runtime = _load_workflow_runtime()
    workflows_raw = runtime.get("workflows")
    workflows = workflows_raw if isinstance(workflows_raw, dict) else {}
    entry_raw = workflows.get(workflow.name)
    entry = entry_raw if isinstance(entry_raw, dict) else {}

    order_sig = "|".join(prompt_ids)
    stage = state.get("stage")
    checkpoint = state.get("checkpoint")

    raw_cursor = entry.get("next_index", 0)
    try:
        cursor = int(raw_cursor)
    except (TypeError, ValueError):
        cursor = 0
    if cursor < 0:
        cursor = 0

    if (
        entry.get("order_sig") != order_sig
        or entry.get("stage") != stage
        or entry.get("checkpoint") != checkpoint
    ):
        cursor = 0

    index = cursor % len(prompt_ids)
    selected = prompt_ids[index]
    if not advance:
        return selected

    workflows[workflow.name] = {
        "checkpoint": checkpoint,
        "next_index": (index + 1) % len(prompt_ids),
        "order_sig": order_sig,
        "stage": stage,
        "updated_at": _utc_now(),
    }
    runtime["workflows"] = workflows
    _save_workflow_runtime(runtime)
    return selected


def select_next_prompt(
    workflow_name: str,
    allowed_prompt_ids: set[str] | None = None,
    *,
    advance: bool = True,
) -> str | None:
    workflow = _load_workflow(workflow_name)
    state = _parse_state()
    if workflow.triggers and not any(_trigger_matches(t, state) for t in workflow.triggers):
        return None
    if workflow.name in ROTATING_WORKFLOWS:
        return _select_rotating_prompt(workflow, state, allowed_prompt_ids, advance=advance)
    prompt_ids = _eligible_prompt_ids(workflow, state, allowed_prompt_ids)
    return prompt_ids[0] if prompt_ids else None


def _write_workflow_state(workflow: Workflow, executed: list[str]) -> None:
    state_path = _repo_root() / ".vibe" / "STATE.md"
    text = state_path.read_text(encoding="utf-8")
    block = [
        "## Workflow state",
        f"- Name: {workflow.name}",
        f"- Last run: {len(executed)} step(s)",
        f"- Steps: {', '.join(executed) if executed else 'none'}",
        "",
    ]
    if "## Workflow state" in text:
        text = re.sub(r"## Workflow state[\s\S]*?(?=\n## |\Z)", "\n".join(block), text, flags=re.MULTILINE)
    else:
        text = text.replace("\n## Evidence", "\n" + "\n".join(block) + "\n## Evidence")
    state_path.write_text(text, encoding="utf-8")


def cmd_list() -> int:
    root = _workflows_root()
    if not root.exists():
        print("No workflows directory found.")
        return 1
    for path in sorted(root.glob("*.y*ml")):
        wf = _parse_yaml_workflow(path.read_text(encoding="utf-8"), path)
        print(f"{wf.name}\t{wf.description}")
    return 0


def cmd_describe(name: str) -> int:
    wf = _load_workflow(name)
    print(f"Name: {wf.name}")
    print(f"Description: {wf.description}")
    print("Triggers:")
    for trig in wf.triggers:
        print(f"- {trig.get('type')}: {trig.get('value')}")
    print("Steps:")
    for step in wf.steps:
        extra = []
        if step.condition:
            extra.append(f"condition={step.condition}")
        if step.every:
            extra.append(f"every={step.every}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        print(f"- {step.prompt_id}{suffix}")
    return 0


def cmd_run(name: str) -> int:
    wf = _load_workflow(name)
    state = _parse_state()
    if wf.triggers and not any(_trigger_matches(t, state) for t in wf.triggers):
        print("Workflow triggers not satisfied.")
        return 1

    executed: list[str] = []
    for step in wf.steps:
        if not step.prompt_id:
            continue
        if not _condition_matches(step.condition, state):
            print(f"SKIP {step.prompt_id} (condition)")
            continue
        if not _every_matches(step.every, state.get("checkpoint")):
            print(f"SKIP {step.prompt_id} (frequency)")
            continue
        print(f"RUN {step.prompt_id}")
        executed.append(step.prompt_id)

    _write_workflow_state(wf, executed)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="workflow_engine.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List workflows")

    desc = sub.add_parser("describe", help="Describe workflow")
    desc.add_argument("name")

    run = sub.add_parser("run", help="Run workflow")
    run.add_argument("name")

    args = parser.parse_args(argv)
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "describe":
        return cmd_describe(args.name)
    if args.cmd == "run":
        return cmd_run(args.name)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
