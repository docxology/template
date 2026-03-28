"""Configuration loader for manuscript metadata.

This module provides functions for loading manuscript configuration from YAML files
and formatting metadata for LaTeX and bash export. Part of the infrastructure layer.

Implementation is split across:
- ``schema``: TypedDict and dataclass type definitions
- ``formatting``: author formatting utilities
"""

from __future__ import annotations

import difflib
import os
from pathlib import Path
from typing import Any, cast

from infrastructure.core.logging.utils import get_logger

# Re-export all schema types so existing imports continue to work
from infrastructure.core.config.schema import (  # noqa: F401
    AuthorConfig,
    LLMYAMLConfig,
    ManuscriptConfig,
    PaperConfig,
    PublicationConfig,
    ResolvedTestingConfig,
    ReviewsConfig,
    SteganographyConfigYAML,
    TestingConfig,
    TranslationsConfig,
)

# Re-export formatting functions so existing imports continue to work
from infrastructure.core.config.formatting import (  # noqa: F401
    format_author_details,
    format_author_name,
)

logger = get_logger(__name__)

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def validate_config_keys(config: dict[str, Any], config_path: Path | str = "") -> list[str]:
    """Validate top-level config keys against known schema.

    Logs warnings for unrecognized keys with typo suggestions via
    difflib.get_close_matches().

    Args:
        config: Parsed YAML configuration dictionary
        config_path: Path to config file (for log messages)

    Returns:
        List of warning messages for unknown keys
    """
    known_keys = frozenset(ManuscriptConfig.__annotations__.keys())
    warnings: list[str] = []

    if not isinstance(config, dict):
        return warnings

    for key in config:
        if key not in known_keys:
            matches = difflib.get_close_matches(key, known_keys, n=1, cutoff=0.6)
            if matches:
                msg = f"Unknown config key '{key}' in {config_path} — did you mean '{matches[0]}'?"
            else:
                msg = f"Unknown config key '{key}' in {config_path}"
            logger.warning(msg)
            warnings.append(msg)

    return warnings


def load_config(config_path: Path | str) -> ManuscriptConfig | None:
    """Load configuration from YAML file.

    Validates top-level keys and logs warnings for unrecognized keys.

    Design note: returns None (not ConfigurationError) for missing / unreadable configs
    because config.yaml is *optional* — all callers treat None as "use defaults".
    Errors that indicate programmer mistakes (e.g. wrong key names) are logged as
    warnings, not raised, for the same reason: the pipeline should proceed with defaults
    rather than aborting over a missing or partial config file.

    Args:
        config_path: Path to config.yaml file

    Returns:
        ManuscriptConfig dictionary, or None if file doesn't exist or cannot be parsed
    """
    if not YAML_AVAILABLE:
        return None

    config_path = Path(config_path)
    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                validate_config_keys(data, config_path)
            return cast(ManuscriptConfig, data)
    except FileNotFoundError:
        return None
    except PermissionError as e:
        logger.warning(f"Permission denied reading config {config_path}: {e}")
        return None
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error in config {config_path}: {e}")
        return None


def get_config_as_dict(repo_root: Path | str, respect_existing: bool = False) -> dict[str, str]:
    """Get configuration as a dictionary of key-value pairs.

    Loads configuration from project/manuscript/config.yaml.

    Args:
        repo_root: Root directory of the repository
        respect_existing: If True, filter out keys already set in os.environ

    Returns:
        Dictionary of configuration values (PROJECT_TITLE, AUTHOR_NAME, etc.)
    """
    repo_root = Path(repo_root)

    # Find config file at standard location
    config_path = find_config_file(repo_root)
    if not config_path:
        return {}

    config = load_config(config_path)
    if not config:
        return {}

    result = {}

    # Paper title
    if paper_title := config.get("paper", {}).get("title"):
        result["PROJECT_TITLE"] = paper_title

    # DOI is independent of authors — extract it first
    doi = config.get("publication", {}).get("doi", "")
    if doi:
        result["DOI"] = doi

    # Authors
    if authors := config.get("authors", []):
        result["AUTHOR_NAME"] = format_author_name(authors)

        # Get first author's ORCID and email
        primary = authors[0]
        if orcid := primary.get("orcid"):
            result["AUTHOR_ORCID"] = orcid
        if email := primary.get("email"):
            result["AUTHOR_EMAIL"] = email

        # Full author details for LaTeX
        author_details = format_author_details(authors, doi)
        if author_details:
            result["AUTHOR_DETAILS"] = author_details

    if respect_existing:
        return {k: v for k, v in result.items() if k not in os.environ}
    return result


def find_config_file(
    repo_root: Path | str,
    project_name: str | None = None,
    projects_dir: str = "projects",
) -> Path | None:
    """Find the manuscript config file at the standard location.

    Args:
        repo_root: Root directory of the repository.
        project_name: Name of the project; if None, the first config found under
                      ``<projects_dir>/*/manuscript/`` is returned.
        projects_dir: Name of the active projects directory (default: ``'projects'``).

    Returns:
        Path to config.yaml if found, None otherwise.
    """
    repo_root = Path(repo_root)

    if project_name:
        config_path = repo_root / projects_dir / project_name / "manuscript" / "config.yaml"
        if config_path.exists():
            return config_path
        return None

    # Scan for any project config under <projects_dir>/*/manuscript/config.yaml
    for config_path in sorted((repo_root / projects_dir).glob("*/manuscript/config.yaml")):
        return config_path

    return None
