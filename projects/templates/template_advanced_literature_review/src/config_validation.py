"""Typed configuration validation for literature pipeline boundaries.

Validation is deliberately separate from configuration loading: loaders remain
side-effect free and permissive for callers that only inspect optional values,
while executable runners call :func:`require_valid_config` before creating
outputs or contacting a network/LLM provider.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

Config = dict[str, Any]
Validator = Callable[[Config], list[str]]


class ConfigValidationError(ValueError):
    """Raised when an executable pipeline receives an invalid configuration."""


def _project_config(config: Config) -> Mapping[str, Any]:
    value = config.get("project_config", {})
    return value if isinstance(value, Mapping) else {}


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_search_config(
    config: Config,
    *,
    query_override: str | None = None,
) -> list[str]:
    """Validate settings consumed by the literature-search runner."""
    issues: list[str] = []
    project = _project_config(config)
    raw_search = project.get("search", config.get("search", {}))
    if not isinstance(raw_search, Mapping):
        return ["project_config.search must be a mapping"]
    search = raw_search

    term = search.get("term")
    query = search.get("query")
    if not any(isinstance(value, str) and value.strip() for value in (term, query, query_override)):
        issues.append("Set at least one of project_config.search.term or project_config.search.query")

    raw_engines = search.get("engines")
    if raw_engines is not None:
        if not isinstance(raw_engines, Mapping):
            issues.append("project_config.search.engines must be a mapping of engine names to booleans")
        else:
            invalid = sorted(name for name, enabled in raw_engines.items() if not isinstance(enabled, bool))
            if invalid:
                issues.append(f"Search engine toggles must be boolean: {', '.join(map(str, invalid))}")
            elif raw_engines and not any(raw_engines.values()):
                issues.append("All configured search engines are disabled")

    start_year = search.get("start_year")
    max_year = date.today().year + 1
    if start_year is not None and (not _is_int(start_year) or start_year < 1800 or start_year > max_year):
        issues.append(f"Invalid start_year: {start_year!r} (must be an integer in 1800-{max_year})")

    max_results = search.get("max_results")
    if max_results is not None and (not _is_int(max_results) or max_results < 1):
        issues.append(f"Invalid max_results: {max_results!r} (must be a positive integer)")

    for name in ("resume", "clear_corpus"):
        value = search.get(name)
        if value is not None and not isinstance(value, bool):
            issues.append(f"Invalid search.{name}: {value!r} (must be boolean)")

    for name in ("arxiv_queries", "relevance_keywords"):
        value = search.get(name)
        if value is not None and (
            not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value)
        ):
            issues.append(f"Invalid search.{name}: must be a list of non-empty strings")

    return issues


def validate_hypothesis_config(config: Config) -> list[str]:
    """Validate hypothesis definitions when that analysis surface is requested."""
    issues: list[str] = []
    hypotheses = _project_config(config).get("hypothesis_definitions", {})
    if not isinstance(hypotheses, Mapping) or not hypotheses:
        return ["No hypothesis definitions configured"]

    for hypothesis_id, hypothesis in hypotheses.items():
        if not isinstance(hypothesis, Mapping):
            issues.append(f"Hypothesis {hypothesis_id}: must be a mapping")
            continue
        for field in ("name", "description", "scope"):
            value = hypothesis.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"Hypothesis {hypothesis_id}: missing required field '{field}'")
    return issues


def validate_sampling_config(config: Config) -> list[str]:
    """Validate the optional deterministic LLM-stage sampling settings."""
    project = _project_config(config)
    raw_sampling = project.get("sampling")
    if raw_sampling is None:
        return []
    if not isinstance(raw_sampling, Mapping):
        return ["project_config.sampling must be a mapping"]

    issues: list[str] = []
    fraction = raw_sampling.get("fraction")
    if fraction is not None and (not _is_number(fraction) or not 0 < float(fraction) <= 1):
        issues.append(f"Invalid sampling.fraction: {fraction!r} (must be > 0.0 and <= 1.0)")
    seed = raw_sampling.get("seed")
    if seed is not None and (not _is_int(seed) or seed < 0):
        issues.append(f"Invalid sampling.seed: {seed!r} (must be a non-negative integer)")
    return issues


def validate_llm_config(config: Config) -> list[str]:
    """Validate the optional knowledge-graph LLM extraction settings."""
    raw_llm = config.get("llm_extraction") or _project_config(config).get("llm_extraction")
    if raw_llm is None:
        return []
    if not isinstance(raw_llm, Mapping):
        return ["project_config.llm_extraction must be a mapping"]

    issues: list[str] = []
    for name in ("model", "base_url"):
        value = raw_llm.get(name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            issues.append(f"Invalid llm_extraction.{name}: must be a non-empty string")

    ranges: dict[str, tuple[float, float | None]] = {
        "temperature": (0.0, 2.0),
        "timeout_seconds": (1.0, None),
        "min_confidence": (0.0, 1.0),
    }
    for name, (minimum, maximum) in ranges.items():
        value = raw_llm.get(name)
        if value is None:
            continue
        if not _is_number(value):
            issues.append(f"Invalid llm_extraction.{name}: {value!r} (must be numeric)")
            continue
        numeric = float(value)
        if numeric < minimum or (maximum is not None and numeric > maximum):
            ceiling = f" and <= {maximum:g}" if maximum is not None else ""
            issues.append(f"Invalid llm_extraction.{name}: {value!r} (must be >= {minimum:g}{ceiling})")
    for name in ("max_tokens", "max_retries"):
        value = raw_llm.get(name)
        if value is not None and (not _is_int(value) or value < 1):
            issues.append(f"Invalid llm_extraction.{name}: {value!r} (must be a positive integer)")
    return issues


def validate_knowledge_graph_config(config: Config) -> list[str]:
    """Validate knowledge-graph orchestration limits and booleans."""
    raw = config.get("knowledge_graph") or _project_config(config).get("knowledge_graph")
    if raw is None:
        return []
    if not isinstance(raw, Mapping):
        return ["project_config.knowledge_graph must be a mapping"]
    return _validate_orchestration_config(raw, "knowledge_graph", clear_key="clear_assertions")


def validate_reproducibility_config(config: Config) -> list[str]:
    """Validate reproducibility orchestration, score thresholds, and weights."""
    raw = config.get("reproducibility_assessment") or _project_config(config).get("reproducibility_assessment")
    if raw is None:
        return []
    if not isinstance(raw, Mapping):
        return ["project_config.reproducibility_assessment must be a mapping"]

    issues = _validate_orchestration_config(
        raw,
        "reproducibility_assessment",
        clear_key="clear_workflow_graphs",
    )
    for name in ("low_score_threshold", "fuzzy_quote_threshold"):
        value = raw.get(name)
        if value is not None and (not _is_number(value) or not 0 <= float(value) <= 1):
            issues.append(f"Invalid reproducibility_assessment.{name}: {value!r} (must be 0.0-1.0)")
    for name in ("llm_model", "llm_url"):
        value = raw.get(name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            issues.append(f"Invalid reproducibility_assessment.{name}: must be a non-empty string")
    llm_temperature = raw.get("llm_temperature")
    if llm_temperature is not None and (not _is_number(llm_temperature) or not 0 <= float(llm_temperature) <= 2):
        issues.append(f"Invalid reproducibility_assessment.llm_temperature: {llm_temperature!r} (must be 0.0-2.0)")
    llm_timeout = raw.get("llm_timeout")
    if llm_timeout is not None and (not _is_number(llm_timeout) or float(llm_timeout) <= 0):
        issues.append(f"Invalid reproducibility_assessment.llm_timeout: {llm_timeout!r} (must be positive)")
    for name in ("llm_max_tokens", "llm_max_retries"):
        value = raw.get(name)
        if value is not None and (not _is_int(value) or value < 1):
            issues.append(f"Invalid reproducibility_assessment.{name}: {value!r} (must be a positive integer)")
    for name in ("content_weights", "structural_weights"):
        weights = raw.get(name)
        if weights is None:
            continue
        if not isinstance(weights, Mapping):
            issues.append(f"reproducibility_assessment.{name} must be a mapping")
            continue
        invalid = [key for key, value in weights.items() if not _is_number(value) or float(value) < 0]
        if invalid:
            issues.append(f"reproducibility_assessment.{name} has invalid weights: {', '.join(invalid)}")
        elif weights and sum(float(value) for value in weights.values()) <= 0:
            issues.append(f"reproducibility_assessment.{name} must have a positive total weight")
    return issues


def _validate_orchestration_config(
    raw: Mapping[str, Any],
    section: str,
    *,
    clear_key: str,
) -> list[str]:
    issues: list[str] = []
    checkpoint = raw.get("checkpoint_interval")
    if checkpoint is not None and (not _is_int(checkpoint) or checkpoint < 1):
        issues.append(f"Invalid {section}.checkpoint_interval: {checkpoint!r} (must be positive)")
    max_papers = raw.get("max_papers")
    if max_papers is not None and (not _is_int(max_papers) or max_papers < 0):
        issues.append(f"Invalid {section}.max_papers: {max_papers!r} (must be non-negative)")
    clear = raw.get(clear_key)
    if clear is not None and not isinstance(clear, bool):
        issues.append(f"Invalid {section}.{clear_key}: {clear!r} (must be boolean)")
    return issues


def validate_fulltext_config(config: Config) -> list[str]:
    """Validate the optional fulltext-download settings."""
    raw = config.get("fulltext") or _project_config(config).get("fulltext")
    if raw is None:
        return []
    if not isinstance(raw, Mapping):
        return ["project_config.fulltext must be a mapping"]

    issues: list[str] = []
    enabled = raw.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        issues.append(f"Invalid fulltext.enabled: {enabled!r} (must be boolean)")
    email = raw.get("unpaywall_email")
    if email is not None and not isinstance(email, str):
        issues.append(f"Invalid fulltext.unpaywall_email: {email!r} (must be a string)")
    download_dir = raw.get("download_dir")
    if download_dir is not None and (not isinstance(download_dir, str) or not download_dir.strip()):
        issues.append("Invalid fulltext.download_dir: must be a non-empty string")
    return issues


_VALIDATORS: dict[str, Validator] = {
    "search_config": validate_search_config,
    "hypothesis_config": validate_hypothesis_config,
    "sampling_config": validate_sampling_config,
    "llm_config": validate_llm_config,
    "knowledge_graph_config": validate_knowledge_graph_config,
    "reproducibility_config": validate_reproducibility_config,
    "fulltext_config": validate_fulltext_config,
}


def _load_config(config_path: Path) -> tuple[Config | None, list[str]]:
    try:
        with config_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"Failed to load config file: {exc}"]
    if not isinstance(loaded, dict):
        kind = "empty" if loaded is None else type(loaded).__name__
        return None, [f"Configuration root must be a mapping, got {kind}"]
    project = loaded.get("project_config")
    if project is not None and not isinstance(project, Mapping):
        return None, ["project_config must be a mapping"]
    return loaded, []


def validate_full_config(
    config_path: Path,
    *,
    categories: Iterable[str] | None = None,
) -> dict[str, list[str]]:
    """Validate a YAML configuration and return categorized issues."""
    config, file_errors = _load_config(Path(config_path))
    if file_errors:
        return {"file_errors": file_errors}
    assert config is not None

    selected = tuple(categories) if categories is not None else tuple(_VALIDATORS)
    unknown = sorted(set(selected) - set(_VALIDATORS))
    if unknown:
        raise ValueError(f"Unknown config validation categories: {', '.join(unknown)}")
    results = {name: _VALIDATORS[name](config) for name in selected}
    return {name: issues for name, issues in results.items() if issues}


def require_valid_config(config_path: Path, *, categories: Iterable[str]) -> None:
    """Raise :class:`ConfigValidationError` when selected config sections are invalid."""
    issues = validate_full_config(config_path, categories=categories)
    if not issues:
        return
    details = "; ".join(f"{category}: {message}" for category, messages in issues.items() for message in messages)
    raise ConfigValidationError(f"Invalid configuration {config_path}: {details}")


def require_valid_search_config(
    config_path: Path,
    *,
    query_override: str | None = None,
) -> None:
    """Validate search config while honoring an explicit CLI query override."""
    config, file_errors = _load_config(Path(config_path))
    issues = (
        {"file_errors": file_errors}
        if file_errors
        else {
            "search_config": validate_search_config(
                config or {},
                query_override=query_override,
            )
        }
    )
    filtered = {name: messages for name, messages in issues.items() if messages}
    if not filtered:
        return
    details = "; ".join(f"{category}: {message}" for category, messages in filtered.items() for message in messages)
    raise ConfigValidationError(f"Invalid configuration {config_path}: {details}")


def check_config_health(config_path: Path) -> bool:
    """Log all configuration issues and return whether the file is valid."""
    issues = validate_full_config(config_path)
    if not issues:
        logger.info("Configuration validation passed: %s", config_path)
        return True
    for category, messages in issues.items():
        for message in messages:
            logger.warning("Config %s: %s", category, message)
    return False


__all__ = [
    "ConfigValidationError",
    "check_config_health",
    "require_valid_config",
    "require_valid_search_config",
    "validate_full_config",
    "validate_fulltext_config",
    "validate_hypothesis_config",
    "validate_knowledge_graph_config",
    "validate_llm_config",
    "validate_reproducibility_config",
    "validate_sampling_config",
    "validate_search_config",
]
