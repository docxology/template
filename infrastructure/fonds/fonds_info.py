"""FondInfo dataclass for representing discovered fonds (resource pools).

A fond is a stable pool of reusable research resources — bibliographies,
contact registries, dataset catalogs, literature databases — distinct from
executable research projects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.files.serialization import load_optional_resource_metadata


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
    metadata = load_optional_resource_metadata(fond_dir / "fonds.yaml")
    return FondInfo(
        name=fond_dir.name,
        path=fond_dir,
        fond_type=metadata.get("type", "generic"),
        has_data=(fond_dir / "data").exists(),
        has_manuscript=(fond_dir / "manuscript").exists(),
        metadata=metadata,
        program=program,
    )


__all__ = [
    "FondInfo",
    "build_fond_info",
]
