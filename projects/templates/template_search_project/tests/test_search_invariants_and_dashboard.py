"""Tests for src.search_invariants + scripts/zzz_build_dashboard.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.search_invariants import (
    InvariantResult,
    all_invariants,
    coverage_invariants,
    keyword_invariants,
    schema_invariants,
    uniqueness_invariants,
    year_invariants,
)


THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
BUNDLED_CORPUS = PROJECT_ROOT / "data" / "corpus.json"
OUTPUT_CORPUS = PROJECT_ROOT / "output" / "corpus.json"
AGGREGATE = PROJECT_ROOT / "output" / "deep_search" / "aggregate.json"


def _evaluate(r: InvariantResult) -> bool:
    if r.kind == "equal":
        return abs(float(r.actual) - float(r.expected)) <= r.tol
    if r.kind == "le":
        return float(r.actual) <= float(r.expected) + r.tol
    if r.kind == "ge":
        return float(r.actual) >= float(r.expected) - r.tol
    return False


@pytest.fixture(scope="session")
def runtime_corpus(tmp_path_factory) -> Path:
    """Pipeline-mode-safe corpus path.

    Prefers the live ``output/corpus.json`` if a prior pipeline populated
    it; otherwise materialises a copy of the bundled ``data/corpus.json``
    in a session-scoped tmp dir so dashboard CLI tests work even when
    stage 0 of the pipeline has just wiped ``output/``.
    """
    if OUTPUT_CORPUS.exists():
        return OUTPUT_CORPUS
    dest = tmp_path_factory.mktemp("search_corpus") / "corpus.json"
    dest.write_text(BUNDLED_CORPUS.read_text(), encoding="utf-8")
    return dest


@pytest.fixture(scope="module")
def papers():
    source = OUTPUT_CORPUS if OUTPUT_CORPUS.exists() else BUNDLED_CORPUS
    raw = json.loads(source.read_text())
    return raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw


@pytest.fixture(scope="module")
def aggregate():
    """Real aggregate when present, synthesised one otherwise.

    A deep-search aggregate has the shape produced by
    ``src.deep_search.run_deep_search``:
    ``{"keywords": [...], "unique_papers": [...], "citation_keys": {...}}``.
    When stage 4 of the pipeline hasn't run, we synthesise one from the
    bundled corpus so invariant tests still cover ``keyword_invariants``
    and the ``all_invariants`` aggregate path.
    """
    if AGGREGATE.exists():
        return json.loads(AGGREGATE.read_text())
    raw = json.loads(BUNDLED_CORPUS.read_text())
    papers = raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw
    return {
        "keywords": ["bundled-corpus"],
        "unique_papers": papers,
        "citation_keys": {p["id"]: p["id"] for p in papers},
    }


@pytest.fixture(scope="module")
def aggregate_min_per_keyword() -> int:
    """Floor for ``keyword_invariants(min_per_keyword=…)``.

    Real deep-search aggregates retrieve ≥10 papers per keyword;
    synthesised aggregates from the bundled corpus carry a single
    keyword over the full corpus, so the floor must drop to 1.
    """
    if AGGREGATE.exists():
        return 10
    return 1


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class TestSchemaInvariants:
    def test_real_corpus_passes(self, papers):
        for inv in schema_invariants(papers):
            assert _evaluate(inv), inv.description

    def test_missing_id_caught(self):
        invs = schema_invariants([{"title": "T"}])
        id_inv = next(i for i in invs if i.name == "paper_field_present_id")
        assert id_inv.actual == 1.0


# ---------------------------------------------------------------------------
# Uniqueness
# ---------------------------------------------------------------------------


class TestUniquenessInvariants:
    def test_real_corpus_unique(self, papers):
        for inv in uniqueness_invariants(papers):
            assert _evaluate(inv)

    def test_dup_caught(self):
        invs = uniqueness_invariants(
            [
                {"id": "a", "title": "X"},
                {"id": "a", "title": "Y"},
            ]
        )
        assert invs[0].actual == 1.0


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


class TestCoverageInvariants:
    def test_real_corpus_passes(self, papers):
        for inv in coverage_invariants(papers):
            assert _evaluate(inv), inv.description

    def test_strict_floor_fails_when_low(self):
        invs = coverage_invariants(
            [{"id": "x", "title": "T"}],  # no DOI / abstract / year
            doi_floor=0.99,
        )
        doi = next(i for i in invs if i.name == "doi_coverage_above_floor")
        assert not _evaluate(doi)


class TestYearInvariants:
    def test_real_corpus_in_range(self, papers):
        for inv in year_invariants(papers):
            assert _evaluate(inv), inv.description

    def test_no_dated_papers_returns_empty(self):
        assert year_invariants([{"id": "x", "title": "T"}]) == []


class TestKeywordInvariants:
    def test_real_aggregate_passes(self, aggregate, aggregate_min_per_keyword):
        for inv in keyword_invariants(aggregate, min_per_keyword=aggregate_min_per_keyword):
            assert _evaluate(inv), inv.description


class TestAllInvariants:
    def test_real_corpus_all_pass(self, papers, aggregate, aggregate_min_per_keyword):
        invs = all_invariants(papers, aggregate=aggregate, min_per_keyword=aggregate_min_per_keyword)
        # n_pass == n_total > some floor
        assert len(invs) >= 9
        for inv in invs:
            assert _evaluate(inv), inv.name


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestBuildDashboardCLI:
    def test_default_run(self, tmp_path, runtime_corpus):
        html = tmp_path / "d.html"
        js = tmp_path / "d.json"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "zzz_build_dashboard.py"),
                "--corpus",
                str(runtime_corpus),
                "--html-out",
                str(html),
                "--json-out",
                str(js),
                "--invariants-out",
                str(tmp_path / "i.txt"),
                "--summary-out",
                str(tmp_path / "s.txt"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        bundle = json.loads(js.read_text())
        n_pass = sum(1 for i in bundle["invariants"] if i["passed"])
        assert n_pass == len(bundle["invariants"]) >= 8

    def test_strict_floors_fail_invariants(self, tmp_path, runtime_corpus):
        # Force impossible coverage floors: invariant should fail and CLI exits 1
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "zzz_build_dashboard.py"),
                "--corpus",
                str(runtime_corpus),
                "--doi-floor",
                "0.99",
                "--abstract-floor",
                "0.99",
                "--year-floor",
                "0.99",
                "--html-out",
                str(tmp_path / "d.html"),
                "--json-out",
                str(tmp_path / "d.json"),
                "--invariants-out",
                str(tmp_path / "i.txt"),
                "--summary-out",
                str(tmp_path / "s.txt"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # The corpus has 100% abstract / year coverage but only 66% DOI,
        # so the strict floor must catch the doi_coverage invariant.
        assert result.returncode != 0
        assert "doi_coverage" in (result.stderr + result.stdout)

    def test_year_filter_propagates(self, tmp_path, runtime_corpus):
        js = tmp_path / "d.json"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "zzz_build_dashboard.py"),
                "--corpus",
                str(runtime_corpus),
                "--year-min",
                "2010",
                "--year-max",
                "2020",
                "--html-out",
                str(tmp_path / "d.html"),
                "--json-out",
                str(js),
                "--invariants-out",
                str(tmp_path / "i.txt"),
                "--summary-out",
                str(tmp_path / "s.txt"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        bundle = json.loads(js.read_text())
        for year_str in bundle["payload"]["year_distribution"]:
            assert 2010 <= int(year_str) <= 2020

    def test_rejects_inverted_year_range(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "zzz_build_dashboard.py"),
                "--year-min",
                "2020",
                "--year-max",
                "2000",
                "--html-out",
                str(tmp_path / "x.html"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
