"""Shared row-summary predicates for roadmap artifact validators."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


Row = dict[str, Any]


def rows(payload: dict[str, Any], key: str = "rows") -> list[Row]:
    """Return a payload row list with a stable empty-list fallback."""
    values = payload.get(key) or []
    return [row for row in values if isinstance(row, dict)]


def all_rows(payload: dict[str, Any], predicate: Callable[[Row], bool], key: str = "rows") -> bool:
    """True only when the payload has rows and every row satisfies ``predicate``."""
    payload_rows = rows(payload, key)
    return bool(payload_rows) and all(predicate(row) for row in payload_rows)


def all_field_present(payload: dict[str, Any], fields: Iterable[str], key: str = "rows") -> bool:
    """True iff every row has truthy values for all requested fields."""
    required = tuple(fields)
    return all_rows(payload, lambda row: all(bool(row.get(field)) for field in required), key=key)
