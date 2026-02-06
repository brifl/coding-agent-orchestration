"""Shared HTTP request helpers for provider checks."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout_s: int) -> tuple[int, str, float]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url=url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        request.add_header(key, value)

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # nosec B310
            response_body = response.read().decode("utf-8", errors="replace")
            latency_ms = (time.perf_counter() - start) * 1000.0
            return int(response.status), response_body, latency_ms
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        latency_ms = (time.perf_counter() - start) * 1000.0
        return int(exc.code), response_body, latency_ms
    except urllib.error.URLError as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return 0, f"URLError: {exc.reason}", latency_ms
    except OSError as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return 0, f"OSError: {exc}", latency_ms
