"""No-op-aware, confined publication HTML writes."""

from __future__ import annotations

from pathlib import Path
import stat

from infrastructure.core.files.secure_write import atomic_write_text_confined


def write_if_changed(path: Path, content: str) -> None:
    """Atomically replace changed HTML, retaining its mode and unchanged mtime.

    The confined writer owns an exclusive temporary file in the same directory;
    predictable temporary names cannot redirect writes or collide with peers.
    """
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"HTML write target must be a regular file: {path}")
    if content == path.read_text(encoding="utf-8"):
        return
    atomic_write_text_confined(path.parent, path, content, mode=stat.S_IMODE(metadata.st_mode))
