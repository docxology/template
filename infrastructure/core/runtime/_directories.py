"""Directory setup, validation, and source structure verification.

Creates and validates the project output directory layout and verifies
the source code directory structure.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


def _project_output_dirs(project_name: str) -> list[str]:
    """Return the canonical list of output directories for a project.

    Used by both setup_directories and validate_directory_structure to
    ensure the two functions always reference the same layout.
    """
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
        f"projects/{project_name}/output",
        f"projects/{project_name}/output/figures",
        f"projects/{project_name}/output/data",
        f"projects/{project_name}/output/pdf",
        f"projects/{project_name}/output/tex",
        f"projects/{project_name}/output/logs",
        f"projects/{project_name}/output/reports",
        f"projects/{project_name}/output/simulations",
        f"projects/{project_name}/output/slides",
        f"projects/{project_name}/output/web",
        f"projects/{project_name}/output/llm",
    ]


def setup_directories(
    repo_root: Path, project_name: str = "project", directories: list[str] | None = None
) -> bool:
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
        directories = _project_output_dirs(project_name)

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
    required_dirs = [
        "infrastructure",  # Generic tools (build_verifier, figure_manager, etc.)
        f"projects/{project_name}",  # Project directory
        f"projects/{project_name}/src",  # Source code
        f"projects/{project_name}/tests",  # Tests
    ]

    optional_dirs = [
        "scripts",  # Optional: orchestration scripts
        "tests",  # Optional: infrastructure tests
        f"projects/{project_name}/scripts",  # Optional: project scripts
        f"projects/{project_name}/manuscript",  # Optional: manuscript
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
    required_dirs = _project_output_dirs(project_name)

    missing = []
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    return missing
