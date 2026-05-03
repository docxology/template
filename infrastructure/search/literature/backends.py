"""Backends for literature search.

Three concrete backends ship in-tree:

* :class:`LocalBackend` — searches a JSON corpus on disk. Used for
  reproducible offline testing and for caching curated reading lists.
* :class:`CrossrefBackend` — hits the public Crossref REST API
  (``https://api.crossref.org``); no auth, generous rate limit.
* :class:`ArxivBackend` — hits the arXiv export API
  (``http://export.arxiv.org/api``); no auth.

A :class:`PaperclipBackend` adapter is provided for sites that have a
Paperclip API key configured; it is OFF by default because Paperclip is a
paid service and we do not want tests reaching out to it.

All HTTP backends accept an injectable ``http_client`` (anything with a
``.get(url, params=..., headers=..., timeout=...) -> Response`` method) so
that tests can use ``pytest-httpserver`` instead of mocks.
"""

from __future__ import annotations

import abc
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.literature.models import Paper, SearchQuery

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# HTTP client protocol — kept minimal so callers can inject `requests`,
# `httpx`, or a thin urllib wrapper. We default to a urllib wrapper so the
# infrastructure module has no required HTTP dependency.
# ---------------------------------------------------------------------------


@dataclass
class HttpResponse:
    """Minimal response object used by HTTP backends."""

    status_code: int
    text: str
    url: str

    def json(self) -> Any:
        return json.loads(self.text)


class HttpClient(Protocol):
    """Structural type for an HTTP client used by backends."""

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> HttpResponse: ...  # pragma: no cover

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: bytes | str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse: ...  # pragma: no cover


class UrllibHttpClient:
    """Tiny stdlib HTTP client. Adequate for read-only API calls in tests."""

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> HttpResponse:
        if params:
            qs = urllib.parse.urlencode(params, doseq=True)
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{qs}"
        req = urllib.request.Request(url, headers=dict(headers or {}))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - search API
                charset = resp.headers.get_content_charset() or "utf-8"
                body = resp.read().decode(charset, errors="replace")
                return HttpResponse(status_code=resp.status, text=body, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover
                pass
            return HttpResponse(status_code=exc.code, text=body, url=url)
        except urllib.error.URLError as exc:
            raise BackendError(f"HTTP error fetching {url}: {exc.reason}") from exc

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: bytes | str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        body: bytes
        if json is not None:
            import json as _json

            body = _json.dumps(json).encode("utf-8")
            hdrs = dict(headers or {})
            hdrs.setdefault("Content-Type", "application/json")
        elif isinstance(data, str):
            body = data.encode("utf-8")
            hdrs = dict(headers or {})
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)
            hdrs = dict(headers or {})
        else:
            body = b""
            hdrs = dict(headers or {})

        req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - search API
                charset = resp.headers.get_content_charset() or "utf-8"
                resp_body = resp.read().decode(charset, errors="replace")
                return HttpResponse(status_code=resp.status, text=resp_body, url=resp.geturl())
        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")
            except (OSError, AttributeError):  # pragma: no cover
                pass
            return HttpResponse(status_code=exc.code, text=err_body, url=url)
        except urllib.error.URLError as exc:
            raise BackendError(f"HTTP error posting to {url}: {exc.reason}") from exc


class BackendError(RuntimeError):
    """Raised by a backend when the request itself fails (network, parse)."""


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class SearchBackend(abc.ABC):
    """Abstract base class for literature-search backends."""

    name: str = "abstract"

    @abc.abstractmethod
    def search(self, query: SearchQuery) -> list[Paper]:
        """Run *query* against the backend and return a list of papers.

        Implementations must:

        * Honour ``query.max_results``.
        * Apply ``query.year_min`` / ``query.year_max`` filters (the
          aggregator re-applies them, but doing it here cuts useless I/O).
        * Stamp ``Paper.source = self.name`` on every returned record.
        * Return an empty list rather than raising when no results match.
        * Raise :class:`BackendError` on transport / parse failures so the
          aggregator can record the error per source.
        """


# ---------------------------------------------------------------------------
# Local backend
# ---------------------------------------------------------------------------


class LocalBackend(SearchBackend):
    """Search a JSON corpus on disk.

    The JSON file may be either a list of paper dicts or
    ``{"papers": [...]}``. Matching is a case-insensitive substring search
    over the title, abstract, and keyword fields, ranked by hit count.
    """

    name = "local"

    def __init__(self, corpus_path: Path | str) -> None:
        self.corpus_path = Path(corpus_path)
        self._corpus: list[Paper] | None = None

    def _load(self) -> list[Paper]:
        if self._corpus is not None:
            return self._corpus
        raw = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        records = raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw
        if not isinstance(records, list):
            raise BackendError(f"LocalBackend corpus {self.corpus_path} must be a list or {{'papers': [...]}}")
        self._corpus = [Paper.from_dict(r) for r in records]
        return self._corpus

    def search(self, query: SearchQuery) -> list[Paper]:
        try:
            corpus = self._load()
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendError(f"Cannot load corpus {self.corpus_path}: {exc}") from exc
        terms = [t.lower() for t in re.split(r"\s+", query.text.strip()) if t]
        if not terms:
            return []
        scored: list[tuple[int, Paper]] = []
        for paper in corpus:
            if not query.matches_year(paper.year):
                continue
            haystack = " ".join(
                filter(
                    None,
                    [
                        paper.title or "",
                        paper.abstract or "",
                        " ".join(paper.keywords or []),
                        " ".join(paper.authors or []),
                    ],
                )
            ).lower()
            hits = sum(1 for term in terms if term in haystack)
            if hits == 0:
                continue
            paper_copy = Paper.from_dict({**paper.to_dict(), "source": self.name})
            paper_copy.score = hits / max(1, len(terms))
            scored.append((hits, paper_copy))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [p for _, p in scored[: query.max_results]]


# ---------------------------------------------------------------------------
# Crossref backend
# ---------------------------------------------------------------------------


class CrossrefBackend(SearchBackend):
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
        try:
            resp = self.http.get(self.base_url, params=params, timeout=self.timeout)
        except BackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise BackendError(f"Crossref request failed: {exc}") from exc

        if resp.status_code != 200:
            raise BackendError(f"Crossref returned HTTP {resp.status_code}")

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise BackendError(f"Crossref returned non-JSON body: {exc}") from exc

        items = (payload.get("message") or {}).get("items") or []
        return [self._item_to_paper(item) for item in items if item]

    def _item_to_paper(self, item: dict[str, Any]) -> Paper:
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
            abstract=_clean_jats(item.get("abstract")),
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
            source=self.name,
            score=float(item.get("score", 0.0)),
            raw=item,
        )


def _clean_jats(text: str | None) -> str | None:
    """Strip JATS XML tags Crossref sometimes embeds in abstracts."""
    if not text:
        return None
    return re.sub(r"<[^>]+>", "", text).strip() or None


# ---------------------------------------------------------------------------
# arXiv backend
# ---------------------------------------------------------------------------


class ArxivBackend(SearchBackend):
    """arXiv export API. Returns Atom XML; we parse it locally."""

    name = "arxiv"
    base_url = "http://export.arxiv.org/api/query"

    _ATOM_NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.base_url = base_url or self.base_url
        self.timeout = timeout

    def search(self, query: SearchQuery) -> list[Paper]:
        params = {
            "search_query": f"all:{query.text}",
            "start": 0,
            "max_results": query.max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            resp = self.http.get(self.base_url, params=params, timeout=self.timeout)
        except BackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise BackendError(f"arXiv request failed: {exc}") from exc
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

    def _entry_to_paper(self, entry: ET.Element) -> Paper | None:
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

        # ID has the form "http://arxiv.org/abs/2501.12948v1".
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


# ---------------------------------------------------------------------------
# Paperclip backend (opt-in; needs API key)
# ---------------------------------------------------------------------------


class PaperclipBackend(SearchBackend):
    """Paperclip (paperclip.gxl.ai) HTTP backend.

    Talks to the Paperclip service over MCP-style JSON-RPC at
    ``https://paperclip.gxl.ai/mcp`` using a ``tools/call`` invocation
    with the ``paperclip`` tool. Authentication is via an ``X-API-Key``
    header. Requires an API key (passed as ``api_key`` or, for callers,
    via the ``PAPERCLIP_API_KEY`` environment variable).

    The service returns either a structured ``result.structuredContent.papers``
    list (newer responses) or a CLI-style text result inside
    ``result.content[].text`` (older responses). Both shapes are parsed
    into our :class:`Paper` schema.

    Endpoint history: an earlier ``/papers`` route is now the HTML web
    app (it returns 200 OK serving HTML on GET, and 405 on POST). The
    JSON-RPC endpoint moved to ``/mcp``. Override ``base_url`` if the
    service migrates again.
    """

    name = "paperclip"
    base_url = "https://paperclip.gxl.ai/mcp"
    sdk_user_agent = "gxl-paperclip/0.3.0"

    def __init__(
        self,
        *,
        api_key: str,
        http_client: HttpClient | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("PaperclipBackend requires an api_key")
        self.api_key = api_key
        self.http = http_client or UrllibHttpClient()
        self.base_url = base_url or self.base_url
        self.timeout = timeout
        self._call_id = 0

    def _build_command(self, query: SearchQuery) -> str:
        # Mirrors the SDK's argv-flavoured command construction.
        import shlex

        parts = ["search", shlex.quote(query.text)]
        if query.max_results:
            parts += ["-n", str(query.max_results)]
        if query.year_min is not None:
            parts += ["--since", str(query.year_min)]
        return " ".join(parts)

    def search(self, query: SearchQuery) -> list[Paper]:
        self._call_id += 1
        command = self._build_command(query)
        payload = {
            "jsonrpc": "2.0",
            "id": self._call_id,
            "method": "tools/call",
            "params": {
                "name": "paperclip",
                "arguments": {
                    "command": command,
                    "description": command[:80],
                    "skip_truncation": True,
                },
            },
        }
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": self.sdk_user_agent,
            "Accept": "application/json, text/event-stream",
        }
        try:
            resp = self.http.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except BackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise BackendError(f"Paperclip request failed: {exc}") from exc

        if resp.status_code != 200:
            raise BackendError(f"Paperclip returned HTTP {resp.status_code} (body[:200]: {resp.text[:200]!r})")
        try:
            envelope = resp.json()
        except json.JSONDecodeError as exc:
            raise BackendError(f"Paperclip returned non-JSON body: {exc}") from exc

        if isinstance(envelope, dict) and "error" in envelope:
            err = envelope["error"]
            msg = err.get("message", "Unknown MCP error") if isinstance(err, dict) else str(err)
            raise BackendError(f"Paperclip MCP error: {msg}")

        return self._extract_papers(envelope)

    def _extract_papers(self, envelope: Any) -> list[Paper]:
        """Pull a list of Paper records out of the MCP response envelope."""
        # Newer responses: {"result": {"structuredContent": {"papers": [...]}}}
        # Older responses: {"result": {"content": [{"type":"text","text": "..."}]}}
        # Bare list: just a list of paper dicts.
        if isinstance(envelope, list):
            return self._records_to_papers(envelope)

        if not isinstance(envelope, dict):
            raise BackendError("Paperclip returned an unexpected payload shape")

        result = envelope.get("result")
        if isinstance(result, dict):
            sc = result.get("structuredContent")
            if isinstance(sc, dict):
                for key in ("papers", "results", "items"):
                    if isinstance(sc.get(key), list):
                        return self._records_to_papers(sc[key])
            for key in ("papers", "results", "items"):
                if isinstance(result.get(key), list):
                    return self._records_to_papers(result[key])
            content = result.get("content")
            if isinstance(content, list):
                return self._papers_from_text_content(content)
        # Top-level fallbacks
        for key in ("papers", "results", "items"):
            if isinstance(envelope.get(key), list):
                return self._records_to_papers(envelope[key])
        return []

    def _records_to_papers(self, records: Iterable[dict[str, Any]]) -> list[Paper]:
        out: list[Paper] = []
        for record in records or []:
            if not isinstance(record, dict):
                continue
            try:
                paper = Paper.from_dict({**record, "source": self.name})
                out.append(paper)
            except (TypeError, ValueError) as exc:
                logger.debug("Skipping malformed Paperclip record: %s", exc)
                continue
        return out

    def _papers_from_text_content(self, content: list[dict[str, Any]]) -> list[Paper]:
        """Best-effort parse of the textual CLI-style output.

        The live Paperclip MCP service emits records like::

              1. <Title>
                 <Authors, comma-separated, * marks corresponding>
                 <internal_id> · <venue> · <YYYY-MM-DD>
                 https://doi.org/<doi>
                 "<abstract>"

        We extract title, authors, internal id, venue, year, DOI, and
        abstract. Older CLI responses that only contain titles still
        produce a record with the title set; missing fields stay
        ``None``.
        """
        text = "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
        if not text.strip():
            return []

        # Split into one block per numbered entry. The leading guard
        # group keeps the index/title line on the matched block.
        block_re = re.compile(r"(?=^[ \t]*\d+\.[ \t]+)", re.MULTILINE)
        blocks = [b for b in block_re.split(text) if re.match(r"^\s*\d+\.", b)]
        # Pre-compiled patterns reused below.
        title_re = re.compile(r"^\s*\d+\.[ \t]+(.+?)\s*$", re.MULTILINE)
        id_token_re = re.compile(
            r"\b((?:pmc|arxiv|doi|biorxiv|medrxiv|pmid):[A-Za-z0-9._/+-]+)\b",
            re.IGNORECASE,
        )
        meta_row_re = re.compile(
            r"^\s+([A-Za-z0-9_.]+)\s*·\s*([^·\n]+?)\s*·\s*(\d{4})(?:-\d{2}-\d{2})?\s*$",
            re.MULTILINE,
        )
        doi_url_re = re.compile(r"https?://(?:dx\.)?doi\.org/(\S+)", re.IGNORECASE)
        # Authors are the first indented non-numbered line after the title,
        # before the metadata row. They use commas as separators and may
        # contain ``*`` markers for corresponding authors (which we strip).
        out: list[Paper] = []
        for idx, block in enumerate(blocks, start=1):
            title_match = title_re.search(block)
            if not title_match:
                continue
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
            tail = block[title_match.end() :]

            # Authors: the first indented line that is NOT a metadata row
            # (no ` · ` triple) and NOT a URL or quoted abstract.
            authors: list[str] = []
            for line in tail.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("http") or stripped.startswith('"'):
                    break
                if " · " in stripped:
                    break
                # Likely an authors line — split on commas, strip ``*``.
                authors = [re.sub(r"\s*\*+\s*$", "", a).strip() for a in stripped.split(",") if a.strip()]
                break

            meta = meta_row_re.search(tail)
            internal_id = meta.group(1) if meta else None
            venue = meta.group(2).strip() if meta else None
            year: int | None = None
            if meta:
                try:
                    year = int(meta.group(3))
                except ValueError:
                    year = None

            doi_match = doi_url_re.search(tail)
            doi = doi_match.group(1).rstrip(").,;") if doi_match else None

            id_token_match = id_token_re.search(tail)
            if id_token_match:
                paper_id = id_token_match.group(1).lower()
            elif internal_id and internal_id.startswith(("arx_", "arxiv_")):
                # Paperclip exposes arXiv IDs as ``arx_<arxiv_id>`` —
                # canonicalise to the standard ``arxiv:<id>`` shape.
                arxiv_id = internal_id.split("_", 1)[1]
                paper_id = f"arxiv:{arxiv_id}"
            elif internal_id and internal_id.startswith("pmc_"):
                paper_id = f"pmc:{internal_id.split('_', 1)[1]}"
            elif internal_id and internal_id.startswith("pmid_"):
                paper_id = f"pmid:{internal_id.split('_', 1)[1]}"
            elif doi:
                paper_id = f"doi:{doi}"
            elif internal_id:
                paper_id = f"paperclip:{internal_id}"
            else:
                paper_id = f"paperclip:result_{idx}"

            # Abstract: the first quoted block (may span multiple lines).
            abstract_match = re.search(r'"([^"]+)"', tail, re.DOTALL)
            abstract = re.sub(r"\s+", " ", abstract_match.group(1)).strip() if abstract_match else None

            url = f"https://doi.org/{doi}" if doi else None
            venue_type = None
            if venue:
                v_lower = venue.lower()
                if "arxiv" in v_lower:
                    venue_type = "preprint"
                elif "biorxiv" in v_lower or "medrxiv" in v_lower:
                    venue_type = "preprint"
                elif "pubmed" in v_lower or "pmc" in v_lower:
                    venue_type = "journal"

            try:
                out.append(
                    Paper(
                        id=paper_id,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        year=year,
                        doi=doi,
                        url=url,
                        venue=venue,
                        venue_type=venue_type,
                        source=self.name,
                    )
                )
            except (TypeError, ValueError) as exc:  # pragma: no cover
                logger.debug("Skipping unparsable Paperclip text record: %s", exc)
        return out
