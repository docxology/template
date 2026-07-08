"""OpenAlex connector — open catalog of scholarly works.

OpenAlex (https://openalex.org) is a fully open index of scholarly works,
authors, institutions, and concepts.  The API is free without authentication;
polite use requires a ``mailto`` parameter.
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

_BASE_URL = "https://api.openalex.org"


class OpenAlexConnector:
    """Connector for the OpenAlex scholarly-works catalog."""

    name: str = "openalex"
    domain: ConnectorDomain = ConnectorDomain.literature
    description: str = "OpenAlex — open index of scholarly works, authors, and concepts"
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
        """Search for results matching a query."""
        opts = options or SearchOptions()
        params: dict[str, str] = {
            "search": query,
            "per-page": str(min(opts.max_results, 200)),
            "mailto": self.mailto,
        }
        filters: list[str] = []
        if opts.year_min:
            filters.append(f"publication_year:>{opts.year_min - 1}")
        if opts.year_max:
            filters.append(f"publication_year:<{opts.year_max + 1}")
        if filters:
            params["filter"] = ",".join(filters)

        try:
            data = self._http.get_json(f"{self.base_url}/works", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        results = data.get("results", []) if isinstance(data, dict) else []
        hits: list[ConnectorHit] = []
        for item in results[: opts.max_results]:
            hits.append(self._parse_work(item))
        return hits

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        """Fetch a resource by identifier."""
        oa_id = record_id.removeprefix("openalex:")
        try:
            data = self._http.get_json(f"{self.base_url}/works/{oa_id}")
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc
        return self._parse_work(data)

    @staticmethod
    def _parse_work(item: dict[str, Any]) -> ConnectorHit:
        oa_id = item.get("id", "")
        short_id = oa_id.rsplit("/", 1)[-1] if oa_id else ""
        title = item.get("title") or item.get("display_name") or ""
        authors = [
            a.get("author", {}).get("display_name", "") for a in item.get("authorships", []) if isinstance(a, dict)
        ]
        year = item.get("publication_year")
        doi_raw = item.get("doi") or ""
        doi = doi_raw.removeprefix("https://doi.org/") if doi_raw else None
        url = item.get("primary_location", {}).get("landing_page_url") or item.get("id") or None
        abstract_inv = item.get("abstract_inverted_index")
        abstract = _reconstruct_abstract(abstract_inv) if abstract_inv else None
        score = item.get("relevance_score") or 0.0
        return ConnectorHit(
            id=f"openalex:{short_id}",
            title=title,
            authors=tuple(a for a in authors if a),
            year=int(year) if year else None,
            doi=doi,
            url=url,
            abstract=abstract,
            source="openalex",
            score=float(score),
            extra={"openalex_id": oa_id},
        )


def _reconstruct_abstract(inverted_index: dict[str, list[int]]) -> str:
    """Reconstruct an abstract from OpenAlex's inverted index format."""
    if not isinstance(inverted_index, dict):
        return ""
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


__all__ = ["OpenAlexConnector"]
