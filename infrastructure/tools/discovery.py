"""Tool discovery for multi-tool support.

Scans the tools/ directory for valid tools (executable entry points) and returns
ToolInfo objects. Follows the same architecture as infrastructure/fonds/discovery.py
but for executable entry points rather than passive data stores.
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
from infrastructure.tools.tools_info import ToolInfo, build_tool_info
from infrastructure.tools.validation import validate_tool_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``tools/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired tools.
NON_RENDERED_TOOL_SUBDIRS = POOL_NON_RENDERED_SUBDIRS

#: Rendered subdirectories under ``tools/``.
RENDERED_TOOL_SUBDIRS = POOL_RENDERED_SUBDIRS

#: Public API of this module.
__all__ = [
    "NON_RENDERED_TOOL_SUBDIRS",
    "RENDERED_TOOL_SUBDIRS",
    "discover_tools",
    "resolve_tool_root",
]


def discover_tools(
    repo_root: Path | str,
) -> list[ToolInfo]:
    """Discover all valid tools in the tools/ directory.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of ToolInfo objects for valid tools.

    The lifecycle subfolders in :data:`NON_RENDERED_TOOL_SUBDIRS`
    (``working``/``archive``) are deliberately excluded from discovery.
    """
    return discover_lifecycle_items(
        Path(repo_root) / "tools",
        validate_tool_structure,
        build_tool_info,
        excluded=NON_RENDERED_TOOL_SUBDIRS,
        kind="tool",
        logger=logger,
    )


def resolve_tool_root(repo_root: Path | str, tool_name: str) -> Path:
    """Resolve a tool directory by qualified name.

    A qualified ``<subfolder>/<name>`` path (head in ``templates/``, ``working/``,
    ``archive/``) resolves directly under ``tools/<subfolder>/<name>``. A bare name
    prefers ``tools/templates/<name>``, then a flat standalone ``tools/<name>``.

    Args:
        repo_root: Repository root directory.
        tool_name: Tool name or qualified path.

    Returns:
        Absolute resolved path to the tool directory.
    """
    return resolve_pool_root(
        Path(repo_root) / "tools",
        tool_name,
        NON_RENDERED_TOOL_SUBDIRS | RENDERED_TOOL_SUBDIRS,
    )
