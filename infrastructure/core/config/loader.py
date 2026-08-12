"""Configuration loader for manuscript metadata.

This module provides functions for loading manuscript configuration from YAML files
and formatting metadata for LaTeX and bash export. Part of the infrastructure layer.

Implementation is split across:
- ``schema``: TypedDict and dataclass type definitions
- ``formatting``: author formatting utilities
"""

import difflib
import os
from pathlib import Path
from typing import Any, cast

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.project_paths import validate_project_name

# Re-export all schema types so existing imports continue to work
from infrastructure.core.config.schema import (  # noqa: F401
    AnalysisConfig,
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
    generate_manuscript_config_schema,
    get_project_schema_extensions,
    register_project_schema_extension,
)

# Re-export formatting functions so existing imports continue to work
from infrastructure.core.config.formatting import (  # noqa: F401
    format_author_details,
    format_author_name,
)

logger = get_logger(__name__)

# Standard Pandoc / manuscript frontmatter keys used by projects that author a
# "Pandoc-flat" manuscript config (e.g. ``bibliography: refs.bib`` at top level
# with sibling Pandoc keys) rather than the nested template blocks. Recognized so
# they do not surface as spurious "Unknown config key" warnings. Several are
# hyphenated (Pandoc style) and so cannot be ``ManuscriptConfig`` TypedDict
# fields; they are whitelisted here instead.
_PANDOC_FRONTMATTER_KEYS = frozenset(
    {
        "csl",
        "link-citations",
        "reference-section-title",
        "chapters",
        "preamble",
        "fail_on_missing",
    }
)
_PUBLIC_EXEMPLAR_CONFIG_KEYS = frozenset({"gold_refinement", "madlib"})

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def validate_config_keys(
    config: dict[str, Any],
    config_path: Path | str = "",
    project_name: str = "",
    *,
    strict: bool = False,
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
        strict: If True, raise ``ValueError`` after collecting unknown-key
            warnings. The default remains permissive for existing pipelines.

    Returns:
        List of warning messages for unknown keys
    """
    canonical_keys = set(ManuscriptConfig.__annotations__.keys())
    if project_name:
        canonical_keys.update(get_project_schema_extensions(project_name).keys())
    # Globally registered extensions (under "") apply to all projects.
    canonical_keys.update(get_project_schema_extensions("").keys())
    # Standard Pandoc-flat frontmatter keys (csl, link-citations, chapters, …).
    canonical_keys.update(_PANDOC_FRONTMATTER_KEYS)
    canonical_keys.update(_PUBLIC_EXEMPLAR_CONFIG_KEYS)
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

    if strict and warnings:
        raise ValueError("\n".join(warnings))

    return warnings


def load_config(
    config_path: Path | str,
    project_name: str = "",
    *,
    strict: bool = False,
) -> ManuscriptConfig | None:
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
        strict: If True, unknown top-level keys raise ``ValueError`` instead
            of only logging warnings.

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
                validate_config_keys(
                    data,
                    config_path,
                    project_name=resolved_project,
                    strict=strict,
                )
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

    Looks for a ``…/<parent>/<project_name>/manuscript/config.yaml`` pattern.
    Returns an empty string when the layout doesn't match. Recognized parents
    are ``projects`` itself plus the typed lifecycle subfolders under it
    (``active``, ``working``, ``ongoing``, ``published``, ``archive``, ``other``,
    ``templates``) — e.g. ``projects/active/<name>/manuscript/config.yaml`` or
    ``projects/templates/<name>/manuscript/config.yaml``.
    """
    parts = config_path.parts
    candidates = {
        "projects",
        "active",
        "working",
        "ongoing",
        "archive",
        "templates",
    }
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

    projects_root = (repo_root / projects_dir).resolve()

    if project_name:
        try:
            normalized_name = validate_project_name(project_name)
        except ValueError as exc:
            logger.warning("Ignoring unsafe project name %r: %s", project_name, exc)
            return None

        direct = projects_root.joinpath(*normalized_name.split("/"), "manuscript", "config.yaml")
        if direct.is_file():
            return direct

        # Bare names must also resolve canonical nested exemplars and
        # lifecycle trees. Prefer the same active/working/flat/templates order
        # used by project-path resolution, then refuse a genuinely ambiguous
        # match instead of silently choosing filesystem order.
        candidates = sorted(
            path
            for path in projects_root.rglob("config.yaml")
            if path.parent.name == "manuscript" and path.parent.parent.name == normalized_name
        )
        if not candidates:
            return None

        def priority(path: Path) -> int:
            relative = path.relative_to(projects_root).parts
            if relative and relative[0] == "active":
                return 0
            if relative and relative[0] == "working":
                return 1
            if relative and relative[0] == "templates":
                return 3
            if len(relative) == 3:
                return 2
            return 4

        best_priority = min(priority(path) for path in candidates)
        best = [path for path in candidates if priority(path) == best_priority]
        if len(best) == 1:
            return best[0]
        logger.warning("Ambiguous config for project %r: %s", project_name, ", ".join(map(str, best)))
        return None

    # Unqualified discovery is intentionally fail-closed. A repository with
    # multiple project configs must provide a project name rather than letting
    # the first glob result select an arbitrary manuscript.
    candidates = sorted(path for path in projects_root.rglob("config.yaml") if path.parent.name == "manuscript")
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        logger.warning(
            "Multiple manuscript configs found under %s; pass project_name explicitly",
            projects_root,
        )
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
    "generate_manuscript_config_schema",
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
