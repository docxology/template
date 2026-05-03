"""Tests for src.pipeline — uses real LocalBackend, real temp files, no mocks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.search.literature import (
    Paper,
    SearchBackend,
)

from src.config import (
    EnrichmentConfig,
    LLMConfig,
    ProjectConfig,
    ReportConfig,
    SearchConfig,
)
from src.pipeline import _build_backends, run_literature_pipeline


def _write_corpus(tmp_path: Path) -> Path:
    papers = [
        {
            "id": "doi:10.1126/science.1213847",
            "title": "Reproducible research in computational science",
            "authors": ["Roger D Peng"],
            "year": 2011,
            "doi": "10.1126/science.1213847",
            "venue": "Science",
            "venue_type": "journal",
            "abstract": "Reproducible research is a hallmark of computational work.",
        },
        {
            "id": "arxiv:1412.6980",
            "title": "Adam: A method for stochastic optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "venue": "ICLR",
            "venue_type": "conference",
            "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization.",
        },
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


def _make_config(query: str, sources: list[str]) -> ProjectConfig:
    return ProjectConfig(
        title="Demo",
        search=SearchConfig(
            query=query,
            max_results=10,
            sources=sources,
            cache_dir="output/search/cache",
        ),
        enrichment=EnrichmentConfig(
            fetch_abstracts=False,
            fetch_fulltext=False,
        ),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )


class TestBuildBackends:
    def test_local_requires_corpus(self):
        config = _make_config("x", ["local"])
        with pytest.raises(ValueError, match="corpus_path"):
            _build_backends(config)

    def test_local_corpus_path_accepted(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("x", ["local"])
        backends = _build_backends(config, corpus_path=corpus)
        assert len(backends) == 1
        assert backends[0].name == "local"

    def test_unknown_source_raises(self):
        config = _make_config("x", ["fictional"])
        with pytest.raises(ValueError, match="Unknown search source"):
            _build_backends(config)

    def test_paperclip_requires_env(self, monkeypatch):
        monkeypatch.delenv("PAPERCLIP_API_KEY", raising=False)
        config = _make_config("x", ["paperclip"])
        with pytest.raises(RuntimeError, match="PAPERCLIP_API_KEY"):
            _build_backends(config)

    def test_arxiv_backend_constructed(self):
        config = _make_config("x", ["arxiv"])
        backends = _build_backends(config)
        assert len(backends) == 1
        assert backends[0].name == "arxiv"

    def test_crossref_backend_constructed(self):
        config = _make_config("x", ["crossref"])
        backends = _build_backends(config)
        assert len(backends) == 1
        assert backends[0].name == "crossref"

    def test_paperclip_backend_constructed_when_env_set(self, monkeypatch):
        monkeypatch.setenv("PAPERCLIP_API_KEY", "gxl_test_dummy")
        config = _make_config("x", ["paperclip"])
        backends = _build_backends(config)
        assert len(backends) == 1
        assert backends[0].name == "paperclip"

    def test_extra_backends_appended(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("x", ["local"])

        class _Fake(SearchBackend):
            name = "fake"
            def search(self, query):
                return []

        backends = _build_backends(config, corpus_path=corpus, extra_backends=[_Fake()])
        assert [b.name for b in backends] == ["local", "fake"]


class TestRunLiteraturePipeline:
    def test_local_pipeline_writes_corpus_and_bibtex(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("research optimization", ["local"])
        artifacts = run_literature_pipeline(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
        )
        assert len(artifacts.papers) == 2
        assert artifacts.corpus_path is not None and artifacts.corpus_path.exists()
        assert artifacts.bibtex_path is not None and artifacts.bibtex_path.exists()
        bibtex = artifacts.bibtex_path.read_text(encoding="utf-8")
        assert "@inproceedings{kingma2014adam" in bibtex
        assert "@article{peng2011reproducible" in bibtex

    def test_search_cache_created(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("research", ["local"])
        artifacts = run_literature_pipeline(
            config, project_root=tmp_path, corpus_path=corpus
        )
        assert artifacts.cache_dir is not None
        cache_files = list(artifacts.cache_dir.glob("search_*.json"))
        assert len(cache_files) == 1

    def test_no_write_outputs_skips_files(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("research", ["local"])
        artifacts = run_literature_pipeline(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            write_outputs=False,
        )
        assert artifacts.bibtex_path is None
        assert artifacts.corpus_path is None
        # But the search result is still populated.
        assert len(artifacts.papers) > 0

    def test_bibtex_byte_identical_across_reruns(self, tmp_path: Path):
        """Two consecutive single-query pipeline runs over the same
        corpus must produce a byte-identical ``references.bib`` (the
        artefact the manuscript build consumes). Cache file timestamps
        live in ``output/search/cache/search_*.json``, not the bib."""
        corpus = _write_corpus(tmp_path)
        config = _make_config("research", ["local"])
        first = run_literature_pipeline(
            config, project_root=tmp_path, corpus_path=corpus
        )
        first_bib = first.bibtex_path.read_bytes()
        first_corpus = first.corpus_path.read_bytes()

        second = run_literature_pipeline(
            config, project_root=tmp_path, corpus_path=corpus
        )
        assert second.bibtex_path.read_bytes() == first_bib
        assert second.corpus_path.read_bytes() == first_corpus

    def test_extra_backend_papers_included(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path)
        config = _make_config("research", ["local"])

        class _ExtraBackend(SearchBackend):
            name = "extra"
            def search(self, query):
                return [Paper(id="extra:1", title="Extra Paper", year=2024)]

        artifacts = run_literature_pipeline(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            extra_backends=[_ExtraBackend()],
        )
        ids = {p.id for p in artifacts.papers}
        assert "extra:1" in ids
        assert "extra" in artifacts.result.per_source_counts
