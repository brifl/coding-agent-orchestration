"""Provider registry for RLM tooling."""

from __future__ import annotations

from typing import Any

from .anthropic_provider import AnthropicProvider
from .base import Provider
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider
from .triton_provider import TritonProvider


def build_provider(name: str, config: dict[str, Any]) -> Provider:
    normalized = name.strip().lower()
    if normalized == "openai":
        return OpenAIProvider(config)
    if normalized == "anthropic":
        return AnthropicProvider(config)
    if normalized == "google":
        return GoogleProvider(config)
    if normalized == "triton":
        return TritonProvider(config)
    raise ValueError(f"Unknown provider '{name}'.")


def provider_names() -> tuple[str, ...]:
    return ("openai", "anthropic", "google", "triton")
