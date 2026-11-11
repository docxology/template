"""Bounded native tool input/output observations shared by the real supervisor.

These helpers retain DATA only. Actual Popen, guardian and live owner creation
remain in native_tool_process; no serialized observation grants that custody.
"""

from __future__ import annotations

import hashlib
import math
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_STREAM_BYTES = 8 * 1024 * 1024


def _physical_identity(path: Path) -> dict[str, int]:
    """Retain actual executable metadata; this grants no loaded-library proof."""
    metadata = path.stat()
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "links": metadata.st_nlink,
    }


def _nomination_observation(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": metadata.st_mode,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "ctime_ns": metadata.st_ctime_ns,
        "links": metadata.st_nlink,
        "symlink_target": os.readlink(path) if stat.S_ISLNK(metadata.st_mode) else None,
    }


def _stamp() -> dict[str, str | float]:
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
    }


def _remaining(deadline: float) -> float:
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("native tool requires the original finite absolute deadline")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("native tool exhausted its original admitted deadline")
    return remaining


def _stream(path: Path) -> tuple[dict[str, Any], str]:
    digest = hashlib.sha256()
    size, chunks = 0, []
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
            size += len(chunk)
            if size > MAX_STREAM_BYTES:
                raise ValueError("native tool stream exceeds its finite retained byte ceiling")
            chunks.append(chunk)
    raw = b"".join(chunks)
    return {"path": str(path), "sha256": digest.hexdigest(), "bytes": size}, raw.decode("utf-8", errors="replace")


def _stdin_observation(stream: Any, path: Path, deadline: float) -> dict[str, Any]:
    """Observe the exact held descriptor; the pathname cannot swap its body."""
    _remaining(deadline)
    before = os.fstat(stream.fileno())
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_STREAM_BYTES:
        raise ValueError("native stdin requires a bounded nonempty regular input")
    digest, count = hashlib.sha256(), 0
    while chunk := os.pread(stream.fileno(), 65536, count):
        _remaining(deadline)
        digest.update(chunk)
        count += len(chunk)
        if count > MAX_STREAM_BYTES:
            raise ValueError("native stdin exceeds the existing native stream ceiling")
    physical = _physical_identity(path)
    held = {
        "device": before.st_dev,
        "inode": before.st_ino,
        "mode": before.st_mode,
        "size": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
        "links": before.st_nlink,
    }
    after = os.fstat(stream.fileno())
    if (
        held != physical
        or any(
            getattr(before, key) != getattr(after, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
                "st_nlink",
            )
        )
        or count != before.st_size
    ):
        raise ValueError("native stdin descriptor/path changed during admission")
    return {
        "path": str(path),
        "sha256": digest.hexdigest(),
        "bytes": count,
        "identity": physical,
    }
