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
    """
    name: str
    path: Path
    has_src: bool
    has_tests: bool
    has_scripts: bool
    has_manuscript: bool
    metadata: dict
    
    @property
    def is_valid(self) -> bool:
        """Check if project has minimum required structure."""
        return self.has_src and self.has_tests


def discover_projects(repo_root: Path | str) -> list[ProjectInfo]:
    """Discover all valid projects in projects/ directory.
    
    A valid project must have:
    - src/ directory with Python modules
    - tests/ directory
    
    Optional directories:
    - scripts/ directory (analysis scripts)
    - manuscript/ directory (research manuscript)
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        List of ProjectInfo objects for valid projects
        
    Examples:
        >>> projects = discover_projects(Path("/path/to/template"))
        >>> for project in projects:
        ...     print(f"{project.name}: {project.path}")
        project: /path/to/template/projects/project
        myresearch: /path/to/template/projects/myresearch
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    projects_dir = repo_root / "projects"
    
    if not projects_dir.exists():
        logger.warning(f"Projects directory not found: {projects_dir}")
        return []
    
    projects = []
    
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
            
        if project_dir.name.startswith('.'):
            continue
        
        # Validate project structure
        is_valid, message = validate_project_structure(project_dir)
        
        if not is_valid:
            logger.debug(f"Skipping {project_dir.name}: {message}")
            continue
        
        # Extract metadata
        metadata = get_project_metadata(project_dir)
        
        # Create ProjectInfo
        project_info = ProjectInfo(
            name=project_dir.name,
            path=project_dir,
            has_src=(project_dir / "src").exists(),
            has_tests=(project_dir / "tests").exists(),
            has_scripts=(project_dir / "scripts").exists(),
            has_manuscript=(project_dir / "manuscript").exists(),
            metadata=metadata,
        )
        
        projects.append(project_info)
        logger.debug(f"Discovered project: {project_info.name} at {project_info.path}")
    
    return projects


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
                metadata["description"] = project_config.get("description", metadata["description"])
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
                    author.get("name", "Unknown")
                    for author in config_data["authors"]
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
    )
