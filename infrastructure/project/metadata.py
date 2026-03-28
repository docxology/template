"""Project metadata extraction from configuration files.

This module reads project metadata from pyproject.toml and
manuscript/config.yaml files.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml
except ImportError:
    _yaml = None  # type: ignore[assignment]

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def get_project_metadata(project_dir: Path) -> dict[str, Any]:
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
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse {pyproject_path}: {e}")

    # Try manuscript/config.yaml for additional metadata
    config_path = project_dir / "manuscript" / "config.yaml"
    if config_path.exists():
        if _yaml is None:
            logger.debug("PyYAML not available, skipping config.yaml")
        else:
            try:
                with open(config_path) as f:
                    config_data = _yaml.safe_load(f)

                if config_data and "paper" in config_data:
                    paper_config = config_data["paper"]
                    if "title" in paper_config:
                        metadata["title"] = paper_config["title"]

                if config_data and "authors" in config_data:
                    # Manuscript authors override pyproject authors
                    metadata["authors"] = [
                        author.get("name", "Unknown") for author in config_data["authors"]
                    ]
            except (OSError, ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse {config_path}: {e}")
            except _yaml.YAMLError as e:
                logger.warning(f"Failed to parse {config_path}: {e}")

    return metadata
