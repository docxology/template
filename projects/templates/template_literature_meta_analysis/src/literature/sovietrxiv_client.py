"""SovietRxiv / RussiaRxiv / ChinaRxiv public API client.

Provides a keyless engine adapter over the unified SovietRxiv / ChinaRxiv
``/api/v1/papers`` endpoint. SovietRxiv (https://russiarxiv.org) is a
translated archive of Soviet-era scientific preprints and journal articles
sourced from Math-Net.Ru and CyberLeninka. ChinaRxiv (https://chinaxiv.org)
shares the identical unified API and serves translated Chinese preprints from
ChinaXiv. Both retain original-language PDFs alongside each translation.

The ``source`` query parameter (``"russiarxiv"`` or ``"chinaxiv"``) selects
which sub-corpus to search; when omitted, the combined corpus is searched.

Mirrors the shape of the sibling adapters (``crossref_client``,
``openalex_client``): module-level ``SOVIETRXIV_API_URL`` and
``CHINARXIV_API_URL`` constants, a pure ``_parse_sovietrxiv_paper`` parser,
and a ``search_sovietrxiv`` entry point with cursor-based pagination and a
polite ``X-API-Email`` header.

The ``PaperList`` response is::

    {
        "total": <int>,
        "limit": <int>,
        "next_cursor": <str|null>,
        "data": [ <PaperSummary>, ... ]
    }

``PaperSummary`` exposes ``id``, ``title``, ``authors`` (list of strings),
``abstract`` (may be truncated in list view), ``abstract_source``
(``source`` | ``machine_generated`` | ``none``), ``date`` (YYYY-MM-DD),
``subjects`` (list of strings), ``has_full_text``, ``has_figures``,
``has_pdf``, ``source_language``, ``source_url``, ``source``
(``chinaxiv`` | ``russiarxiv``), ``publication`` (nullable), and ``_links``.

All functions accept an injectable ``base_url`` for testing with
pytest-httpserver. ``search_sovietrxiv`` is graceful: on any network error or
non-200 status it logs and returns the results collected so far (``[]`` if
none) and never raises to the caller.

API reference: https://sovietrxiv.org/api/docs
OpenAPI spec: https://sovietrxiv.org/api/openapi.json
"""

from __future__ import annotations

import logging
import random
import time
from datetime import date
from typing import Callable, Optional

import requests

from .models import Author, Paper

logger = logging.getLogger(__name__)

# Default API base URL (the papers endpoint is f"{base_url}/api/v1/papers").
SOVIETRXIV_API_URL = "https://russiarxiv.org"

# ChinaRxiv shares the identical unified API (https://chinaxiv.org/api/v1/papers).
# The `source` query parameter distinguishes chinaxiv vs russiarxiv records.
CHINARXIV_API_URL = "https://chinaxiv.org"

# Pagination settings. The API permits 1–100 results per page (default 20).
SOVIETRXIV_PAGE_SIZE = 100

# Retry settings (mirrors crossref_client / openalex_client).
MAX_RETRIES = 1
RETRY_BASE_SECONDS = 10.0


def _extract_year(date_str: Optional[str]) -> Optional[int]:
    """Extract the publication year from an ISO date string (YYYY-MM-DD).

    The API returns ``date`` as ``YYYY-MM-DD`` or ``null``. We only need the
    year for the ``Paper`` model. Partial dates (``YYYY`` or ``YYYY-MM``) are
    tolerated by splitting on ``-`` and taking the first part.

    Args:
        date_str: ISO date string or None.

    Returns:
        Year as an int, or None if it cannot be resolved.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    year_part = date_str.split("-")[0]
    try:
        return int(year_part)
    except ValueError:
        return None


def _extract_authors(authors_list: object) -> list[Author]:
    """Build the author list from a SovietRxiv ``authors`` array.

    SovietRxiv returns authors as a list of plain strings (full names), not
    objects with ``given``/``family`` like Crossref. Empty or non-string
    entries are skipped.

    Args:
        authors_list: The raw ``authors`` field (expected list of strings).

    Returns:
        List of Author objects (possibly empty).
    """
    authors: list[Author] = []
    if not isinstance(authors_list, list):
        return authors
    for entry in authors_list:
        if isinstance(entry, str) and entry.strip():
            authors.append(Author(name=entry.strip()))
    return authors


def _parse_sovietrxiv_paper(item: dict) -> Paper:
    """Parse a single SovietRxiv ``PaperSummary`` object into a Paper.

    Args:
        item: Dictionary representing one SovietRxiv paper summary.

    Returns:
        Paper populated from the SovietRxiv fields. Pure: performs no I/O.
    """
    title = item.get("title") or ""
    abstract = item.get("abstract") or ""
    authors = _extract_authors(item.get("authors"))
    year = _extract_year(item.get("date"))
    venue = item.get("publication_title") or item.get("publication")
    if not venue:
        # Use the source as venue fallback for display clarity.
        source = item.get("source")
        venue = f"SovietRxiv ({source})" if source else None

    source_url = item.get("source_url")
    english_pdf_url = item.get("english_pdf_url")
    pdf_url = english_pdf_url or source_url or None

    has_pdf = item.get("has_pdf")
    is_open_access = bool(has_pdf) if isinstance(has_pdf, bool) else None

    # Parse publication_date for the full-date field.
    pub_date: Optional[date] = None
    date_str = item.get("date")
    if date_str and isinstance(date_str, str):
        try:
            pub_date = date.fromisoformat(date_str)
        except ValueError:
            pub_date = None

    # The SovietRxiv paper ID is a stable identifier (e.g., "202312.00001").
    # We store it in pdf_url's sibling field set — there is no dedicated
    # sovietrxiv_id field on Paper, so we use the title-hash fallback for
    # canonical_id unless a DOI is present. The source_url provides a
    # persistent link.
    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=None,  # SovietRxiv does not expose DOIs in the summary schema
        venue=venue,
        citation_count=0,  # Not provided by the API
        publication_date=pub_date,
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        full_text_source="sovietrxiv" if item.get("has_full_text") else None,
    )


def _request_with_retry(
    http: requests.Session,
    url: str,
    params: dict,
    headers: dict,
    max_retries: int = MAX_RETRIES,
    delay_override: Optional[Callable[[float], None]] = None,
) -> requests.Response:
    """Make an HTTP GET request with bounded retry on transient HTTP errors.

    Uses exponential backoff with jitter, matching the sibling clients.

    Args:
        http: requests.Session for the request.
        url: URL to request.
        params: Query parameters.
        headers: Request headers (e.g., X-API-Email for polite pool).
        max_retries: Maximum number of retry attempts.
        delay_override: Optional sleep function (test injection).

    Returns:
        Successful response object.

    Raises:
        requests.HTTPError: If a non-2xx status survives all retries.
    """
    sleep_fn = delay_override or time.sleep
    response = None
    for attempt in range(max_retries + 1):
        response = http.get(url, params=params, headers=headers, timeout=30)
        if response.status_code in (429, 500, 502, 503, 504):
            wait = min(10.0, RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 1))
            logger.warning(
                "SovietRxiv HTTP %d (attempt %d/%d) — retrying in %.1fs",
                response.status_code,
                attempt + 1,
                max_retries,
                wait,
            )
            sleep_fn(wait)
            continue
        response.raise_for_status()
        return response

    # All retries exhausted: surface the last bad status as an error.
    logger.error("SovietRxiv retries exhausted after %d attempts", max_retries)
    if response is not None:
        response.raise_for_status()
    raise requests.HTTPError("SovietRxiv retries exhausted")  # pragma: no cover


def search_sovietrxiv(
    query: str,
    *,
    base_url: str = SOVIETRXIV_API_URL,
    max_results: int = 100,
    api_email: Optional[str] = None,
    source: Optional[str] = None,
    page_size: int = SOVIETRXIV_PAGE_SIZE,
    session: Optional[requests.Session] = None,
    delay_override: Optional[Callable[[float], None]] = None,
) -> list[Paper]:
    """Search SovietRxiv / RussiaRxiv for papers matching a free-text query.

    Pages through results with cursor-based pagination (the API's preferred
    method) until ``max_results`` is reached or the API stops returning a
    ``next_cursor``. Graceful by contract: any network error or non-200 status
    is logged and the results collected so far are returned (``[]`` if none) —
    this function never raises for transport or HTTP problems.

    Args:
        query: Full-text search query.
        base_url: API base URL (injectable for testing). The papers endpoint
            is ``f"{base_url}/api/v1/papers"``.
        max_results: Maximum number of results to retrieve.
        api_email: Optional contact email for the polite rate-limit pool
            (300/min vs 30/min anonymous). Sent as the ``X-API-Email`` header.
        source: Optional source filter (``"chinaxiv"`` or ``"russiarxiv"``).
            When None, searches both sources.
        page_size: Number of results requested per page (1–100). The final
            page may request fewer results so the total never exceeds
            max_results.
        session: Optional requests.Session for connection reuse.
        delay_override: Optional sleep function (test injection).

    Returns:
        List of Paper objects (possibly empty).
    """
    http = session or requests.Session()
    all_papers: list[Paper] = []
    papers_url = f"{base_url}/api/v1/papers"
    window = max(1, min(page_size, SOVIETRXIV_PAGE_SIZE))

    headers: dict[str, str] = {}
    if api_email:
        headers["X-API-Email"] = api_email

    try:
        cursor: Optional[str] = None
        page_num = 0

        while len(all_papers) < max_results:
            page_limit = min(window, max_results - len(all_papers))
            page_num += 1

            params: dict = {
                "q": query,
                "limit": page_limit,
            }
            if cursor:
                params["cursor"] = cursor
            if source:
                params["source"] = source

            logger.info(
                "SovietRxiv page %d: fetching %d results (total so far: %d, target: %d)",
                page_num,
                page_limit,
                len(all_papers),
                max_results,
            )

            try:
                response = _request_with_retry(
                    http,
                    papers_url,
                    params,
                    headers,
                    delay_override=delay_override,
                )
                payload = response.json()
                # Parse inside the try so the "never raises" contract also covers
                # any payload-shape surprise during extraction — not just the
                # network/JSON-decode boundary.
                if not isinstance(payload, dict):
                    break
                page_data = payload.get("data", [])
                if not isinstance(page_data, list):
                    break
                page_papers = [_parse_sovietrxiv_paper(item) for item in page_data if isinstance(item, dict)]
            except (requests.RequestException, ValueError) as e:
                # RequestException covers transport + retried HTTP errors;
                # ValueError covers a malformed JSON body (requests'
                # JSONDecodeError subclasses both). Either way: stop and return
                # what we have rather than raising to the caller.
                logger.warning("SovietRxiv search stopped early: %s", e)
                break

            if not page_papers:
                logger.info(
                    "SovietRxiv page %d: no more results (total fetched: %d)",
                    page_num,
                    len(all_papers),
                )
                break

            all_papers.extend(page_papers)
            logger.info(
                "SovietRxiv page %d: fetched %d papers (total: %d)",
                page_num,
                len(page_papers),
                len(all_papers),
            )

            # Cursor-based pagination: stop if no next_cursor is returned.
            next_cursor = payload.get("next_cursor")
            if not next_cursor or not isinstance(next_cursor, str):
                logger.info("SovietRxiv: no next_cursor, all results fetched")
                break

            cursor = next_cursor
    finally:
        if session is None:
            http.close()

    logger.info(
        "SovietRxiv search complete: %d total papers for query '%s'",
        len(all_papers),
        query[:80],
    )
    return all_papers[:max_results]
