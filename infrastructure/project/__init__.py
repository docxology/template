"""Project management infrastructure.

Provides project discovery, validation, and metadata extraction
for multi-project support.

Usage::

    from infrastructure.project import discover_projects
"""

from infrastructure.project.discovery import discover_projects

__all__ = ["discover_projects"]
