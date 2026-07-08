"""bioRxiv/medRxiv connector — life-sciences preprints.

Queries the bioRxiv/medRxiv API (https://api.biorxiv.org).
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

_BASE_URL = "https://api.biorxiv.org"


class BiorxivConnector:
    """Connector for the bioRxiv and medRxiv preprint servers."""

    name: str = "biorxiv"
    domain: ConnectorDomain = ConnectorDomain.biology
    description: str = "bioRxiv/medRxiv — life-science and medical preprints"
    base_url: str = _BASE_URL

    def __init__(
        self,
        server: str = "biorxiv",
        http_client: ConnectorHttpClient | None = None,
        base_url: str = _BASE_URL,
    ) -> None:
        self.server = server  # "biorxiv" or "medrxiv"
        self._http = http_client or ConnectorHttpClient()
        self.base_url = base_url

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        """Search for results matching a query."""
        opts = options or SearchOptions()
        # bioRxiv's search endpoint does not support free-text via v2; use details
        # endpoint with a date window or fall back to the pubs endpoint.
        year_min = opts.year_min or 2013
        year_max = opts.year_max or 2099
        interval = f"{year_min}-01-01/{year_max}-12-31"
        url = f"{self.base_url}/details/{self.server}/{interval}/0/json"
        try:
            data = self._http.get_json(url)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        items: list[dict[str, Any]] = data.get("collection", []) if isinstance(data, dict) else []
        # Filter by query terms in title/abstract (best-effort, API lacks FTS)
        terms = [t.lower() for t in query.split()]
        filtered: list[dict[str, Any]] = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
            if all(t in text for t in terms):
                filtered.append(item)
            if len(filtered) >= opts.max_results:
                break
        return [self._parse_item(item) for item in filtered]

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        """Fetch a resource by identifier."""
        doi = record_id.removeprefix("biorxiv:")
        url = f"{self.base_url}/details/{self.server}/{doi}/na/json"
        try:
            data = self._http.get_json(url)
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc
        items = data.get("collection", []) if isinstance(data, dict) else []
        return self._parse_item(items[0]) if items else None

    @staticmethod
    def _parse_item(item: dict[str, Any]) -> ConnectorHit:
        doi = item.get("doi", "")
        title = item.get("title") or ""
        authors_raw = item.get("authors", "") or ""
        authors = [a.strip() for a in str(authors_raw).split(";") if a.strip()]
        date = item.get("date", "")
        year: int | None = None
        if date and len(date) >= 4:
            try:
                year = int(date[:4])
            except (ValueError, TypeError):
                pass
        abstract = item.get("abstract") or None
        return ConnectorHit(
            id=f"biorxiv:{doi}" if doi else f"biorxiv:{title[:40]}",
            title=title,
            authors=tuple(authors),
            year=year,
            doi=doi or None,
            url=f"https://www.biorxiv.org/content/{doi}" if doi else None,
            abstract=abstract,
            source="biorxiv",
            score=0.0,
            extra={"category": item.get("category", ""), "server": item.get("server", "biorxiv")},
        )


__all__ = ["BiorxivConnector"]
