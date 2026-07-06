"""Shared JSON artifact read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``; return ``{}`` when missing or invalid."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    """Alias for :func:`load_json`."""
    return load_json(path)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write ``payload`` as sorted JSON and return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
