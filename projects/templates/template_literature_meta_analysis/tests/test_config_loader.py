"""Tests for config_loader."""

from __future__ import annotations

from pathlib import Path


from config import DEFAULT_ARXIV_QUERIES, DEFAULT_RELEVANCE_KEYWORDS, MANUSCRIPT_DIR
from config_loader import default_config_path, load_kg_config, load_search_config


def test_load_search_config_defaults_when_missing(tmp_path: Path) -> None:
    cfg = load_search_config(tmp_path / "missing.yaml")
    assert cfg["arxiv_queries"] == DEFAULT_ARXIV_QUERIES
    assert cfg["relevance_keywords"] == DEFAULT_RELEVANCE_KEYWORDS


def test_load_kg_config_empty_when_missing(tmp_path: Path) -> None:
    cfg = load_kg_config(tmp_path / "missing.yaml")
    assert cfg.get("checkpoint_interval") is None


def test_load_search_config_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  search:
    query: "variational free energy"
    max_results: 99
    resume: true
    clear_corpus: true
    start_year: 2015
    arxiv_queries:
      - 'all:"variational"'
    relevance_keywords:
      - "variational"
""".strip(),
        encoding="utf-8",
    )
    cfg = load_search_config(config_path)
    assert cfg["query"] == "variational free energy"
    assert cfg["max_results"] == 99
    assert cfg["resume"] is True
    assert cfg["clear_corpus"] is True
    assert cfg["start_year"] == 2015
    assert cfg["arxiv_queries"] == ['all:"variational"']
    assert cfg["relevance_keywords"] == ["variational"]


def test_load_kg_config_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  knowledge_graph:
    checkpoint_interval: 10
    clear_assertions: true
    max_papers: 5
  llm_extraction:
    model: gemma3:4b
    base_url: http://127.0.0.1:11434
    temperature: 0.1
    max_tokens: 512
    timeout_seconds: 30
    max_retries: 2
    min_confidence: 0.5
""".strip(),
        encoding="utf-8",
    )
    cfg = load_kg_config(config_path)
    assert cfg["checkpoint_interval"] == 10
    assert cfg["clear_assertions"] is True
    assert cfg["max_papers"] == 5
    assert cfg["llm_model"] == "gemma3:4b"
    assert cfg["llm_url"] == "http://127.0.0.1:11434"
    assert cfg["llm_temperature"] == 0.1
    assert cfg["llm_max_tokens"] == 512
    assert cfg["llm_timeout"] == 30
    assert cfg["llm_max_retries"] == 2
    assert cfg["llm_min_confidence"] == 0.5


def test_default_config_path_points_at_manuscript() -> None:
    assert default_config_path() == MANUSCRIPT_DIR / "config.yaml"


def test_load_yaml_import_error_returns_empty_dict(tmp_path: Path) -> None:
    from config_loader import _load_yaml

    def blocked_import(name: str):
        raise ImportError(f"{name} unavailable in test")

    assert _load_yaml(tmp_path / "missing.yaml", yaml_importer=blocked_import) == {}
