"""Project management infrastructure.

Provides project discovery, validation, and metadata extraction
for multi-project support.

Usage::

    from infrastructure.project import (
        ProjectInfo,
        discover_projects,
        get_project_metadata,
        validate_project_structure,
    )
"""

from infrastructure.project.discovery import discover_projects
from infrastructure.project.metadata import get_project_metadata
from infrastructure.project.project_info import ProjectInfo
from infrastructure.project.validation import validate_project_structure

__all__ = [
    "ProjectInfo",
    "discover_projects",
    "get_project_metadata",
    "validate_project_structure",
]
