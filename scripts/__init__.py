"""Scripts package - entry point orchestrators for the build pipeline.

This package contains thin orchestrators that coordinate the template's
build pipeline stages. All business logic is in infrastructure/ modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_logger = logging.getLogger(__name__)


def ensure_repo_root_on_path() -> Path:
    """Prepend the repository root to ``sys.path`` and return the Path.

    Idempotent — subsequent calls do not re-insert if already present. Lets each
    script in this package be runnable directly (``python scripts/foo.py``) while
    still importing ``infrastructure`` and ``projects`` as top-level packages.

    Returns:
        The absolute :class:`Path` to the repository root.
    """
    repo_root = Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    return repo_root


# Note: the former MENU_SCRIPT_MAPPING / PipelineStageDefinition were removed —
# they had zero functional consumers and had drifted from the live interactive
# menu, whose single source of truth is infrastructure.orchestration.menu.MENU_OPTIONS.
__all__ = [
    "ensure_repo_root_on_path",
]
