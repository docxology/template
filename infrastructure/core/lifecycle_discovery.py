"""Discover top-level entries under ``projects/`` for pipeline discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from infrastructure.core.project_paths import NON_RENDERED_SUBDIRS
from infrastructure.project.validation import validate_project_structure

EntryKind = Literal["standalone", "program"]


@dataclass(frozen=True)
class LifecycleDiscoveryConfig:
    """Data container for LifecycleDiscoveryConfig."""

    non_rendered_subdirs: frozenset[str] = field(default_factory=lambda: NON_RENDERED_SUBDIRS)
    skip_dot_prefixed: bool = True


@dataclass(frozen=True)
class ProgramEntry:
    """Data container for ProgramEntry."""

    name: str
    path: Path
    kind: EntryKind


def discover_program_entries(
    projects_dir: Path,
    config: LifecycleDiscoveryConfig | None = None,
) -> list[ProgramEntry]:
    """Process discover program entries."""
    cfg = config or LifecycleDiscoveryConfig()
    if not projects_dir.is_dir():
        return []
    entries: list[ProgramEntry] = []
    for child in sorted(projects_dir.iterdir()):
        if not child.is_dir():
            continue
        if cfg.skip_dot_prefixed and child.name.startswith("."):
            continue
        if child.name in cfg.non_rendered_subdirs:
            continue
        is_valid, _ = validate_project_structure(child)
        kind: EntryKind = "standalone" if is_valid else "program"
        entries.append(ProgramEntry(name=child.name, path=child, kind=kind))
    return entries


__all__ = [
    "EntryKind",
    "LifecycleDiscoveryConfig",
    "ProgramEntry",
    "discover_program_entries",
]
