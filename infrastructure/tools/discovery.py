"""Tool discovery for multi-tool support.

Scans the tools/ directory for valid tools (executable entry points) and returns
ToolInfo objects. Follows the same architecture as infrastructure/fonds/discovery.py
but for executable entry points rather than passive data stores.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.tools.tools_info import ToolInfo, build_tool_info
from infrastructure.tools.validation import validate_tool_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``tools/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired tools.
NON_RENDERED_TOOL_SUBDIRS: frozenset[str] = frozenset({"working", "archive"})

#: Rendered subdirectories under ``tools/``.
RENDERED_TOOL_SUBDIRS: frozenset[str] = frozenset({"templates"})

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
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    tools_dir_path = repo_root / "tools"

    if not tools_dir_path.exists():
        logger.warning(f"Tools directory not found: {tools_dir_path}")
        return []

    tools: list[ToolInfo] = []

    for child_dir in sorted(tools_dir_path.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        # Non-rendered lifecycle mirrors are never discovered
        if child_dir.name in NON_RENDERED_TOOL_SUBDIRS:
            logger.debug(f"Skipping non-rendered lifecycle subfolder: {child_dir.name}")
            continue

        # First, check if this is a valid standalone tool
        is_valid, _ = validate_tool_structure(child_dir)

        if is_valid:
            tool_info = build_tool_info(child_dir)
            tools.append(tool_info)
            logger.debug(f"Discovered standalone tool: {tool_info.name} at {tool_info.path}")
        else:
            # Not a valid tool — check if it's a program directory containing tools
            nested = _discover_nested_tools(child_dir, program_name=child_dir.name)
            if nested:
                tools.extend(nested)
                logger.debug(f"Discovered program directory: {child_dir.name} with {len(nested)} tools")
            else:
                logger.debug(f"Skipping {child_dir.name}: not a valid tool or program directory")

    return tools


def _discover_nested_tools(
    program_dir: Path,
    program_name: str,
    *,
    _allow_category: bool = True,
) -> list[ToolInfo]:
    """Discover tools nested within a program directory.

    A program directory is a folder that contains multiple related tools,
    but is not a tool itself. A child directory whose name starts with
    ``_`` is a category grouping — its own direct children are the actual
    tools, discovered with the compound qualified name ``<program>/_<category>/<name>``.
    Category nesting is exactly one level deep.
    """
    nested = []
    for child_dir in sorted(program_dir.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        is_valid, _ = validate_tool_structure(child_dir)

        if is_valid:
            tool_info = build_tool_info(child_dir, program=program_name)
            nested.append(tool_info)
            logger.debug(f"Discovered nested tool: {tool_info.qualified_name} at {tool_info.path}")
        elif _allow_category and child_dir.name.startswith("_"):
            nested.extend(
                _discover_nested_tools(
                    child_dir,
                    program_name=f"{program_name}/{child_dir.name}",
                    _allow_category=False,
                )
            )

    return nested


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
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)

    valid_heads = NON_RENDERED_TOOL_SUBDIRS | RENDERED_TOOL_SUBDIRS

    head = tool_name.replace("\\", "/").split("/", 1)[0]
    if head in valid_heads:
        qualified = repo_root / "tools" / tool_name
        if qualified.is_dir():
            return qualified.resolve()
        return qualified

    # Try templates first, then flat
    for candidate in [
        repo_root / "tools" / "templates" / tool_name,
        repo_root / "tools" / tool_name,
    ]:
        if candidate.is_dir():
            return candidate.resolve()

    return repo_root / "tools" / tool_name
