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
    clear_project_schema_extensions,
    get_project_schema_extensions,
    register_project_schema_extension,
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


def validate_config_keys(
    config: dict[str, Any],
    config_path: Path | str = "",
    project_name: str = "",
) -> list[str]:
    """Validate top-level config keys against known schema.

    Logs warnings for unrecognized keys with typo suggestions via
    difflib.get_close_matches(). When ``project_name`` is supplied,
    keys registered via
    :func:`infrastructure.core.config.schema.register_project_schema_extension`
    for that project (and any registered globally under the empty
    string) are also accepted without warning.

    Args:
        config: Parsed YAML configuration dictionary
        config_path: Path to config file (for log messages)
        project_name: Name of the project being validated. Optional;
            defaults to "" (no per-project extensions applied).

    Returns:
        List of warning messages for unknown keys
    """
    canonical_keys = set(ManuscriptConfig.__annotations__.keys())
    if project_name:
        canonical_keys.update(get_project_schema_extensions(project_name).keys())
    # Globally registered extensions (under "") apply to all projects.
    canonical_keys.update(get_project_schema_extensions("").keys())
    known_keys = frozenset(canonical_keys)
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


def load_config(config_path: Path | str, project_name: str = "") -> ManuscriptConfig | None:
    """Load configuration from YAML file.

    Validates top-level keys and logs warnings for unrecognized keys.
    When ``project_name`` is supplied (or inferable from the config
    path), per-project schema extensions registered via
    :func:`infrastructure.core.config.schema.register_project_schema_extension`
    suppress warnings for the project's custom keys.

    Design note: returns None (not ConfigurationError) for missing / unreadable configs
    because config.yaml is *optional* — all callers treat None as "use defaults".
    Errors that indicate programmer mistakes (e.g. wrong key names) are logged as
    warnings, not raised, for the same reason: the pipeline should proceed with defaults
    rather than aborting over a missing or partial config file.

    Args:
        config_path: Path to config.yaml file
        project_name: Name of the project this config belongs to.
            Optional. When empty, the loader attempts to infer it from
            the path layout ``…/projects/<name>/manuscript/config.yaml``;
            when that fails, no per-project extensions are applied.

    Returns:
        ManuscriptConfig dictionary, or None if file doesn't exist or cannot be parsed
    """
    if not YAML_AVAILABLE:
        return None

    config_path = Path(config_path)
    if not config_path.exists():
        return None

    resolved_project = project_name or _infer_project_name_from_path(config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                validate_config_keys(data, config_path, project_name=resolved_project)
            return cast(ManuscriptConfig, data)
    except FileNotFoundError:
        return None
    except PermissionError as e:
        logger.warning(f"Permission denied reading config {config_path}: {e}")
        return None
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error in config {config_path}: {e}")
        return None


def _infer_project_name_from_path(config_path: Path) -> str:
    """Infer a project name from a config path's layout.

    Looks for a ``…/<projects_dir>/<project_name>/manuscript/config.yaml``
    pattern. Returns an empty string when the layout doesn't match.
    Recognized parent directory names: ``projects``, ``projects_in_progress``,
    ``projects_archive``.
    """
    parts = config_path.parts
    candidates = {"projects", "projects_in_progress", "projects_archive"}
    for idx, part in enumerate(parts):
        if part in candidates and idx + 2 < len(parts) and parts[idx + 2] == "manuscript":
            return parts[idx + 1]
    return ""


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


__all__ = [
    # Re-exports from schema
    "AuthorConfig",
    "LLMYAMLConfig",
    "ManuscriptConfig",
    "PaperConfig",
    "PublicationConfig",
    "ResolvedTestingConfig",
    "ReviewsConfig",
    "SteganographyConfigYAML",
    "TestingConfig",
    "TranslationsConfig",
    "clear_project_schema_extensions",
    "get_project_schema_extensions",
    "register_project_schema_extension",
    # Re-exports from formatting
    "format_author_details",
    "format_author_name",
    # Local functions
    "find_config_file",
    "get_config_as_dict",
    "load_config",
    "validate_config_keys",
    "YAML_AVAILABLE",
]
