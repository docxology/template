"""Project discovery for multi-project support.

Scans the projects/ directory for valid projects and returns ProjectInfo objects.
For metadata extraction, validation, and ProjectInfo construction, import from the
sibling sub-modules (``metadata``, ``validation``, ``project_info``) or from the
``infrastructure.project`` package, which re-exports the full public API.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.project_info import ProjectInfo, build_project_info
from infrastructure.project.validation import validate_project_structure

logger = get_logger(__name__)

#: Typed subfolders under ``projects/`` that hold non-rendered lifecycle mirrors.
#: Their nested projects are deliberately excluded from discovery so they never
#: enter the render set. Only ``templates/`` (public exemplars) and ``active/``
#: (the hot seat) are discovered. Keep in sync with
#: :data:`infrastructure.project.linking.LIFECYCLE_LINK_DIRS`.
NON_RENDERED_SUBDIRS: frozenset[str] = frozenset({"working", "published", "archive", "other"})


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


def resolve_project_root(repo_root: Path | str, project_name: str) -> Path:
    """Return the directory for *project_name*, preferring the hot seat over WIP trees.

    Use this when a tool should find a work-in-progress tree (for example COGANT) that has not
    been promoted to ``projects/active/`` yet. If ``projects/active/<project_name>`` exists and
    looks like a project source tree, that path wins; otherwise
    ``projects/working/<project_name>`` is used when present, then a flat
    standalone ``projects/<project_name>`` tree. A skeletal generated-output
    directory does not shadow an actual WIP source tree.

    If none of those exist, returns ``projects/active/<project_name>`` so callers get a
    stable path for error messages.

    Args:
        repo_root: Repository root (directory containing ``infrastructure/``).
        project_name: Final path segment (e.g. ``\"cogant\"``).

    Returns:
        Absolute resolved path to the project directory.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)

    def has_project_markers(path: Path) -> bool:
        return any((path / marker).exists() for marker in ("src", "tests", "scripts", "manuscript"))

    # A name that already carries a typed-subfolder prefix (e.g. ``active/demo``,
    # ``working/draft``, ``templates/template_code_project``) is resolved directly
    # under ``projects/`` without re-prepending the hot-seat prefix.
    head = project_name.replace("\\", "/").split("/", 1)[0]
    if head in (NON_RENDERED_SUBDIRS | {"active", "templates"}):
        qualified = repo_root / "projects" / project_name
        if qualified.is_dir():
            return qualified.resolve()
        return qualified

    primary = repo_root / "projects" / "active" / project_name
    if primary.is_dir() and has_project_markers(primary):
        return primary.resolve()
    wip = repo_root / "projects" / "working" / project_name
    if wip.is_dir():
        return wip.resolve()
    flat = repo_root / "projects" / project_name
    if flat.is_dir():
        return flat.resolve()
    # Public canonical exemplars live under ``projects/templates/<name>`` and
    # must resolve by bare name as well. Without this, an output-only shadow
    # under ``projects/active/<name>`` (or the stable error-path fallback below)
    # shadows a real exemplar source tree, so consumers such as
    # ``infrastructure.autoresearch.build_autoresearch_plan`` silently load
    # default config instead of the exemplar's own. Checked after the
    # hot-seat/WIP/flat trees so an actually-promoted project still wins.
    templated = repo_root / "projects" / "templates" / project_name
    if templated.is_dir() and has_project_markers(templated):
        return templated.resolve()
    if primary.is_dir():
        return primary.resolve()
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
