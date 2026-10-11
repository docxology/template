"""Bounded owner-controlled installed preparation capacity; no cleanup authority."""

from __future__ import annotations

import shutil
from pathlib import Path

from infrastructure.project.public_reference_git import remaining

RESERVE_BYTES = 2 * 1024**3
PREPARATION_PEAK_BYTES = 8 * 1024**3
TRANSPORT_PEAK_BYTES = 16 * 1024**3


def require_native_capacity(path: Path, *, peak_bytes: int, deadline: float) -> None:
    """Refuse before allocation unless the original volume retains its reserve.

    These are declared finite disk peaks, not measurements or memory admission.
    This function never removes earlier evidence or changes another owner.
    """
    remaining(deadline)
    if peak_bytes not in (PREPARATION_PEAK_BYTES, TRANSPORT_PEAK_BYTES):
        raise ValueError("native allocation requires a Source-declared capacity phase")
    probe = path.absolute()
    while not probe.exists():
        probe = probe.parent
    if shutil.disk_usage(probe).free < RESERVE_BYTES + peak_bytes:
        raise ValueError("native preparation cannot retain the2GiB reserve plus its declared bounded peak")
    remaining(deadline)
