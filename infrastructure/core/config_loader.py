"""Configuration loader for manuscript metadata.

This module provides functions for loading manuscript configuration from YAML files
and formatting metadata for LaTeX and bash export. Part of the infrastructure layer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

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
    languages: List[str]

class ReviewsConfig(TypedDict, total=False):
    enabled: bool
    types: List[str]

class LLMConfig(TypedDict, total=False):
    translations: TranslationsConfig
    reviews: ReviewsConfig

class TestingConfig(TypedDict, total=False):
    max_test_failures: int | str
    max_infra_test_failures: int | str
    max_project_test_failures: int | str
    infra_coverage_threshold: int | str
    project_coverage_threshold: int | str

class ManuscriptConfig(TypedDict, total=False):
    paper: PaperConfig
    authors: List[AuthorConfig]
    publication: PublicationConfig
    llm: LLMConfig
    testing: TestingConfig

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_config(config_path: Path | str) -> Optional[ManuscriptConfig]:
    """Load configuration from YAML file.

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
            return yaml.safe_load(f)
    except (FileNotFoundError, PermissionError, yaml.YAMLError):
        return None
    except Exception:
        # Log unexpected errors but don't fail
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Unexpected error loading config from {config_path}")
        return None


def format_author_details(authors: List[AuthorConfig], doi: str = "") -> str:
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


def format_author_name(authors: List[AuthorConfig]) -> str:
    """Format author name(s) for display.

    Args:
        authors: List of author dictionaries

    Returns:
        Primary author name or "Project Author" if empty
    """
    if not authors:
        return "Project Author"

    # For single author, return name
    if len(authors) == 1:
        return authors[0].get("name", "Project Author")

    # For multiple authors, return first author name
    return authors[0].get("name", "Project Author")


def get_config_as_dict(repo_root: Path | str) -> Dict[str, str]:
    """Get configuration as a dictionary of key-value pairs.

    Loads configuration from project/manuscript/config.yaml.

    Args:
        repo_root: Root directory of the repository

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

    # Authors
    if authors := config.get("authors", []):
        result["AUTHOR_NAME"] = format_author_name(authors)

        # Get first author's ORCID and email
        primary = authors[0]
        if orcid := primary.get("orcid"):
            result["AUTHOR_ORCID"] = orcid
        if email := primary.get("email"):
            result["AUTHOR_EMAIL"] = email

        # DOI
        doi = config.get("publication", {}).get("doi", "")
        if doi:
            result["DOI"] = doi

        # Full author details for LaTeX
        author_details = format_author_details(authors, doi)
        if author_details:
            result["AUTHOR_DETAILS"] = author_details

    return result


def get_config_as_env_vars(
    repo_root: Path | str, respect_existing: bool = True
) -> Dict[str, str]:
    """Get configuration as environment variables.

    Args:
        repo_root: Root directory of the repository
        respect_existing: If True, don't override existing environment variables

    Returns:
        Dictionary of environment variable assignments
    """
    config_dict = get_config_as_dict(repo_root)

    if respect_existing:
        # Filter out variables that are already set in environment
        return {k: v for k, v in config_dict.items() if k not in os.environ}
    else:
        return config_dict


def find_config_file(repo_root: Path | str) -> Optional[Path]:
    """Find the manuscript config file at the standard location.

    Args:
        repo_root: Root directory of the repository

    Returns:
        Path to config.yaml if found at project/manuscript/config.yaml, None otherwise
    """
    repo_root = Path(repo_root)

    config_path = repo_root / "project" / "manuscript" / "config.yaml"

    if config_path.exists():
        return config_path

    return None


def get_translation_languages(
    repo_root: Path | str, project_name: str = "project"
) -> List[str]:
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
    repo_root = Path(repo_root)

    # Look for config in the project-specific directory
    config_path = repo_root / "projects" / project_name / "manuscript" / "config.yaml"

    if not config_path.exists():
        return []

    config = load_config(config_path)
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


def get_review_types(repo_root: Path | str, project_name: str = "project") -> List[str]:
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
    repo_root = Path(repo_root)

    # Valid review types that can be configured
    VALID_REVIEW_TYPES = [
        "executive_summary",
        "quality_review",
        "methodology_review",
        "improvement_suggestions",
    ]

    # Look for config in the project-specific directory
    config_path = repo_root / "projects" / project_name / "manuscript" / "config.yaml"

    if not config_path.exists():
        # Default to single review if no config found
        return ["executive_summary"]

    config = load_config(config_path)
    if not config:
        # Default to single review if config can't be loaded
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
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid review types ignored: {invalid_types}")

    # If no valid types after filtering, default to single review
    if not valid_types:
        return ["executive_summary"]

    return valid_types


def get_testing_config(repo_root: Path | str) -> Dict[str, Any]:
    """Get testing configuration from config.yaml.

    Reads the testing section from config.yaml and returns
    configuration values for test failure tolerance and coverage thresholds.

    Configuration priority (highest to lowest):
    1. Environment variables (e.g., INFRA_COVERAGE_THRESHOLD)
    2. Config file (project/manuscript/config.yaml)
    3. Default values

    Args:
        repo_root: Root directory of the repository

    Returns:
        Dictionary with testing configuration values:
        - max_test_failures: Maximum acceptable test failures (default: 0)
        - max_infra_test_failures: Maximum acceptable infrastructure test failures (default: 0)
        - max_project_test_failures: Maximum acceptable project test failures (default: 0)
        - infra_coverage_threshold: Minimum infrastructure coverage % (default: 60)
        - project_coverage_threshold: Minimum project coverage % (default: 90)
        Returns empty dict if config file not found or testing section missing
    """
    # Default values
    defaults = {
        "infra_coverage_threshold": 60,
        "project_coverage_threshold": 90,
    }

    result: Dict[str, Any] = {}

    # Priority 1: Check environment variables first
    if env_infra := os.environ.get("INFRA_COVERAGE_THRESHOLD"):
        try:
            result["infra_coverage_threshold"] = int(env_infra)
        except (ValueError, TypeError):
            pass

    if env_project := os.environ.get("PROJECT_COVERAGE_THRESHOLD"):
        try:
            result["project_coverage_threshold"] = int(env_project)
        except (ValueError, TypeError):
            pass

    # Priority 2: Load from config file
    config_path = find_config_file(repo_root)
    config = load_config(config_path) if config_path else None
    testing_config = config.get("testing", {}) if config else {}

    # Read max_test_failures (general/default)
    if "max_test_failures" in testing_config:
        try:
            result["max_test_failures"] = int(testing_config["max_test_failures"])
        except (ValueError, TypeError):
            pass  # Invalid value, skip

    # Read max_infra_test_failures (infrastructure-specific)
    if "max_infra_test_failures" in testing_config:
        try:
            result["max_infra_test_failures"] = int(
                testing_config["max_infra_test_failures"]
            )
        except (ValueError, TypeError):
            pass  # Invalid value, skip

    # Read max_project_test_failures (project-specific)
    if "max_project_test_failures" in testing_config:
        try:
            result["max_project_test_failures"] = int(
                testing_config["max_project_test_failures"]
            )
        except (ValueError, TypeError):
            pass  # Invalid value, skip

    # Read coverage thresholds from config (if not already set by env vars)
    if "infra_coverage_threshold" not in result:
        if "infra_coverage_threshold" in testing_config:
            try:
                result["infra_coverage_threshold"] = int(
                    testing_config["infra_coverage_threshold"]
                )
            except (ValueError, TypeError):
                pass

    if "project_coverage_threshold" not in result:
        if "project_coverage_threshold" in testing_config:
            try:
                result["project_coverage_threshold"] = int(
                    testing_config["project_coverage_threshold"]
                )
            except (ValueError, TypeError):
                pass

    # Priority 3: Apply defaults for any missing values
    for key, default_val in defaults.items():
        if key not in result:
            result[key] = default_val

    return result

