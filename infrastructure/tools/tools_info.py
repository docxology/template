"""ToolInfo dataclass for representing discovered tools (executable entry points).

A tool is an executable entry point — a script, skill, or agent — stored as
a passive manifest with an accompanying scripts/ directory. Tools are distinct
from fonds (passive data stores) and projects (full research environments).

Typical tool types:
- code_executor: Runs or evaluates code
- validator: Checks structure, schema, or invariants
- renderer: Produces outputs (PDFs, HTML, etc.)
- skill: Reusable agent skill
- agent: Autonomous agent entry point
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolInfo:
    """Information about a discovered tool.

    Attributes:
        name: Tool directory name
        path: Absolute path to tool directory
        tool_type: Execution category (code_executor, validator, renderer, skill, agent)
        has_scripts: Whether tool has scripts/ directory
        has_tests: Whether tool has tests/ directory
        metadata: Raw metadata dict from tools.yaml
        program: Parent program directory name (empty for standalone tools)
    """

    name: str
    path: Path
    tool_type: str = "generic"
    has_scripts: bool = False
    has_tests: bool = False
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
        """Tool is valid if it has a scripts/ directory."""
        return self.has_scripts


def build_tool_info(tool_dir: Path, program: str = "") -> ToolInfo:
    """Build a ToolInfo from a validated tool directory.

    Args:
        tool_dir: Path to the tool directory.
        program: Parent program directory name (empty for standalone tools).

    Returns:
        Populated ToolInfo instance.
    """
    metadata = _load_tool_manifest(tool_dir)
    return ToolInfo(
        name=tool_dir.name,
        path=tool_dir,
        tool_type=metadata.get("type", "generic") if metadata else "generic",
        has_scripts=(tool_dir / "scripts").exists(),
        has_tests=(tool_dir / "tests").exists(),
        metadata=metadata or {},
        program=program,
    )


def _load_tool_manifest(tool_dir: Path) -> dict[str, Any] | None:
    """Load tools.yaml if present.

    Args:
        tool_dir: Path to the tool directory.

    Returns:
        Parsed YAML dict or None if the file is absent or unreadable.
    """
    manifest_path = tool_dir / "tools.yaml"
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                return loaded if isinstance(loaded, dict) else None
        except Exception:  # noqa: BLE001
            return None
    return None


__all__ = [
    "ToolInfo",
    "build_tool_info",
]
