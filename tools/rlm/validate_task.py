#!/usr/bin/env python3
"""Validate RLM task JSON files with fail-fast, file/line diagnostics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOP_LEVEL_REQUIRED = (
    "task_id",
    "query",
    "context_sources",
    "bundle",
    "mode",
    "provider_policy",
    "limits",
    "outputs",
    "trace",
)

ALLOWED_MODES = {"baseline", "subcalls"}


@dataclass(frozen=True)
class Diagnostic:
    field: str
    line: int
    message: str


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _build_line_index(raw: str) -> dict[str, int]:
    index: dict[str, int] = {}
    key_re = re.compile(r'"([^"\\]+)"\s*:')
    for lineno, line in enumerate(raw.splitlines(), start=1):
        match = key_re.search(line)
        if not match:
            continue
        key = match.group(1)
        # First match is enough for readable diagnostics.
        index.setdefault(key, lineno)
    return index


def _line_for(field: str, line_index: dict[str, int], default: int = 1) -> int:
    leaf = field.split(".")[-1].split("[")[0]
    return line_index.get(leaf, default)


def _add_error(errors: list[Diagnostic], field: str, msg: str, line_index: dict[str, int]) -> None:
    errors.append(Diagnostic(field=field, line=_line_for(field, line_index), message=msg))


def _ensure_string_list(
    value: Any,
    field: str,
    errors: list[Diagnostic],
    line_index: dict[str, int],
    *,
    allow_empty: bool,
) -> None:
    if not isinstance(value, list):
        _add_error(errors, field, f"Field '{field}' must be an array.", line_index)
        return
    if not allow_empty and not value:
        _add_error(errors, field, f"Field '{field}' must not be empty.", line_index)
        return
    for idx, item in enumerate(value):
        if not _is_nonempty_string(item):
            _add_error(
                errors,
                f"{field}[{idx}]",
                f"{field}[{idx}] must be a non-empty string.",
                line_index,
            )


def _validate_context_sources(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, list):
        _add_error(errors, "context_sources", "Field 'context_sources' must be an array.", line_index)
        return
    if not value:
        _add_error(errors, "context_sources", "Field 'context_sources' must not be empty.", line_index)
        return

    for idx, item in enumerate(value):
        field_prefix = f"context_sources[{idx}]"
        if not isinstance(item, dict):
            _add_error(errors, field_prefix, f"{field_prefix} must be an object.", line_index)
            continue
        source_type = item.get("type")
        source_path = item.get("path")
        if not _is_nonempty_string(source_type):
            _add_error(
                errors,
                f"{field_prefix}.type",
                f"{field_prefix}.type must be a non-empty string.",
                line_index,
            )
        if not _is_nonempty_string(source_path):
            _add_error(
                errors,
                f"{field_prefix}.path",
                f"{field_prefix}.path must be a non-empty string.",
                line_index,
            )
        include = item.get("include")
        if include is not None:
            _ensure_string_list(
                include,
                f"{field_prefix}.include",
                errors,
                line_index,
                allow_empty=True,
            )
        exclude = item.get("exclude")
        if exclude is not None:
            _ensure_string_list(
                exclude,
                f"{field_prefix}.exclude",
                errors,
                line_index,
                allow_empty=True,
            )


def _validate_bundle(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, dict):
        _add_error(errors, "bundle", "Field 'bundle' must be an object.", line_index)
        return

    strategy = value.get("chunking_strategy")
    max_chars = value.get("max_chars")
    if not _is_nonempty_string(strategy):
        _add_error(
            errors,
            "bundle.chunking_strategy",
            "Field 'bundle.chunking_strategy' must be a non-empty string.",
            line_index,
        )
    if not _is_int(max_chars) or max_chars <= 0:
        _add_error(
            errors,
            "bundle.max_chars",
            "Field 'bundle.max_chars' must be an integer >= 1.",
            line_index,
        )


def _validate_provider_policy(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, dict):
        _add_error(errors, "provider_policy", "Field 'provider_policy' must be an object.", line_index)
        return

    primary = value.get("primary")
    if not _is_nonempty_string(primary):
        _add_error(
            errors,
            "provider_policy.primary",
            "Field 'provider_policy.primary' must be a non-empty string.",
            line_index,
        )

    allowed = value.get("allowed")
    _ensure_string_list(allowed, "provider_policy.allowed", errors, line_index, allow_empty=False)
    fallback = value.get("fallback")
    _ensure_string_list(fallback, "provider_policy.fallback", errors, line_index, allow_empty=True)

    if _is_nonempty_string(primary) and isinstance(allowed, list):
        normalized_primary = str(primary).strip().lower()
        normalized_allowed = {
            str(item).strip().lower()
            for item in allowed
            if _is_nonempty_string(item)
        }
        if normalized_primary not in normalized_allowed:
            _add_error(
                errors,
                "provider_policy.primary",
                "Field 'provider_policy.primary' must be present in provider_policy.allowed.",
                line_index,
            )

    if isinstance(allowed, list) and isinstance(fallback, list):
        normalized_allowed = {
            str(item).strip().lower()
            for item in allowed
            if _is_nonempty_string(item)
        }
        for idx, item in enumerate(fallback):
            if not _is_nonempty_string(item):
                continue
            normalized_item = str(item).strip().lower()
            if normalized_item not in normalized_allowed:
                _add_error(
                    errors,
                    f"provider_policy.fallback[{idx}]",
                    "provider_policy.fallback entries must also be present in provider_policy.allowed.",
                    line_index,
                )



def _validate_limits(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, dict):
        _add_error(errors, "limits", "Field 'limits' must be an object.", line_index)
        return

    numeric_specs = {
        "max_root_iters": 1,
        "max_depth": 0,
        "max_subcalls_total": 0,
        "max_subcalls_per_iter": 0,
        "timeout_s": 1,
        "max_stdout_chars": 1,
    }
    for key, minimum in numeric_specs.items():
        raw = value.get(key)
        if not _is_int(raw) or raw < minimum:
            _add_error(
                errors,
                f"limits.{key}",
                f"Field 'limits.{key}' must be an integer >= {minimum}.",
                line_index,
            )


def _validate_outputs(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, dict):
        _add_error(errors, "outputs", "Field 'outputs' must be an object.", line_index)
        return

    final_path = value.get("final_path")
    artifact_paths = value.get("artifact_paths")
    if not _is_nonempty_string(final_path):
        _add_error(
            errors,
            "outputs.final_path",
            "Field 'outputs.final_path' must be a non-empty string.",
            line_index,
        )
    _ensure_string_list(artifact_paths, "outputs.artifact_paths", errors, line_index, allow_empty=True)


def _validate_trace(value: Any, errors: list[Diagnostic], line_index: dict[str, int]) -> None:
    if not isinstance(value, dict):
        _add_error(errors, "trace", "Field 'trace' must be an object.", line_index)
        return

    trace_path = value.get("trace_path")
    redaction_mode = value.get("redaction_mode")
    if not _is_nonempty_string(trace_path):
        _add_error(
            errors,
            "trace.trace_path",
            "Field 'trace.trace_path' must be a non-empty string.",
            line_index,
        )
    if not _is_nonempty_string(redaction_mode):
        _add_error(
            errors,
            "trace.redaction_mode",
            "Field 'trace.redaction_mode' must be a non-empty string.",
            line_index,
        )


def validate_task(task: Any, line_index: dict[str, int]) -> list[Diagnostic]:
    errors: list[Diagnostic] = []
    if not isinstance(task, dict):
        _add_error(errors, "<root>", "Task document must be a JSON object.", line_index)
        return errors

    for key in TOP_LEVEL_REQUIRED:
        if key not in task:
            _add_error(errors, key, f"Missing required top-level field '{key}'.", line_index)

    task_id = task.get("task_id")
    if task_id is not None and not _is_nonempty_string(task_id):
        _add_error(errors, "task_id", "Field 'task_id' must be a non-empty string.", line_index)

    query = task.get("query")
    if query is not None and not _is_nonempty_string(query):
        _add_error(errors, "query", "Field 'query' must be a non-empty string.", line_index)

    mode = task.get("mode")
    if mode is not None:
        if not _is_nonempty_string(mode):
            _add_error(errors, "mode", "Field 'mode' must be a non-empty string.", line_index)
        elif mode not in ALLOWED_MODES:
            _add_error(
                errors,
                "mode",
                "Field 'mode' must be one of: baseline, subcalls.",
                line_index,
            )

    _validate_context_sources(task.get("context_sources"), errors, line_index)
    _validate_bundle(task.get("bundle"), errors, line_index)
    _validate_provider_policy(task.get("provider_policy"), errors, line_index)
    _validate_limits(task.get("limits"), errors, line_index)
    _validate_outputs(task.get("outputs"), errors, line_index)
    _validate_trace(task.get("trace"), errors, line_index)

    return errors


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate RLM task schema.")
    parser.add_argument("task", help="Path to task JSON file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    task_path = Path(args.task)

    try:
        raw = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read task file '{task_path}': {exc}", file=sys.stderr)
        return 1

    line_index = _build_line_index(raw)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"INVALID: {task_path}")
        print(f"{task_path}:{exc.lineno}: invalid JSON ({exc.msg}).")
        return 1

    errors = validate_task(payload, line_index)
    if errors:
        print(f"INVALID: {task_path}")
        for err in errors:
            print(f"{task_path}:{err.line}: {err.message} (field: {err.field})")
        return 1

    print(f"VALID: {task_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
