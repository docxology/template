"""Semantic Scholar Graph API client.

Provides functions to search papers, retrieve paper details, and
fetch citation relationships via the Semantic Scholar API. All
functions accept an injectable base_url for testing with pytest-httpserver.

Includes pagination via offset, retry with exponential backoff and jitter
on 429 rate-limit responses, and structured logging throughout.

API reference: https://api.semanticscholar.org/api-docs/graph
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

import requests

from .models import Author, Citation, Paper

logger = logging.getLogger(__name__)

# Default API base URL
S2_API_URL = "https://api.semanticscholar.org/graph/v1"

# Fields we request from the API
PAPER_FIELDS = "title,abstract,authors,year,externalIds,citationCount,venue,references,isOpenAccess,openAccessPdf"
CITATION_FIELDS = "title,authors,year,externalIds"

# Retry settings
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 10.0

# Pagination
S2_PAGE_SIZE = 100


def _parse_s2_paper(data: dict) -> Paper:
    """Parse a Semantic Scholar paper JSON object into a Paper.

    Args:
        data: Dictionary from the S2 API representing a paper.

    Returns:
        Paper object populated from the API data.
    """
    # Authors
    authors = []
    for a in data.get("authors", []) or []:
        name = a.get("name") or a.get("authorId", "Unknown")
        authors.append(Author(name=name))

    # External IDs
    ext_ids = data.get("externalIds") or {}
    doi = ext_ids.get("DOI")
    arxiv_id = ext_ids.get("ArXiv")

    # References (list of paper IDs)
    references = []
    for ref in data.get("references", []) or []:
        if isinstance(ref, dict) and ref.get("paperId"):
            references.append(f"s2:{ref['paperId']}")
        elif isinstance(ref, str):
            references.append(f"s2:{ref}")

    # Open access and PDF URL
    is_open_access = data.get("isOpenAccess")
    pdf_url = None
    full_text_source = None
    oa_pdf = data.get("openAccessPdf")
    if isinstance(oa_pdf, dict) and oa_pdf.get("url"):
        pdf_url = oa_pdf["url"]
        full_text_source = "semantic_scholar"

    return Paper(
        title=data.get("title", ""),
        abstract=data.get("abstract") or "",
        authors=authors,
        year=data.get("year"),
        doi=doi,
        arxiv_id=arxiv_id,
        s2_id=data.get("paperId"),
        venue=data.get("venue") or None,
        citation_count=data.get("citationCount") or 0,
        references=references,
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        full_text_source=full_text_source,
    )


def _request_with_retry(
    http: requests.Session,
    url: str,
    params: dict,
    max_retries: int = MAX_RETRIES,
    delay_override: Callable[[float], None] | None = None,
) -> requests.Response:
    """Make an HTTP GET request with retry on 429 rate-limit errors.

    Uses exponential backoff with jitter to avoid thundering herd.

    Args:
        http: requests.Session for the request.
        url: URL to request.
        params: Query parameters.
        max_retries: Maximum number of retry attempts.
        delay_override: Optional sleep function (test injection).

    Returns:
        Successful response object.

    Raises:
        requests.HTTPError: If all retries are exhausted or a non-429 error occurs.
    """
    sleep_fn = delay_override or time.sleep
    response = None
    for attempt in range(max_retries + 1):
        response = http.get(url, params=params, timeout=30)
        if response.status_code == 429:
            if attempt == max_retries:
                break
            wait = min(10.0, RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 1))
            logger.warning(
                "S2 rate-limited (429), retry %d/%d after %.1fs",
                attempt + 1,
                max_retries,
                wait,
            )
            sleep_fn(wait)
            continue
        response.raise_for_status()
        return response

    # All retries exhausted
    logger.error("S2 rate-limit retries exhausted after %d attempts", max_retries)
    if response is not None:
        response.raise_for_status()
    raise requests.HTTPError("S2 retries exhausted")  # pragma: no cover


def search_semantic_scholar(
    query: str,
    max_results: int = 100,
    base_url: str = S2_API_URL,
    session: requests.Session | None = None,
    delay_override: Callable[[float], None] | None = None,
) -> list[Paper]:
    """Search Semantic Scholar for papers matching a query.

    Automatically paginates via offset when max_results exceeds the
    per-page limit (100 per page). Retries on 429 rate-limit errors
    with exponential backoff and jitter.

    Args:
        query: Free-text search query.
        max_results: Maximum number of results to retrieve.
        base_url: API base URL (injectable for testing).
        session: Optional requests.Session for connection reuse.

    Returns:
        List of Paper objects from the search results.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status after retries.
    """
    http = session or requests.Session()
    all_papers: list[Paper] = []

    try:
        offset = 0
        page_num = 0

        while offset < max_results:
            page_size = min(S2_PAGE_SIZE, max_results - offset)
            page_num += 1

            params = {
                "query": query,
                "offset": offset,
                "limit": page_size,
                "fields": PAPER_FIELDS,
            }

            logger.info(
                "S2 page %d: fetching %d results (offset %d, target %d)",
                page_num,
                page_size,
                offset,
                max_results,
            )

            try:
                response = _request_with_retry(
                    http,
                    f"{base_url}/paper/search",
                    params,
                    delay_override=delay_override,
                )
                result = response.json()
            except requests.HTTPError as e:
                logger.warning("S2 search stopped early due to HTTP error (rate limit): %s", e)
                break

            page_papers = [_parse_s2_paper(item) for item in result.get("data", [])]

            if not page_papers:
                logger.info(
                    "S2 page %d: no more results (total fetched: %d)",
                    page_num,
                    len(all_papers),
                )
                break

            all_papers.extend(page_papers)
            logger.info(
                "S2 page %d: fetched %d papers (total: %d)",
                page_num,
                len(page_papers),
                len(all_papers),
            )

            # Check if S2 reports a total and we've reached it
            total_available = result.get("total", max_results)
            if offset + page_size >= total_available:
                logger.info("S2: all available results fetched (%d total)", total_available)
                break

            if len(page_papers) < page_size:
                logger.info("S2: received partial page, all results fetched")
                break

            offset += page_size
    finally:
        if session is None:
            http.close()

    logger.info(
        "S2 search complete: %d total papers for query '%s'",
        len(all_papers),
        query[:80],
    )
    return all_papers


def get_paper_details(
    paper_id: str,
    base_url: str = S2_API_URL,
    session: requests.Session | None = None,
) -> Paper:
    """Retrieve detailed metadata for a single paper by ID.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or arXiv ID.
        base_url: API base URL (injectable for testing).
        session: Optional requests.Session for connection reuse.

    Returns:
        Paper object with full metadata.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status (e.g. 404).
    """
    url = f"{base_url}/paper/{paper_id}"
    params = {"fields": PAPER_FIELDS}

    http = session or requests.Session()
    try:
        response = _request_with_retry(http, url, params)
    finally:
        if session is None:
            http.close()

    logger.debug("Retrieved paper details for %s", paper_id)
    return _parse_s2_paper(response.json())


def get_citations(
    paper_id: str,
    max_results: int = 100,
    base_url: str = S2_API_URL,
    session: requests.Session | None = None,
) -> list[Citation]:
    """Retrieve papers that cite the given paper.

    Args:
        paper_id: Semantic Scholar paper ID.
        max_results: Maximum number of citations to retrieve.
        base_url: API base URL (injectable for testing).
        session: Optional requests.Session for connection reuse.

    Returns:
        List of Citation objects representing citing papers.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status.
    """
    url = f"{base_url}/paper/{paper_id}/citations"
    params = {
        "limit": min(max_results, 100),
        "fields": CITATION_FIELDS,
    }

    http = session or requests.Session()
    try:
        response = _request_with_retry(http, url, params)
    finally:
        if session is None:
            http.close()

    result = response.json()
    citations: list[Citation] = []
    target_id = f"s2:{paper_id}"

    for item in result.get("data", []):
        citing_paper = item.get("citingPaper", {})
        citing_id = citing_paper.get("paperId")
        if citing_id:
            context = item.get("contexts", [None])
            context_text = context[0] if isinstance(context, list) and context else None
            citations.append(
                Citation(
                    source_id=f"s2:{citing_id}",
                    target_id=target_id,
                    context=context_text,
                )
            )

    logger.info("Retrieved %d citations for paper %s", len(citations), paper_id)
    return citations
