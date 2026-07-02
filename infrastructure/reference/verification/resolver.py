"""Resolve a bibliographic identifier against external indices.

The resolver answers one question per call: *does this DOI / arXiv id / title
correspond to a real record in Crossref, OpenAlex, or arXiv, and if so what is
its canonical metadata?* It is deliberately offline-first: with ``allow_network``
false (the default in CI and tests) it consults only the persistent
:class:`ResolutionCache`, returning an explicit "unchecked" result on a miss so
nothing silently passes.

Cross-index resolution (Crossref then OpenAlex for DOIs) mirrors the
"contamination triangulation" idea from Academic Research Skills (CC-BY-NC-4.0):
agreement across independent indices raises confidence that a record is real.
Implementation is original and Apache-2.0; the Crossref/arXiv field mapping is
reused from :mod:`infrastructure.search.literature` so the two paths cannot
drift.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any

from infrastructure.reference.verification.cache import CacheMiss, ResolutionCache
from infrastructure.search.literature.arxiv_backend import ArxivBackend
from infrastructure.search.literature.base import BackendError
from infrastructure.search.literature.crossref_backend import CrossrefBackend, crossref_item_to_paper
from infrastructure.search.literature.http_client import HttpClient, UrllibHttpClient
from infrastructure.search.literature.models import Paper, SearchQuery

__all__ = ["Resolution", "ReferenceResolver", "normalize_doi"]


_DOI_PREFIX_RE = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:)", re.IGNORECASE)


def normalize_doi(doi: str) -> str:
    """Lower-case and strip ``doi:`` / ``(http|https)://(dx.)?doi.org/`` prefixes."""
    return _DOI_PREFIX_RE.sub("", doi.strip()).strip().lower()


@dataclass
class Resolution:
    """The outcome of resolving one identifier.

    Attributes:
        paper: The resolved record, or ``None`` when an index was consulted and
            returned nothing.
        via: Index that produced the record (``crossref`` / ``openalex`` /
            ``arxiv`` / ``cache``), or ``None`` when unresolved.
        checked: ``True`` if the identifier was actually looked up (online or via
            cache); ``False`` only when offline *and* absent from cache.
        from_cache: ``True`` if the answer came from the persistent cache.
    """

    paper: Paper | None
    via: str | None
    checked: bool
    from_cache: bool


class ReferenceResolver:
    """Resolve DOIs / arXiv ids / titles against Crossref, OpenAlex, and arXiv."""

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        cache: ResolutionCache | None = None,
        allow_network: bool = False,
        crossref_base_url: str = "https://api.crossref.org/works",
        openalex_base_url: str = "https://api.openalex.org/works",
        arxiv_base_url: str = "http://export.arxiv.org/api/query",
        mailto: str | None = None,
        timeout: float = 15.0,
        title_match_floor: float = 0.82,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.cache = cache
        self.allow_network = allow_network
        self.crossref_base_url = crossref_base_url.rstrip("/")
        self.openalex_base_url = openalex_base_url.rstrip("/")
        self.arxiv_base_url = arxiv_base_url
        self.mailto = mailto
        self.timeout = timeout
        self.title_match_floor = title_match_floor

    # -- public API ---------------------------------------------------------

    def resolve(
        self,
        *,
        doi: str | None = None,
        arxiv_id: str | None = None,
        title: str | None = None,
    ) -> Resolution:
        """Resolve by DOI (preferred), then arXiv id, then title search."""
        key = self._cache_key(doi=doi, arxiv_id=arxiv_id, title=title)
        if key is None:
            return Resolution(paper=None, via=None, checked=False, from_cache=False)

        if self.cache is not None:
            cached = self.cache.get(key)
            if not isinstance(cached, CacheMiss) and _cache_payload_consistent(key, cached):
                paper = cached  # Paper or None (negative cache)
                return Resolution(
                    paper=paper,
                    via=(paper.source if isinstance(paper, Paper) and paper.source else "cache"),
                    checked=True,
                    from_cache=True,
                )

        if not self.allow_network:
            return Resolution(paper=None, via=None, checked=False, from_cache=False)

        paper, via, definitive = self._resolve_online(doi=doi, arxiv_id=arxiv_id, title=title)
        if not definitive:
            # Transport / parse failure (5xx, network, malformed body). This is
            # NOT a "does not exist" answer — never cache it, never let it pass
            # as checked, so the verifier reports `unchecked` not `fabricated`.
            return Resolution(paper=None, via=None, checked=False, from_cache=False)
        if self.cache is not None:
            self.cache.put(key, paper, resolved_via=via)
        return Resolution(paper=paper, via=via, checked=True, from_cache=False)

    # -- network resolution -------------------------------------------------

    def _resolve_online(
        self,
        *,
        doi: str | None,
        arxiv_id: str | None,
        title: str | None,
    ) -> tuple[Paper | None, str | None, bool]:
        """Return ``(paper, via, definitive)``.

        ``definitive`` is ``True`` when an index gave a real answer — a found
        record *or* a genuine "no such record" (HTTP 404 / empty result set).
        It is ``False`` on any transport/parse failure (5xx, network down,
        malformed body), which must NOT be cached as a negative result.
        """
        if doi:
            paper, cr_definitive = self._crossref_by_doi(doi)
            if paper is not None:
                return paper, "crossref", True
            oa_paper, oa_definitive = self._openalex_by_doi(doi)
            if oa_paper is not None:
                return oa_paper, "openalex", True
            # Genuinely-not-found only if BOTH indices answered definitively.
            return None, None, cr_definitive and oa_definitive
        if arxiv_id:
            paper, definitive = self._arxiv_by_id(arxiv_id)
            return (paper, "arxiv" if paper is not None else None, definitive)
        if title:
            paper, definitive = self._crossref_by_title(title)
            return (paper, "crossref" if paper is not None else None, definitive)
        return None, None, True

    def _crossref_by_doi(self, doi: str) -> tuple[Paper | None, bool]:
        norm = normalize_doi(doi)
        url = f"{self.crossref_base_url}/{urllib.parse.quote(norm, safe='/')}"
        params = {"mailto": self.mailto} if self.mailto else None
        try:
            resp = self.http.get(url, params=params, timeout=self.timeout)
        except BackendError:
            return None, False
        if resp.status_code == 404:
            return None, True  # definitive: no such DOI
        if resp.status_code != 200:
            return None, False  # transient (5xx, rate limit, ...)
        try:
            message = resp.json().get("message")
        except (json.JSONDecodeError, AttributeError):
            return None, False
        if not isinstance(message, dict):
            return None, False
        return crossref_item_to_paper(message, source="crossref"), True

    def _openalex_by_doi(self, doi: str) -> tuple[Paper | None, bool]:
        norm = normalize_doi(doi)
        params: dict[str, object] = {"filter": f"doi:{norm}", "per-page": 1}
        if self.mailto:
            params["mailto"] = self.mailto
        try:
            resp = self.http.get(self.openalex_base_url, params=params, timeout=self.timeout)
        except BackendError:
            return None, False
        if resp.status_code == 404:
            return None, True
        if resp.status_code != 200:
            return None, False
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return None, False
        if not isinstance(payload, dict):
            return None, False
        results = payload.get("results")
        if not isinstance(results, list):
            return None, False
        if not results or not isinstance(results[0], dict):
            return None, True  # definitive: queried OK, no match
        return _openalex_work_to_paper(results[0]), True

    def _arxiv_by_id(self, arxiv_id: str) -> tuple[Paper | None, bool]:
        backend = ArxivBackend(http_client=self.http, base_url=self.arxiv_base_url, timeout=self.timeout)
        try:
            return backend.fetch_by_id(arxiv_id), True
        except BackendError:
            return None, False

    def _crossref_by_title(self, title: str) -> tuple[Paper | None, bool]:
        backend = CrossrefBackend(
            http_client=self.http,
            base_url=self.crossref_base_url,
            mailto=self.mailto,
            timeout=self.timeout,
        )
        try:
            candidates = backend.search(SearchQuery(text=title, max_results=5))
        except BackendError:
            return None, False
        best: Paper | None = None
        best_sim = 0.0
        for candidate in candidates:
            sim = title_similarity(title, candidate.title)
            if sim > best_sim:
                best_sim, best = sim, candidate
        if best is not None and best_sim >= self.title_match_floor:
            return best, True
        return None, True  # queried OK, nothing cleared the similarity floor

    # -- cache keys ---------------------------------------------------------

    @staticmethod
    def _cache_key(*, doi: str | None, arxiv_id: str | None, title: str | None) -> str | None:
        if doi:
            return f"doi:{normalize_doi(doi)}"
        if arxiv_id:
            cleaned = arxiv_id.strip().lower()
            if cleaned.startswith("arxiv:"):
                cleaned = cleaned.split(":", 1)[1].strip()
            return f"arxiv:{cleaned}" if cleaned else None
        if title and title.strip():
            digest = hashlib.sha256(_normalize_title(title).encode("utf-8")).hexdigest()[:20]
            return f"title:{digest}"
        return None


def _strip_arxiv_version(arxiv_id: str) -> str:
    """Drop a trailing ``vN`` version suffix from an arXiv id for comparison."""
    return re.sub(r"v\d+$", "", arxiv_id.strip().lower())


def _cache_payload_consistent(key: str, value: Paper | None) -> bool:
    """Guard against a corrupt/poisoned positive cache row.

    Conservative by design: reject only when the payload carries an identifier
    that *contradicts* the key (the realistic corruption/tamper case Forge
    flagged — e.g. a row keyed to a fabricated DOI but carrying a different real
    paper). A negative row, or a payload that simply omits the identifier, is
    trusted — the resolver only ever writes payloads it fetched for that key, so
    a missing identifier is not evidence of tampering and rejecting it would
    drop legitimate cache hits. Title keys hash the *query*, not the matched
    record, so they cannot be cross-checked here; the title-only certification
    guard in the verifier limits their blast radius.
    """
    if value is None:
        return True
    if key.startswith("doi:") and value.doi:
        return normalize_doi(value.doi) == key[len("doi:") :]
    if key.startswith("arxiv:") and value.id:
        candidate = value.id.lower()
        if candidate.startswith("arxiv:"):
            candidate = candidate.split(":", 1)[1]
        return _strip_arxiv_version(candidate) == _strip_arxiv_version(key[len("arxiv:") :])
    return True


def _normalize_title(title: str) -> str:
    """Collapse a title to comparable form: lowercase alphanumerics + spaces."""
    chars = [ch.lower() if ch.isalnum() else " " for ch in title]
    return " ".join("".join(chars).split())


def title_similarity(a: str | None, b: str | None) -> float:
    """Deterministic similarity in ``[0, 1]`` between two titles.

    Uses :class:`difflib.SequenceMatcher` over normalized titles — pure stdlib,
    no randomness, stable across runs and platforms.
    """
    from difflib import SequenceMatcher

    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalize_title(a), _normalize_title(b)).ratio()


def _openalex_work_to_paper(work: dict[str, Any]) -> Paper:
    """Map an OpenAlex ``works`` record to a :class:`Paper` (minimal fields)."""
    title = work.get("title") or work.get("display_name") or "Untitled"
    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        author = (authorship or {}).get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)
    doi = work.get("doi")
    if isinstance(doi, str):
        doi = normalize_doi(doi)
    year = work.get("publication_year")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    venue = None
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    if isinstance(source, dict):
        venue = source.get("display_name")
    return Paper(
        id=f"doi:{doi}" if doi else (work.get("id") or title),
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        url=work.get("id"),
        venue=venue,
        source="openalex",
    )
