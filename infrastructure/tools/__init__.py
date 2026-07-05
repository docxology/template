"""Tools infrastructure — executable entry points for research workflows.

Provides tool discovery, validation, sidecar symlink sync, and public-scope
helpers for the ``tools/`` top-level directory, mirroring the architecture
of ``infrastructure/fonds/`` but for executable entry points rather than
passive data stores.

Usage::

    from infrastructure.tools import (
        ToolInfo,
        discover_tools,
        resolve_tool_root,
        validate_tool_structure,
    )
"""

from infrastructure.tools.discovery import discover_tools, resolve_tool_root
from infrastructure.tools.tools_info import ToolInfo, build_tool_info
from infrastructure.tools.validation import validate_tool_structure

__all__ = [
    "ToolInfo",
    "build_tool_info",
    "discover_tools",
    "resolve_tool_root",
    "validate_tool_structure",
]
