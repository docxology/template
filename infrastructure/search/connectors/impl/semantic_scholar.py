"""Semantic Scholar connector — AI-powered paper search and citation graph.

Queries the Semantic Scholar Graph API (https://api.semanticscholar.org/graph/v1).
Authentication is optional; unauthenticated requests are subject to rate limits.
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

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "paperId,title,authors,year,externalIds,abstract,url,venue,citationCount"


class SemanticScholarConnector:
    """Connector for the Semantic Scholar academic graph."""

    name: str = "semantic_scholar"
    domain: ConnectorDomain = ConnectorDomain.literature
    description: str = "Semantic Scholar — AI-powered scientific paper search with citation graph"
    base_url: str = _BASE_URL

    def __init__(
        self,
        api_key: str | None = None,
        http_client: ConnectorHttpClient | None = None,
        base_url: str = _BASE_URL,
    ) -> None:
        self._api_key = api_key
        self._http = http_client or ConnectorHttpClient()
        self.base_url = base_url

    def _headers(self) -> dict[str, str]:
        if self._api_key:
            return {"x-api-key": self._api_key}
        return {}

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        opts = options or SearchOptions()
        params: dict[str, str] = {
            "query": query,
            "limit": str(min(opts.max_results, 100)),
            "fields": _FIELDS,
        }
        if opts.year_min and opts.year_max:
            params["year"] = f"{opts.year_min}-{opts.year_max}"
        elif opts.year_min:
            params["year"] = f"{opts.year_min}-"
        elif opts.year_max:
            params["year"] = f"-{opts.year_max}"

        try:
            data = self._http.get_json(
                f"{self.base_url}/paper/search",
                params,
                self._headers(),
            )
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        items = data.get("data", []) if isinstance(data, dict) else []
        return [self._parse_paper(item, rank) for rank, item in enumerate(items[: opts.max_results])]

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        ss_id = record_id.removeprefix("semantic_scholar:")
        params = {"fields": _FIELDS}
        try:
            data = self._http.get_json(
                f"{self.base_url}/paper/{ss_id}",
                params,
                self._headers(),
            )
        except ConnectorHttpError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise ConnectorError(str(exc)) from exc
        return self._parse_paper(data, 0)

    @staticmethod
    def _parse_paper(item: dict[str, Any], rank: int) -> ConnectorHit:
        paper_id = item.get("paperId", "")
        title = item.get("title") or ""
        authors = [a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)]
        year = item.get("year")
        ext = item.get("externalIds") or {}
        doi = ext.get("DOI")
        url = item.get("url") or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None)
        abstract = item.get("abstract")
        total = max(1, 100 - rank)
        score = min(1.0, float(item.get("citationCount", 0) or 0) / 10000.0 + total / 100.0)
        return ConnectorHit(
            id=f"semantic_scholar:{paper_id}",
            title=title,
            authors=tuple(a for a in authors if a),
            year=int(year) if year else None,
            doi=doi or None,
            url=url,
            abstract=abstract,
            source="semantic_scholar",
            score=min(1.0, score),
            extra={"paper_id": paper_id, "external_ids": ext},
        )


__all__ = ["SemanticScholarConnector"]
