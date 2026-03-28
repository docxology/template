"""Project structure validation.

This module provides validation for the required directory structure
of projects within the repository.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_project_structure(project_dir: Path) -> tuple[bool, str]:
    """Validate that project has required directory structure.

    Required directories:
    - src/ - Source code
    - tests/ - Test suite

    Optional but recommended:
    - scripts/ - Analysis scripts
    - manuscript/ - Research manuscript
    - output/ - Generated outputs (created automatically)

    Args:
        project_dir: Path to project directory

    Returns:
        Tuple of (is_valid, message)

    Examples:
        >>> validate_project_structure(Path("projects/project"))
        (True, "Valid project structure")

        >>> validate_project_structure(Path("projects/invalid"))
        (False, "Missing required directory: src")
    """
    if not project_dir.exists():
        return False, f"Project directory does not exist: {project_dir}"

    if not project_dir.is_dir():
        return False, f"Not a directory: {project_dir}"

    # Check required directories
    src_dir = project_dir / "src"
    if not src_dir.exists():
        return False, "Missing required directory: src"

    tests_dir = project_dir / "tests"
    if not tests_dir.exists():
        return False, "Missing required directory: tests"

    # Check that src/ contains Python files
    python_files = list(src_dir.glob("**/*.py"))
    if not python_files:
        return False, "src/ directory contains no Python files"

    # Check optional but recommended directories
    scripts_dir = project_dir / "scripts"
    manuscript_dir = project_dir / "manuscript"

    if not scripts_dir.exists():
        logger.debug(f"{project_dir.name}: Optional scripts/ directory not found")

    if not manuscript_dir.exists():
        logger.debug(f"{project_dir.name}: Optional manuscript/ directory not found")

    return True, "Valid project structure"
