"""Base provider interfaces for RLM subcall integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCheckResult:
    provider: str
    ok: bool
    detail: str
    status_code: int | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": self.provider,
            "ok": self.ok,
            "detail": self.detail,
        }
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.latency_ms is not None:
            payload["latency_ms"] = round(float(self.latency_ms), 2)
        return payload


class Provider(ABC):
    """Unified provider interface for health checks and subcalls."""

    name: str

    @abstractmethod
    def check(self) -> ProviderCheckResult:
        """Run a lightweight health check against the provider endpoint."""

