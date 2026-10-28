"""Crossref REST API backend."""

from __future__ import annotations

import json
import re
from typing import Any

from infrastructure.search.literature.base import BackendError, SearchBackend
from infrastructure.search.literature.http_client import HttpClient, HttpGetMixin, UrllibHttpClient
from infrastructure.search.literature.models import Paper, SearchQuery


def clean_jats(text: str | None) -> str | None:
    """Strip JATS XML tags Crossref sometimes embeds in abstracts."""
    if not text:
        return None
    return re.sub(r"<[^>]+>", "", text).strip() or None


class CrossrefBackend(SearchBackend, HttpGetMixin):
    """Crossref REST API (no auth required)."""

    name = "crossref"
    base_url = "https://api.crossref.org/works"

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        mailto: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.base_url = base_url or self.base_url
        self.mailto = mailto
        self.timeout = timeout

    def search(self, query: SearchQuery) -> list[Paper]:
        """Search for results matching a query."""
        params: dict[str, Any] = {"query": query.text, "rows": query.max_results}
        filters: list[str] = []
        if query.year_min is not None:
            filters.append(f"from-pub-date:{query.year_min}")
        if query.year_max is not None:
            filters.append(f"until-pub-date:{query.year_max}-12-31")
        if filters:
            params["filter"] = ",".join(filters)
        if self.mailto:
            params["mailto"] = self.mailto

        resp = self._http_get(params, label="Crossref")
        if resp.status_code != 200:
            raise BackendError(f"Crossref returned HTTP {resp.status_code}")

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise BackendError(f"Crossref returned non-JSON body: {exc}") from exc

        items = (payload.get("message") or {}).get("items") or []
        return [self._item_to_paper(item) for item in items if item]

    def _item_to_paper(self, item: dict[str, Any]) -> Paper:
        return crossref_item_to_paper(item, source=self.name)


def crossref_item_to_paper(item: dict[str, Any], *, source: str = "crossref") -> Paper:
    """Map a Crossref ``message`` / ``items[*]`` record to a :class:`Paper`.

    Exposed as a module-level function (not just a backend method) so the
    reference-verification resolver can reuse the exact same field mapping when
    it resolves a single work via ``GET /works/{doi}`` — keeping the search and
    verification code paths from drifting.
    """
    title_list = item.get("title") or []
    title = title_list[0] if title_list else item.get("DOI", "Untitled")

    authors_list = item.get("author") or []
    authors: list[str] = []
    for author in authors_list:
        given = author.get("given", "")
        family = author.get("family", "")
        full = f"{given} {family}".strip()
        if full:
            authors.append(full)

    date_parts = (
        (item.get("issued") or {}).get("date-parts")
        or (item.get("published-print") or {}).get("date-parts")
        or (item.get("published-online") or {}).get("date-parts")
        or []
    )
    year = None
    if date_parts and date_parts[0]:
        try:
            year = int(date_parts[0][0])
        except (TypeError, ValueError, IndexError):
            year = None

    venue_list = item.get("container-title") or []
    venue = venue_list[0] if venue_list else None
    kind = (item.get("type") or "").lower()
    venue_type_map = {
        "journal-article": "journal",
        "proceedings-article": "conference",
        "book": "book",
        "book-chapter": "book",
        "monograph": "book",
        "report": "report",
        "dissertation": "thesis",
        "posted-content": "preprint",
    }
    venue_type = venue_type_map.get(kind)

    doi = item.get("DOI")
    return Paper(
        id=f"doi:{doi}" if doi else f"crossref:{item.get('URL') or title}",
        title=title,
        authors=authors,
        abstract=clean_jats(item.get("abstract")),
        year=year,
        doi=doi,
        url=item.get("URL"),
        venue=venue,
        venue_type=venue_type,
        volume=item.get("volume"),
        issue=item.get("issue"),
        pages=item.get("page"),
        publisher=item.get("publisher"),
        isbn=(item.get("ISBN") or [None])[0],
        keywords=list(item.get("subject") or []),
        source=source,
        score=float(item.get("score", 0.0)),
        raw=item,
    )


__all__ = ["CrossrefBackend", "clean_jats", "crossref_item_to_paper"]
