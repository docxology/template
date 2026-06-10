"""arXiv Atom export API backend."""

from __future__ import annotations

import re
import time
from collections.abc import Callable

import defusedxml.ElementTree as ET
from xml.etree.ElementTree import Element as XMLElement

from infrastructure.search.literature.base import BackendError, SearchBackend
from infrastructure.search.literature.http_client import HttpClient, HttpGetMixin, UrllibHttpClient
from infrastructure.search.literature.models import Paper, SearchQuery


class ArxivBackend(SearchBackend, HttpGetMixin):
    """arXiv export API. Returns Atom XML; we parse it locally."""

    name = "arxiv"
    base_url = "http://export.arxiv.org/api/query"

    _ATOM_NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    #: HTTP statuses arXiv uses for throttling; retried with backoff in
    #: :meth:`fetch_by_id` because batch reference verification reliably
    #: trips the rate limit partway through a bibliography.
    _RETRY_STATUSES = frozenset({429, 503})

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 3,
        retry_base_delay: float = 3.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.base_url = base_url or self.base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._sleep = sleeper

    def search(self, query: SearchQuery) -> list[Paper]:
        params = {
            "search_query": f"all:{query.text}",
            "start": 0,
            "max_results": query.max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        resp = self._http_get(params, label="arXiv")
        if resp.status_code != 200:
            raise BackendError(f"arXiv returned HTTP {resp.status_code}")
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as exc:
            raise BackendError(f"arXiv returned non-XML body: {exc}") from exc

        papers: list[Paper] = []
        for entry in root.findall("atom:entry", self._ATOM_NS):
            paper = self._entry_to_paper(entry)
            if paper is not None and query.matches_year(paper.year):
                papers.append(paper)
        return papers

    def fetch_by_id(self, arxiv_id: str) -> Paper | None:
        """Resolve a single arXiv identifier (e.g. ``"2501.12948"``).

        Used by the reference-verification resolver to confirm a cited arXiv
        preprint exists. Returns ``None`` when arXiv reports no matching entry.
        Raises :class:`BackendError` on transport or parse failure.
        """
        cleaned = arxiv_id.strip()
        if cleaned.lower().startswith("arxiv:"):
            cleaned = cleaned.split(":", 1)[1].strip()
        if not cleaned:
            return None
        resp = self._http_get({"id_list": cleaned, "max_results": 1}, label="arXiv")
        for attempt in range(self.max_retries):
            if resp.status_code not in self._RETRY_STATUSES:
                break
            self._sleep(self.retry_base_delay * (2**attempt))
            resp = self._http_get({"id_list": cleaned, "max_results": 1}, label="arXiv")
        if resp.status_code != 200:
            raise BackendError(f"arXiv returned HTTP {resp.status_code}")
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as exc:
            raise BackendError(f"arXiv returned non-XML body: {exc}") from exc
        for entry in root.findall("atom:entry", self._ATOM_NS):
            paper = self._entry_to_paper(entry)
            if paper is not None:
                return paper
        return None

    def _entry_to_paper(self, entry: XMLElement) -> Paper | None:
        def text(tag: str, ns: str = "atom") -> str | None:
            el = entry.find(f"{ns}:{tag}", self._ATOM_NS)
            return el.text.strip() if (el is not None and el.text) else None

        title = text("title") or ""
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            return None
        summary = text("summary") or ""
        summary = re.sub(r"\s+", " ", summary).strip()
        published = text("published")
        year: int | None = None
        if published:
            try:
                year = int(published[:4])
            except ValueError:
                year = None

        id_text = text("id") or ""
        arxiv_id = id_text.rsplit("/", 1)[-1].split("v")[0]
        url = id_text or None
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

        authors: list[str] = []
        for author in entry.findall("atom:author", self._ATOM_NS):
            name = author.find("atom:name", self._ATOM_NS)
            if name is not None and name.text:
                authors.append(name.text.strip())

        doi_el = entry.find("arxiv:doi", self._ATOM_NS)
        doi = doi_el.text.strip() if (doi_el is not None and doi_el.text) else None

        return Paper(
            id=f"arxiv:{arxiv_id}",
            title=title,
            authors=authors,
            abstract=summary or None,
            year=year,
            doi=doi,
            url=url,
            venue="arXiv",
            venue_type="preprint",
            source=self.name,
            score=0.0,
            pdf_url=pdf_url,
        )


__all__ = ["ArxivBackend"]
