"""Resolver + cache tests (no mocks; pytest-httpserver + real SQLite)."""

from __future__ import annotations

from pathlib import Path

from pytest_httpserver import HTTPServer

from infrastructure.reference.verification.cache import CACHE_MISS, ResolutionCache
from infrastructure.reference.verification.resolver import (
    ReferenceResolver,
    normalize_doi,
    title_similarity,
)
from infrastructure.search.literature.models import Paper

CROSSREF_MESSAGE = {
    "message": {
        "DOI": "10.1234/abcd",
        "title": ["A Study of Deterministic Gates"],
        "author": [{"given": "Ada", "family": "Lovelace"}],
        "issued": {"date-parts": [[2020]]},
        "type": "journal-article",
        "container-title": ["Journal of Reproducibility"],
        "URL": "https://doi.org/10.1234/abcd",
    }
}

OPENALEX_RESULTS = {
    "results": [
        {
            "title": "A Study of Deterministic Gates",
            "publication_year": 2020,
            "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
            "doi": "https://doi.org/10.1234/abcd",
            "id": "https://openalex.org/W1",
            "primary_location": {"source": {"display_name": "Journal of Reproducibility"}},
        }
    ]
}

ARXIV_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.12948v1</id>
    <title>Reinforcement Learning Survey</title>
    <summary>A survey of RL.</summary>
    <published>2025-01-15T00:00:00Z</published>
    <author><name>Grace Hopper</name></author>
  </entry>
</feed>
"""


class TestPureHelpers:
    def test_normalize_doi_strips_prefixes(self):
        assert normalize_doi("https://doi.org/10.1/AB") == "10.1/ab"
        assert normalize_doi("doi:10.2/Cd") == "10.2/cd"
        assert normalize_doi("  10.3/EF  ") == "10.3/ef"

    def test_normalize_doi_dx_and_http_variants(self):
        # Legacy dx.doi.org and bare http:// prefixes must also strip.
        assert normalize_doi("http://dx.doi.org/10.1/AB") == "10.1/ab"
        assert normalize_doi("https://dx.doi.org/10.1/AB") == "10.1/ab"
        assert normalize_doi("HTTP://DOI.ORG/10.1/AB") == "10.1/ab"

    def test_title_similarity_bounds(self):
        assert title_similarity("Same Title", "Same Title") == 1.0
        assert title_similarity(None, "x") == 0.0
        assert title_similarity("alpha beta", "completely different words") < 0.5


class TestResolutionCache:
    def test_positive_roundtrip(self, tmp_path: Path):
        cache = ResolutionCache(tmp_path / "c.db")
        paper = Paper(id="doi:10.1/a", title="T", source="crossref")
        cache.put("doi:10.1/a", paper, resolved_via="crossref")
        got = cache.get("doi:10.1/a")
        assert isinstance(got, Paper)
        assert got.title == "T"

    def test_negative_cache_distinct_from_miss(self, tmp_path: Path):
        cache = ResolutionCache(tmp_path / "c.db")
        cache.put("doi:10.1/missing", None)
        assert cache.get("doi:10.1/missing") is None  # negative result
        assert cache.get("never-looked-up") is CACHE_MISS

    def test_ttl_expiry(self, tmp_path: Path):
        cache = ResolutionCache(tmp_path / "c.db", ttl_seconds=0)
        cache.put("k", Paper(id="x", title="T"))
        # ttl 0 → anything older than 'now' is expired; treated as a miss.
        assert cache.get("k") is CACHE_MISS

    def test_clear(self, tmp_path: Path):
        cache = ResolutionCache(tmp_path / "c.db")
        cache.put("a", None)
        cache.put("b", Paper(id="x", title="T"))
        assert cache.clear() == 2
        assert cache.get("a") is CACHE_MISS


class TestResolverOffline:
    def test_offline_cache_miss_is_unchecked(self, tmp_path: Path):
        resolver = ReferenceResolver(cache=ResolutionCache(tmp_path / "c.db"), allow_network=False)
        res = resolver.resolve(doi="10.1234/abcd")
        assert res.checked is False
        assert res.paper is None

    def test_offline_cache_hit(self, tmp_path: Path):
        cache = ResolutionCache(tmp_path / "c.db")
        cache.put("doi:10.1234/abcd", Paper(id="doi:10.1234/abcd", title="Cached", source="crossref"))
        resolver = ReferenceResolver(cache=cache, allow_network=False)
        res = resolver.resolve(doi="10.1234/abcd")
        assert res.checked is True
        assert res.from_cache is True
        assert res.paper is not None and res.paper.title == "Cached"

    def test_no_identifier_returns_unchecked(self, tmp_path: Path):
        resolver = ReferenceResolver(allow_network=True)
        res = resolver.resolve()  # nothing to resolve
        assert res.checked is False

    def test_poisoned_positive_row_is_rejected(self, tmp_path: Path):
        # A row keyed to a fabricated DOI but carrying a different real paper
        # must NOT be trusted offline (corruption / tampering guard).
        cache = ResolutionCache(tmp_path / "c.db")
        cache.put(
            "doi:10.9/fake",
            Paper(id="doi:10.1/real", title="A Real Different Paper", doi="10.1/real", source="crossref"),
        )
        resolver = ReferenceResolver(cache=cache, allow_network=False)
        res = resolver.resolve(doi="10.9/fake")
        assert res.checked is False  # inconsistent payload ignored → unchecked


class TestResolverOnline:
    def _resolver(self, httpserver: HTTPServer, tmp_path: Path) -> ReferenceResolver:
        return ReferenceResolver(
            cache=ResolutionCache(tmp_path / "c.db"),
            allow_network=True,
            crossref_base_url=httpserver.url_for("/crossref/works"),
            openalex_base_url=httpserver.url_for("/openalex/works"),
            arxiv_base_url=httpserver.url_for("/arxiv/query"),
        )

    def test_crossref_by_doi(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        res = self._resolver(httpserver, tmp_path).resolve(doi="10.1234/abcd")
        assert res.via == "crossref"
        assert res.paper is not None
        assert res.paper.title == "A Study of Deterministic Gates"

    def test_crossref_404_falls_back_to_openalex(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_data("", status=404)
        httpserver.expect_request("/openalex/works").respond_with_json(OPENALEX_RESULTS)
        res = self._resolver(httpserver, tmp_path).resolve(doi="10.1234/abcd")
        assert res.via == "openalex"
        assert res.paper is not None and res.paper.year == 2020

    def test_doi_not_found_anywhere(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.9/zz").respond_with_data("", status=404)
        httpserver.expect_request("/openalex/works").respond_with_json({"results": []})
        res = self._resolver(httpserver, tmp_path).resolve(doi="10.9/zz")
        assert res.checked is True
        assert res.paper is None
        assert res.via is None

    def test_transient_5xx_is_unchecked_not_cached(self, httpserver: HTTPServer, tmp_path: Path):
        # A 5xx outage is NOT "does not exist": it must yield unchecked and must
        # NOT be persisted as a negative result that later reads as fabricated.
        httpserver.expect_request("/crossref/works/10.1/x").respond_with_data("", status=503)
        httpserver.expect_request("/openalex/works").respond_with_data("", status=503)
        resolver = self._resolver(httpserver, tmp_path)
        res = resolver.resolve(doi="10.1/x")
        assert res.checked is False
        # Nothing cached: an offline replay on the same DB is still a miss.
        offline = ReferenceResolver(cache=ResolutionCache(tmp_path / "c.db"), allow_network=False)
        assert offline.resolve(doi="10.1/x").checked is False

    def test_arxiv_by_id(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/arxiv/query").respond_with_data(ARXIV_FEED, content_type="application/atom+xml")
        res = self._resolver(httpserver, tmp_path).resolve(arxiv_id="2501.12948")
        assert res.via == "arxiv"
        assert res.paper is not None and res.paper.title == "Reinforcement Learning Survey"

    def test_title_search(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works").respond_with_json(
            {"message": {"items": [CROSSREF_MESSAGE["message"]]}}
        )
        res = self._resolver(httpserver, tmp_path).resolve(title="A Study of Deterministic Gates")
        assert res.via == "crossref"
        assert res.paper is not None

    def test_online_result_is_cached(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        resolver = self._resolver(httpserver, tmp_path)
        first = resolver.resolve(doi="10.1234/abcd")
        assert first.from_cache is False
        assert first.paper is not None
        second = resolver.resolve(doi="10.1234/abcd")
        assert second.from_cache is True
        assert second.paper is not None and second.paper.title == first.paper.title
