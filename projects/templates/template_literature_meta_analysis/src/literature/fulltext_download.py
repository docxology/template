"""Open-access full-text resolution and download.

Two responsibilities, both opt-in and network-gated so the default offline pipeline
never depends on them:

* ``resolve_fulltext_url`` — find a downloadable PDF URL for a record. Prefers an
  already-known ``pdf_url``; otherwise, given a DOI, queries the Unpaywall API for
  the best open-access location.
* ``download_fulltext`` — resolve (optionally) then GET the URL and write the bytes
  to a deterministic path ``<dest_dir>/<sanitized canonical_id>.pdf``.

``assess_fulltext_availability`` is a pure (no-network) summary of how much full text
a corpus could yield.

Every network function degrades gracefully: on any error, or when nothing is
resolvable, the resolver returns ``None`` and the downloader returns ``None`` — they
never raise to the caller. This mirrors the multiple-dispatch contract of the engine
clients: a missing key or no network is a ``skipped``, not a failure.
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

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
