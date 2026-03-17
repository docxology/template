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

from infrastructure.project.discovery import (
    ProjectInfo,
    discover_projects,
    get_project_metadata,
    validate_project_structure,
)

__all__ = [
    "ProjectInfo",
    "discover_projects",
    "get_project_metadata",
    "validate_project_structure",
]
