"""Anthropic provider health check."""

from __future__ import annotations

import os
from typing import Any

from .base import Provider, ProviderCheckResult
from .http_utils import post_json


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def check(self) -> ProviderCheckResult:
        api_key_env = str(self.config.get("api_key_env", "ANTHROPIC_API_KEY"))
        api_key = os.getenv(api_key_env)
        if not api_key:
            return ProviderCheckResult(
                provider=self.name,
                ok=False,
                detail=f"Missing required env var: {api_key_env}",
            )

        base_url = str(self.config.get("base_url", "https://api.anthropic.com/v1")).rstrip("/")
        model = str(self.config.get("model", "claude-3-5-haiku-latest"))
        timeout_s = int(self.config.get("timeout_s", 20))
        url = f"{base_url}/messages"

        payload = {
            "model": model,
            "max_tokens": 8,
            "messages": [
                {"role": "user", "content": "ping"},
            ],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

        status_code, response_text, latency_ms = post_json(url, payload, headers, timeout_s)
        ok = 200 <= status_code < 300
        detail = "ok" if ok else f"HTTP {status_code}: {response_text[:240]}"
        return ProviderCheckResult(
            provider=self.name,
            ok=ok,
            detail=detail,
            status_code=status_code,
            latency_ms=latency_ms,
        )
