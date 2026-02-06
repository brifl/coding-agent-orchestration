#!/usr/bin/env python3
"""Health checks for configured RLM providers."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from providers import build_provider, provider_names  # type: ignore
from providers.base import ProviderCheckResult  # type: ignore
from providers.config import resolve_provider_config  # type: ignore

ACTIVE_PROVIDER_NAMES = ("openai", "anthropic", "google")
ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RLM provider health checks.")
    parser.add_argument(
        "--provider",
        default="all",
        help=(
            "Provider selection: all (active providers) | "
            "openai|anthropic|google|triton | comma-separated list"
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for .vibe/rlm/providers.json resolution",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to load before checks (default: .env)",
    )
    parser.add_argument(
        "--no-env-file",
        action="store_true",
        help="Disable dotenv loading even when --env-file is set",
    )
    return parser.parse_args(argv)


def _normalize_provider_selection(raw: str) -> list[str]:
    normalized = raw.strip().lower()
    if normalized in {"", "all"}:
        return list(ACTIVE_PROVIDER_NAMES)
    values = [item.strip().lower() for item in normalized.split(",") if item.strip()]
    valid = set(provider_names())
    invalid = [name for name in values if name not in valid]
    if invalid:
        raise ValueError(
            f"Unknown provider(s): {', '.join(invalid)}. Allowed: {', '.join(sorted(valid))}, all"
        )
    return values


def _resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (repo_root / path)


def _load_env_file(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    loaded = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not ENV_KEY_RE.match(key):
            continue
        value = value.strip().rstrip("\r")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        selected = _normalize_provider_selection(args.provider)
        config = resolve_provider_config(repo_root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not args.no_env_file and args.env_file:
        env_path = _resolve_path(args.env_file, repo_root)
        _load_env_file(env_path)

    results: list[dict[str, Any]] = []
    failures = 0

    for name in selected:
        provider_cfg = config.get(name, {})
        provider = build_provider(name, provider_cfg)
        try:
            result = provider.check()
        except Exception as exc:  # noqa: BLE001
            result = ProviderCheckResult(
                provider=name,
                ok=False,
                detail=f"Unhandled {type(exc).__name__} during provider check.",
            )
        payload = result.to_dict()
        results.append(payload)
        if not result.ok:
            failures += 1

    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
