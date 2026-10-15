"""Exact wheel/lock/RECORD physical comparisons; DATA, never Source authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_pdfium_provider import _file, _installed
from infrastructure.reporting.native_pdfium_source_wheel import inspect_pdfium_locked_wheel


def observe_provider_files(
    site: Path,
    wheel_path: Path,
    held_members: Mapping[str, bytes],
    held_wheel: dict[str, Any],
    held_installed: dict[str, Any],
    lock: bytes,
    *,
    deadline: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reobserve actual bytes and physical membership against already-held DATA."""
    remaining(deadline)
    raw, identity = _file(wheel_path, deadline)
    members, declared = inspect_pdfium_locked_wheel(wheel_path.name, raw, lock, deadline=deadline)
    wheel = {"path": str(wheel_path), **declared, "identity": identity}
    installed = _installed(site, members, deadline)
    if dict(held_members) != members or held_wheel != wheel or held_installed != installed:
        raise ValueError("PDFium actual selected namespace/wheel/RECORD/physical closure changed")
    remaining(deadline)
    return wheel, installed
