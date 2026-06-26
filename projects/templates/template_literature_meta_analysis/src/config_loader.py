"""YAML configuration loading for pipeline scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import DEFAULT_ARXIV_QUERIES, DEFAULT_RELEVANCE_KEYWORDS, MANUSCRIPT_DIR


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def default_config_path() -> Path:
    """Return the canonical manuscript config path."""
    return MANUSCRIPT_DIR / "config.yaml"


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
