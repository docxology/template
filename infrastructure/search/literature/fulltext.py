"""Abstract and full-text retrieval for :class:`Paper` records.

The literature backends produce metadata (title / authors / abstract /
DOI). Many downstream agents — LLM-based synthesis, gap analysis, prior-art
review — also need the *content* of the papers. This module bridges that
gap.

Two layers:

* :class:`AbstractFetcher` — populate a :class:`Paper`'s ``abstract`` field
  when the search backend did not already supply one. Uses the same
  injectable :class:`HttpClient` as the search backends, so tests use
  ``pytest-httpserver`` instead of mocks.

* :class:`FulltextFetcher` — populate a :class:`Paper`'s ``fulltext`` field
  by downloading the PDF (arXiv URL, ``paper.pdf_url``, or a caller-supplied
  override) and extracting plain text. PDF text extraction depends on the
  optional ``pypdf`` package; when unavailable we degrade gracefully and
  return the cached path of the downloaded PDF instead.

Both fetchers cache content on disk by paper id (``arxiv:1234.5678`` →
``cache/arxiv_1234.5678.txt``) so re-runs are deterministic and
LLM-prompt synthesis can replay against frozen text.
"""

import json
import re

import defusedxml.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.literature.backends import (
    BackendError,
    HttpClient,
    UrllibHttpClient,
)
from infrastructure.search.literature.models import Paper

logger = get_logger(__name__)

# arXiv abstract URLs — used when only a DOI / title is known.
_ARXIV_ABS_BASE = "http://export.arxiv.org/api/query"


def _safe_id(paper_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)


@dataclass
class FetchResult:
    """Outcome of a fetch operation.

    Attributes:
        paper: The (possibly mutated) :class:`Paper` record.
        status: ``"hit"`` (content fetched), ``"cached"`` (read from cache),
            ``"skipped"`` (no fetchable URL or content already present), or
            ``"error"`` (network / parse failure).
        message: Optional human-readable detail, populated for ``error`` and
            sometimes for ``skipped``.
        path: When content was written to / read from disk, the path; else
            ``None``.
    """

    paper: Paper
    status: str
    message: str | None = None
    path: Path | None = None


class AbstractFetcher:
    """Populate :attr:`Paper.abstract` for records that lack one.

    Args:
        http_client: HTTP client (defaults to :class:`UrllibHttpClient`).
        cache_dir: Optional cache directory; abstracts are written as
            ``<safe_id>.txt`` and re-used on subsequent calls.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        cache_dir: Path | str | None = None,
        timeout: float = 15.0,
        arxiv_base_url: str | None = None,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.arxiv_base_url = arxiv_base_url or _ARXIV_ABS_BASE

    def _cache_path(self, paper: Paper) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"abs_{_safe_id(paper.id)}.txt"

    def fetch(self, paper: Paper, *, force: bool = False) -> FetchResult:
        if paper.abstract and not force:
            return FetchResult(paper=paper, status="skipped", message="already present")

        cache_path = self._cache_path(paper)
        if cache_path is not None and cache_path.exists() and not force:
            paper.abstract = cache_path.read_text(encoding="utf-8")
            return FetchResult(paper=paper, status="cached", path=cache_path)

        # arXiv: query the export API by id_list.
        if paper.id.lower().startswith("arxiv:"):
            arxiv_id = paper.id.split(":", 1)[1]
            try:
                resp = self.http.get(
                    self.arxiv_base_url,
                    params={"id_list": arxiv_id, "max_results": 1},
                    timeout=self.timeout,
                )
            except BackendError as exc:
                return FetchResult(paper=paper, status="error", message=str(exc))
            if resp.status_code != 200:
                return FetchResult(paper=paper, status="error", message=f"HTTP {resp.status_code}")
            try:
                root = ET.fromstring(resp.text)
            except ET.ParseError as exc:
                return FetchResult(paper=paper, status="error", message=f"XML: {exc}")
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is None:
                return FetchResult(paper=paper, status="error", message="no entry")
            summary_el = entry.find("atom:summary", ns)
            if summary_el is None or not summary_el.text:
                return FetchResult(paper=paper, status="error", message="no summary")
            paper.abstract = re.sub(r"\s+", " ", summary_el.text).strip()
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(paper.abstract, encoding="utf-8")
            return FetchResult(paper=paper, status="hit", path=cache_path)

        return FetchResult(
            paper=paper,
            status="skipped",
            message=f"no abstract source available for id={paper.id!r}",
        )

    def fetch_all(self, papers: Iterable[Paper], *, force: bool = False) -> list[FetchResult]:
        return [self.fetch(p, force=force) for p in papers]


def _extract_pdf_text(pdf_bytes: bytes) -> str | None:
    """Return plain text from *pdf_bytes*, or ``None`` if pypdf is missing."""
    try:
        import pypdf  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        from io import BytesIO

        reader = pypdf.PdfReader(BytesIO(pdf_bytes))
        chunks: list[str] = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:  # pragma: no cover - per-page failure  # nosec B112
                continue
        return re.sub(r"\n{3,}", "\n\n", "\n".join(chunks)).strip() or None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("PDF parse error: %s", exc)
        return None


class FulltextFetcher:
    """Populate :attr:`Paper.fulltext` from PDF / HTML sources.

    Resolution order:

    1. ``pdf_url`` argument to :meth:`fetch`, if given.
    2. ``paper.pdf_url`` if present.
    3. arXiv: derive ``https://arxiv.org/pdf/<id>.pdf`` from
       ``paper.id == "arxiv:<id>"``.

    PDFs are written verbatim to ``<cache_dir>/<safe_id>.pdf`` (when a cache
    directory is configured), and the extracted text is written to
    ``<cache_dir>/<safe_id>.txt``. Without ``pypdf``, the PDF is downloaded
    and its path is returned in :attr:`FetchResult.path` but ``fulltext``
    stays ``None``.
    """

    name = "fulltext"

    def __init__(
        self,
        *,
        http_client: HttpClient | None = None,
        cache_dir: Path | str | None = None,
        timeout: float = 60.0,
        max_chars: int | None = 200_000,
    ) -> None:
        self.http = http_client or UrllibHttpClient()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_chars = max_chars

    def _cache_paths(self, paper: Paper) -> tuple[Path, Path] | None:
        if self.cache_dir is None:
            return None
        safe = _safe_id(paper.id)
        return (
            self.cache_dir / f"{safe}.pdf",
            self.cache_dir / f"{safe}.txt",
        )

    def _resolve_pdf_url(self, paper: Paper, override: str | None) -> str | None:
        if override:
            return override
        if paper.pdf_url:
            return paper.pdf_url
        if paper.id.lower().startswith("arxiv:"):
            arxiv_id = paper.id.split(":", 1)[1]
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        return None

    def fetch(
        self,
        paper: Paper,
        *,
        pdf_url: str | None = None,
        force: bool = False,
    ) -> FetchResult:
        if paper.fulltext and not force:
            return FetchResult(paper=paper, status="skipped", message="already present")

        cache = self._cache_paths(paper)
        if cache is not None and not force:
            pdf_path, text_path = cache
            if text_path.exists():
                paper.fulltext = text_path.read_text(encoding="utf-8")
                return FetchResult(paper=paper, status="cached", path=text_path)

        url = self._resolve_pdf_url(paper, pdf_url)
        if url is None:
            return FetchResult(
                paper=paper,
                status="skipped",
                message=f"no fulltext URL for id={paper.id!r}",
            )

        try:
            resp = self.http.get(url, timeout=self.timeout)
        except BackendError as exc:
            return FetchResult(paper=paper, status="error", message=str(exc))
        if resp.status_code != 200:
            return FetchResult(paper=paper, status="error", message=f"HTTP {resp.status_code}")

        pdf_bytes = resp.text.encode("latin-1", errors="ignore")
        # Write PDF to cache regardless of whether we can extract text.
        path: Path | None = None
        if cache is not None:
            pdf_path, text_path = cache
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_bytes(pdf_bytes)
            path = pdf_path

        text = _extract_pdf_text(pdf_bytes)
        if text is None:
            return FetchResult(
                paper=paper,
                status="error",
                message="pypdf unavailable; PDF cached but text not extracted",
                path=path,
            )

        if self.max_chars and len(text) > self.max_chars:
            text = text[: self.max_chars]

        paper.fulltext = text
        if cache is not None:
            text_path.write_text(text, encoding="utf-8")
            path = text_path
        return FetchResult(paper=paper, status="hit", path=path)

    def fetch_all(self, papers: Iterable[Paper], *, force: bool = False) -> list[FetchResult]:
        return [self.fetch(p, force=force) for p in papers]


def enrich_papers(
    papers: Iterable[Paper],
    *,
    abstracts: AbstractFetcher | None = None,
    fulltext: FulltextFetcher | None = None,
    force: bool = False,
) -> list[FetchResult]:
    """Run the configured fetchers over *papers* in order (abstract first)."""
    results: list[FetchResult] = []
    paper_list = list(papers)
    if abstracts is not None:
        for paper in paper_list:
            results.append(abstracts.fetch(paper, force=force))
    if fulltext is not None:
        for paper in paper_list:
            results.append(fulltext.fetch(paper, force=force))
    return results


def write_corpus(papers: Iterable[Paper], path: Path | str) -> Path:
    """Persist a list of (possibly enriched) papers as a JSON corpus file.

    The output is compatible with :class:`infrastructure.search.literature.LocalBackend`.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"papers": [p.to_dict() for p in papers]},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return out
