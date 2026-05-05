"""Project management infrastructure.

Provides project discovery, validation, metadata extraction, and the
optional per-project ``setup_hook`` runner used during pipeline bootstrap.

Usage::

    from infrastructure.project import (
        ProjectInfo,
        discover_projects,
        find_setup_hook,
        get_project_metadata,
        preflight_setup_hook,
        resolve_project_root,
        run_project_setup_hook,
        validate_project_structure,
    )
"""

from infrastructure.project.discovery import discover_projects, resolve_project_root
from infrastructure.project.metadata import get_project_metadata
from infrastructure.project.project_info import ProjectInfo
from infrastructure.project.setup_hook import (
    find_setup_hook,
    preflight_setup_hook,
    run_project_setup_hook,
)
from infrastructure.project.validation import validate_project_structure

__all__ = [
    "ProjectInfo",
    "discover_projects",
    "find_setup_hook",
    "get_project_metadata",
    "preflight_setup_hook",
    "resolve_project_root",
    "run_project_setup_hook",
    "validate_project_structure",
]
