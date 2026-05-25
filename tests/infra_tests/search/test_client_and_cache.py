"""Tests for the LiteratureClient aggregator and SearchCache."""

from __future__ import annotations

import json
import time
from pathlib import Path


from infrastructure.search.literature.backends import (
    BackendError,
    LocalBackend,
    SearchBackend,
)
from infrastructure.search.literature.cache import SearchCache
from infrastructure.search.literature.client import LiteratureClient
from infrastructure.search.literature.models import (
    Paper,
    SearchQuery,
    SearchResult,
)


# ---------------------------------------------------------------------------
# Test backends — real classes (no mocking framework), just predictable
# subclasses we can drop into the aggregator.
# ---------------------------------------------------------------------------


class _FixedBackend(SearchBackend):
    """Returns a fixed list of papers; honours year filter."""

    def __init__(self, name: str, papers: list[Paper]) -> None:
        self.name = name
        self._papers = papers

    def search(self, query: SearchQuery) -> list[Paper]:
        out: list[Paper] = []
        for paper in self._papers:
            if not query.matches_year(paper.year):
                continue
            paper.source = self.name
            out.append(paper)
        return out[: query.max_results]


class _FailingBackend(SearchBackend):
    def __init__(self, name: str, message: str = "boom") -> None:
        self.name = name
        self._message = message

    def search(self, query: SearchQuery) -> list[Paper]:
        raise BackendError(self._message)


# ---------------------------------------------------------------------------
# LiteratureClient
# ---------------------------------------------------------------------------


class TestLiteratureClient:
    def test_aggregates_across_backends(self):
        a = _FixedBackend("a", [Paper(id="x:1", title="P1", score=0.9)])
        b = _FixedBackend("b", [Paper(id="x:2", title="P2", score=0.4)])
        client = LiteratureClient([a, b])
        result = client.search(SearchQuery(text="anything"))
        assert {p.id for p in result.papers} == {"x:1", "x:2"}
        assert result.per_source_counts == {"a": 1, "b": 1}
        assert result.errors == {}

    def test_dedupes_across_backends_by_doi(self):
        p_a = Paper(id="a:1", title="X", doi="10.1/x", score=0.3, source="a")
        p_b = Paper(id="b:1", title="X copy", doi="10.1/x", score=0.9, source="b")
        client = LiteratureClient(
            [
                _FixedBackend("a", [p_a]),
                _FixedBackend("b", [p_b]),
            ]
        )
        result = client.search(SearchQuery(text="x"))
        assert len(result.papers) == 1
        # Higher-scored copy wins.
        assert result.papers[0].score == 0.9

    def test_per_backend_failure_recorded_not_raised(self):
        client = LiteratureClient(
            [
                _FailingBackend("flaky", "transient"),
                _FixedBackend("ok", [Paper(id="a", title="A")]),
            ]
        )
        result = client.search(SearchQuery(text="x"))
        assert "flaky" in result.errors
        assert result.errors["flaky"] == "transient"
        assert len(result.papers) == 1

    def test_query_sources_filters_backends(self):
        client = LiteratureClient(
            [
                _FixedBackend("a", [Paper(id="a", title="A")]),
                _FixedBackend("b", [Paper(id="b", title="B")]),
            ]
        )
        result = client.search(SearchQuery(text="x", sources=["b"]))
        assert {p.id for p in result.papers} == {"b"}
        assert "a" not in result.per_source_counts

    def test_results_capped_to_max(self):
        client = LiteratureClient(
            [
                _FixedBackend(
                    "a",
                    [Paper(id=f"x:{i}", title=f"T{i}", score=0.1 * i) for i in range(10)],
                )
            ]
        )
        result = client.search(SearchQuery(text="x", max_results=3))
        assert len(result.papers) == 3
        # Sorted by score desc.
        scores = [p.score for p in result.papers]
        assert scores == sorted(scores, reverse=True)

    def test_year_filter_applied_defensively(self):
        # Backend ignores the year filter; client must still apply it.
        class _IgnoresYearFilter(SearchBackend):
            name = "ignore_year"

            def search(self, query: SearchQuery) -> list[Paper]:
                return [
                    Paper(id="old", title="old", year=1990),
                    Paper(id="new", title="new", year=2020),
                ]

        client = LiteratureClient([_IgnoresYearFilter()])
        result = client.search(SearchQuery(text="x", year_min=2000))
        assert {p.id for p in result.papers} == {"new"}

    def test_real_local_backend_integration(self, tmp_path: Path):
        corpus = tmp_path / "c.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "id": "doi:10.1/x",
                        "title": "Convex Optimization",
                        "authors": ["Boyd, Stephen"],
                        "year": 2004,
                        "doi": "10.1/x",
                    }
                ]
            ),
            encoding="utf-8",
        )
        client = LiteratureClient([LocalBackend(corpus)])
        result = client.search(SearchQuery(text="convex"))
        assert len(result.papers) == 1
        assert result.per_source_counts["local"] == 1


# ---------------------------------------------------------------------------
# SearchCache
# ---------------------------------------------------------------------------


class TestSearchCache:
    def test_miss_returns_none(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        assert cache.get(SearchQuery(text="anything")) is None

    def test_round_trip(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        q = SearchQuery(text="convex", max_results=5)
        result = SearchResult(
            query=q,
            papers=[Paper(id="x", title="T", year=2024)],
            per_source_counts={"local": 1},
        )
        path = cache.put(result)
        assert path.exists()
        recovered = cache.get(q)
        assert recovered is not None
        assert len(recovered.papers) == 1
        assert recovered.papers[0].id == "x"
        assert recovered.per_source_counts == {"local": 1}

    def test_hash_distinguishes_queries(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        q1 = SearchQuery(text="A")
        q2 = SearchQuery(text="B")
        assert cache.path_for(q1) != cache.path_for(q2)

    def test_text_normalisation_in_hash(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        # Whitespace and case should not change cache identity.
        assert cache.path_for(SearchQuery(text="  Foo  ")) == cache.path_for(SearchQuery(text="foo"))

    def test_ttl_expires_old_entries(self, tmp_path: Path):
        cache = SearchCache(tmp_path, ttl_seconds=1)
        q = SearchQuery(text="x")
        cache.put(SearchResult(query=q))
        # Force the timestamp to be older than TTL.
        path = cache.path_for(q)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_cached_at"] = time.time() - 10
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert cache.get(q) is None

    def test_clear_removes_entries(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        q = SearchQuery(text="x")
        cache.put(SearchResult(query=q))
        assert cache.clear() == 1
        assert cache.get(q) is None

    def test_corrupt_file_returns_none(self, tmp_path: Path):
        cache = SearchCache(tmp_path)
        q = SearchQuery(text="x")
        cache.path_for(q).parent.mkdir(parents=True, exist_ok=True)
        cache.path_for(q).write_text("{not json", encoding="utf-8")
        assert cache.get(q) is None

    def test_client_uses_cache_when_provided(self, tmp_path: Path):
        called = {"count": 0}

        class _CountingBackend(SearchBackend):
            name = "counter"

            def search(self, query: SearchQuery) -> list[Paper]:
                called["count"] += 1
                return [Paper(id="x", title="T")]

        cache = SearchCache(tmp_path)
        client = LiteratureClient([_CountingBackend()], cache=cache)

        q = SearchQuery(text="convex")
        client.search(q)
        client.search(q)
        client.search(q)
        # Backend was called exactly once; the rest were cache hits.
        assert called["count"] == 1

    def test_use_cache_false_bypasses_cache_read(self, tmp_path: Path):
        called = {"count": 0}

        class _CountingBackend(SearchBackend):
            name = "counter"

            def search(self, query: SearchQuery) -> list[Paper]:
                called["count"] += 1
                return [Paper(id="x", title="T")]

        cache = SearchCache(tmp_path)
        client = LiteratureClient([_CountingBackend()], cache=cache)
        q = SearchQuery(text="convex")
        client.search(q)
        client.search(q, use_cache=False)
        assert called["count"] == 2
