"""Google Gemini provider health check."""

from __future__ import annotations

import os
from typing import Any

from .base import Provider, ProviderCheckResult
from .http_utils import post_json


class GoogleProvider(Provider):
    name = "google"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def check(self) -> ProviderCheckResult:
        api_key_env = str(self.config.get("api_key_env", "GOOGLE_API_KEY"))
        api_key = os.getenv(api_key_env)
        if not api_key:
            return ProviderCheckResult(
                provider=self.name,
                ok=False,
                detail=f"Missing required env var: {api_key_env}",
            )

        base_url = str(
            self.config.get("base_url", "https://generativelanguage.googleapis.com/v1beta")
        ).rstrip("/")
        model = str(self.config.get("model", "gemini-1.5-flash"))
        timeout_s = int(self.config.get("timeout_s", 20))
        url = f"{base_url}/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "ping"},
                    ]
                }
            ]
        }
        headers: dict[str, str] = {}

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
