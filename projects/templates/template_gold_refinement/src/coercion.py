from __future__ import annotations

from typing import Any


TRUE_STRINGS = frozenset({"true", "yes", "on", "1"})
FALSE_STRINGS = frozenset({"false", "no", "off", "0"})


def coerce_bool(value: Any, *, default: bool, field_name: str) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(f"{field_name} must be a boolean value, got {value!r}")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_STRINGS:
            return True
        if normalized in FALSE_STRINGS:
            return False
        raise ValueError(f"{field_name} must be a boolean value, got {value!r}")
    raise ValueError(f"{field_name} must be a boolean value, got {type(value).__name__}")


__all__ = ["coerce_bool"]
