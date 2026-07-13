"""Tests for src.config — typed YAML loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.config import (
    EnrichmentConfig,
    LLMConfig,
    ProjectConfig,
    SearchConfig,
    load_project_config,
)


def _write_config(path: Path, body: str) -> Path:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_minimal_config_loads(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        """
        paper:
          title: "Demo"
        search:
          query: "convex optimization"
          max_results: 5
        """,
    )
    config = load_project_config(cfg_path)
    assert config.title == "Demo"
    assert config.search.query == "convex optimization"
    assert config.search.max_results == 5
    # Defaults filled in.
    assert config.search.sources == ["arxiv", "crossref"]
    assert config.enrichment.fetch_abstracts is True
    assert config.llm.enabled is True
    assert config.llm.seed == 42


def test_year_filters_and_sources(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        """
        paper:
          title: "Demo"
        search:
          query: "legacy"
        project_config:
          search:
            query: "x"
            year_min: 2010
            year_max: 2024
            sources: [local, arxiv]
        """,
    )
    config = load_project_config(cfg_path)
    assert config.search.year_min == 2010
    assert config.search.year_max == 2024
    assert config.search.sources == ["local", "arxiv"]


def test_optional_int_handles_empty_string(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        """
        paper: {title: "Demo"}
        search:
          query: "x"
          year_min: ""
          year_max: ""
        """,
    )
    config = load_project_config(cfg_path)
    assert config.search.year_min is None
    assert config.search.year_max is None


def test_empty_query_raises(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        """
        paper: {title: "Demo"}
        search:
          query: "   "
        """,
    )
    with pytest.raises(ValueError, match="query"):
        load_project_config(cfg_path)


def test_top_level_must_be_mapping(tmp_path: Path):
    cfg_path = _write_config(tmp_path / "config.yaml", "- not\n- a\n- mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        load_project_config(cfg_path)


def test_direct_construction():
    config = ProjectConfig(
        title="X",
        search=SearchConfig(query="convex", max_results=3),
        enrichment=EnrichmentConfig(fetch_fulltext=True),
        llm=LLMConfig(enabled=False),
    )
    assert config.search.max_results == 3
    assert config.enrichment.fetch_fulltext is True
    assert config.llm.enabled is False


def test_llm_and_deep_llm_budget_yaml(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        """
        paper:
          title: "Demo"
        search:
          query: "x"
        llm:
          enabled: false
          context_window: 65536
          long_max_tokens: 8192
          max_input_length: 100000
          review_timeout: 120.0
        deep_search:
          enabled: true
          llm_context_window: 1
        project_config:
          deep_search:
            enabled: false
            llm_context_window: 262144
            keywords: []
        """,
    )
    config = load_project_config(cfg_path)
    assert config.llm.context_window == 65536
    assert config.llm.long_max_tokens == 8192
    assert config.llm.max_input_length == 100000
    assert config.llm.review_timeout == 120.0
    assert config.deep_search.llm_context_window == 262144
    cw, lmt, mil, rt = config.deep_search.resolve_llm_budget(config.llm)
    assert cw == 262144
    assert lmt == 8192
    assert mil == 100000
    assert rt == 120.0
