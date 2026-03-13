"""Configuration loader for manuscript metadata.

This module provides functions for loading manuscript configuration from YAML files
and formatting metadata for LaTeX and bash export. Part of the infrastructure layer.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

class AuthorConfig(TypedDict, total=False):
    name: str
    corresponding: bool
    orcid: str
    email: str

class PaperConfig(TypedDict, total=False):
    title: str

class PublicationConfig(TypedDict, total=False):
    doi: str

class TranslationsConfig(TypedDict, total=False):
    enabled: bool
    languages: list[str]

class ReviewsConfig(TypedDict, total=False):
    enabled: bool
    types: list[str]

class LLMConfig(TypedDict, total=False):
    translations: TranslationsConfig
    reviews: ReviewsConfig

class TestingConfig(TypedDict, total=False):
    max_test_failures: int
    max_infra_test_failures: int
    max_project_test_failures: int
    infra_coverage_threshold: int
    project_coverage_threshold: int

class SteganographyConfigYAML(TypedDict, total=False):
    """YAML schema for the steganography config section."""
    enabled: bool
    overlays: bool
    barcodes: bool
    metadata: bool
    hashing: bool
    encryption: bool
    overlay_text: str
    overlay_opacity: float
    pdf_password: str

@dataclass(frozen=True)
class ResolvedTestingConfig:
    """Immutable, fully-resolved testing configuration with defaults applied."""

    max_test_failures: int = 0
    max_infra_test_failures: int = 0
    max_project_test_failures: int = 0
    infra_coverage_threshold: int = 60
    project_coverage_threshold: int = 90

class ManuscriptConfig(TypedDict, total=False):
    paper: PaperConfig
    authors: list[AuthorConfig]
    publication: PublicationConfig
    llm: LLMConfig
    testing: TestingConfig
    steganography: SteganographyConfigYAML
    keywords: list[str]
    metadata: dict[str, str]
    project_config: dict[str, Any]  # passthrough for project-specific config sections

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

    Args:
        config_path: Path to config.yaml file

    Returns:
        ManuscriptConfig dictionary, or None if file doesn't exist or can't be loaded
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
            return data  # type: ignore[no-any-return]  # yaml.safe_load returns Any
    except FileNotFoundError:
        return None
    except PermissionError as e:
        logger.warning(f"Permission denied reading config {config_path}: {e}")
        return None
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error in config {config_path}: {e}")
        return None

def format_author_details(authors: list[AuthorConfig], doi: str = "") -> str:
    """Format author details string for LaTeX.

    Args:
        authors: List of author dictionaries (name, orcid, email, etc.)
        doi: Optional DOI string to include

    Returns:
        Formatted string with LaTeX line breaks
    """
    if not authors:
        return ""

    # Get primary/corresponding author (first one marked corresponding, or first)
    primary = next((a for a in authors if a.get("corresponding", False)), authors[0])

    parts = []
    if primary.get("orcid"):
        parts.append(f"ORCID: {primary['orcid']}")
    if primary.get("email"):
        parts.append(f"Email: {primary['email']}")
    if doi:
        parts.append(f"DOI: {doi}")

    # Join with "\\\\ " (double backslash + space) for LaTeX line breaks
    return "\\\\ ".join(parts)

def format_author_name(authors: list[AuthorConfig]) -> str:
    """Format author name(s) for display.

    Args:
        authors: List of author dictionaries

    Returns:
        Primary author name or "Project Author" if empty
    """
    if not authors:
        return "Project Author"

    return authors[0].get("name", "Project Author")

def get_config_as_dict(
    repo_root: Path | str, respect_existing: bool = False
) -> dict[str, str]:
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

# Re-export query functions from config_queries for backwards compatibility.
# TODO: Remove these re-exports after all callers are updated to import from config_queries directly.
from infrastructure.core.config_queries import (  # noqa: E402, F401
    get_review_types,
    get_testing_config,
    get_translation_languages,
)
