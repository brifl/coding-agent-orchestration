"""Triton HTTP provider health check."""

from __future__ import annotations

from typing import Any

from .base import Provider, ProviderCheckResult
from .http_utils import post_json


class TritonProvider(Provider):
    name = "triton"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def check(self) -> ProviderCheckResult:
        base_url = str(self.config.get("base_url", "http://localhost:8000")).rstrip("/")
        model = str(self.config.get("model", "tensorrt_llm"))
        timeout_s = int(self.config.get("timeout_s", 20))
        codec = str(self.config.get("codec", "raw_text"))
        input_name = str(self.config.get("input_name", "text_input"))

        if codec != "raw_text":
            return ProviderCheckResult(
                provider=self.name,
                ok=False,
                detail=f"Unsupported Triton codec '{codec}' (expected raw_text).",
            )

        url = f"{base_url}/v2/models/{model}/infer"
        payload = {
            "inputs": [
                {
                    "name": input_name,
                    "shape": [1],
                    "datatype": "BYTES",
                    "data": ["ping"],
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
