"""Atomic, deterministic file I/O helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_text_atomic(path: Path, content: str) -> Path:
    """Write ``content`` to ``path`` atomically (temp file + rename).

    Creates parent directories as needed. Returns the written path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return path


def read_text(path: Path) -> str:
    """Read UTF-8 text from ``path``."""
    return Path(path).read_text(encoding="utf-8")
