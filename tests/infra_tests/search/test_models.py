"""Tests for infrastructure.search.literature.models."""

from __future__ import annotations

import pytest

from infrastructure.search.literature.models import (
    Paper,
    SearchQuery,
    SearchResult,
    merge_papers,
)


class TestPaper:
    def test_minimal_paper(self):
        p = Paper(id="doi:10.1/x", title="A Title")
        assert p.id == "doi:10.1/x"
        assert p.title == "A Title"
        assert p.authors == []
        assert p.year is None

    def test_year_coerced_to_int(self):
        p = Paper(id="x", title="T", year="2024")
        assert p.year == 2024
        assert isinstance(p.year, int)

    def test_invalid_year_raises(self):
        with pytest.raises(ValueError, match="year"):
            Paper(id="x", title="T", year="not-a-year")

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="id"):
            Paper(id="", title="T")

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="title"):
            Paper(id="x", title="")

    def test_round_trip_dict(self):
        p = Paper(
            id="x",
            title="T",
            authors=["A", "B"],
            year=2024,
            doi="10.1/x",
            keywords=["foo"],
        )
        d = p.to_dict()
        p2 = Paper.from_dict(d)
        assert p == p2

    def test_from_dict_drops_unknown_keys(self):
        p = Paper.from_dict({"id": "x", "title": "T", "extra_field": "ignore"})
        assert p.id == "x"

    def test_tuples_coerced_to_lists(self):
        p = Paper(id="x", title="T", authors=("A", "B"), keywords=("k",))
        assert isinstance(p.authors, list)
        assert isinstance(p.keywords, list)


class TestSearchQuery:
    def test_minimal_query(self):
        q = SearchQuery(text="convex optimization")
        assert q.text == "convex optimization"
        assert q.max_results == 10

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="text"):
            SearchQuery(text="")

    def test_zero_max_results_raises(self):
        with pytest.raises(ValueError, match="max_results"):
            SearchQuery(text="x", max_results=0)

    def test_inverted_year_range_raises(self):
        with pytest.raises(ValueError, match="year_min"):
            SearchQuery(text="x", year_min=2025, year_max=2020)

    def test_year_filter_passes_when_unset(self):
        q = SearchQuery(text="x")
        assert q.matches_year(2024) is True
        assert q.matches_year(None) is True

    def test_year_min_filter(self):
        q = SearchQuery(text="x", year_min=2020)
        assert q.matches_year(2019) is False
        assert q.matches_year(2020) is True
        assert q.matches_year(2024) is True

    def test_year_max_filter(self):
        q = SearchQuery(text="x", year_max=2020)
        assert q.matches_year(2019) is True
        assert q.matches_year(2020) is True
        assert q.matches_year(2021) is False

    def test_year_range_inclusive(self):
        q = SearchQuery(text="x", year_min=2010, year_max=2020)
        assert q.matches_year(2010) is True
        assert q.matches_year(2020) is True
        assert q.matches_year(2009) is False
        assert q.matches_year(2021) is False


class TestMergePapers:
    def test_empty_input_returns_empty(self):
        assert merge_papers([]) == []

    def test_unique_papers_returned_as_is(self):
        a = Paper(id="doi:10.1/a", title="A", doi="10.1/a")
        b = Paper(id="doi:10.1/b", title="B", doi="10.1/b")
        merged = merge_papers([a, b])
        assert len(merged) == 2

    def test_dedupes_by_doi(self):
        a = Paper(id="x:1", title="A", doi="10.1/x", source="s1", score=0.4)
        b = Paper(id="x:2", title="A copy", doi="10.1/X", source="s2", score=0.9)
        merged = merge_papers([a, b])
        assert len(merged) == 1
        # Higher score wins.
        assert merged[0].score == 0.9
        assert merged[0].title == "A copy"

    def test_dedupes_by_arxiv_id(self):
        a = Paper(id="arxiv:1234.5678", title="P", source="arxiv", score=0.2)
        b = Paper(id="arxiv:1234.5678", title="P", source="local", score=0.8)
        merged = merge_papers([a, b])
        assert len(merged) == 1
        assert merged[0].score == 0.8

    def test_dedupes_by_title_year_when_no_doi(self):
        a = Paper(id="a", title="Hello World", year=2024, score=0.1)
        b = Paper(id="b", title="Hello World!", year=2024, score=0.5)
        merged = merge_papers([a, b])
        assert len(merged) == 1
        assert merged[0].score == 0.5

    def test_loser_fields_filled_into_winner(self):
        a = Paper(id="x", title="P", doi="10.1/x", score=0.1, abstract="Abs")
        b = Paper(id="y", title="P2", doi="10.1/x", score=0.9, year=2024, venue="Nature")
        merged = merge_papers([a, b])
        assert len(merged) == 1
        winner = merged[0]
        assert winner.score == 0.9
        # Winner had no abstract; loser had one — should be filled in.
        assert winner.abstract == "Abs"
        assert winner.year == 2024
        assert winner.venue == "Nature"

    def test_authors_merged_in_order_no_duplicates(self):
        a = Paper(id="x", title="P", doi="10.1/x", authors=["A", "B"], score=0.5)
        b = Paper(id="y", title="P", doi="10.1/x", authors=["B", "C"], score=0.3)
        merged = merge_papers([a, b])
        assert merged[0].authors == ["A", "B", "C"]


class TestSearchResult:
    def test_empty_result_serialises(self):
        q = SearchQuery(text="x")
        r = SearchResult(query=q)
        assert len(r) == 0
        assert "papers" in r.to_dict()
        # JSON round trip.
        import json as _json

        assert _json.loads(r.to_json()) == r.to_dict()

    def test_iter_yields_papers(self):
        q = SearchQuery(text="x")
        papers = [Paper(id=f"p{i}", title=f"T{i}") for i in range(3)]
        r = SearchResult(query=q, papers=papers)
        assert list(r) == papers
