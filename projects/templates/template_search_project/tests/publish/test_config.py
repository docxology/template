"""Tests for src.config — typed YAML loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from template_search_project.publish.config import (
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
        "paper:\n  title: Demo\nproject_config:\n  search:\n    query: convex optimization\n    max_results: 5\n",
    )
    config = load_project_config(cfg_path)
    assert config.title == "Demo"
    assert config.search.query == "convex optimization"
    assert config.search.max_results == 5
    # Defaults filled in.
    assert config.search.sources == []
    assert config.enrichment.fetch_abstracts is False
    assert config.llm.enabled is False
    assert config.llm.seed == 42


def test_year_filters_and_sources(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        "paper:\n  title: Demo\nproject_config:\n  search:\n    query: x\n    year_min: 2010\n    year_max: 2024\n    sources:\n    - local\n    - arxiv\n",
    )
    config = load_project_config(cfg_path)
    assert config.search.year_min == 2010
    assert config.search.year_max == 2024
    assert config.search.sources == ["local", "arxiv"]


def test_optional_int_handles_empty_string(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        "paper:\n  title: Demo\nproject_config:\n  search:\n    query: x\n    year_min: ''\n    year_max: ''\n",
    )
    config = load_project_config(cfg_path)
    assert config.search.year_min is None
    assert config.search.year_max is None


def test_empty_query_raises(tmp_path: Path):
    cfg_path = _write_config(
        tmp_path / "config.yaml",
        "paper:\n  title: Demo\nproject_config:\n  search:\n    query: '   '\n",
    )
    with pytest.raises(ValueError, match="query"):
        load_project_config(cfg_path)


def test_top_level_must_be_mapping(tmp_path: Path):
    cfg_path = _write_config(tmp_path / "config.yaml", "- not\n- a\n- mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        load_project_config(cfg_path)


@pytest.mark.parametrize("field", ["search", "enrichment", "deep_search", "references_path"])
def test_project_owned_settings_require_namespace(field: str):
    with pytest.raises(ValueError, match="place project-owned settings under project_config"):
        ProjectConfig.from_dict({"project_config": {"search": {"query": "topic"}}, field: {}})


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
        "paper:\n  title: Demo\nllm:\n  enabled: false\n  context_window: 65536\n  long_max_tokens: 8192\n  max_input_length: 100000\n  review_timeout: 120.0\nproject_config:\n  deep_search:\n    enabled: false\n    llm_context_window: 262144\n    keywords: []\n  search:\n    query: x\n",
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
