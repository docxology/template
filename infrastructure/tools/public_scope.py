"""Public-repository tool scope helpers.

Runtime tool discovery intentionally includes local symlinked workspaces so
the orchestration CLI can operate on private tools. Public CI and generated docs
must stay narrower: only the tracked exemplar tools are part of the
public template repository.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.tools.discovery import discover_tools
from infrastructure.tools.tools_info import ToolInfo

#: Canonical roster of git-tracked public exemplar tool names.
#: Each entry is qualified as ``<program>/<name>`` (e.g. ``templates/template_code_executor``).
PUBLIC_TOOL_NAMES: tuple[str, ...] = (
    "templates/template_code_executor",
    "templates/template_model",
    "templates/template_skill",
    "templates/template_validator",
)


def public_tool_infos(repo_root: Path | str) -> list[ToolInfo]:
    """Return discovered tools that are part of the public template repo."""
    root = Path(repo_root)
    allowed = set(PUBLIC_TOOL_NAMES)
    return [tool for tool in discover_tools(root) if tool.qualified_name in allowed]


def public_tool_names(repo_root: Path | str) -> list[str]:
    """Return public template tool names present in this checkout."""
    return sorted(tool.qualified_name for tool in public_tool_infos(repo_root))


__all__ = [
    "PUBLIC_TOOL_NAMES",
    "public_tool_infos",
    "public_tool_names",
]
