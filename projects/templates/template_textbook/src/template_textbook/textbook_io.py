"""Atomic, deterministic file I/O helpers.

All writes go through a temp-file-plus-rename protocol so readers never see a
partial file, and any failure between ``write`` and ``rename`` is automatically
cleaned up by the ``finally`` block.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_text_atomic(path: Path, content: str) -> Path:
    """Write ``content`` to ``path`` atomically (temp file + rename).

    Creates parent directories as needed. The temp file is written to the same
    directory as the target so the rename is atomic on POSIX systems (same
    filesystem).  Any leftover temp file is removed on failure.

    Args:
        path: Destination path (created if it doesn't exist).
        content: UTF-8 text content to write.

    Returns:
        The written path (same as ``path``).
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


__all__ = ["read_text", "write_text_atomic"]
