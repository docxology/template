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
from typing import Any

from infrastructure.core.files.secure_write import (
    atomic_write_text_confined,
    confined_file_lock,
    read_bytes_confined,
    unlink_confined,
)
from infrastructure.search.literature.models import Paper, SearchQuery, SearchResult


SEARCH_CACHE_SCHEMA_VERSION = 1


def query_identity(query: SearchQuery) -> dict[str, Any]:
    """Return the canonical, receipt-friendly identity of *query*."""
    import re

    # Normalize whitespace: collapse consecutive spaces, tabs, and newlines
    normalized_text = re.sub(r"\s+", " ", query.text.strip().lower())
    return {
        "text": normalized_text,
        "max_results": query.max_results,
        "year_min": query.year_min,
        "year_max": query.year_max,
        "sources": sorted(query.sources or []),
    }


def query_cache_key(query: SearchQuery) -> str:
    """Return the deterministic short cache key for *query*."""
    payload = json.dumps(query_identity(query), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def validate_cache_payload(payload: Any, query: SearchQuery | None = None) -> list[str]:
    """Return actionable schema/identity errors for a JSON cache payload.

    Legacy entries without the new metadata remain readable; newly written
    entries carry both a schema version and an explicit cache key so receipts
    can prove which query identity was replayed.
    """
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a mapping"]
    version = payload.get("_schema_version")
    if version is not None and version != SEARCH_CACHE_SCHEMA_VERSION:
        errors.append(f"unsupported _schema_version: {version!r}")
    stored_query = payload.get("query")
    if not isinstance(stored_query, dict):
        errors.append("query must be a mapping")
    elif query is not None:
        import re

        stored_text = re.sub(r"\s+", " ", str(stored_query.get("text", "")).strip().lower())
        stored_identity = {
            "text": stored_text,
            "max_results": stored_query.get("max_results"),
            "year_min": stored_query.get("year_min"),
            "year_max": stored_query.get("year_max"),
            "sources": sorted(stored_query.get("sources") or []),
        }
        if stored_identity != query_identity(query):
            errors.append("query identity does not match requested query")
    stored_key = payload.get("_cache_key")
    if stored_key is not None and query is not None and stored_key != query_cache_key(query):
        errors.append("_cache_key does not match requested query")
    if not isinstance(payload.get("papers", []), list):
        errors.append("papers must be a list")
    for field in ("per_source_counts", "errors"):
        if not isinstance(payload.get(field, {}), dict):
            errors.append(f"{field} must be a mapping")
    cached_at = payload.get("_cached_at")
    if cached_at is not None and (not isinstance(cached_at, (int, float)) or cached_at < 0):
        errors.append("_cached_at must be a non-negative number")
    return errors


class SearchCache:
    """JSON-file cache for :class:`SearchResult` objects.

    Args:
        cache_dir: Directory where JSON cache entries are written. Created on
            first access.
        ttl_seconds: Optional TTL. Hits older than ``now - ttl_seconds`` are
            treated as misses. ``None`` disables expiry.
        confinement_root: Optional nominated project directory. Cache paths
            remain lexical children of this directory; every opted-in read,
            write and clear refuses symlink ancestors and leaves through the
            platform's held-directory I/O. Unsafe reads raise instead of
            becoming cache misses. Callers without a root retain ordinary
            filesystem cache semantics.
    """

    def __init__(
        self,
        cache_dir: Path | str,
        *,
        ttl_seconds: int | None = None,
        confinement_root: Path | str | None = None,
    ) -> None:
        self.confinement_root = Path(confinement_root).absolute() if confinement_root is not None else None
        self.cache_dir = Path(cache_dir)
        if self.confinement_root is not None:
            self.cache_dir = self.cache_dir if self.cache_dir.is_absolute() else self.confinement_root / self.cache_dir
            if not self.cache_dir.is_relative_to(self.confinement_root) or ".." in self.cache_dir.parts:
                raise ValueError("Search cache directory escapes nominated confinement root")
        self.ttl_seconds = ttl_seconds

    def path_for(self, query: SearchQuery) -> Path:
        """Process path for."""
        return self.cache_dir / f"search_{query_cache_key(query)}.json"

    def get(self, query: SearchQuery) -> SearchResult | None:
        """Get a cached value, or None if not present."""
        path = self.path_for(query)
        if self.confinement_root is None and not path.exists():
            return None
        try:
            raw = (
                read_bytes_confined(self.confinement_root, path).decode("utf-8")
                if self.confinement_root is not None
                else path.read_text(encoding="utf-8")
            )
            payload = json.loads(raw)
        except FileNotFoundError, json.JSONDecodeError:
            return None
        except OSError:
            if self.confinement_root is not None:
                raise
            return None
        if validate_cache_payload(payload, query):
            return None
        if self.ttl_seconds is not None:
            ts = payload.get("_cached_at", 0)
            if time.time() - ts > self.ttl_seconds:
                return None
        try:
            stored_query = SearchQuery(**payload["query"])
            papers = [Paper.from_dict(p) for p in payload.get("papers") or []]
        except KeyError, TypeError, ValueError:
            return None
        return SearchResult(
            query=stored_query,
            papers=papers,
            per_source_counts=dict(payload.get("per_source_counts") or {}),
            errors=dict(payload.get("errors") or {}),
        )

    def put(self, result: SearchResult) -> Path:
        """Process put."""
        payload = result.to_dict()
        payload["_schema_version"] = SEARCH_CACHE_SCHEMA_VERSION
        payload["_cache_key"] = query_cache_key(result.query)
        payload["_cached_at"] = time.time()
        # Use vanilla json so the dataclass nesting is plain dicts.
        # SearchQuery → dict was already done by `to_dict()`; just confirm.
        if not isinstance(payload["query"], dict):
            payload["query"] = asdict(result.query)
        path = self.path_for(result.query)
        content = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
        if self.confinement_root is not None:
            atomic_write_text_confined(self.confinement_root, path, content)
        else:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return path

    def clear(self) -> int:
        """Delete every ``search_*.json`` entry. Returns the number removed."""
        if self.confinement_root is not None:
            with confined_file_lock(self.confinement_root, self.cache_dir / ".cache-clear.lock"):
                count = 0
                for path in self.cache_dir.glob("search_*.json"):
                    unlink_confined(self.confinement_root, path)
                    count += 1
                return count
        if not self.cache_dir.exists():
            return 0
        count = 0
        for path in self.cache_dir.glob("search_*.json"):
            path.unlink()
            count += 1
        return count
