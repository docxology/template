"""Fonds infrastructure — stable pools of reusable research resources.

Provides fond discovery, validation, sidecar symlink sync, and public-scope
helpers for the ``fonds/`` top-level directory, mirroring the architecture
of ``infrastructure/project/`` but for passive data stores rather than
executable code projects.

Usage::

    from infrastructure.fonds import (
        FondInfo,
        discover_fonds,
        resolve_fond_root,
        validate_fond_structure,
    )
"""

from infrastructure.fonds.discovery import discover_fonds, resolve_fond_root
from infrastructure.fonds.fonds_info import FondInfo, build_fond_info
from infrastructure.fonds.validation import validate_fond_structure

__all__ = [
    "FondInfo",
    "build_fond_info",
    "discover_fonds",
    "resolve_fond_root",
    "validate_fond_structure",
]
