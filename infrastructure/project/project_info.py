"""ProjectInfo dataclass for representing discovered projects.

This module defines the data structure used to represent a discovered
project and its directory layout within the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectInfo:
    """Information about a discovered project.

    Attributes:
        name: Project directory name
        path: Absolute path to project directory
        has_src: Whether project has src/ directory
        has_tests: Whether project has tests/ directory
        has_scripts: Whether project has scripts/ directory
        has_manuscript: Whether project has manuscript/ directory
        metadata: Raw metadata dict from pyproject.toml or config.yaml
        program: Parent program directory name (empty for standalone projects)
    """

    name: str
    path: Path
    has_src: bool
    has_tests: bool
    has_scripts: bool
    has_manuscript: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    program: str = ""

    @property
    def is_valid(self) -> bool:
        """Check if project has minimum required structure."""
        return self.has_src and self.has_tests

    @property
    def qualified_name(self) -> str:
        """Full path-like name for display and selection.

        Returns:
            For standalone projects: just the name (e.g., "act_inf_metaanalysis")
            For nested projects: program/name (e.g., "cognitive_integrity/cogsec_multiagent_1_theory")
        """
        if self.program:
            return f"{self.program}/{self.name}"
        return self.name
