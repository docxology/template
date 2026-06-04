"""JSON/text I/O helpers for AutoResearch artifact writers."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, payload: object) -> Path:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    """Write text payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def relative_path(project_root: Path, path: Path) -> str:
    """Return a project-relative path string when possible."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)
