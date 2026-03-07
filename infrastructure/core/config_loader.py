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


def get_config_as_env_vars(repo_root: Path | str, respect_existing: bool = True) -> dict[str, str]:
    """Get configuration as environment variables.

    Thin wrapper over get_config_as_dict with respect_existing=True by default.
    """
    return get_config_as_dict(repo_root, respect_existing=respect_existing)


def find_config_file(repo_root: Path | str, project_name: str | None = None) -> Path | None:
    """Find the manuscript config file at the standard location.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project; if None, the first config found under
                      projects/*/manuscript/ is returned

    Returns:
        Path to config.yaml if found, None otherwise
    """
    repo_root = Path(repo_root)

    if project_name:
        config_path = repo_root / "projects" / project_name / "manuscript" / "config.yaml"
        if config_path.exists():
            return config_path
        return None

    # Scan for any project config under projects/*/manuscript/config.yaml
    for config_path in sorted((repo_root / "projects").glob("*/manuscript/config.yaml")):
        return config_path

    return None


def get_translation_languages(repo_root: Path | str, project_name: str = "project") -> list[str]:
    """Get list of enabled translation languages from config.

    Reads the llm.translations section from config.yaml and returns
    the list of enabled language codes.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project (default: "project")

    Returns:
        List of language codes (e.g., ['zh', 'hi', 'ru']) if translations
        are enabled, empty list otherwise
    """
    config_path = find_config_file(repo_root, project_name)
    config = load_config(config_path) if config_path else None
    if not config:
        return []

    llm_config = config.get("llm", {})
    translations_config = llm_config.get("translations", {})

    # Check if translations are enabled
    if not translations_config.get("enabled", False):
        return []

    # Return the list of language codes
    languages = translations_config.get("languages", [])
    return languages if isinstance(languages, list) else []


def get_review_types(repo_root: Path | str, project_name: str = "project") -> list[str]:
    """Get list of enabled review types from config.

    Reads the llm.reviews section from config.yaml and returns
    the list of enabled review type codes.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project (default: "project")

    Returns:
        List of review type codes (e.g., ['executive_summary']) if reviews
        are enabled, empty list if disabled, or ['executive_summary'] as default
        if no config found.
    """
    VALID_REVIEW_TYPES = [
        "executive_summary",
        "quality_review",
        "methodology_review",
        "improvement_suggestions",
    ]

    config_path = find_config_file(repo_root, project_name)
    config = load_config(config_path) if config_path else None
    if not config:
        return ["executive_summary"]

    llm_config = config.get("llm", {})
    reviews_config = llm_config.get("reviews", {})

    # Check if reviews are explicitly disabled
    if reviews_config.get("enabled", True) is False:
        return []

    # Get the list of review types
    review_types = reviews_config.get("types", [])

    # If types is not a list, default to single review
    if not isinstance(review_types, list):
        return ["executive_summary"]

    # If types list is empty, default to single review
    if not review_types:
        return ["executive_summary"]

    # Filter out invalid review types and log warnings
    valid_types = [rt for rt in review_types if rt in VALID_REVIEW_TYPES]
    invalid_types = [rt for rt in review_types if rt not in VALID_REVIEW_TYPES]

    if invalid_types:
        logger.warning(f"Invalid review types ignored: {invalid_types}")

    # If no valid types after filtering, default to single review
    if not valid_types:
        return ["executive_summary"]

    return valid_types


def _safe_int_from_dict(config_dict: dict, key: str) -> int | None:
    """Safely extract an integer value from a config dict by key."""
    val = config_dict.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        logger.debug(f"Invalid {key} value: {val!r}")
        return None


def _resolve_int_setting(
    env_var: str,
    config_dict: dict,
    config_key: str,
    default: int,
) -> int:
    """Resolve an int setting with env-var priority over config file.

    Environment variable takes precedence over config file value.
    Config file takes precedence over default.
    """
    raw = os.environ.get(env_var)
    if raw is not None:
        try:
            return int(raw)
        except (ValueError, TypeError):
            logger.debug(f"{env_var}={raw!r} is not a valid int, ignoring")
    config_val = _safe_int_from_dict(config_dict, config_key)
    if config_val is not None:
        return config_val
    return default


def get_testing_config(repo_root: Path | str) -> ResolvedTestingConfig:
    """Get testing configuration from config.yaml.

    Reads the testing section from config.yaml and returns an immutable
    ResolvedTestingConfig with all defaults applied.

    Configuration priority (highest to lowest):
    1. Environment variables (e.g., INFRA_COVERAGE_THRESHOLD)
    2. Config file (project/manuscript/config.yaml)
    3. Default values

    Args:
        repo_root: Root directory of the repository

    Returns:
        ResolvedTestingConfig with all fields populated:
        - max_test_failures: Maximum acceptable test failures (default: 0)
        - max_infra_test_failures: Maximum acceptable infrastructure test failures (default: 0)
        - max_project_test_failures: Maximum acceptable project test failures (default: 0)
        - infra_coverage_threshold: Minimum infrastructure coverage % (default: 60)
        - project_coverage_threshold: Minimum project coverage % (default: 90)
    """
    defaults = ResolvedTestingConfig()

    # Load config file (env vars take priority, applied inside _resolve_int_setting)
    config_path = find_config_file(repo_root)
    config = load_config(config_path) if config_path else None
    testing_cfg = config.get("testing", {}) if config else {}

    def _int_or_default(key: str, default: int) -> int:
        v = _safe_int_from_dict(testing_cfg, key)
        return v if v is not None else default

    return ResolvedTestingConfig(
        max_test_failures=_int_or_default("max_test_failures", defaults.max_test_failures),
        max_infra_test_failures=_int_or_default(
            "max_infra_test_failures", defaults.max_infra_test_failures
        ),
        max_project_test_failures=_int_or_default(
            "max_project_test_failures", defaults.max_project_test_failures
        ),
        infra_coverage_threshold=_resolve_int_setting(
            "INFRA_COVERAGE_THRESHOLD",
            testing_cfg,
            "infra_coverage_threshold",
            defaults.infra_coverage_threshold,
        ),
        project_coverage_threshold=_resolve_int_setting(
            "PROJECT_COVERAGE_THRESHOLD",
            testing_cfg,
            "project_coverage_threshold",
            defaults.project_coverage_threshold,
        ),
    )
