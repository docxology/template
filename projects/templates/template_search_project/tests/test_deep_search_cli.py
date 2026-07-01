"""Direct-call tests for src.deep_search_cli (no mocks; real LocalBackend)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import DeepSearchConfig, ProjectConfig, SearchConfig
from src.deep_search_cli import run_deep_search_cli

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUNDLED_CORPUS = PROJECT_ROOT / "data" / "corpus.json"


def _args(**overrides) -> argparse.Namespace:
    defaults = dict(
        config="manuscript/config.yaml",
        project_root=".",
        no_llm=True,
        no_cache=False,
        keyword=None,
        corpus=None,
        enable=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _make_config(*, enabled: bool, keywords: list[str] | None = None) -> ProjectConfig:
    return ProjectConfig(
        title="X",
        search=SearchConfig(query="x", sources=["local"]),
        deep_search=DeepSearchConfig(
            enabled=enabled,
            keywords=list(keywords or []),
            sources=["local"],
            fetch_abstracts=False,
            fetch_fulltext=False,
            output_dir="output/deep_search",
            search_cache_dir="output/cache/search",
            unified_bibtex_path="manuscript/refs.bib",
        ),
    )


def test_disabled_config_exits_zero_without_running(tmp_path: Path):
    config = _make_config(enabled=False)
    args = _args()
    exit_code = run_deep_search_cli(args, tmp_path, config)
    assert exit_code == 0
    assert not (tmp_path / "output").exists()


def test_enabled_but_no_keywords_exits_zero(tmp_path: Path):
    config = _make_config(enabled=True, keywords=[])
    args = _args()
    exit_code = run_deep_search_cli(args, tmp_path, config)
    assert exit_code == 0
    assert not (tmp_path / "output").exists()


def test_enabled_with_corpus_writes_artifacts(tmp_path: Path, capsys):
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "data").mkdir()
    corpus = tmp_path / "data" / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    config = _make_config(enabled=True, keywords=["convex"])
    args = _args(keyword=["convex"], corpus=str(corpus), enable=True)
    exit_code = run_deep_search_cli(args, tmp_path, config)
    assert exit_code == 0

    assert (tmp_path / "output" / "deep_search" / "convex" / "papers.json").exists()
    assert (tmp_path / "manuscript" / "refs.bib").exists()
    summary_path = tmp_path / "output" / "deep_search" / "run_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["keywords"] == ["convex"]
    assert summary["llm_used"] is False

    captured = capsys.readouterr()
    assert str(tmp_path / "output" / "deep_search" / "convex" / "papers.json") in captured.out


def test_cli_keyword_override_replaces_config_keywords(tmp_path: Path):
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "data").mkdir()
    corpus = tmp_path / "data" / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    config = _make_config(enabled=True, keywords=["ignored-keyword"])
    args = _args(keyword=["convex", "optimization"], corpus=str(corpus), enable=True)
    exit_code = run_deep_search_cli(args, tmp_path, config)
    assert exit_code == 0
    assert (tmp_path / "output" / "deep_search" / "convex").exists()
    assert (tmp_path / "output" / "deep_search" / "optimization").exists()
