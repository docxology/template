"""YAML configuration loading for pipeline scripts."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any

from config import DEFAULT_ARXIV_QUERIES, DEFAULT_RELEVANCE_KEYWORDS, MANUSCRIPT_DIR


def _load_yaml(
    path: Path,
    *,
    yaml_importer: Callable[[str], Any] = import_module,
) -> dict[str, Any]:
    try:
        yaml = yaml_importer("yaml")
    except ImportError:
        return {}
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def default_config_path() -> Path:
    """Return the canonical manuscript config path."""
    return Path(MANUSCRIPT_DIR / "config.yaml")


def load_project_config(config_path: Path | None = None) -> dict[str, Any]:
    """Return the project-specific configuration mapping.

    Keeping this public boundary here prevents pipeline runners from reaching
    through the private YAML loader or duplicating the ``project_config``
    traversal.
    """
    data = _load_yaml(config_path or default_config_path())
    project_config = data.get("project_config", {})
    return project_config if isinstance(project_config, dict) else {}


def load_search_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load literature search settings from YAML."""
    data = _load_yaml(config_path or default_config_path())
    search_cfg = data.get("project_config", data).get("search", data.get("search", {}))
    cfg = {
        "query": search_cfg.get("query"),
        "max_results": search_cfg.get("max_results"),
        "resume": search_cfg.get("resume"),
        "clear_corpus": search_cfg.get("clear_corpus"),
        "arxiv_queries": search_cfg.get("arxiv_queries") or list(DEFAULT_ARXIV_QUERIES),
        "relevance_keywords": search_cfg.get("relevance_keywords") or list(DEFAULT_RELEVANCE_KEYWORDS),
        "start_year": search_cfg.get("start_year"),
        # Per-engine enable toggles (default: all engines on). A missing key
        # defaults to enabled so a minimal config still dispatches every engine.
        "engines": search_cfg.get("engines") or {},
        # SovietRxiv-specific settings (optional, passed through as a sub-dict).
        "sovietrxiv": search_cfg.get("sovietrxiv") or {},
        # ChinaRxiv-specific settings (optional, passed through as a sub-dict).
        "chinarxiv": search_cfg.get("chinarxiv") or {},
    }
    return cfg


def load_kg_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load knowledge-graph and LLM settings from YAML."""
    data = _load_yaml(config_path or default_config_path())
    project_cfg = data.get("project_config", {})
    kg_cfg = data.get("knowledge_graph", {}) or project_cfg.get("knowledge_graph", {})
    llm_cfg = data.get("llm_extraction", {}) or project_cfg.get("llm_extraction", {})
    return {
        "checkpoint_interval": kg_cfg.get("checkpoint_interval"),
        "clear_assertions": kg_cfg.get("clear_assertions"),
        "max_papers": kg_cfg.get("max_papers"),
        "llm_model": llm_cfg.get("model"),
        "llm_url": llm_cfg.get("base_url"),
        "llm_temperature": llm_cfg.get("temperature"),
        "llm_max_tokens": llm_cfg.get("max_tokens"),
        "llm_timeout": llm_cfg.get("timeout_seconds"),
        "llm_max_retries": llm_cfg.get("max_retries"),
        "llm_min_confidence": llm_cfg.get("min_confidence"),
    }


def load_reproducibility_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load reproducibility-assessment settings from YAML.

    Mirrors :func:`load_kg_config`'s shape exactly: looks for a
    ``reproducibility_assessment`` block either at the YAML top level or
    nested under ``project_config`` (top-level wins when both are present),
    and returns every key with a default of ``None`` when absent so callers
    can safely ``cfg.get(...)``-chain against argparse/module defaults.
    """
    data = _load_yaml(config_path or default_config_path())
    project_cfg = data.get("project_config", {})
    repro_cfg = data.get("reproducibility_assessment", {}) or project_cfg.get("reproducibility_assessment", {})
    return {
        "checkpoint_interval": repro_cfg.get("checkpoint_interval"),
        "clear_workflow_graphs": repro_cfg.get("clear_workflow_graphs"),
        "max_papers": repro_cfg.get("max_papers"),
        "llm_model": repro_cfg.get("llm_model"),
        "llm_url": repro_cfg.get("llm_url"),
        "llm_temperature": repro_cfg.get("llm_temperature"),
        "llm_max_tokens": repro_cfg.get("llm_max_tokens"),
        "llm_timeout": repro_cfg.get("llm_timeout"),
        "llm_max_retries": repro_cfg.get("llm_max_retries"),
        "content_weights": repro_cfg.get("content_weights"),
        "structural_weights": repro_cfg.get("structural_weights"),
        "low_score_threshold": repro_cfg.get("low_score_threshold"),
        "fuzzy_quote_threshold": repro_cfg.get("fuzzy_quote_threshold"),
    }


def load_fulltext_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load the full-text download settings from YAML.

    Reads the existing ``project_config.fulltext`` block (``enabled``,
    ``unpaywall_email``, ``download_dir``) that
    :func:`literature.fulltext_download.download_and_extract_fulltext`
    already consumes as parameters. Prior to
    :func:`reproducibility.runner.run_reproducibility_pipeline`, no
    ``scripts/`` orchestrator read this block at all -- it needs
    ``enabled``/``download_dir`` to decide whether workflow-graph
    extraction has any fulltext to work from.
    """
    data = _load_yaml(config_path or default_config_path())
    project_cfg = data.get("project_config", {})
    fulltext_cfg = data.get("fulltext", {}) or project_cfg.get("fulltext", {})
    return {
        "enabled": fulltext_cfg.get("enabled"),
        "unpaywall_email": fulltext_cfg.get("unpaywall_email"),
        "download_dir": fulltext_cfg.get("download_dir"),
    }


def resolve_fulltext_directory(
    *,
    project_root: Path,
    fulltext_config: dict[str, Any],
    override: str | Path | None = None,
) -> tuple[Path, bool]:
    """Resolve the shared producer/consumer full-text directory.

    Priority is an explicit CLI override, then ``fulltext.download_dir`` from
    configuration, then the project-local ``output/fulltext`` default. Relative
    paths are always anchored to *project_root* so producer and consumer cannot
    silently resolve the same setting against different working directories.

    Returns:
        The resolved directory and whether the caller supplied an explicit
        override.
    """
    configured = override if override is not None else fulltext_config.get("download_dir")
    candidate = Path(configured) if configured else Path("output/fulltext")
    resolved = candidate if candidate.is_absolute() else project_root / candidate
    return resolved.resolve(), override is not None
