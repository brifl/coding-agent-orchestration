"""Shared helpers for concise, consistent CLI error rendering."""
from __future__ import annotations


def format_cli_error(exc: BaseException) -> str:
    """Return a stable one-line error description for command handlers."""
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return type(exc).__name__

