"""Europe PMC connector — life-sciences literature and data.

Queries the Europe PMC REST API (https://europepmc.org/RestfulWebService).
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

_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"


class EuropePMCConnector:
    """Connector for the Europe PubMed Central literature database."""

    name: str = "europepmc"
    domain: ConnectorDomain = ConnectorDomain.biology
    description: str = "Europe PMC — life-sciences literature from PubMed Central and partner repositories"
    base_url: str = _BASE_URL

    def __init__(
        self,
        http_client: ConnectorHttpClient | None = None,
        base_url: str = _BASE_URL,
    ) -> None:
        self._http = http_client or ConnectorHttpClient()
        self.base_url = base_url

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        opts = options or SearchOptions()
        q = query
        if opts.year_min:
            q += f" AND PUB_YEAR:[{opts.year_min} TO *]"
        if opts.year_max:
            q += f" AND PUB_YEAR:[* TO {opts.year_max}]"
        params: dict[str, str] = {
            "query": q,
            "pageSize": str(min(opts.max_results, 1000)),
            "format": "json",
            "resultType": "core",
        }
        try:
            data = self._http.get_json(f"{self.base_url}/search", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        results = data.get("resultList", {}).get("result", []) if isinstance(data, dict) else []
        return [self._parse_result(item) for item in results[: opts.max_results]]

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        pmid = record_id.removeprefix("europepmc:")
        params = {"query": f"EXT_ID:{pmid}", "format": "json", "resultType": "core"}
        try:
            data = self._http.get_json(f"{self.base_url}/search", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc
        results = data.get("resultList", {}).get("result", []) if isinstance(data, dict) else []
        return self._parse_result(results[0]) if results else None

    @staticmethod
    def _parse_result(item: dict[str, Any]) -> ConnectorHit:
        pmid = item.get("pmid") or item.get("id", "")
        title = item.get("title") or ""
        authors = [
            a.get("fullName", "") or f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
            for a in (item.get("authorList") or {}).get("author", [])
            if isinstance(a, dict)
        ]
        year_raw = item.get("pubYear")
        year: int | None = None
        if year_raw:
            try:
                year = int(year_raw)
            except (TypeError, ValueError):
                pass
        doi = item.get("doi") or None
        url_list = item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])
        url = url_list[0].get("url") if url_list else None
        abstract = item.get("abstractText") or None
        return ConnectorHit(
            id=f"europepmc:{pmid}",
            title=title.rstrip("."),
            authors=tuple(a for a in authors if a),
            year=year,
            doi=doi,
            url=url,
            abstract=abstract,
            source="europepmc",
            score=0.0,
            extra={"pmcid": item.get("pmcid"), "source_db": item.get("source")},
        )


__all__ = ["EuropePMCConnector"]
