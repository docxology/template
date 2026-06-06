"""Persistent SQLite cache for reference-resolution lookups.

Resolving a DOI/arXiv id against Crossref, OpenAlex, or arXiv is a slow network
round-trip whose answer is effectively immutable (a published work does not
un-publish). Caching results lets the verification gate run offline in CI after
a single online pass, and keeps repeated local runs fast.

The cache stores *negative* results too (a looked-up identifier that no index
could resolve), because "we checked and it does not exist" is exactly the
signal the fabricated-citation gate needs — and re-checking it every run would
be both slow and non-deterministic.

Distilled from the verification-cache concept in Academic Research Skills
(CC-BY-NC-4.0); implementation is original and Apache-2.0. Unlike the JSON
``SearchCache`` used for whole-query results, this is a single SQLite file
keyed by individual identifier, which suits the one-lookup-per-reference access
pattern.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from infrastructure.search.literature.models import Paper

__all__ = ["CACHE_MISS", "CacheMiss", "DEFAULT_TTL_SECONDS", "ResolutionCache"]

# 90 days — a published reference's metadata is stable, so a long TTL is safe.
DEFAULT_TTL_SECONDS = 90 * 24 * 60 * 60

_SCHEMA = """
CREATE TABLE IF NOT EXISTS resolutions (
    key         TEXT PRIMARY KEY,
    found       INTEGER NOT NULL,
    paper_json  TEXT,
    resolved_via TEXT,
    cached_at   REAL NOT NULL
)
"""


class CacheMiss:
    """Sentinel type distinguishing a cache miss from a cached negative result."""


CACHE_MISS = CacheMiss()


class ResolutionCache:
    """SQLite-backed cache mapping an identifier to a resolved :class:`Paper`.

    A stored value is one of:

    * a :class:`Paper` — the identifier resolved to this record;
    * ``None`` — the identifier was looked up and *not* found (negative cache);
    * :data:`CACHE_MISS` — never looked up (or expired).
    """

    def __init__(self, db_path: Path | str, *, ttl_seconds: int | None = DEFAULT_TTL_SECONDS) -> None:
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(_SCHEMA)
        return conn

    def get(self, key: str) -> Paper | None | CacheMiss:
        """Return cached :class:`Paper`, ``None`` (negative), or ``CACHE_MISS``."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT found, paper_json, resolved_via, cached_at FROM resolutions WHERE key = ?",
                (key,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return CACHE_MISS
        found, paper_json, resolved_via, cached_at = row
        if self.ttl_seconds is not None and (time.time() - float(cached_at)) > self.ttl_seconds:
            return CACHE_MISS
        if not found:
            return None
        try:
            data = json.loads(paper_json)
        except (TypeError, json.JSONDecodeError):
            return CACHE_MISS
        paper = Paper.from_dict(data)
        if resolved_via and not paper.source:
            paper.source = resolved_via
        return paper

    def put(self, key: str, paper: Paper | None, *, resolved_via: str | None = None) -> None:
        """Store a positive (``paper``) or negative (``None``) resolution."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO resolutions (key, found, paper_json, resolved_via, cached_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    key,
                    1 if paper is not None else 0,
                    json.dumps(paper.to_dict(), ensure_ascii=False) if paper is not None else None,
                    resolved_via or (paper.source if paper is not None else None),
                    time.time(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def clear(self) -> int:
        """Delete all cached resolutions. Returns the number of rows removed."""
        if not self.db_path.exists():
            return 0
        conn = self._connect()
        try:
            cur = conn.execute("SELECT COUNT(*) FROM resolutions")
            count = int(cur.fetchone()[0])
            conn.execute("DELETE FROM resolutions")
            conn.commit()
        finally:
            conn.close()
        return count
