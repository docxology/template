"""Project discovery for multi-project support.

Scans the projects/ directory for valid projects and returns ProjectInfo objects.
For metadata extraction, validation, and ProjectInfo construction, import from the
sibling sub-modules (``metadata``, ``validation``, ``project_info``) or from the
``infrastructure.project`` package, which re-exports the full public API.
"""

from collections.abc import Sequence
from pathlib import Path

from infrastructure.core.lifecycle_discovery import discover_lifecycle_items
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
    "discover_qualified_names",
    "get_default_project",
    "project_name_from_root",
    "resolve_project_info",
    "resolve_project_root",
    "validate_project_slug",
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
            - ``projects/ongoing/``    — long-lived, no publication target; NOT discovered
            - ``projects/archive/``    — retired; NOT discovered

    Returns:
        List of ProjectInfo objects for valid projects.

    Note:
        The lifecycle subfolders in :data:`NON_RENDERED_SUBDIRS`
        (``working``/``ongoing``/``archive``) are deliberately excluded
        from discovery to prevent accidental execution/rendering.

    Examples:
        >>> projects = discover_projects(Path("/path/to/template"))
        >>> for project in projects:
        ...     print(f"{project.qualified_name}: {project.path}")
        templates/template_code_project: /path/to/template/projects/templates/template_code_project
        active/cogsec_multiagent: /path/to/template/projects/active/cogsec_multiagent
    """
    return discover_lifecycle_items(
        Path(repo_root) / projects_dir,
        validate_project_structure,
        build_project_info,
        excluded=NON_RENDERED_SUBDIRS,
        kind="project",
        logger=logger,
    )


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


def discover_qualified_names(repo_root: Path) -> list[str]:
    """Return a sorted list of qualified project names discovered under ``repo_root``."""
    projects = discover_projects(repo_root)
    return sorted(p.qualified_name for p in projects)


def _canonical_project_slug(slug: str, projects: Sequence[ProjectInfo]) -> str | None:
    """Return the discovered qualified slug for an exact or unique bare-name match."""
    exact = {project.qualified_name: project.qualified_name for project in projects}
    if slug in exact:
        return exact[slug]

    matches = [project.qualified_name for project in projects if project.name == slug]
    if not matches:
        return None
    priority = (
        f"active/{slug}",
        slug,
        f"templates/{slug}",
    )
    for candidate in priority:
        if candidate in matches:
            return candidate
    return sorted(matches)[0]


def _reject_unsafe_slug(slug: str) -> None:
    """Raise ``ValueError`` when *slug* is empty or a path-safety reject."""
    if not slug:
        raise ValueError("project slug must be a non-empty string")
    if "\x00" in slug:
        raise ValueError("project slug must not contain NUL bytes")
    if ".." in slug:
        raise ValueError(f"project slug must not contain '..': {slug!r}")
    if slug.startswith("/"):
        raise ValueError(f"project slug must not start with '/': {slug!r}")
    if slug.startswith("-"):
        raise ValueError(f"project slug must not start with '-': {slug!r}")


def validate_project_slug(
    slug: str,
    repo_root: Path,
    *,
    projects: Sequence[ProjectInfo] | None = None,
) -> str:
    """Validate a user-supplied project slug against discovered projects.

    Rejects (in order):

    1. ``None`` / empty string
    2. embedded NUL bytes
    3. ``..`` anywhere (path traversal)
    4. leading ``/`` or ``-`` (absolute path or flag-spoofing)
    5. names not present in the discovered project list or an explicitly
       qualified, marker-bearing lifecycle tree

    Returns the validated slug verbatim on success.

    Raises:
        ValueError: with a precise reason for the rejection.
    """
    _reject_unsafe_slug(slug)
    discovered = list(projects) if projects is not None else discover_projects(repo_root)
    resolved = _canonical_project_slug(slug, discovered)
    if resolved is None:
        normalized = slug.replace("\\", "/")
        head = normalized.split("/", 1)[0]
        if "/" in normalized and head in NON_RENDERED_SUBDIRS:
            lifecycle_root = resolve_project_root(repo_root, normalized)
            has_markers = lifecycle_root.is_dir() and any(
                (lifecycle_root / marker).exists()
                for marker in ("src", "tests", "scripts", "manuscript", "docs/manuscript")
            )
            if has_markers:
                return normalized
    if resolved is None:
        available = sorted(p.qualified_name for p in discovered)
        raise ValueError(f"project {slug!r} not found. Available: {', '.join(available) or '(none)'}")
    return resolved


def resolve_project_info(slug: str, repo_root: Path) -> ProjectInfo:
    """Resolve a validated rendered or qualified lifecycle project once."""
    projects = discover_projects(repo_root)
    qualified_name = validate_project_slug(slug, repo_root, projects=projects)
    for project in projects:
        if project.qualified_name == qualified_name:
            return project

    project_root = resolve_project_root(repo_root, qualified_name)
    program, separator, _name = qualified_name.rpartition("/")
    return build_project_info(project_root, program=program if separator else "")
