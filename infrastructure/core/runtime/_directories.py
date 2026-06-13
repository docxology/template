"""Directory setup, validation, and source structure verification.

Creates and validates the project output directory layout and verifies
the source code directory structure.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.project_paths import NON_RENDERED_SUBDIRS, resolve_project_root

logger = get_logger(__name__)


def _repo_visible_project_path(repo_root: Path | str, project_name: str) -> Path:
    """Return the project path to check/create from inside ``repo_root``.

    ``resolve_project_root`` follows symlinks so callers can operate on the real
    project source tree. Directory setup and source-structure checks, however,
    must address the repo-visible symlink path when the target lives outside
    this repository.
    """
    repo_root = Path(repo_root)
    project_parts = tuple(part for part in project_name.replace("\\", "/").split("/") if part)
    if project_parts and project_parts[0] in (NON_RENDERED_SUBDIRS | {"active", "templates"}):
        return Path("projects", *project_parts)

    project_root = resolve_project_root(repo_root, project_name)
    if not project_root.is_absolute():
        return project_root

    try:
        return project_root.relative_to(repo_root.resolve())
    except ValueError:
        for subdir in ("active", "working"):
            candidate = repo_root / "projects" / subdir / project_name
            if candidate.is_dir():
                return Path("projects") / subdir / project_name
        return Path("projects") / "active" / project_name


def _project_output_dirs(repo_root: Path | str, project_name: str | None = None) -> list[str]:
    """Return the canonical list of output directories for a project.

    Used by both setup_directories and validate_directory_structure to
    ensure the two functions always reference the same layout. The one-argument
    form (``_project_output_dirs("myproj")``) is retained for older tests and
    callers; it resolves paths relative to the current directory.
    """
    if project_name is None:
        project_name = str(repo_root)
        repo_root = Path(".")
    else:
        repo_root = Path(repo_root)

    project_rel = _repo_visible_project_path(repo_root, project_name)

    return [
        f"output/{project_name}",
        f"output/{project_name}/figures",
        f"output/{project_name}/data",
        f"output/{project_name}/tex",
        f"output/{project_name}/pdf",
        f"output/{project_name}/logs",
        f"output/{project_name}/reports",
        f"output/{project_name}/simulations",
        f"output/{project_name}/slides",
        f"output/{project_name}/web",
        f"output/{project_name}/llm",
        f"{project_rel}/output",
        f"{project_rel}/output/figures",
        f"{project_rel}/output/data",
        f"{project_rel}/output/pdf",
        f"{project_rel}/output/tex",
        f"{project_rel}/output/logs",
        f"{project_rel}/output/reports",
        f"{project_rel}/output/simulations",
        f"{project_rel}/output/slides",
        f"{project_rel}/output/web",
        f"{project_rel}/output/llm",
    ]


def setup_directories(repo_root: Path, project_name: str = "project", directories: list[str] | None = None) -> bool:
    """Create required directory structure.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        directories: List of directory paths to create (relative to repo_root).
                    If None, uses default directories.

    Returns:
        True if all directories created successfully, False otherwise
    """
    if directories is None:
        directories = _project_output_dirs(repo_root, project_name)

    try:
        for directory in directories:
            dir_path = repo_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ready: {directory}")
        log_success(f"All {len(directories)} directories ready", logger)
        return True
    except OSError as e:
        logger.error(f"Failed to create directories: {e}", exc_info=True)
        return False


def verify_source_structure(repo_root: Path, project_name: str = "project") -> bool:
    """Verify source code structure exists.

    For multi-project template, checks:
    - infrastructure/ - Generic reusable build tools
    - projects/{name}/ - Specified project structure

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        True if required directories exist, False otherwise
    """
    # Core components (required for template operation)
    project_rel = _repo_visible_project_path(repo_root, project_name)
    required_dirs = [
        Path("infrastructure"),  # Generic tools (build_verifier, figure_manager, etc.)
        project_rel,  # Project directory
        project_rel / "src",  # Source code
        project_rel / "tests",  # Tests
    ]

    optional_dirs = [
        Path("scripts"),  # Optional: orchestration scripts
        Path("tests"),  # Optional: infrastructure tests
        project_rel / "scripts",  # Optional: project scripts
        project_rel / "manuscript",  # Optional: manuscript
    ]

    all_present = True
    for directory in required_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            logger.debug(f"Directory found: {directory}")
        else:
            logger.error(f"Directory not found: {directory}")
            all_present = False

    # Check optional directories
    for directory in optional_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            logger.debug(f"Directory found: {directory} (optional)")
        else:
            logger.warning(f"Directory not found: {directory} (optional)")

    if all_present:
        log_success(f"All {len(required_dirs)} required directories present", logger)
    return all_present


def validate_directory_structure(repo_root: Path, project_name: str = "project") -> list[str]:
    """Return list of missing output directories for project (empty = all present)."""
    required_dirs = _project_output_dirs(repo_root, project_name)

    missing = []
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    return missing
