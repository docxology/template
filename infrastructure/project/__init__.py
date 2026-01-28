"""Project management infrastructure.

This module provides project discovery, validation, and metadata extraction
for multi-project support in the template.

Key Functions:
    - discover_projects: Find all valid projects in projects/ directory
    - validate_project_structure: Validate required directories exist
    - get_project_metadata: Extract project configuration
"""

from infrastructure.project.discovery import (ProjectInfo, discover_projects,
                                              get_project_metadata,
                                              validate_project_structure)

__all__ = [
    "discover_projects",
    "validate_project_structure",
    "get_project_metadata",
    "ProjectInfo",
]
