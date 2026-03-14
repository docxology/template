"""Environment setup and validation utilities.

Validates dependencies, build tools, and directory structure for the research template.
Use this module to check or install requirements before running the pipeline.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def check_python_version() -> bool:
    """Verify Python 3.8+ is available."""
    version_str = platform.python_version()

    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required, found {version_str}")
        return False

    log_success(f"Python {version_str} available", logger)
    return True


def check_dependencies(
    packages: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """Check that required Python packages are importable.

    Args:
        packages: Package names to check. Defaults to ["pytest", "uv", "reportlab"].

    Returns:
        Tuple of (all_present, missing_packages).
    """
    if packages is None:
        packages = ["pytest", "uv", "reportlab"]

    missing: list[str] = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    return len(missing) == 0, missing


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


def check_uv_available() -> bool:
    """Check if uv package manager is available and working."""
    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=False, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def get_python_command() -> list[str]:
    """Get sys.executable for subprocess calls."""
    return [sys.executable]


def validate_interpreter() -> bool:
    """Validate that sys.executable is inside the expected virtual environment.

    Checks that the Python interpreter being used is the one managed by
    uv inside the project's .venv directory. This prevents "environment escape"
    where a system Python accidentally intercepts pipeline execution.

    Returns:
        True if interpreter is inside the venv (or no venv is expected), False otherwise.

    Note:
        Logs a warning if the interpreter is outside the venv but does not
        raise an exception, since CI environments and direct invocations
        may have valid reasons for running outside a venv.
    """
    interpreter = Path(sys.executable).resolve()

    # Check if VIRTUAL_ENV is set and matches
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        venv_resolved = Path(venv_path).resolve()
        try:
            interpreter.relative_to(venv_resolved)
            logger.debug(f"Interpreter validated: {interpreter} is inside {venv_resolved}")
            return True
        except ValueError:
            logger.warning(
                f"⚠️  Interpreter escape detected: sys.executable={interpreter} "
                f"is NOT inside VIRTUAL_ENV={venv_resolved}"
            )
            return False

    # Check for .venv in common ancestor directories
    for parent in interpreter.parents:
        if parent.name == ".venv":
            logger.debug(f"Interpreter validated: {interpreter} is inside a .venv")
            return True

    # No venv detected — might be CI or system Python, just note it
    logger.debug(f"No virtual environment detected for interpreter: {interpreter}")
    return True


def get_subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return env dict with VIRTUAL_ENV stripped when uv is active (avoids warnings).

    Args:
        base_env: Base environment dictionary (defaults to os.environ if None)

    Returns:
        Environment dictionary suitable for subprocess.run(env=...)
    """
    env = dict(base_env or os.environ)
    # Unset VIRTUAL_ENV when using uv to avoid warnings about absolute paths
    if check_uv_available() and "VIRTUAL_ENV" in env:
        env.pop("VIRTUAL_ENV", None)
    return env


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


def set_environment_variables(repo_root: Path) -> bool:
    """Configure environment variables for pipeline.

    Sets MPLBACKEND=Agg (headless matplotlib), PYTHONIOENCODING=utf-8,
    and PROJECT_ROOT for the pipeline scripts.

    Args:
        repo_root: Repository root directory

    Returns:
        True if environment variables set successfully, False otherwise
    """
    # Set matplotlib backend for headless operation
    os.environ["MPLBACKEND"] = "Agg"

    # Ensure UTF-8 encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # Set project root in environment
    os.environ["PROJECT_ROOT"] = str(repo_root)

    log_success("Environment variables configured (MPLBACKEND, PYTHONIOENCODING, PROJECT_ROOT)", logger)
    return True


def validate_uv_sync_result(repo_root: Path) -> tuple[bool, str]:
    """Check for .venv/ and uv.lock after uv sync; returns (success, message)."""
    # Check for .venv directory
    venv_path = repo_root / ".venv"
    if not venv_path.exists():
        return False, "Virtual environment not created"

    # Check for uv.lock file
    lock_file = repo_root / "uv.lock"
    if not lock_file.exists():
        return False, "Lock file not generated"

    return True, "uv sync completed successfully"


def validate_directory_structure(repo_root: Path, project_name: str = "project") -> list[str]:
    """Return list of missing output directories for project (empty = all present)."""
    required_dirs = _project_output_dirs(project_name)

    missing = []
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    return missing

