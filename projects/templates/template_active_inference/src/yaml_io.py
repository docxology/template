"""Shared YAML artifact read helpers with mtime/size memoization."""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache(maxsize=256)
def _parse_yaml_cached(path_str: str, _mtime_ns: int, _size: int) -> dict[str, Any]:
    """Parse a YAML file, memoized on (path, mtime, size)."""
    try:
        data = yaml.safe_load(Path(path_str).read_text(encoding="utf-8")) or {}
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
        stat = path.stat()
        loaded = copy.deepcopy(_parse_yaml_cached(str(path.resolve()), stat.st_mtime_ns, stat.st_size))
    except (OSError, ValueError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    return dict(loaded)


def read_yaml(path: Path) -> dict[str, Any]:
    """Alias for :func:`load_yaml`."""
    return load_yaml(path)


__all__ = ["load_yaml", "read_yaml"]
