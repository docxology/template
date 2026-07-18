"""Direct-call tests for src.search_pipeline_cli (no mocks; real LocalBackend)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

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
    assert summary["evidence_scope"] == "bundled_deterministic_fixture"
    assert "not empirical literature findings" in (tmp_path / "output" / "reading_report.md").read_text(
        encoding="utf-8"
    )

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


def test_llm_enabled_runs_real_synthesis_stage_with_offline_stub(tmp_path: Path):
    """Cover the ``do_llm`` branch (config.llm.enabled and not --no-llm):
    ``build_llm_callable`` returns a real callable, so per-paper +
    corpus synthesis actually run and write their artifacts.

    Injects a deterministic offline LLM callable, so no live Ollama server is
    required while the real synthesis and artifact-writing paths still run.
    """

    class _FakeClient:
        def __init__(self, _config) -> None:
            pass

        def query_long(self, prompt: str) -> str:
            return f"stub-synthesis-for: {prompt[:20]}"

    class _FakeConfig:
        def __init__(self, **kwargs) -> None:
            self.base_url = "http://stub"

        @classmethod
        def from_env(cls) -> "_FakeConfig":
            return cls()

    corpus = tmp_path / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    config = _make_config()
    config.llm.enabled = True
    args = _args(corpus=str(corpus), no_llm=False)

    def llm_builder(**kwargs):
        return _FakeClient(_FakeConfig()).query_long

    exit_code = run_search_pipeline_cli(args, tmp_path, config, llm_builder=llm_builder)
    assert exit_code == 0

    summary = json.loads((tmp_path / "output" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["llm_used"] is True

    llm_dir = tmp_path / "output" / "llm"
    per_paper_files = list((llm_dir / "per_paper").glob("*.md"))
    assert per_paper_files, "expected at least one per-paper synthesis file"
    assert "stub-synthesis-for:" in per_paper_files[0].read_text(encoding="utf-8")

    corpus_synthesis_path = llm_dir / "synthesis.md"
    assert corpus_synthesis_path.exists()
    assert "stub-synthesis-for:" in corpus_synthesis_path.read_text(encoding="utf-8")


def test_fixture_scope_rejects_empirical_synthesis_language(tmp_path: Path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(BUNDLED_CORPUS.read_text(encoding="utf-8"), encoding="utf-8")
    config = _make_config()
    config.llm.enabled = True

    def llm_builder(**kwargs):
        return lambda prompt: "This study found a reliable empirical effect."

    with pytest.raises(ValueError, match="empirical claim language"):
        run_search_pipeline_cli(_args(corpus=str(corpus), no_llm=False), tmp_path, config, llm_builder=llm_builder)
