"""bioRxiv / medRxiv public API client.

Provides a keyless engine adapter over the unified bioRxiv/medRxiv
``/details/{server}/{interval}/{cursor}/json`` endpoint. bioRxiv
(https://www.biorxiv.org) and medRxiv (https://www.medrxiv.org) are life-
science and medical preprint servers that share the identical Rxivist-style
public API hosted at ``https://api.biorxiv.org``. The ``server`` parameter
(``"biorxiv"`` or ``"medrxiv"``) selects which corpus is queried — mirroring
the ``source`` parameter precedent in ``sovietrxiv_client``.

**This is NOT a free-text search API.** bioRxiv's public API exposes no
query/search parameter at all: a call to the ``details`` endpoint returns
*every* preprint posted within a given date interval, paginated 100-at-a-time
via an integer ``cursor``. ``search_biorxiv`` is therefore a **date-window-
then-filter** engine, not true full-text search: it walks the date window
page by page and keeps only the items where every whitespace-split query
term appears (case-insensitively) in the concatenated title + abstract —
exactly the approach already verified working in the reference connector at
``infrastructure/search/connectors/impl/biorxiv.py``. Callers should not
expect ranked-by-relevance results, and a query with very common terms over
a wide date range may need many pages before ``max_results`` matches are
found (or the page cap below is hit first).

Response shape for one page::

    {
        "collection": [
            {
                "doi": "10.1101/2020.01.01.000001",
                "title": "...",
                "authors": "Last A;Last B",  # semicolon-separated string
                "date": "2020-01-01",
                "abstract": "...",
                "category": "...",
                "server": "biorxiv",
            },
            ...
        ],
        "messages": [...],
    }

Pagination: the cursor is a 0-based integer offset advanced by 100 (the
API's fixed page size) after each request. A page returning fewer than 100
raw items is the last page. To bound worst-case latency against a query
whose terms never/rarely match within the default (2013-2099) window, the
walk hard-stops after ``BIORXIV_MAX_PAGES`` (20) pages - 2000 raw items -
even if fewer than ``max_results`` matches have been found. This is a
deliberate, documented constraint, not a bug.

All functions accept an injectable ``base_url`` for testing with
pytest-httpserver, reuse ``literature.http.request_with_retry`` for the page
GET, and never raise to the caller: any HTTP/parse/timeout error is logged
as a warning and the matches collected so far are returned (``[]`` if none).

API reference: https://api.biorxiv.org
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import requests

from literature.http import request_with_retry

from .models import Author, Paper

logger = logging.getLogger(__name__)

# Default API base URL. The per-page details endpoint is
# f"{base_url}/details/{server}/{interval}/{cursor}/json".
BIORXIV_API_URL = "https://api.biorxiv.org"

# The API returns up to 100 items per page; this is fixed by the server, not
# a caller-tunable request parameter.
BIORXIV_PAGE_SIZE = 100

# Hard cap on pages walked per search (2000 raw items) — bounds worst-case
# latency for a date-window-then-filter query over the default multi-decade
# window. Deliberate, documented constraint (see module docstring).
BIORXIV_MAX_PAGES = 20

# Default date window: bioRxiv's actual launch year (2013) through a far-
# future date. medRxiv launched in 2019, but using the same 2013 lower bound
# is harmless — medRxiv simply has no items before its own launch.
BIORXIV_YEAR_MIN = 2013
BIORXIV_YEAR_MAX = 2099


def _extract_year(date_str: str | None) -> int | None:
    """Extract the publication year from an ISO date string (YYYY-MM-DD).

    Args:
        date_str: ISO date string or None.

    Returns:
        Year as an int, or None if it cannot be resolved.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    year_part = date_str[:4]
    try:
        return int(year_part)
    except ValueError:
        return None


def _extract_authors(authors_raw: object) -> list[Author]:
    """Split a bioRxiv ``authors`` field into individual Author objects.

    bioRxiv/medRxiv return authors as a single semicolon-separated string
    (e.g. ``"Smith J;Doe A"``), not a list like most other engines. Empty or
    whitespace-only parts are dropped.

    Args:
        authors_raw: The raw ``authors`` field (expected a string).

    Returns:
        List of Author objects (possibly empty).
    """
    if not isinstance(authors_raw, str):
        return []
    return [Author(name=part.strip()) for part in authors_raw.split(";") if part.strip()]


def _build_pdf_url(server: str, doi: str | None) -> str | None:
    """Build the conventional bioRxiv/medRxiv full-text PDF URL for a DOI.

    Args:
        server: ``"biorxiv"`` or ``"medrxiv"``.
        doi: The preprint's DOI, if present.

    Returns:
        The PDF URL, or None when no DOI is available.
    """
    if not doi:
        return None
    return f"https://www.{server}.org/content/{doi}v1.full.pdf"


def _parse_biorxiv_paper(item: dict, server: str) -> Paper:
    """Parse a single bioRxiv/medRxiv ``collection`` entry into a Paper.

    Args:
        item: Dictionary representing one collection entry.
        server: ``"biorxiv"`` or ``"medrxiv"`` — recorded as
            ``full_text_source`` (this also doubles as the ``is_preprint``
            hint the ``Paper.is_preprint`` property already checks for).

    Returns:
        Paper populated from the bioRxiv/medRxiv fields. Pure: no I/O.
    """
    title = item.get("title") or ""
    abstract = item.get("abstract") or ""
    authors = _extract_authors(item.get("authors"))
    year = _extract_year(item.get("date"))
    doi = item.get("doi") or None

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        venue=None,
        pdf_url=_build_pdf_url(server, doi),
        full_text_source=server,
    )


def _matches_query(item: dict, terms: list[str]) -> bool:
    """Check whether every query term appears in an item's title + abstract.

    Case-insensitive substring match, mirroring the reference connector's
    client-side filter (the bioRxiv API itself has no free-text search).
    An empty ``terms`` list matches every item (vacuously true).

    Args:
        item: Raw collection entry (title/abstract fields).
        terms: Lower-cased, whitespace-split query terms.

    Returns:
        True if all terms are present in the concatenated text.
    """
    text = f"{item.get('title', '') or ''} {item.get('abstract', '') or ''}".lower()
    return all(term in text for term in terms)


def search_biorxiv(
    query: str,
    *,
    max_results: int = 100,
    base_url: str = BIORXIV_API_URL,
    session: requests.Session | None = None,
    delay_override: Callable[[float], None] | None = None,
    server: str = "biorxiv",
) -> list[Paper]:
    """Search bioRxiv/medRxiv for papers matching a free-text query.

    Not true full-text search: walks the default (2013-2099) date window
    page by page (100 raw items per page, cursor-based) and keeps only items
    where every whitespace-split query term appears case-insensitively in
    the concatenated title + abstract. Stops when ``max_results`` matches
    have been collected, a page returns fewer than ``BIORXIV_PAGE_SIZE`` raw
    items (the last page), or ``BIORXIV_MAX_PAGES`` pages have been walked
    (whichever comes first). Graceful by contract: any network error,
    non-200 status, or malformed payload is logged and the matches collected
    so far are returned (``[]`` if none) - this function never raises.

    Args:
        query: Free-text query. Split on whitespace into required terms;
            an empty query matches every item in the window.
        max_results: Maximum number of matching results to retrieve.
        base_url: API base URL (injectable for testing). The per-page
            endpoint is ``f"{base_url}/details/{server}/{interval}/{cursor}/json"``.
        session: Optional requests.Session for connection reuse.
        delay_override: Optional sleep function (test injection), forwarded
            to ``request_with_retry``.
        server: ``"biorxiv"`` or ``"medrxiv"`` — selects which preprint
            corpus is queried.

    Returns:
        List of Paper objects (possibly empty).
    """
    http = session or requests.Session()
    matches: list[Paper] = []
    terms = [t.lower() for t in query.split() if t.strip()]
    interval = f"{BIORXIV_YEAR_MIN}-01-01/{BIORXIV_YEAR_MAX}-12-31"

    try:
        cursor = 0
        page_num = 0

        while len(matches) < max_results and page_num < BIORXIV_MAX_PAGES:
            page_num += 1
            url = f"{base_url}/details/{server}/{interval}/{cursor}/json"

            logger.info(
                "bioRxiv/%s page %d: fetching cursor=%d (matches so far: %d, target: %d)",
                server,
                page_num,
                cursor,
                len(matches),
                max_results,
            )

            try:
                response = request_with_retry(http, "GET", url, delay_override=delay_override)
                payload = response.json()
                # Parse inside the try so the "never raises" contract also
                # covers any payload-shape surprise during extraction — not
                # just the network/JSON-decode boundary.
                if not isinstance(payload, dict):
                    break
                items = payload.get("collection", [])
                if not isinstance(items, list):
                    break
            except (requests.RequestException, ValueError) as e:
                # RequestException covers transport + retried HTTP errors;
                # ValueError covers a malformed JSON body (requests'
                # JSONDecodeError subclasses both). Either way: stop and
                # return what we have rather than raising to the caller.
                logger.warning("bioRxiv/%s search stopped early: %s", server, e)
                break

            raw_count = len(items)
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not _matches_query(item, terms):
                    continue
                matches.append(_parse_biorxiv_paper(item, server))
                if len(matches) >= max_results:
                    break

            logger.info(
                "bioRxiv/%s page %d: %d raw items, %d cumulative matches",
                server,
                page_num,
                raw_count,
                len(matches),
            )

            if raw_count < BIORXIV_PAGE_SIZE:
                logger.info("bioRxiv/%s: last page reached (raw_count < page size)", server)
                break

            cursor += BIORXIV_PAGE_SIZE

        if len(matches) < max_results and page_num >= BIORXIV_MAX_PAGES:
            logger.warning(
                "bioRxiv/%s search stopped: hit the %d-page cap before finding %d matches",
                server,
                BIORXIV_MAX_PAGES,
                max_results,
            )
    finally:
        if session is None:
            http.close()

    logger.info(
        "bioRxiv/%s search complete: %d matches for query %r",
        server,
        len(matches),
        query[:80],
    )
    return matches[:max_results]
