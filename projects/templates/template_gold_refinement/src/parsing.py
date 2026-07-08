"""Shared parsing and I/O helpers for the gold-refinement exemplar."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml

try:
    from .coercion import coerce_bool
except ImportError:
    from coercion import coerce_bool  # type: ignore[no-redef]


def build_timestamp() -> str:
    """Build timestamp."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_yaml_dict(path: Path) -> dict[str, Any]:
    """Load yaml dict from a file."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def load_manuscript_config(project_root: Path) -> dict[str, Any]:
    """Load manuscript config from a file."""
    return load_yaml_dict(project_root / "manuscript" / "config.yaml")


def load_json_object(path: Path) -> dict[str, Any]:
    """Load json object from a file."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def as_str_tuple(value: Any) -> tuple[str, ...]:
    """Process as str tuple."""
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def as_int_tuple(value: Any) -> tuple[int, ...]:
    """Process as int tuple."""
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(int(item) for item in value if str(item).strip())
    return ()


def as_float(value: Any, default: float = 0.0) -> float:
    """Process as float."""
    if value is None:
        return default
    return float(value)


def as_bool(value: Any, default: bool = False, *, field_name: str) -> bool:
    """Process as bool."""
    return coerce_bool(value, default=default, field_name=field_name)
