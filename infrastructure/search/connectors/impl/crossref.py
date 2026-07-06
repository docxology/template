"""Crossref connector — DOI metadata and works search.

Queries the Crossref REST API (https://api.crossref.org).  Polite pool
access requires a ``mailto`` parameter in every request.
"""

from __future__ import annotations

from typing import Any

from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.types import (
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)

_BASE_URL = "https://api.crossref.org"


class CrossrefConnector:
    """Connector for the Crossref DOI registry and works catalog."""

    name: str = "crossref"
    domain: ConnectorDomain = ConnectorDomain.literature
    description: str = "Crossref — DOI metadata, journal articles, books, and conference papers"
    base_url: str = _BASE_URL

    def __init__(
        self,
        mailto: str = "team@example.org",
        http_client: ConnectorHttpClient | None = None,
        base_url: str = _BASE_URL,
    ) -> None:
        self.mailto = mailto
        self._http = http_client or ConnectorHttpClient()
        self.base_url = base_url

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        opts = options or SearchOptions()
        params: dict[str, str] = {
            "query": query,
            "rows": str(min(opts.max_results, 1000)),
            "mailto": self.mailto,
        }
        filters: list[str] = []
        if opts.year_min:
            filters.append(f"from-pub-date:{opts.year_min}")
        if opts.year_max:
            filters.append(f"until-pub-date:{opts.year_max}")
        if filters:
            params["filter"] = ",".join(filters)

        try:
            data = self._http.get_json(f"{self.base_url}/works", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        items = data.get("message", {}).get("items", []) if isinstance(data, dict) else []
        return [self._parse_item(item) for item in items[: opts.max_results]]

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        doi = record_id.removeprefix("crossref:").removeprefix("doi:")
        url = f"{self.base_url}/works/{doi}"
        try:
            data = self._http.get_json(url)
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc

        item = data.get("message") if isinstance(data, dict) else None
        if not item:
            return None
        return self._parse_item(item)

    @staticmethod
    def _parse_item(item: dict[str, Any]) -> ConnectorHit:
        doi = item.get("DOI", "")
        title_list = item.get("title") or []
        title = title_list[0] if title_list else item.get("subtitle", [""])[0] if item.get("subtitle") else ""
        authors: list[str] = []
        for a in item.get("author") or []:
            if isinstance(a, dict):
                given = a.get("given", "")
                family = a.get("family", "")
                name = f"{given} {family}".strip() if given or family else a.get("name", "")
                if name:
                    authors.append(name)
        date_parts = (item.get("published") or item.get("published-print") or {}).get("date-parts", [[]])
        year: int | None = None
        if date_parts and date_parts[0]:
            try:
                year = int(date_parts[0][0])
            except (TypeError, ValueError):
                pass
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
        score = float(item.get("score", 0.0) or 0.0)
        return ConnectorHit(
            id=f"crossref:{doi}" if doi else f"crossref:{title[:40]}",
            title=title,
            authors=tuple(authors),
            year=year,
            doi=doi or None,
            url=url,
            abstract=None,
            source="crossref",
            score=score,
            extra={"type": item.get("type", "")},
        )


__all__ = ["CrossrefConnector"]
