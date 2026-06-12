"""Project discovery for multi-project support.

Scans the projects/ directory for valid projects and returns ProjectInfo objects.
For metadata extraction, validation, and ProjectInfo construction, import from the
sibling sub-modules (``metadata``, ``validation``, ``project_info``) or from the
``infrastructure.project`` package, which re-exports the full public API.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

# resolve_project_root and NON_RENDERED_SUBDIRS now live in the foundation layer
# (core.project_paths). Re-exported here so existing
# ``from infrastructure.project.discovery import resolve_project_root`` callers
# keep working, without the foundation having to import upward into project.
from infrastructure.core.project_paths import (
    NON_RENDERED_SUBDIRS,
    resolve_project_root,
)
from infrastructure.project.project_info import ProjectInfo, build_project_info
from infrastructure.project.validation import validate_project_structure

logger = get_logger(__name__)

#: Public API of this module. ``resolve_project_root`` and ``NON_RENDERED_SUBDIRS``
#: are re-exported from :mod:`infrastructure.core.project_paths` (declared here so
#: the re-export is explicit per docs/rules/api_design.md).
__all__ = [
    "NON_RENDERED_SUBDIRS",
    "discover_projects",
    "get_default_project",
    "project_name_from_root",
    "resolve_project_root",
]


def project_name_from_root(project_root: Path, repo_root: Path) -> str:
    """Return the project discovery name for active or WIP project roots.

    The discovery name is the project path relative to ``<repo_root>/projects``
    (e.g. ``active/demo``) when the project lives under that tree; otherwise the
    bare directory name is returned.

    Args:
        project_root: Filesystem root of the project.
        repo_root: Repository root directory.

    Returns:
        The project's discovery name.
    """
    try:
        return str(project_root.resolve().relative_to((repo_root / "projects").resolve()))
    except ValueError:
        return project_root.name


def discover_projects(
    repo_root: Path | str,
    projects_dir: str = "projects",
) -> list[ProjectInfo]:
    """Discover all valid projects in the active projects directory.

    This function scans ``projects_dir`` (default ``projects/``) for both:
    - Standalone projects (direct children with src/ and tests/)
    - Nested projects within program directories (subdirectories that contain projects)

    A program directory is a subdirectory that does not have src/ and tests/ itself,
    but contains one or more valid project subdirectories. The public exemplars in
    ``projects/templates/`` and the hot-seat ``projects/active/`` projects are
    discovered as program directories (qualified ``templates/<name>`` and
    ``active/<name>``).

    A valid project must have:
    - src/ directory with Python modules
    - tests/ directory

    Optional directories:
    - scripts/ directory (analysis scripts)
    - manuscript/ directory (research manuscript)

    Args:
        repo_root: Repository root directory.
        projects_dir: Name of the active projects directory relative to repo_root.
            Default ``'projects'``. ``projects/`` holds typed lifecycle subfolders:

            - ``projects/templates/`` — public canonical exemplars (rendered)
            - ``projects/active/``     — hot-seat private projects (rendered)
            - ``projects/working/``    — work-in-progress; NOT discovered
            - ``projects/published/``  — published; NOT discovered
            - ``projects/archive/``    — retired; NOT discovered
            - ``projects/other/``      — miscellaneous; NOT discovered

    Returns:
        List of ProjectInfo objects for valid projects.

    Note:
        The four lifecycle subfolders in :data:`NON_RENDERED_SUBDIRS`
        (``working``/``published``/``archive``/``other``) are deliberately excluded
        from discovery to prevent accidental execution/rendering.

    Examples:
        >>> projects = discover_projects(Path("/path/to/template"))
        >>> for project in projects:
        ...     print(f"{project.qualified_name}: {project.path}")
        templates/template_code_project: /path/to/template/projects/templates/template_code_project
        active/cogsec_multiagent: /path/to/template/projects/active/cogsec_multiagent
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    projects_dir_path = repo_root / projects_dir

    if not projects_dir_path.exists():
        logger.warning(f"Projects directory not found: {projects_dir_path}")
        return []

    projects = []

    for child_dir in sorted(projects_dir_path.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        # Non-rendered lifecycle mirrors are never discovered — they hold
        # backburner/published/retired/misc work that must stay out of the
        # render set.
        if child_dir.name in NON_RENDERED_SUBDIRS:
            logger.debug(f"Skipping non-rendered lifecycle subfolder: {child_dir.name}")
            continue

        # First, check if this is a valid standalone project
        is_valid, message = validate_project_structure(child_dir)

        if is_valid:
            # It's a standalone project
            project_info = build_project_info(child_dir)
            projects.append(project_info)
            logger.debug(f"Discovered standalone project: {project_info.name} at {project_info.path}")
        else:
            # Not a valid project - check if it's a program directory containing projects
            nested_projects = _discover_nested_projects(child_dir, program_name=child_dir.name)
            if nested_projects:
                projects.extend(nested_projects)
                logger.debug(
                    f"Discovered program directory: {child_dir.name} with {len(nested_projects)} projects"  # noqa: E501
                )
            else:
                logger.debug(f"Skipping {child_dir.name}: {message}")

    return projects


def _discover_nested_projects(program_dir: Path, program_name: str) -> list[ProjectInfo]:
    """Discover projects nested within a program directory.

    A program directory is a folder that contains multiple related projects,
    but is not a project itself.

    Args:
        program_dir: Path to the program directory
        program_name: Name of the program (parent directory name)

    Returns:
        List of ProjectInfo objects for valid nested projects
    """
    nested_projects = []

    for child_dir in sorted(program_dir.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        is_valid, _ = validate_project_structure(child_dir)

        if is_valid:
            project_info = build_project_info(child_dir, program=program_name)
            nested_projects.append(project_info)
            logger.debug(f"Discovered nested project: {project_info.qualified_name} at {project_info.path}")

    return nested_projects


def get_default_project(repo_root: Path, projects_dir: str = "projects") -> ProjectInfo | None:
    """Get the default project (projects/project by default).

    Args:
        repo_root: Repository root directory.
        projects_dir: Active projects directory name (default: ``'projects'``).

    Returns:
        ProjectInfo for default project, or None if not found
    """
    default_project_dir = repo_root / projects_dir / "project"

    if not default_project_dir.exists():
        return None

    is_valid, message = validate_project_structure(default_project_dir)
    if not is_valid:
        logger.warning(f"Default project is invalid: {message}")
        return None

    return build_project_info(default_project_dir)
