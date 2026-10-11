"""Bounded, traversal-safe ZIP member admission shared across layers.

Rendering reads Office packages and reporting, publishing and project
acceptance read native release archives. All of them admit members through
this one check so none of those layers has to import another to share it.
"""

from __future__ import annotations

import zipfile
from pathlib import Path


def bounded_members(archive: zipfile.ZipFile) -> set[str]:
    """Reject malformed members and unbounded native archive expansion."""
    members = archive.infolist()
    all_names = [item.filename for item in members]
    if (
        len(all_names) != len(set(all_names))
        or sum(item.file_size for item in members) > 64 * 1024 * 1024
        or any(
            not Path(name).parts
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or "\\" in name
            or "\x00" in name
            for name in all_names
        )
        or any(item.external_attr >> 16 & 0o170000 == 0o120000 for item in members)
    ):
        raise ValueError("native archive contains unsafe, duplicate or unbounded members")
    if archive.testzip() is not None:
        raise ValueError("native archive member CRC is invalid")
    return {item.filename for item in members if not item.is_dir()}


__all__ = ["bounded_members"]
