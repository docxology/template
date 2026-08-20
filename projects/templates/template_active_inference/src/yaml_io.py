"""Shared YAML artifact read helpers with content-safe memoization."""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache(maxsize=256)
def _parse_yaml_cached(path_str: str, payload: bytes) -> dict[str, Any]:
    """Parse exact YAML bytes, memoized on (path, content)."""
    del path_str
    try:
        data = yaml.safe_load(payload.decode("utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    if not isinstance(data, dict):
        return {}
    return dict(data)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from ``path``; return ``{}`` when missing or invalid."""
    if not path.is_file():
        return {}
    try:
        loaded = copy.deepcopy(_parse_yaml_cached(str(path.resolve()), path.read_bytes()))
    except (OSError, ValueError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    return dict(loaded)


def read_yaml(path: Path) -> dict[str, Any]:
    """Alias for :func:`load_yaml`."""
    return load_yaml(path)


__all__ = ["load_yaml", "read_yaml"]
