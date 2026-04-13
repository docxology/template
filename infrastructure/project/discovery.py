"""Project discovery for multi-project support.

Scans the projects/ directory for valid projects and returns ProjectInfo objects.
For metadata extraction, validation, and ProjectInfo construction, import from the
sibling sub-modules (``metadata``, ``validation``, ``project_info``) or from the
``infrastructure.project`` package, which re-exports the full public API.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.project_info import ProjectInfo, build_project_info
from infrastructure.project.validation import validate_project_structure

logger = get_logger(__name__)


def discover_projects(
    repo_root: Path | str,
    projects_dir: str = "projects",
) -> list[ProjectInfo]:
    """Discover all valid projects in the active projects directory.

    This function scans ``projects_dir`` (default ``projects/``) for both:
    - Standalone projects (direct children with src/ and tests/)
    - Nested projects within program directories (subdirectories that contain projects)

    A program directory is a subdirectory that does not have src/ and tests/ itself,
    but contains one or more valid project subdirectories.

    A valid project must have:
    - src/ directory with Python modules
    - tests/ directory

    Optional directories:
    - scripts/ directory (analysis scripts)
    - manuscript/ directory (research manuscript)

    Args:
        repo_root: Repository root directory.
        projects_dir: Name of the active projects directory relative to repo_root.
            Default ``'projects'``. The three standard directories are:

            - ``projects/``            — active; discovered and rendered by run.sh
            - ``projects_in_progress/`` — work-in-progress; NOT discovered automatically
            - ``projects_archive/``     — completed/retired; NOT discovered automatically

            Only pass a non-default value when you explicitly want to run a project
            from a staging directory.

    Returns:
        List of ProjectInfo objects for valid projects.

    Note:
        ``projects_archive/`` and ``projects_in_progress/`` are deliberately excluded
        from the default discovery path to prevent accidental execution.

    Examples:
        >>> projects = discover_projects(Path("/path/to/template"))
        >>> for project in projects:
        ...     print(f"{project.qualified_name}: {project.path}")
        act_inf_metaanalysis: /path/to/template/projects/act_inf_metaanalysis
        cognitive_integrity/cogsec_multiagent_1_theory: /path/to/template/projects/cognitive_integrity/cogsec_multiagent_1_theory
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

        # First, check if this is a valid standalone project
        is_valid, message = validate_project_structure(child_dir)

        if is_valid:
            # It's a standalone project
            project_info = build_project_info(child_dir)
            projects.append(project_info)
            logger.debug(
                f"Discovered standalone project: {project_info.name} at {project_info.path}"
            )
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


def resolve_project_root(repo_root: Path | str, project_name: str) -> Path:
    """Return the directory for *project_name*, preferring ``projects/`` over ``projects_in_progress/``.

    Use this when a tool should find a work-in-progress tree (for example COGANT) that has not
    been moved into ``projects/`` yet. If ``projects/<project_name>`` exists, that path wins;
    otherwise ``projects_in_progress/<project_name>`` is used when present.

    If neither directory exists, returns ``projects/<project_name>`` so callers get a stable
    path for error messages.

    Args:
        repo_root: Repository root (directory containing ``infrastructure/``).
        project_name: Final path segment (e.g. ``\"cogant\"``).

    Returns:
        Absolute resolved path to the project directory.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    primary = repo_root / "projects" / project_name
    if primary.is_dir():
        return primary.resolve()
    wip = repo_root / "projects_in_progress" / project_name
    if wip.is_dir():
        return wip.resolve()
    return primary


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
            logger.debug(
                f"Discovered nested project: {project_info.qualified_name} at {project_info.path}"
            )

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
