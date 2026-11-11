"""FondInfo dataclass for representing discovered fonds (resource pools).

A fond is a stable pool of reusable research resources — bibliographies,
contact registries, dataset catalogs, literature databases — distinct from
executable research projects.
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FondInfo:
    """Information about a discovered fond.

    Attributes:
        name: Fond directory name
        path: Absolute path to fond directory
        fond_type: Resource type (bibliography, contacts, datasets, etc.)
        has_data: Whether fond has data/ directory
        has_manuscript: Whether fond has manuscript/ directory
        metadata: Raw metadata dict from fonds.yaml
        program: Parent program directory name (empty for standalone fonds)
    """

    name: str
    path: Path
    fond_type: str = "generic"
    has_data: bool = False
    has_manuscript: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    program: str = ""

    @property
    def qualified_name(self) -> str:
        """Full path-like name for display and selection."""
        if self.program:
            return f"{self.program}/{self.name}"
        return self.name

    @property
    def is_valid(self) -> bool:
        """Fond is valid if it has a data/ directory."""
        return self.has_data


def build_fond_info(fond_dir: Path, program: str = "") -> FondInfo:
    """Build a FondInfo from a validated fond directory.

    Args:
        fond_dir: Path to the fond directory.
        program: Parent program directory name (empty for standalone fonds).

    Returns:
        Populated FondInfo instance.
    """
    metadata = _load_fond_manifest(fond_dir)
    return FondInfo(
        name=fond_dir.name,
        path=fond_dir,
        fond_type=metadata.get("type", "generic") if metadata else "generic",
        has_data=(fond_dir / "data").exists(),
        has_manuscript=(fond_dir / "manuscript").exists(),
        metadata=metadata or {},
        program=program,
    )


def _load_fond_manifest(fond_dir: Path) -> dict[str, Any] | None:
    """Load fonds.yaml if present.

    Args:
        fond_dir: Path to the fond directory.

    Returns:
        Parsed YAML dict or None if the file is absent or unreadable.
    """
    manifest_path = fond_dir / "fonds.yaml"
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                return loaded if isinstance(loaded, dict) else None
        except Exception:  # noqa: BLE001
            return None
    return None


__all__ = [
    "FondInfo",
    "build_fond_info",
]
