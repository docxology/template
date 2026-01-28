"""Project discovery and validation for multi-project support.

This module provides utilities for discovering, validating, and extracting
metadata from projects in the projects/ directory.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectInfo:
    """Information about a discovered project.

    Attributes:
        name: Project directory name
        path: Absolute path to project directory
        has_src: Whether project has src/ directory
        has_tests: Whether project has tests/ directory
        has_scripts: Whether project has scripts/ directory
        has_manuscript: Whether project has manuscript/ directory
        metadata: Extracted metadata from pyproject.toml or config.yaml
        program: Parent program directory name (empty for standalone projects)
    """

    name: str
    path: Path
    has_src: bool
    has_tests: bool
    has_scripts: bool
    has_manuscript: bool
    metadata: dict
    program: str = ""

    @property
    def is_valid(self) -> bool:
        """Check if project has minimum required structure."""
        return self.has_src and self.has_tests

    @property
    def qualified_name(self) -> str:
        """Full path-like name for display and selection.

        Returns:
            For standalone projects: just the name (e.g., "code_project")
            For nested projects: program/name (e.g., "cognitive_integrity/cogsec_multiagent_1_theory")
        """
        if self.program:
            return f"{self.program}/{self.name}"
        return self.name


def discover_projects(repo_root: Path | str) -> list[ProjectInfo]:
    """Discover all valid projects in projects/ directory.

    This function scans the projects/ directory for both:
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
        repo_root: Repository root directory

    Returns:
        List of ProjectInfo objects for valid projects in projects/ only

    Note:
        Projects in projects_archive/ are preserved but not discovered or executed.

    Examples:
        >>> projects = discover_projects(Path("/path/to/template"))
        >>> for project in projects:
        ...     print(f"{project.qualified_name}: {project.path}")
        code_project: /path/to/template/projects/code_project
        cognitive_integrity/cogsec_multiagent_1_theory: /path/to/template/projects/cognitive_integrity/cogsec_multiagent_1_theory
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    projects_dir = repo_root / "projects"

    if not projects_dir.exists():
        logger.warning(f"Projects directory not found: {projects_dir}")
        return []

    projects = []

    for child_dir in sorted(projects_dir.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        # First, check if this is a valid standalone project
        is_valid, message = validate_project_structure(child_dir)

        if is_valid:
            # It's a standalone project
            metadata = get_project_metadata(child_dir)
            project_info = ProjectInfo(
                name=child_dir.name,
                path=child_dir,
                has_src=(child_dir / "src").exists(),
                has_tests=(child_dir / "tests").exists(),
                has_scripts=(child_dir / "scripts").exists(),
                has_manuscript=(child_dir / "manuscript").exists(),
                metadata=metadata,
                program="",
            )
            projects.append(project_info)
            logger.debug(f"Discovered standalone project: {project_info.name} at {project_info.path}")
        else:
            # Not a valid project - check if it's a program directory containing projects
            nested_projects = _discover_nested_projects(child_dir, program_name=child_dir.name)
            if nested_projects:
                projects.extend(nested_projects)
                logger.debug(f"Discovered program directory: {child_dir.name} with {len(nested_projects)} projects")
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
            metadata = get_project_metadata(child_dir)
            project_info = ProjectInfo(
                name=child_dir.name,
                path=child_dir,
                has_src=(child_dir / "src").exists(),
                has_tests=(child_dir / "tests").exists(),
                has_scripts=(child_dir / "scripts").exists(),
                has_manuscript=(child_dir / "manuscript").exists(),
                metadata=metadata,
                program=program_name,
            )
            nested_projects.append(project_info)
            logger.debug(
                f"Discovered nested project: {project_info.qualified_name} at {project_info.path}"
            )

    return nested_projects


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


def get_project_metadata(project_dir: Path) -> dict:
    """Extract metadata from project configuration files.

    Checks the following sources in priority order:
    1. pyproject.toml - Python project configuration
    2. manuscript/config.yaml - Manuscript configuration
    3. Default metadata

    Args:
        project_dir: Path to project directory

    Returns:
        Dictionary containing project metadata

    Examples:
        >>> metadata = get_project_metadata(Path("projects/project"))
        >>> metadata['name']
        'project'
        >>> metadata['description']
        'Research project template'
    """
    metadata = {
        "name": project_dir.name,
        "description": "",
        "version": "0.1.0",
        "authors": [],
    }

    # Try pyproject.toml first
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)

            if "project" in pyproject_data:
                project_config = pyproject_data["project"]
                metadata["name"] = project_config.get("name", metadata["name"])
                metadata["description"] = project_config.get(
                    "description", metadata["description"]
                )
                metadata["version"] = project_config.get("version", metadata["version"])

                # Extract authors
                if "authors" in project_config:
                    metadata["authors"] = [
                        author.get("name", author.get("email", "Unknown"))
                        for author in project_config["authors"]
                    ]
        except Exception as e:
            logger.debug(f"Failed to parse {pyproject_path}: {e}")

    # Try manuscript/config.yaml for additional metadata
    config_path = project_dir / "manuscript" / "config.yaml"
    if config_path.exists():
        try:
            import yaml

            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            if config_data and "paper" in config_data:
                paper_config = config_data["paper"]
                if "title" in paper_config:
                    metadata["title"] = paper_config["title"]

            if config_data and "authors" in config_data:
                # Manuscript authors override pyproject authors
                metadata["authors"] = [
                    author.get("name", "Unknown") for author in config_data["authors"]
                ]
        except ImportError:
            logger.debug("PyYAML not available, skipping config.yaml")
        except Exception as e:
            logger.debug(f"Failed to parse {config_path}: {e}")

    return metadata


def get_default_project(repo_root: Path) -> Optional[ProjectInfo]:
    """Get the default project (projects/project).

    Args:
        repo_root: Repository root directory

    Returns:
        ProjectInfo for default project, or None if not found
    """
    default_project_dir = repo_root / "projects" / "project"

    if not default_project_dir.exists():
        return None

    is_valid, message = validate_project_structure(default_project_dir)
    if not is_valid:
        logger.warning(f"Default project is invalid: {message}")
        return None

    metadata = get_project_metadata(default_project_dir)

    return ProjectInfo(
        name="project",
        path=default_project_dir,
        has_src=(default_project_dir / "src").exists(),
        has_tests=(default_project_dir / "tests").exists(),
        has_scripts=(default_project_dir / "scripts").exists(),
        has_manuscript=(default_project_dir / "manuscript").exists(),
        metadata=metadata,
        program="",
    )
