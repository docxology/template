"""arXiv Atom API search client.

Provides functions to query the arXiv API and parse Atom XML responses
into Paper objects. Supports injectable base_url for testing with
pytest-httpserver.

The arXiv API returns Atom XML. We parse it using xml.etree.ElementTree.
Rate limiting is enforced with a configurable sleep between requests.
Pagination is handled automatically for large result sets.
"""

from __future__ import annotations

import logging
import random
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date

import requests
from defusedxml.ElementTree import fromstring as _safe_fromstring

from .models import Author, Paper

logger = logging.getLogger(__name__)

# arXiv Atom XML namespaces
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"

# Default API endpoint
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Rate limit sleep in seconds (arXiv requests 3s between calls)
DEFAULT_RATE_LIMIT_SECONDS = 3.0

# Pagination batch size (arXiv API max per page)
ARXIV_PAGE_SIZE = 100

# Retry settings
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 3.0


def parse_arxiv_response(xml_text: str) -> list[Paper]:
    """Parse arXiv Atom XML response into Paper objects.

    Args:
        xml_text: Raw XML string from the arXiv API.

    Returns:
        List of Paper objects parsed from the Atom feed entries.

    Raises:
        ET.ParseError: If the XML is malformed.
    """
    root = _safe_fromstring(xml_text)
    papers: list[Paper] = []

    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        paper = _parse_entry(entry)
        if paper is not None:
            papers.append(paper)

    logger.debug("Parsed %d papers from arXiv XML response", len(papers))
    return papers


def _parse_entry(entry: ET.Element) -> Paper | None:
    """Parse a single Atom entry element into a Paper.

    Args:
        entry: An Atom <entry> XML element.

    Returns:
        Paper object, or None if the entry lacks a title.
    """
    title_elem = entry.find(f"{{{ATOM_NS}}}title")
    if title_elem is None or title_elem.text is None:
        return None

    title = " ".join(title_elem.text.strip().split())

    # Abstract / summary
    summary_elem = entry.find(f"{{{ATOM_NS}}}summary")
    abstract = ""
    if summary_elem is not None and summary_elem.text:
        abstract = " ".join(summary_elem.text.strip().split())

    # Authors
    authors: list[Author] = []
    for author_elem in entry.findall(f"{{{ATOM_NS}}}author"):
        name_elem = author_elem.find(f"{{{ATOM_NS}}}name")
        if name_elem is not None and name_elem.text:
            affiliation_elem = author_elem.find(f"{{{ARXIV_NS}}}affiliation")
            affiliation = None
            if affiliation_elem is not None and affiliation_elem.text:
                affiliation = affiliation_elem.text.strip()
            authors.append(Author(name=name_elem.text.strip(), affiliation=affiliation))

    # Publication date
    published_elem = entry.find(f"{{{ATOM_NS}}}published")
    pub_date: date | None = None
    year: int | None = None
    if published_elem is not None and published_elem.text:
        date_str = published_elem.text.strip()
        try:
            pub_date = date.fromisoformat(date_str[:10])
            year = pub_date.year
        except ValueError:
            pass

    # arXiv ID from the <id> element
    arxiv_id: str | None = None
    id_elem = entry.find(f"{{{ATOM_NS}}}id")
    if id_elem is not None and id_elem.text:
        raw_id = id_elem.text.strip()
        # Extract ID from URL like http://arxiv.org/abs/2201.06387v1
        if "/abs/" in raw_id:
            arxiv_id = raw_id.split("/abs/")[-1]
            # Strip version suffix for canonical form
            if "v" in arxiv_id:
                arxiv_id = arxiv_id.rsplit("v", 1)[0]

    # DOI from arxiv namespace
    doi: str | None = None
    doi_elem = entry.find(f"{{{ARXIV_NS}}}doi")
    if doi_elem is not None and doi_elem.text:
        doi = doi_elem.text.strip()

    # All arXiv papers are open access with PDF available
    pdf_url = None
    if arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        arxiv_id=arxiv_id,
        publication_date=pub_date,
        pdf_url=pdf_url,
        is_open_access=True,
        full_text_source="arxiv" if arxiv_id else None,
    )


def _fetch_page(
    query: str,
    start: int,
    page_size: int,
    base_url: str,
    session: requests.Session,
    rate_limit_seconds: float,
    delay_override: Callable[[float], None] | None = None,
) -> list[Paper]:
    """Fetch a single page of results from the arXiv API with retry.

    Args:
        query: arXiv search query string.
        start: Starting index for pagination.
        page_size: Number of results to request.
        base_url: API endpoint URL.
        session: requests.Session for connection reuse.
        rate_limit_seconds: Seconds to sleep before making the request.
        delay_override: Optional sleep function (test injection).

    Returns:
        List of Paper objects from the page.

    Raises:
        requests.HTTPError: If all retries are exhausted.
    """
    sleep_fn = delay_override or time.sleep
    params: dict[str, str | int | float] = {
        "search_query": query,
        "start": start,
        "max_results": page_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    for attempt in range(MAX_RETRIES):
        if rate_limit_seconds > 0:
            sleep_fn(rate_limit_seconds)

        try:
            response = session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            return parse_arxiv_response(response.text)
        except requests.HTTPError as e:
            wait = RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 1)
            logger.warning(
                "arXiv HTTP error (attempt %d/%d): %s — retrying in %.1fs",
                attempt + 1,
                MAX_RETRIES,
                e,
                wait,
            )
            if attempt < MAX_RETRIES - 1:
                sleep_fn(wait)
            else:
                raise

    return []  # pragma: no cover


def search_arxiv(
    query: str,
    max_results: int = 100,
    base_url: str = ARXIV_API_URL,
    session: requests.Session | None = None,
    rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
    delay_override: Callable[[float], None] | None = None,
) -> list[Paper]:
    """Search the arXiv API for papers matching a query.

    Automatically paginates when max_results exceeds the per-page limit
    (100 results per page). Each page request respects rate limits and
    retries on HTTP errors with exponential backoff.

    Args:
        query: arXiv search query string (e.g., 'all:"modafinil"').
        max_results: Maximum number of results to retrieve.
        base_url: API endpoint URL (injectable for testing).
        session: Optional requests.Session for connection reuse.
        rate_limit_seconds: Seconds to sleep before making each request.

    Returns:
        List of Paper objects from the search results.

    Raises:
        requests.HTTPError: If the API returns a non-200 status after retries.
        requests.ConnectionError: If the API is unreachable.
    """
    http = session or requests.Session()
    all_papers: list[Paper] = []

    try:
        start = 0
        page_num = 0
        while start < max_results:
            page_size = min(ARXIV_PAGE_SIZE, max_results - start)
            page_num += 1

            logger.info(
                "arXiv page %d: fetching %d results (offset %d, target %d)",
                page_num,
                page_size,
                start,
                max_results,
            )

            page_papers = _fetch_page(
                query,
                start,
                page_size,
                base_url,
                http,
                rate_limit_seconds,
                delay_override=delay_override,
            )

            if not page_papers:
                logger.info(
                    "arXiv page %d: no more results (total fetched: %d)",
                    page_num,
                    len(all_papers),
                )
                break

            all_papers.extend(page_papers)
            logger.info(
                "arXiv page %d: fetched %d papers (total: %d)",
                page_num,
                len(page_papers),
                len(all_papers),
            )

            # If we received fewer results than requested, we've reached the end
            if len(page_papers) < page_size:
                logger.info("arXiv: received partial page, all results fetched")
                break

            start += page_size
    finally:
        if session is None:
            http.close()

    logger.info(
        "arXiv search complete: %d total papers for query '%s'",
        len(all_papers),
        query[:80],
    )
    return all_papers
