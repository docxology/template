"""Open-access full-text resolution, download, and local extraction.

Four responsibilities, all opt-in and network/filesystem-gated so the default
offline pipeline never depends on them:

* ``resolve_fulltext_url`` — find a downloadable PDF URL for a record. Prefers an
  already-known ``pdf_url``; otherwise, given a DOI, queries the Unpaywall API for
  the best open-access location.
* ``download_fulltext`` — resolve (optionally) then GET the URL and write the bytes
  to a deterministic path ``<dest_dir>/<sanitized canonical_id>.pdf``.
* ``extract_fulltext_text`` / ``extract_figures`` — parse an already-downloaded PDF
  on disk (via ``pypdf``) into plaintext and embedded raster images. Both degrade to
  ``None`` / ``[]`` on any parse error — a corrupt or unparseable PDF never raises.
* ``download_and_extract_fulltext`` — the end-to-end convenience wrapper: download,
  then (if a PDF was written) extract text and figures alongside it.

``assess_fulltext_availability`` is a pure (no-network, no-filesystem) summary of how
much full text a corpus could yield from its metadata alone.
``assess_fulltext_extraction`` is the filesystem-aware sibling: given a directory of
already-extracted artifacts, it reports how many papers actually have a ``.txt`` and/or
figure files on disk.

Every network function degrades gracefully: on any error, or when nothing is
resolvable, the resolver returns ``None`` and the downloader returns ``None`` — they
never raise to the caller. This mirrors the multiple-dispatch contract of the engine
clients: a missing key or no network is a ``skipped``, not a failure. The extraction
functions extend the same convention to PDF parsing: a corrupt file degrades rather
than raising.
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

from literature.corpus import Corpus
from literature.models import Paper

logger = logging.getLogger(__name__)

UNPAYWALL_API_URL = "https://api.unpaywall.org/v2/"
MAX_RETRIES = 3
_BACKOFF_BASE = 0.5


def _request_with_retry(
    url: str,
    *,
    params: Optional[dict[str, Any]] = None,
    session: Any = None,
    timeout: float = 30.0,
    max_retries: int = MAX_RETRIES,
    delay_override: Optional[float] = None,
    stream: bool = False,
) -> Optional[Any]:
    """GET ``url`` with bounded exponential backoff. Return the response or None.

    Returns None on exhausted retries or any request exception — never raises.
    """
    import requests

    sess = session or requests
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = sess.get(url, params=params, timeout=timeout, stream=stream)
        except Exception as exc:  # noqa: BLE001 pragma: no cover -- safety net: any request error retries/degrades
            last_exc = exc
            resp = None
        if resp is not None:
            if resp.status_code == 200:
                return resp
            if resp.status_code not in (429, 500, 502, 503, 504):
                logger.debug("fulltext request %s -> HTTP %s", url, resp.status_code)
                return None
        sleep_for = delay_override if delay_override is not None else _BACKOFF_BASE * (2**attempt)
        if attempt < max_retries - 1:
            time.sleep(sleep_for)
    if last_exc is not None:
        logger.debug("fulltext request %s failed: %s", url, last_exc)
    return None


def _parse_unpaywall(data: dict) -> Optional[str]:
    """Extract the best OA PDF (or landing) URL from an Unpaywall record."""
    if not isinstance(data, dict):
        return None
    best = data.get("best_oa_location") or {}
    if isinstance(best, dict):
        url = best.get("url_for_pdf") or best.get("url")
        if url:
            return str(url)
    for loc in data.get("oa_locations", []) or []:
        if isinstance(loc, dict):
            url = loc.get("url_for_pdf") or loc.get("url")
            if url:
                return str(url)
    return None


def resolve_fulltext_url(
    paper: Paper,
    *,
    unpaywall_email: Optional[str] = None,
    unpaywall_base_url: str = UNPAYWALL_API_URL,
    session: Any = None,
    delay_override: Optional[float] = None,
) -> Optional[str]:
    """Return a downloadable full-text URL for ``paper`` or None.

    Resolution order: the record's own ``pdf_url`` first; otherwise, if the record
    has a DOI and an Unpaywall email is supplied, query Unpaywall.
    """
    if paper.pdf_url:
        return str(paper.pdf_url)
    if not paper.doi or not unpaywall_email:
        return None
    base = unpaywall_base_url if unpaywall_base_url.endswith("/") else unpaywall_base_url + "/"
    resp = _request_with_retry(
        f"{base}{paper.doi}",
        params={"email": unpaywall_email},
        session=session,
        delay_override=delay_override,
    )
    if resp is None:
        return None
    try:
        return _parse_unpaywall(resp.json())
    except Exception:  # noqa: BLE001 pragma: no cover -- safety net: malformed payload yields no URL
        return None


def _safe_filename(canonical_id: str) -> str:
    """Deterministic, filesystem-safe filename stem from a canonical id."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", canonical_id).strip("_")
    return stem or "record"


# Public alias so other modules (e.g. reproducibility.extraction) can derive the
# same deterministic on-disk filename stem without importing a private name.
safe_filename = _safe_filename


def download_fulltext(
    paper: Paper,
    dest_dir: Path,
    *,
    session: Any = None,
    resolve: bool = True,
    url: Optional[str] = None,
    unpaywall_email: Optional[str] = None,
    delay_override: Optional[float] = None,
) -> Optional[Path]:
    """Download the full-text PDF for ``paper`` into ``dest_dir``; return the path or None.

    Network-gated and non-raising: if no URL can be resolved or the request fails,
    returns None. The filename is deterministic (``<canonical_id>.pdf``) so repeated
    downloads are idempotent.
    """
    target_url = url
    if target_url is None and resolve:
        target_url = resolve_fulltext_url(
            paper,
            unpaywall_email=unpaywall_email,
            session=session,
            delay_override=delay_override,
        )
    if not target_url:
        return None
    resp = _request_with_retry(target_url, session=session, delay_override=delay_override, stream=True)
    if resp is None:
        return None
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / f"{_safe_filename(paper.canonical_id)}.pdf"
    tmp_path = out_path.with_suffix(".pdf.part")
    try:
        content = resp.content if hasattr(resp, "content") else resp.read()
        tmp_path.write_bytes(content)
        tmp_path.replace(out_path)
    except Exception:  # noqa: BLE001 pragma: no cover -- safety net: I/O failure cleans up and returns None
        if tmp_path.exists():
            tmp_path.unlink()
        return None
    return out_path


def assess_fulltext_availability(papers: list[Paper]) -> dict[str, Any]:
    """Pure summary of potential full-text coverage across a record list."""
    total = len(papers)
    has_pdf = sum(1 for p in papers if p.pdf_url)
    is_oa = sum(1 for p in papers if p.is_open_access is True)
    not_oa = sum(1 for p in papers if p.is_open_access is False)
    unknown_oa = sum(1 for p in papers if p.is_open_access is None)
    by_source: dict[str, int] = {}
    for p in papers:
        if p.full_text_source:
            by_source[p.full_text_source] = by_source.get(p.full_text_source, 0) + 1
    return {
        "total": total,
        "has_pdf_url": has_pdf,
        "is_open_access": is_oa,
        "not_open_access": not_oa,
        "unknown_open_access": unknown_oa,
        "pct_with_pdf_url": round(100.0 * has_pdf / total, 2) if total else 0.0,
        "by_source": by_source,
    }


_BLANK_LINES_RE = re.compile(r"\n{3,}")


def extract_fulltext_text(pdf_path: Path) -> Optional[str]:
    """Extract concatenated plaintext from every page of a downloaded PDF.

    Pages are joined with a blank line (``"\\n\\n"``); runs of 3+ consecutive
    newlines are collapsed to 2. Returns ``None`` if the result is empty, or if
    ``pypdf`` raises for any reason (corrupt/unparseable PDF) — this function
    never raises to the caller, matching this module's degrade-to-None convention.
    """
    import pypdf

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 pragma: no cover -- safety net: corrupt/unparseable PDF degrades to None
        logger.warning("extract_fulltext_text: failed to parse %s: %s", pdf_path, exc)
        return None
    text = "\n\n".join(pages_text).strip()
    if not text:
        return None
    return _BLANK_LINES_RE.sub("\n\n", text)


def extract_figures(pdf_path: Path, dest_dir: Path, *, stem: str) -> list[Path]:
    """Extract every embedded raster image from a PDF into ``dest_dir``.

    Files are named ``<stem>_fig<n>.<ext>`` with ``n`` starting at 1, in page then
    in-page order. The extension is derived from the image's own filename suffix
    (``ImageFile.name``, e.g. ``"Im1.png"``), falling back to the PIL image's own
    format (``ImageFile.image.format``), falling back to ``"png"`` if neither is
    available. ``dest_dir`` is created if missing. A PDF with zero embedded images
    returns ``[]``. Any per-image extraction error is skipped (the loop continues) and
    any whole-PDF parse error (corrupt/unparseable PDF) returns ``[]`` — this function
    never raises to the caller.
    """
    import pypdf

    try:
        reader = pypdf.PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 pragma: no cover -- safety net: corrupt/unparseable PDF degrades to []
        logger.warning("extract_figures: failed to parse %s: %s", pdf_path, exc)
        return []

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    n = 0
    for page in reader.pages:
        try:
            images = list(page.images)
        except Exception as exc:  # noqa: BLE001 -- safety net: a malformed page's image list is skipped, not fatal
            logger.warning("extract_figures: failed to enumerate images on a page of %s: %s", pdf_path, exc)
            continue
        for image_file in images:
            try:
                ext = Path(image_file.name).suffix.lstrip(".")
                if not ext:
                    fmt = getattr(image_file.image, "format", None)
                    ext = fmt.lower() if fmt else "png"
                n += 1
                out_path = dest_dir / f"{stem}_fig{n}.{ext}"
                out_path.write_bytes(image_file.data)
                written.append(out_path)
            except Exception as exc:  # noqa: BLE001 -- safety net: a single bad image is skipped, not fatal
                logger.warning("extract_figures: failed to write an image from %s: %s", pdf_path, exc)
                continue
    return written


def download_and_extract_fulltext(
    paper: Paper,
    dest_dir: Path,
    *,
    session: Any = None,
    resolve: bool = True,
    url: Optional[str] = None,
    unpaywall_email: Optional[str] = None,
    delay_override: Optional[float] = None,
) -> dict[str, Any]:
    """Download the full-text PDF for ``paper`` then extract text and figures from it.

    Reuses ``download_fulltext`` for the network step. If (and only if) a PDF was
    written, additionally extracts plaintext into
    ``<dest_dir>/<sanitized canonical_id>.txt`` (written only when
    ``extract_fulltext_text`` returns non-``None``) and embedded figures into
    ``<dest_dir>/figures/`` (stem = the sanitized canonical id). Idempotent: repeated
    calls re-download and re-extract to the same deterministic filenames, which is the
    existing convention — no extra caching layer is added.

    Returns:
        A dict with keys ``pdf_path`` (``Path | None``), ``text_path`` (``Path | None``),
        and ``figure_paths`` (``list[Path]``, empty when there is no PDF or no images).
    """
    pdf_path = download_fulltext(
        paper,
        dest_dir,
        session=session,
        resolve=resolve,
        url=url,
        unpaywall_email=unpaywall_email,
        delay_override=delay_override,
    )
    result: dict[str, Any] = {"pdf_path": pdf_path, "text_path": None, "figure_paths": []}
    if pdf_path is None:
        return result

    dest_dir = Path(dest_dir)
    stem = _safe_filename(paper.canonical_id)

    text = extract_fulltext_text(pdf_path)
    if text is not None:
        text_path = dest_dir / f"{stem}.txt"
        text_path.write_text(text, encoding="utf-8")
        result["text_path"] = text_path

    result["figure_paths"] = extract_figures(pdf_path, dest_dir / "figures", stem=stem)
    return result


def assess_fulltext_extraction(corpus: Corpus, fulltext_dir: Path) -> dict[str, Any]:
    """Report how much of ``corpus`` has already-extracted fulltext artifacts on disk.

    Filesystem-aware sibling of ``fulltext_assessment.assess_corpus`` (kept separate so
    that the otherwise pure, no-I/O ``assess_corpus`` signature is not disturbed). For
    each paper, checks for ``<fulltext_dir>/<sanitized canonical_id>.txt`` and 1+ files
    under ``<fulltext_dir>/figures/<sanitized canonical_id>_fig*.*``.
    """
    fulltext_dir = Path(fulltext_dir)
    figures_dir = fulltext_dir / "figures"
    papers = corpus.papers
    total = len(papers)

    with_text = 0
    with_figures = 0
    for paper in papers:
        stem = _safe_filename(paper.canonical_id)
        if (fulltext_dir / f"{stem}.txt").is_file():
            with_text += 1
        if figures_dir.is_dir() and any(figures_dir.glob(f"{stem}_fig*.*")):
            with_figures += 1

    return {
        "total_papers": total,
        "with_extracted_text": with_text,
        "without_extracted_text": total - with_text,
        "percent_with_extracted_text": round(100.0 * with_text / total, 1) if total else 0.0,
        "with_extracted_figures": with_figures,
        "without_extracted_figures": total - with_figures,
        "percent_with_extracted_figures": round(100.0 * with_figures / total, 1) if total else 0.0,
    }
