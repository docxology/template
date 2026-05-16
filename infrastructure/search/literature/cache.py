"""Simple JSON-file cache for literature-search results.

This is *not* a general-purpose cache — it's a deterministic, observable
on-disk cache that:

* Hashes (query text, max_results, year filters, sources) to produce a key.
* Stores results as pretty-printed JSON, one file per key, so cache hits are
  greppable and version-control-friendly.
* Has no expiry by default; callers pass ``ttl_seconds`` when they want one.

We deliberately avoid pickle / sqlite / per-process locks: the cache is
intended for single-agent reproducibility (run a search once, replay in
tests, ship in CI artifacts).
"""

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from infrastructure.search.literature.models import Paper, SearchQuery, SearchResult


def _query_hash(query: SearchQuery) -> str:
    """Deterministic short hash of *query*'s identity-defining fields."""
    payload = json.dumps(
        {
            "text": query.text.strip().lower(),
            "max_results": query.max_results,
            "year_min": query.year_min,
            "year_max": query.year_max,
            "sources": sorted(query.sources or []),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class SearchCache:
    """JSON-file cache for :class:`SearchResult` objects.

    Args:
        cache_dir: Directory where JSON cache entries are written. Created on
            first access.
        ttl_seconds: Optional TTL. Hits older than ``now - ttl_seconds`` are
            treated as misses. ``None`` disables expiry.
    """

    def __init__(self, cache_dir: Path | str, *, ttl_seconds: int | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds

    def path_for(self, query: SearchQuery) -> Path:
        return self.cache_dir / f"search_{_query_hash(query)}.json"

    def get(self, query: SearchQuery) -> SearchResult | None:
        path = self.path_for(query)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if self.ttl_seconds is not None:
            ts = payload.get("_cached_at", 0)
            if time.time() - ts > self.ttl_seconds:
                return None
        try:
            stored_query = SearchQuery(**payload["query"])
            papers = [Paper.from_dict(p) for p in payload.get("papers") or []]
        except (KeyError, TypeError, ValueError):
            return None
        return SearchResult(
            query=stored_query,
            papers=papers,
            per_source_counts=dict(payload.get("per_source_counts") or {}),
            errors=dict(payload.get("errors") or {}),
        )

    def put(self, result: SearchResult) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = result.to_dict()
        payload["_cached_at"] = time.time()
        # Use vanilla json so the dataclass nesting is plain dicts.
        # SearchQuery → dict was already done by `to_dict()`; just confirm.
        if not isinstance(payload["query"], dict):
            payload["query"] = asdict(result.query)
        path = self.path_for(result.query)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def clear(self) -> int:
        """Delete every ``search_*.json`` entry. Returns the number removed."""
        if not self.cache_dir.exists():
            return 0
        count = 0
        for path in self.cache_dir.glob("search_*.json"):
            path.unlink()
            count += 1
        return count
