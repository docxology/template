"""Shared JSON coercion helpers for defensive parsing."""

from __future__ import annotations

from typing import Any


def mapping(value: object) -> dict[str, Any]:
    """Return *value* when it is a mapping, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def mapping_list(value: object) -> list[dict[str, Any]]:
    """Return dict rows from a list, ignoring non-mapping entries."""
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]
