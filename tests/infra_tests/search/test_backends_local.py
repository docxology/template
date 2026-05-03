"""Tests for LocalBackend (offline, no HTTP, no mocks)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.search.literature.backends import BackendError, LocalBackend
from infrastructure.search.literature.models import SearchQuery


def _write_corpus(path: Path, papers: list[dict]) -> Path:
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


def _sample_papers() -> list[dict]:
    return [
        {
            "id": "doi:10.1/x",
            "title": "Convex Optimization",
            "authors": ["Boyd, Stephen", "Vandenberghe, Lieven"],
            "year": 2004,
            "abstract": "A textbook on convex programming.",
            "keywords": ["convex", "optimization"],
        },
        {
            "id": "arxiv:1412.6980",
            "title": "Adam: a method for stochastic optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "abstract": "An optimizer for deep learning.",
        },
        {
            "id": "x:gradient",
            "title": "Gradient methods for composite functions",
            "authors": ["Nesterov, Yurii"],
            "year": 2013,
            "abstract": "Theory of gradient descent.",
        },
    ]


class TestLocalBackend:
    def test_returns_matches(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        results = backend.search(SearchQuery(text="convex"))
        assert len(results) == 1
        assert results[0].title == "Convex Optimization"

    def test_ranks_by_hit_count(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        results = backend.search(SearchQuery(text="convex optimization"))
        assert results[0].title == "Convex Optimization"
        # Score ∈ [0, 1].
        assert 0.0 <= results[0].score <= 1.0

    def test_caps_at_max_results(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        results = backend.search(SearchQuery(text="optimization", max_results=2))
        assert len(results) <= 2

    def test_year_filter_applied(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        results = backend.search(
            SearchQuery(text="optimization", year_min=2010, year_max=2014)
        )
        years = {p.year for p in results}
        assert all(2010 <= y <= 2014 for y in years if y is not None)

    def test_stamps_source(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        results = backend.search(SearchQuery(text="convex"))
        assert all(p.source == "local" for p in results)

    def test_supports_papers_key_wrapper(self, tmp_path: Path):
        path = tmp_path / "c.json"
        path.write_text(
            json.dumps({"papers": _sample_papers()}), encoding="utf-8"
        )
        backend = LocalBackend(path)
        results = backend.search(SearchQuery(text="convex"))
        assert len(results) == 1

    def test_no_match_returns_empty(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        assert backend.search(SearchQuery(text="quantum entanglement")) == []

    def test_invalid_corpus_path_raises(self, tmp_path: Path):
        backend = LocalBackend(tmp_path / "missing.json")
        with pytest.raises(BackendError):
            backend.search(SearchQuery(text="x"))

    def test_invalid_corpus_format_raises(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"not_a_list": True}), encoding="utf-8")
        backend = LocalBackend(path)
        with pytest.raises(BackendError):
            backend.search(SearchQuery(text="x"))

    def test_corpus_loaded_once(self, tmp_path: Path):
        corpus = _write_corpus(tmp_path / "c.json", _sample_papers())
        backend = LocalBackend(corpus)
        backend.search(SearchQuery(text="convex"))
        # Mutate the underlying file; backend should keep cached load.
        corpus.write_text(json.dumps([]), encoding="utf-8")
        results = backend.search(SearchQuery(text="convex"))
        assert len(results) == 1  # cached
