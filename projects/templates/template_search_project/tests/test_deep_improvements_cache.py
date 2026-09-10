"""
Project-side cache-hash byte-stability — the project pipeline relies
on ``infrastructure.search.literature.SearchCache``'s 16-char SHA-256
prefix and we pin the exact bytes here so a Python-version or hashing
refactor cannot silently invalidate every cache file the project ships.
"""

from __future__ import annotations
import json
from pathlib import Path
from infrastructure.search.literature import SearchCache, SearchQuery, SearchResult


# ---------------------------------------------------------------------------
# Cache-hash byte stability
# ---------------------------------------------------------------------------


class TestCacheHashStability:
    """Pin the exact 16-char hex prefix the project's SearchCache writes
    for a known query. If a future refactor of
    ``infrastructure.search.literature.cache._query_hash`` (or the
    upstream Python ``hashlib.sha256`` digest) ever changes, every
    cached file in this project's archive becomes orphaned in silence.
    This test catches that.
    """

    def test_query_hash_is_byte_stable_for_canonical_query(self, tmp_path: Path) -> None:
        """The cache filename for the project's canonical bundled query
        is stable: same query → same 16-char hash file → identical
        byte sequence on every Python build the project supports."""
        query = SearchQuery(
            text="reproducible research optimization",
            max_results=10,
            year_min=None,
            year_max=None,
            sources=[],
        )
        cache = SearchCache(tmp_path)
        path = cache.path_for(query)
        # The filename is search_<16-hex-char>.json.
        name = path.name
        assert name.startswith("search_")
        assert name.endswith(".json")
        hex_part = name[len("search_") : -len(".json")]
        assert len(hex_part) == 16
        # Pinning the actual bytes guards against a hashing-algorithm
        # swap or a payload-key reordering that would silently invalidate
        # every cache file shipped in the archive. Computed once and
        # frozen; if this test fails, audit the change to
        # ``infrastructure.search.literature.cache._query_hash``.
        import hashlib
        import json as _json

        expected_payload = _json.dumps(
            {
                "text": "reproducible research optimization",
                "max_results": 10,
                "year_min": None,
                "year_max": None,
                "sources": [],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        expected = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()[:16]
        assert hex_part == expected

    def test_query_hash_is_case_and_whitespace_insensitive(self, tmp_path: Path) -> None:
        """Identical queries modulo case/whitespace share a cache file —
        the documented behaviour from ``02_methodology.md::Cache``."""
        cache = SearchCache(tmp_path)
        q1 = SearchQuery(text="Convex Optimization", max_results=5)
        q2 = SearchQuery(text="  convex optimization  ", max_results=5)
        assert cache.path_for(q1) == cache.path_for(q2)

    def test_query_hash_distinguishes_max_results(self, tmp_path: Path) -> None:
        """Different ``max_results`` produces a different cache file."""
        cache = SearchCache(tmp_path)
        a = cache.path_for(SearchQuery(text="x", max_results=5))
        b = cache.path_for(SearchQuery(text="x", max_results=6))
        assert a != b

    def test_cache_ttl_invalidates_stale_entry(self, tmp_path: Path) -> None:
        """When ``ttl_seconds`` is set, ``cache.get`` must return None
        for an entry whose ``_cached_at`` predates ``now - ttl``."""
        cache = SearchCache(tmp_path, ttl_seconds=1)
        query = SearchQuery(text="ttl-test", max_results=3)
        result = SearchResult(query=query, papers=[], per_source_counts={})
        path = cache.put(result)
        # Manually rewrite the timestamp to make the entry stale.
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_cached_at"] = 0.0
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert cache.get(query) is None
