"""Provider configuration loading/resolution for RLM."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_PROVIDER_CONFIG: dict[str, dict[str, Any]] = {
    "openai": {
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "timeout_s": 20,
    },
    "anthropic": {
        "model": "claude-3-5-haiku-latest",
        "base_url": "https://api.anthropic.com/v1",
        "api_key_env": "ANTHROPIC_API_KEY",
        "timeout_s": 20,
    },
    "google": {
        "model": "gemini-1.5-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_key_env": "GOOGLE_API_KEY",
        "timeout_s": 20,
    },
    "triton": {
        "model": "tensorrt_llm",
        "base_url": "http://localhost:8000",
        "timeout_s": 20,
        "codec": "raw_text",
        "input_name": "text_input",
    },
}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain JSON object: {path}")
    return payload


def _merge_config(target: dict[str, dict[str, Any]], incoming: dict[str, Any], source: str) -> None:
    providers = incoming.get("providers")
    if providers is None:
        return
    if not isinstance(providers, dict):
        raise ValueError(f"Config field 'providers' must be object in {source}")

    for provider_name, provider_cfg in providers.items():
        if provider_name not in target:
            target[provider_name] = {}
        if not isinstance(provider_cfg, dict):
            raise ValueError(f"Provider config for '{provider_name}' must be object in {source}")

        for key, value in provider_cfg.items():
            # Secrets are intentionally forbidden in config files.
            if key.lower() in {"api_key", "token", "secret"}:
                raise ValueError(
                    f"Provider '{provider_name}' in {source} contains inline secret field '{key}'. "
                    "Use env vars only."
                )
            target[provider_name][key] = value


def resolve_provider_config(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Resolve provider config from defaults + global + repo-local overlays.

    Precedence (lowest -> highest):
    1) in-code defaults
    2) ~/.vibe/providers.json
    3) <repo>/.vibe/rlm/providers.json
    """

    resolved = deepcopy(DEFAULT_PROVIDER_CONFIG)

    global_cfg_path = Path.home() / ".vibe" / "providers.json"
    repo_cfg_path = repo_root / ".vibe" / "rlm" / "providers.json"

    global_cfg = _read_json(global_cfg_path)
    if global_cfg is not None:
        _merge_config(resolved, global_cfg, str(global_cfg_path))

    repo_cfg = _read_json(repo_cfg_path)
    if repo_cfg is not None:
        _merge_config(resolved, repo_cfg, str(repo_cfg_path))

    return resolved

