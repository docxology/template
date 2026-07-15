"""Crossref REST API client.

Provides a keyless engine adapter over the Crossref ``works`` endpoint
(https://api.crossref.org/works?query=...). Mirrors the shape of the sibling
adapters (``arxiv_client``, ``openalex_client``, ``semantic_scholar``): a
module-level ``CROSSREF_API_URL`` constant, a pure ``_parse_crossref_work``
parser, and a ``search_crossref`` entry point with ``rows``/``offset``
pagination and a polite ``mailto`` parameter.

The Crossref ``works`` response wraps results as
``{"message": {"items": [ ...work objects... ]}}``. Work objects expose
``DOI``, ``title`` (list), ``abstract`` (JATS XML), ``author`` (list of
``{given, family, affiliation}``), ``issued.date-parts``,
``container-title`` (list), ``is-referenced-by-count``, and ``URL``.

All functions accept an injectable ``base_url`` for testing with
pytest-httpserver. ``search_crossref`` is graceful: on any network error or
non-200 status it logs and returns the results collected so far (``[]`` if
none) and never raises to the caller.

API reference: https://api.crossref.org/swagger-ui/index.html
"""

from __future__ import annotations

import html
import logging
import random
import re
import time
from typing import Callable, Optional

import requests

from .models import Author, Paper

logger = logging.getLogger(__name__)

# Default API base URL (the works endpoint is f"{base_url}/works").
CROSSREF_API_URL = "https://api.crossref.org"

# Pagination settings. Crossref permits up to 1000 rows per request.
CROSSREF_PAGE_SIZE = 1000

# Retry settings (mirrors openalex_client).
MAX_RETRIES = 1
RETRY_BASE_SECONDS = 10.0

# Matches any XML/JATS tag, e.g. "<jats:p>" or "</jats:italic>".
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_jats(raw: str) -> str:
    """Strip JATS/XML markup from a Crossref abstract.

    Crossref stores abstracts as JATS XML (e.g. ``<jats:p>Text</jats:p>``).
    This removes all tags, unescapes XML/HTML entities, and collapses runs of
    whitespace into single spaces.

    Args:
        raw: Raw abstract string, possibly containing JATS markup.

    Returns:
        Plain-text abstract with markup removed and whitespace normalized.
    """
    if not raw:
        return ""
    without_tags = _TAG_RE.sub(" ", raw)
    unescaped = html.unescape(without_tags)
    return " ".join(unescaped.split())


def _extract_year(item: dict) -> Optional[int]:
    """Extract the publication year from a Crossref work's ``issued`` field.

    Crossref encodes dates as ``{"date-parts": [[year, month, day]]}``. The
    ``date-parts`` list may be missing, empty, or contain an empty inner list
    (``[[]]``) when no date is known.

    Args:
        item: Crossref work object.

    Returns:
        Year as an int, or None if it cannot be resolved.
    """
    issued = item.get("issued")
    if not isinstance(issued, dict):
        return None
    date_parts = issued.get("date-parts")
    if not isinstance(date_parts, list) or not date_parts:
        return None
    first = date_parts[0]
    if not isinstance(first, list) or not first:
        return None
    year = first[0]
    if isinstance(year, int):
        return year
    return None


def _extract_authors(item: dict) -> list[Author]:
    """Build the author list from a Crossref work's ``author`` array.

    Each Crossref author has optional ``given``/``family`` (personal) or
    ``name`` (organizational). Affiliation comes from
    ``author[i].affiliation[0].name`` when present. Authors with no resolvable
    name are skipped.

    Args:
        item: Crossref work object.

    Returns:
        List of Author objects (possibly empty).
    """
    authors: list[Author] = []
    for entry in item.get("author", []) or []:
        if not isinstance(entry, dict):
            continue

        org_name = entry.get("name")
        if org_name:
            name = str(org_name).strip()
        else:
            given = (entry.get("given") or "").strip()
            family = (entry.get("family") or "").strip()
            name = f"{given} {family}".strip()

        if not name:
            continue

        affiliation: Optional[str] = None
        affil_list = entry.get("affiliation")
        if isinstance(affil_list, list) and affil_list:
            first_affil = affil_list[0]
            if isinstance(first_affil, dict) and first_affil.get("name"):
                affiliation = first_affil["name"]

        authors.append(Author(name=name, affiliation=affiliation))
    return authors


def _first_str(value: object) -> Optional[str]:
    """Return the first non-empty string from a Crossref list-valued field.

    Crossref returns ``title`` and ``container-title`` as lists of strings.

    Args:
        value: The raw field value (expected to be a list).

    Returns:
        The first truthy string element, or None.
    """
    if isinstance(value, list):
        for element in value:
            if element:
                return str(element)
    return None


def _parse_crossref_work(item: dict) -> Paper:
    """Parse a single Crossref ``message.items`` object into a Paper.

    Args:
        item: Dictionary representing one Crossref work.

    Returns:
        Paper populated from the Crossref fields. Pure: performs no I/O.
    """
    title = _first_str(item.get("title")) or ""
    abstract = _strip_jats(item.get("abstract") or "")
    authors = _extract_authors(item)
    year = _extract_year(item)
    doi = item.get("DOI")
    venue = _first_str(item.get("container-title"))

    citation_count = item.get("is-referenced-by-count")
    if not isinstance(citation_count, int):
        citation_count = 0

    url = item.get("URL")
    pdf_url = url if url else None

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        venue=venue,
        citation_count=citation_count,
        pdf_url=pdf_url,
    )


def _request_with_retry(
    http: requests.Session,
    url: str,
    params: dict,
    max_retries: int = MAX_RETRIES,
    delay_override: Optional[Callable[[float], None]] = None,
) -> requests.Response:
    """Make an HTTP GET request with bounded retry on transient HTTP errors.

    Uses exponential backoff with jitter, matching the sibling clients.

    Args:
        http: requests.Session for the request.
        url: URL to request.
        params: Query parameters.
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
        response = http.get(url, params=params, timeout=30)
        if response.status_code in (429, 500, 502, 503, 504):
            wait = min(10.0, RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 1))
            logger.warning(
                "Crossref HTTP %d (attempt %d/%d) — retrying in %.1fs",
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
    logger.error("Crossref retries exhausted after %d attempts", max_retries)
    if response is not None:
        response.raise_for_status()
    raise requests.HTTPError("Crossref retries exhausted")  # pragma: no cover


def search_crossref(
    query: str,
    *,
    base_url: str = CROSSREF_API_URL,
    max_results: int = 100,
    mailto: Optional[str] = None,
    rows_per_page: int = CROSSREF_PAGE_SIZE,
    session: Optional[requests.Session] = None,
    delay_override: Optional[Callable[[float], None]] = None,
) -> list[Paper]:
    """Search Crossref for works matching a free-text query.

    Pages through results with a fixed ``rows`` window and an advancing
    ``offset`` until ``max_results`` is reached or the API stops returning full
    pages. Graceful by contract: any network error or non-200 status is logged
    and the results collected so far are returned (``[]`` if none) — this
    function never raises for transport or HTTP problems.

    Args:
        query: Free-text search query.
        base_url: API base URL (injectable for testing). The ``works`` endpoint
            is ``f"{base_url}/works"``.
        max_results: Maximum number of results to retrieve.
        mailto: Optional contact email for Crossref's polite pool. Included as a
            query parameter only when provided.
        rows_per_page: Number of rows requested per page. Defaults to the
            Crossref maximum; lower values force multi-page traversal. The final
            page may request fewer rows so the total never exceeds max_results.
        session: Optional requests.Session for connection reuse.
        delay_override: Optional sleep function (test injection).

    Returns:
        List of Paper objects (possibly empty).
    """
    http = session or requests.Session()
    all_papers: list[Paper] = []
    works_url = f"{base_url}/works"
    window = max(1, min(rows_per_page, CROSSREF_PAGE_SIZE))

    try:
        offset = 0
        page_num = 0

        while len(all_papers) < max_results:
            page_size = min(window, max_results - len(all_papers))
            page_num += 1

            params: dict = {
                "query": query,
                "rows": page_size,
                "offset": offset,
            }
            if mailto:
                params["mailto"] = mailto

            logger.info(
                "Crossref page %d: fetching %d results at offset %d (total so far: %d, target: %d)",
                page_num,
                page_size,
                offset,
                len(all_papers),
                max_results,
            )

            try:
                response = _request_with_retry(
                    http,
                    works_url,
                    params,
                    delay_override=delay_override,
                )
                payload = response.json()
                # Parse inside the try so the "never raises" contract also covers
                # any payload-shape surprise during extraction — not just the
                # network/JSON-decode boundary.
                message = payload.get("message", {}) if isinstance(payload, dict) else {}
                items = message.get("items", []) if isinstance(message, dict) else []
                page_papers = [_parse_crossref_work(item) for item in items if isinstance(item, dict)]
            except (requests.RequestException, ValueError) as e:
                # RequestException covers transport + retried HTTP errors;
                # ValueError covers a malformed JSON body (requests'
                # JSONDecodeError subclasses both). Either way: stop and return
                # what we have rather than raising to the caller.
                logger.warning("Crossref search stopped early: %s", e)
                break

            if not page_papers:
                logger.info(
                    "Crossref page %d: no more results (total fetched: %d)",
                    page_num,
                    len(all_papers),
                )
                break

            all_papers.extend(page_papers)
            logger.info(
                "Crossref page %d: fetched %d papers (total: %d)",
                page_num,
                len(page_papers),
                len(all_papers),
            )

            if len(page_papers) < page_size:
                logger.info("Crossref: received partial page, all results fetched")
                break

            offset += page_size
    finally:
        if session is None:
            http.close()

    logger.info(
        "Crossref search complete: %d total papers for query '%s'",
        len(all_papers),
        query[:80],
    )
    return all_papers[:max_results]
