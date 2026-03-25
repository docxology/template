"""Configuration query functions for manuscript metadata.

Higher-level functions that query config files for translation languages,
review types, and testing configuration. Split from config_loader.py to
keep each module under 300 LOC.
"""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


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
    from infrastructure.core.config.loader import find_config_file, load_config

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
    from infrastructure.core.config.loader import find_config_file, load_config

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
    except (ValueError, TypeError):  # noqa: BLE001 — return None; caller uses default
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
        except (ValueError, TypeError):  # noqa: BLE001 — fall through to config_dict then default
            logger.debug(f"{env_var}={raw!r} is not a valid int, ignoring")
    config_val = _safe_int_from_dict(config_dict, config_key)
    if config_val is not None:
        return config_val
    return default


def get_testing_config(repo_root: Path | str) -> "ResolvedTestingConfig":
    """Get testing configuration from config.yaml.

    Reads the testing section from config.yaml and returns an immutable
    ResolvedTestingConfig with all defaults applied.

    Configuration priority (highest to lowest):
    1. Environment variables — applies to infra_coverage_threshold
       (INFRA_COVERAGE_THRESHOLD) and project_coverage_threshold
       (PROJECT_COVERAGE_THRESHOLD) only; other fields use config file only.
    2. Config file (project/manuscript/config.yaml)
    3. Default values

    Args:
        repo_root: Root directory of the repository

    Returns:
        ResolvedTestingConfig with all fields populated.
    """
    from infrastructure.core.config.loader import (
        ResolvedTestingConfig,
        find_config_file,
        load_config,
    )

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
