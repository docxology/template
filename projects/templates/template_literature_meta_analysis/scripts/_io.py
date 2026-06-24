"""Shared JSON I/O helpers for orchestrator scripts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


def load_json(path: Path, *, logger: logging.Logger | None = None) -> dict[str, Any]:
    """Load JSON from *path*; return empty dict when missing."""
    log = logger or logging.getLogger("scripts._io")
    if not path.exists():
        log.warning("%s not found, skipping", path)
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """Write *data* as JSON to *path*, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent)
