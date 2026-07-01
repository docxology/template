"""Direct-call tests for src.dashboard (no mocks; real files)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.dashboard import build_dashboard, compute_payload, filter_papers, load_papers

REPO_ROOT = Path(__file__).resolve().parents[4]


def _args(**overrides) -> argparse.Namespace:
    defaults = dict(
        corpus=None,
        aggregate=None,
        year_min=None,
        year_max=None,
        doi_floor=0.5,
        abstract_floor=0.5,
        year_floor=0.7,
        min_per_keyword=1,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _write_corpus(tmp_path: Path) -> Path:
    papers = [
        {"id": "a", "title": "A", "year": 2010, "doi": "10.1/a", "abstract": "x", "source": "arxiv"},
        {"id": "b", "title": "B", "year": 2020, "source": "crossref", "venue_type": "journal"},
        {"id": "c", "title": "C", "year": 2015, "doi": "10.1/c", "abstract": "y", "venue_type": "conference"},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


def test_load_papers_plain_list(tmp_path: Path):
    corpus = _write_corpus(tmp_path)
    args = _args(corpus=corpus, aggregate=tmp_path / "missing.json")
    papers, aggregate = load_papers(args)
    assert len(papers) == 3
    assert aggregate is None


def test_load_papers_dict_wrapped_and_aggregate(tmp_path: Path):
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps({"papers": [{"id": "a", "title": "A"}]}), encoding="utf-8")
    agg_path = tmp_path / "aggregate.json"
    agg_path.write_text(
        json.dumps({"keywords": ["kw"], "unique_papers": [{"id": "a"}]}),
        encoding="utf-8",
    )
    args = _args(corpus=corpus_path, aggregate=agg_path)
    papers, aggregate = load_papers(args)
    assert papers == [{"id": "a", "title": "A"}]
    assert aggregate is not None
    assert aggregate["keywords"] == ["kw"]


def test_load_papers_aggregate_without_unique_papers_key(tmp_path: Path):
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps([{"id": "a"}]), encoding="utf-8")
    agg_path = tmp_path / "aggregate.json"
    agg_path.write_text(json.dumps({"keywords": ["kw"]}), encoding="utf-8")
    args = _args(corpus=corpus_path, aggregate=agg_path)
    _, aggregate = load_papers(args)
    assert aggregate is None


def test_filter_papers_year_range():
    papers = [
        {"id": "a", "year": 2000},
        {"id": "b", "year": 2010},
        {"id": "c", "year": 2020},
        {"id": "d"},  # no year — always kept
    ]
    args = _args(year_min=2005, year_max=2015)
    out = filter_papers(papers, args)
    assert {p["id"] for p in out} == {"b", "d"}


def test_compute_payload_coverage_and_preview():
    papers = [
        {
            "id": "a",
            "title": "T" * 200,
            "year": 2010,
            "doi": "x",
            "abstract": "abc",
            "source": "arxiv",
            "venue_type": "journal",
        },
        {"id": "b", "title": "B", "year": 2010, "source": "crossref"},
    ]
    payload = compute_payload(papers, aggregate=None)
    assert payload["n_total"] == 2
    assert payload["coverage"]["doi"] == 0.5
    assert payload["coverage"]["abstract"] == 0.5
    assert payload["source_distribution"] == {"arxiv": 1, "crossref": 1}
    assert len(payload["papers_preview"][0]["title"]) == 120
    assert payload["keywords"] == []


def test_compute_payload_with_aggregate_keywords():
    payload = compute_payload([{"id": "a", "year": 2020}], aggregate={"keywords": ["kw1", "kw2"]})
    assert payload["keywords"] == ["kw1", "kw2"]


def test_compute_payload_empty_papers_avoids_zero_division():
    payload = compute_payload([], aggregate=None)
    assert payload["n_total"] == 0
    assert payload["coverage"]["doi"] == 0.0


def test_build_dashboard_panels_and_invariants(tmp_path: Path):
    corpus = _write_corpus(tmp_path)
    args = _args(corpus=corpus, aggregate=tmp_path / "missing.json")
    papers, aggregate = load_papers(args)
    payload = compute_payload(papers, aggregate)
    dashboard = build_dashboard(args, payload, papers, aggregate, repo_root=REPO_ROOT)
    panel_ids = {p.panel_id for p in dashboard.panels}
    assert {"year_distribution", "source_distribution", "venue_type", "coverage"} <= panel_ids
    # schema(2) + uniqueness(1) + coverage(3) + year(2) invariants; no
    # aggregate here so keyword_invariants (3 more) are not added.
    assert len(dashboard.invariants) >= 8


def test_build_dashboard_keywords_panel_when_present(tmp_path: Path):
    corpus = _write_corpus(tmp_path)
    args = _args(corpus=corpus, aggregate=tmp_path / "missing.json")
    papers, _ = load_papers(args)
    aggregate = {"keywords": ["kw1"], "unique_papers": papers}
    payload = compute_payload(papers, aggregate)
    dashboard = build_dashboard(args, payload, papers, aggregate, repo_root=REPO_ROOT)
    panel_ids = {p.panel_id for p in dashboard.panels}
    assert "keywords" in panel_ids
