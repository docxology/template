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


def load_json_strict(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``, failing loudly on malformed content.

    Returns ``{}`` when the file is missing, mirroring :func:`load_json`, but a
    present-yet-unparseable artifact raises ``ValueError`` instead of being
    silently treated as empty. Gates that must fail closed on a corrupted or
    truncated artifact use this variant so a bad file cannot masquerade as an
    absent one.
    """
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"malformed JSON artifact: {path}") from exc
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    """Alias for :func:`load_json`."""
    return load_json(path)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write ``payload`` as sorted JSON and return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
