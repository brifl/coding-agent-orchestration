#!/usr/bin/env python3
"""
checkpoint_templates.py

List and preview checkpoint templates stored in templates/checkpoints/.

The parser supports a minimal YAML subset (mapping + lists + simple scalars).
If PyYAML is available, it will be used instead.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TEMPLATE_DIR = Path("templates") / "checkpoints"
LIST_KEYS = {"parameters", "deliverables", "acceptance", "demo_commands", "evidence"}


def _coerce_scalar(value: str) -> Any:
    cleaned = value.strip()
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    if cleaned.lower() in {"null", "none"}:
        return None
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        return cleaned[1:-1]
    return cleaned


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, str | None]] = [(0, root, None)]

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent < stack[-1][0]:
            stack.pop()
        container, current_key = stack[-1][1], stack[-1][2]

        if line.lstrip().startswith("- "):
            if not isinstance(container, list):
                if current_key is None:
                    raise ValueError("List item found without a list context.")
                container = []
                stack[-1] = (stack[-1][0], container, current_key)
            item_text = line.lstrip()[2:].strip()
            if ":" in item_text and not item_text.startswith(("'", '"')):
                key, value = item_text.split(":", 1)
                entry = {key.strip(): _coerce_scalar(value)}
                container.append(entry)
                stack.append((indent + 2, entry, None))
            else:
                container.append(_coerce_scalar(item_text))
            continue

        key, value = (line.strip().split(":", 1) + [""])[:2]
        key = key.strip()
        value = value.strip()
        if value == "":
            if key in LIST_KEYS:
                new_container: Any = []
            else:
                new_container = {}
            if isinstance(container, dict):
                container[key] = new_container
            else:
                raise ValueError("Mapping entry found inside a list without a dict.")
            stack.append((indent + 2, new_container, key))
        else:
            if isinstance(container, dict):
                container[key] = _coerce_scalar(value)
            else:
                raise ValueError("Scalar mapping entry found inside a list without a dict.")

    return root


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError("Template root must be a mapping.")
        return data
    except ModuleNotFoundError:
        return _parse_simple_yaml(text)


def _render_text(text: str, values: dict[str, str]) -> str:
    out = text
    for key, val in values.items():
        out = out.replace(f"{{{{{key}}}}}", val)
    return out


def _render_list(items: list[str], values: dict[str, str]) -> list[str]:
    return [_render_text(str(item), values) for item in items]


def _template_files() -> list[Path]:
    if not TEMPLATE_DIR.exists():
        return []
    return sorted(TEMPLATE_DIR.glob("*.yaml"))


def cmd_list(_args: argparse.Namespace) -> int:
    files = _template_files()
    if not files:
        print("No templates found.")
        return 0
    for path in files:
        data = _load_yaml(path)
        name = data.get("name", path.stem)
        desc = data.get("description", "")
        line = f"{name}"
        if desc:
            line += f" - {desc}"
        print(line)
    return 0


def _parse_param_args(argv: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if not token.startswith("--"):
            idx += 1
            continue
        key = token[2:]
        if not key:
            idx += 1
            continue
        if idx + 1 >= len(argv):
            raise ValueError(f"Missing value for --{key}")
        params[key] = argv[idx + 1]
        idx += 2
    return params


def _build_values(template: dict[str, Any], provided: dict[str, str]) -> dict[str, str]:
    values = dict(provided)
    params = template.get("parameters", [])
    if isinstance(params, list):
        for param in params:
            if not isinstance(param, dict):
                continue
            name = str(param.get("name", "")).strip()
            if not name:
                continue
            if name not in values and "default" in param:
                values[name] = str(param["default"])
            if param.get("required") and name not in values:
                raise ValueError(f"Missing required parameter: {name}")
    return values


def cmd_preview(args: argparse.Namespace) -> int:
    path = TEMPLATE_DIR / f"{args.template}.yaml"
    if not path.exists():
        print(f"Template not found: {path}")
        return 1

    template = _load_yaml(path)
    provided = _parse_param_args(args.params)
    values = _build_values(template, provided)

    print("\n".join(_render_checkpoint_lines(template, values)).rstrip())
    return 0


def cmd_instantiate(args: argparse.Namespace) -> int:
    path = TEMPLATE_DIR / f"{args.template}.yaml"
    if not path.exists():
        print(f"Template not found: {path}")
        return 1

    template = _load_yaml(path)
    provided = _parse_param_args(args.params)
    values = _build_values(template, provided)

    print("\n".join(_render_checkpoint_lines(template, values)).rstrip())
    return 0


def _render_checkpoint_lines(template: dict[str, Any], values: dict[str, str]) -> list[str]:
    title = template.get("title", template.get("name", "Template"))
    objective = _render_text(str(template.get("objective", "")), values)
    deliverables = _render_list(list(template.get("deliverables", [])), values)
    acceptance = _render_list(list(template.get("acceptance", [])), values)
    demo = _render_list(list(template.get("demo_commands", [])), values)
    evidence = _render_list(list(template.get("evidence", [])), values)

    lines: list[str] = []
    lines.append(f"### {title}")
    lines.append("")
    lines.append("* **Objective:**")
    lines.append(f"  {objective}")
    lines.append("")
    if deliverables:
        lines.append("* **Deliverables:**")
        for item in deliverables:
            lines.append(f"  * {item}")
        lines.append("")
    if acceptance:
        lines.append("* **Acceptance:**")
        for item in acceptance:
            lines.append(f"  * {item}")
        lines.append("")
    if demo:
        lines.append("* **Demo commands:**")
        for item in demo:
            lines.append(f"  * {item}")
        lines.append("")
    if evidence:
        lines.append("* **Evidence:**")
        for item in evidence:
            lines.append(f"  * {item}")
        lines.append("")

    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="checkpoint_templates",
        description="List and preview checkpoint templates.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="List available templates.")
    pl.set_defaults(fn=cmd_list)

    pp = sub.add_parser("preview", help="Preview a template with substitutions.")
    pp.add_argument("template", help="Template name (file stem).")
    pp.add_argument("params", nargs=argparse.REMAINDER, help="Template parameters.")
    pp.set_defaults(fn=cmd_preview)

    pi = sub.add_parser("instantiate", help="Instantiate a template with substitutions.")
    pi.add_argument("template", help="Template name (file stem).")
    pi.add_argument("params", nargs=argparse.REMAINDER, help="Template parameters.")
    pi.set_defaults(fn=cmd_instantiate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
