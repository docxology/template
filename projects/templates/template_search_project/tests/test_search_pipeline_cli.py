"""Direct-call tests for src.search_pipeline_cli (no mocks; real LocalBackend)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import EnrichmentConfig, LLMConfig, ProjectConfig, ReportConfig, SearchConfig
from src.search_pipeline_cli import run_search_pipeline_cli

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUNDLED_CORPUS = PROJECT_ROOT / "data" / "corpus.json"


def _args(**overrides) -> argparse.Namespace:
    defaults = dict(no_cache=False, no_llm=True, corpus=None)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _make_config() -> ProjectConfig:
    return ProjectConfig(
        title="Demo",
        search=SearchConfig(query="research optimization", sources=["local"]),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )


def test_offline_smoke_writes_expected_artifacts(tmp_path: Path, capsys):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    config = _make_config()
    args = _args(corpus=str(corpus))
    exit_code = run_search_pipeline_cli(args, tmp_path, config)
    assert exit_code == 0

    assert (tmp_path / "manuscript" / "references.bib").exists()
    assert (tmp_path / "output" / "corpus.json").exists()
    assert (tmp_path / "output" / "search" / "results.json").exists()
    assert (tmp_path / "output" / "reading_report.md").exists()
    summary_path = tmp_path / "output" / "run_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["papers"] >= 1
    assert summary["llm_used"] is False

    captured = capsys.readouterr()
    assert str(tmp_path / "manuscript" / "references.bib") in captured.out


def test_no_llm_flag_skips_llm_stage_even_when_config_enables_it(tmp_path: Path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    config = _make_config()
    config.llm.enabled = True
    args = _args(corpus=str(corpus), no_llm=True)
    exit_code = run_search_pipeline_cli(args, tmp_path, config)
    assert exit_code == 0
    summary = json.loads((tmp_path / "output" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["llm_used"] is False
