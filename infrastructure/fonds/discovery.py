"""Fond discovery for multi-fond support.

Scans the fonds/ directory for valid fonds (passive resource pools) and returns
FondInfo objects. Follows the same architecture as infrastructure/project/discovery.py
but for passive data stores instead of executable projects.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.lifecycle_discovery import (
    POOL_NON_RENDERED_SUBDIRS,
    POOL_RENDERED_SUBDIRS,
    discover_lifecycle_items,
    resolve_pool_root,
)
from infrastructure.core.logging.utils import get_logger
from infrastructure.fonds.fonds_info import FondInfo, build_fond_info
from infrastructure.fonds.validation import validate_fond_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``fonds/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired fonds.
NON_RENDERED_FOND_SUBDIRS = POOL_NON_RENDERED_SUBDIRS

#: Rendered subdirectories under ``fonds/``.
RENDERED_FOND_SUBDIRS = POOL_RENDERED_SUBDIRS

#: Public API of this module.
__all__ = [
    "NON_RENDERED_FOND_SUBDIRS",
    "RENDERED_FOND_SUBDIRS",
    "discover_fonds",
    "resolve_fond_root",
]


def discover_fonds(
    repo_root: Path | str,
) -> list[FondInfo]:
    """Discover all valid fonds in the fonds/ directory.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of FondInfo objects for valid fonds.

    The lifecycle subfolders in :data:`NON_RENDERED_FOND_SUBDIRS`
    (``working``/``archive``) are deliberately excluded from discovery.
    """
    return discover_lifecycle_items(
        Path(repo_root) / "fonds",
        validate_fond_structure,
        build_fond_info,
        excluded=NON_RENDERED_FOND_SUBDIRS,
        kind="fond",
        logger=logger,
    )


def resolve_fond_root(repo_root: Path | str, fond_name: str) -> Path:
    """Resolve a fond directory by qualified name.

    A qualified ``<subfolder>/<name>`` path (head in ``templates/``, ``working/``)
    resolves directly under ``fonds/<subfolder>/<name>``. A bare name prefers
    ``fonds/templates/<name>``, then a flat standalone ``fonds/<name>``.

    Args:
        repo_root: Repository root directory.
        fond_name: Fond name or qualified path.

    Returns:
        Absolute resolved path to the fond directory.
    """
    return resolve_pool_root(
        Path(repo_root) / "fonds",
        fond_name,
        NON_RENDERED_FOND_SUBDIRS | RENDERED_FOND_SUBDIRS,
    )
