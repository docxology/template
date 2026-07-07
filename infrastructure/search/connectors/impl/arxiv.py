"""arXiv connector — preprint server for physics, mathematics, and CS.

Queries the arXiv Atom/OpenSearch API
(https://export.arxiv.org/api/query) without authentication.
"""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.types import (
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)

_BASE_URL = "https://export.arxiv.org/api"
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivConnector:
    """Connector for the arXiv preprint repository."""

    name: str = "arxiv"
    domain: ConnectorDomain = ConnectorDomain.physics
    description: str = "arXiv — open-access preprints in physics, math, CS, quantitative biology"
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
        params: dict[str, str] = {
            "search_query": f"all:{query}",
            "start": "0",
            "max_results": str(min(opts.max_results, 100)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            text = self._http.get_text(f"{self.base_url}/query", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        return self._parse_feed(text, opts)

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        arxiv_id = record_id.removeprefix("arxiv:")
        params = {"id_list": arxiv_id}
        try:
            text = self._http.get_text(f"{self.base_url}/query", params)
        except ConnectorHttpError as exc:
            raise ConnectorError(str(exc)) from exc

        hits = self._parse_feed(text, SearchOptions(max_results=1))
        return hits[0] if hits else None

    def _parse_feed(self, text: str, opts: SearchOptions) -> list[ConnectorHit]:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise ConnectorError(f"Invalid arXiv Atom feed: {exc}") from exc

        hits: list[ConnectorHit] = []
        for entry in root.findall("atom:entry", _NS):
            hit = self._parse_entry(entry)
            if hit is None:
                continue
            if opts.year_min and hit.year and hit.year < opts.year_min:
                continue
            if opts.year_max and hit.year and hit.year > opts.year_max:
                continue
            hits.append(hit)
            if len(hits) >= opts.max_results:
                break
        return hits

    @staticmethod
    def _parse_entry(entry: Element) -> ConnectorHit | None:
        id_elem = entry.find("atom:id", _NS)
        if id_elem is None or not id_elem.text:
            return None
        raw_id = id_elem.text.strip()
        arxiv_id = raw_id.rsplit("/", 1)[-1]

        title_elem = entry.find("atom:title", _NS)
        title = (title_elem.text or "").strip().replace("\n", " ") if title_elem is not None else ""

        authors = []
        for author in entry.findall("atom:author", _NS):
            name = author.find("atom:name", _NS)
            if name is not None and name.text:
                authors.append(name.text.strip())

        published = entry.find("atom:published", _NS)
        year: int | None = None
        if published is not None and published.text:
            m = re.match(r"(\d{4})", published.text.strip())
            if m:
                year = int(m.group(1))

        summary = entry.find("atom:summary", _NS)
        abstract = (summary.text or "").strip().replace("\n", " ") if summary is not None else None

        doi_elem = entry.find("arxiv:doi", _NS)
        doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

        return ConnectorHit(
            id=f"arxiv:{arxiv_id}",
            title=title,
            authors=tuple(authors),
            year=year,
            doi=doi,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            abstract=abstract,
            source="arxiv",
            score=0.0,
        )


__all__ = ["ArxivConnector"]
