#!/usr/bin/env python3
"""Health checks for configured RLM providers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from providers import build_provider, provider_names  # type: ignore
from providers.config import resolve_provider_config  # type: ignore


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RLM provider health checks.")
    parser.add_argument(
        "--provider",
        default="all",
        help="Provider to check: openai|anthropic|google|triton|all",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root for .vibe/rlm/providers.json resolution",
    )
    return parser.parse_args(argv)


def _normalize_provider_selection(raw: str) -> list[str]:
    normalized = raw.strip().lower()
    if normalized in {"", "all"}:
        return list(provider_names())
    values = [item.strip().lower() for item in normalized.split(",") if item.strip()]
    valid = set(provider_names())
    invalid = [name for name in values if name not in valid]
    if invalid:
        raise ValueError(
            f"Unknown provider(s): {', '.join(invalid)}. Allowed: {', '.join(sorted(valid))}, all"
        )
    return values


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    try:
        selected = _normalize_provider_selection(args.provider)
        config = resolve_provider_config(repo_root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    failures = 0

    for name in selected:
        provider_cfg = config.get(name, {})
        provider = build_provider(name, provider_cfg)
        result = provider.check()
        payload = result.to_dict()
        results.append(payload)
        if not result.ok:
            failures += 1

    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
