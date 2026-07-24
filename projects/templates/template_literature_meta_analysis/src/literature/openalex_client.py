"""OpenAlex API client.

Provides functions to search works and retrieve work details via the
OpenAlex API. All functions accept an injectable base_url for testing
with pytest-httpserver.

Includes cursor-based pagination for comprehensive result retrieval,
retry with exponential backoff on HTTP errors, and structured logging.

API reference: https://docs.openalex.org/
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional, Callable

import requests

from .models import Author, Paper

logger = logging.getLogger(__name__)

# Default API base URL
OPENALEX_API_URL = "https://api.openalex.org"

# Pagination settings
OPENALEX_PAGE_SIZE = 200  # OpenAlex max per_page

# Retry settings
MAX_RETRIES = 1
RETRY_BASE_SECONDS = 10.0


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct full abstract text from OpenAlex inverted index format.

    OpenAlex stores abstracts as an inverted index mapping each word to a
    list of positional indices. This function reverses that to produce
    readable text.

    Args:
        inverted_index: Dictionary mapping words to position lists.
            Example: {"The": [0], "free": [1], "energy": [2]}

    Returns:
        Reconstructed abstract as a single string.
    """
    if not inverted_index:
        return ""

    # Build list of (position, word) tuples
    position_words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            position_words.append((pos, word))

    # Sort by position and join
    position_words.sort(key=lambda x: x[0])
    return " ".join(word for _, word in position_words)


def _parse_openalex_work(data: dict) -> Paper:
    """Parse an OpenAlex work JSON object into a Paper.

    Args:
        data: Dictionary from the OpenAlex API representing a work.

    Returns:
        Paper object populated from the API data.
    """
    # Title
    title = data.get("display_name") or data.get("title") or ""

    # Abstract
    abstract = ""
    inverted_index = data.get("abstract_inverted_index")
    if inverted_index:
        abstract = _reconstruct_abstract(inverted_index)

    # Authors from authorships
    authors: list[Author] = []
    for authorship in data.get("authorships", []) or []:
        author_data = authorship.get("author", {})
        name = author_data.get("display_name", "")
        if name:
            # Extract first institution if available
            institutions = authorship.get("institutions", [])
            affiliation = None
            if institutions and institutions[0].get("display_name"):
                affiliation = institutions[0]["display_name"]
            orcid = author_data.get("orcid")
            if orcid and orcid.startswith("https://orcid.org/"):
                orcid = orcid.replace("https://orcid.org/", "")
            authors.append(Author(name=name, affiliation=affiliation, orcid=orcid))

    # DOI: OpenAlex prefixes with https://doi.org/
    doi = data.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    # OpenAlex ID
    openalex_id = data.get("id")

    # Year
    year = data.get("publication_year")

    # Citation count
    citation_count = data.get("cited_by_count") or 0

    # Venue / primary location
    venue = None
    primary_location = data.get("primary_location")
    if primary_location:
        source = primary_location.get("source")
        if source:
            venue = source.get("display_name")

    # References from referenced_works
    references = []
    for ref_url in data.get("referenced_works", []) or []:
        if isinstance(ref_url, str):
            # Extract the OpenAlex work ID from the URL
            ref_id = ref_url.split("/")[-1] if "/" in ref_url else ref_url
            references.append(f"openalex:{ref_id}")

    # Open access status and PDF URL
    oa_data = data.get("open_access") or {}
    is_open_access = oa_data.get("is_oa")
    pdf_url = None
    full_text_source = None

    # Try oa_url first, then best_oa_location for PDF
    oa_url = oa_data.get("oa_url")
    if oa_url and oa_url.endswith(".pdf"):
        pdf_url = oa_url

    best_oa = data.get("best_oa_location") or {}
    if not pdf_url and best_oa.get("pdf_url"):
        pdf_url = best_oa["pdf_url"]
    elif not pdf_url and best_oa.get("url"):
        # Landing page URL as fallback (not direct PDF)
        pass

    license_value = best_oa.get("license") or oa_data.get("license")
    license_name = str(license_value) if license_value else None
    license_url_value = best_oa.get("license_id") or oa_data.get("license_id")
    license_url = str(license_url_value) if license_url_value else None

    # Determine full_text_source from location type
    if pdf_url:
        source_obj = best_oa.get("source") or {}
        source_type = source_obj.get("type", "")
        if source_type == "repository":
            full_text_source = "repository"
        elif source_type == "journal":
            full_text_source = "publisher"
        else:
            full_text_source = "openalex"

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        openalex_id=openalex_id,
        venue=venue,
        citation_count=citation_count,
        references=references,
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        full_text_source=full_text_source,
        license=license_name,
        license_url=license_url,
    )


def _request_with_retry(
    http: requests.Session,
    url: str,
    params: dict,
    max_retries: int = MAX_RETRIES,
    delay_override: Optional[Callable[[float], None]] = None,
) -> requests.Response:
    """Make an HTTP GET request with retry on HTTP errors.

    Uses exponential backoff with jitter.

    Args:
        http: requests.Session for the request.
        url: URL to request.
        params: Query parameters.
        max_retries: Maximum number of retry attempts.
        delay_override: Optional sleep function (test injection).

    Returns:
        Successful response object.

    Raises:
        requests.HTTPError: If all retries are exhausted.
    """
    sleep_fn = delay_override or time.sleep
    response = None
    for attempt in range(max_retries + 1):
        response = http.get(url, params=params, timeout=30)
        if response.status_code in (429, 500, 502, 503, 504):
            wait = min(10.0, RETRY_BASE_SECONDS * (2**attempt) + random.uniform(0, 1))
            logger.warning(
                "OpenAlex HTTP %d (attempt %d/%d) — retrying in %.1fs",
                response.status_code,
                attempt + 1,
                max_retries,
                wait,
            )
            sleep_fn(wait)
            continue
        response.raise_for_status()
        return response

    # All retries exhausted
    logger.error("OpenAlex retries exhausted after %d attempts", max_retries)
    if response is not None:
        response.raise_for_status()
    raise requests.HTTPError("OpenAlex retries exhausted")  # pragma: no cover


def search_openalex(
    query: str,
    max_results: int = 100,
    base_url: str = OPENALEX_API_URL,
    session: Optional[requests.Session] = None,
    delay_override: Optional[Callable[[float], None]] = None,
) -> list[Paper]:
    """Search OpenAlex for works matching a query.

    Uses cursor-based pagination to retrieve results beyond the first
    page. Each page respects rate limits and retries on HTTP errors.

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
        cursor = "*"  # OpenAlex initial cursor value
        page_num = 0

        while len(all_papers) < max_results:
            page_size = min(OPENALEX_PAGE_SIZE, max_results - len(all_papers))
            page_num += 1

            params = {
                "search": query,
                "per_page": page_size,
                "cursor": cursor,
            }

            logger.info(
                "OpenAlex page %d: fetching %d results (total so far: %d, target: %d)",
                page_num,
                page_size,
                len(all_papers),
                max_results,
            )

            try:
                response = _request_with_retry(
                    http,
                    f"{base_url}/works",
                    params,
                    delay_override=delay_override,
                )
                result = response.json()
            except requests.HTTPError as e:
                logger.warning("OpenAlex search stopped early due to HTTP error (rate limit): %s", e)
                break

            page_papers = [_parse_openalex_work(item) for item in result.get("results", [])]

            if not page_papers:
                logger.info(
                    "OpenAlex page %d: no more results (total fetched: %d)",
                    page_num,
                    len(all_papers),
                )
                break

            all_papers.extend(page_papers)
            logger.info(
                "OpenAlex page %d: fetched %d papers (total: %d)",
                page_num,
                len(page_papers),
                len(all_papers),
            )

            if len(page_papers) < page_size:
                logger.info("OpenAlex: received partial page, all results fetched")
                break

            # Get next cursor for pagination
            meta = result.get("meta", {})
            next_cursor = meta.get("next_cursor")
            if not next_cursor:
                logger.info("OpenAlex: no next cursor, pagination complete")
                break
            cursor = next_cursor
    finally:
        if session is None:
            http.close()

    logger.info("OpenAlex search complete: %d total papers for query '%s'", len(all_papers), query[:80])
    return all_papers


def get_work_by_doi(
    doi: str,
    base_url: str = OPENALEX_API_URL,
    session: Optional[requests.Session] = None,
) -> Paper:
    """Retrieve a single work by its DOI.

    Args:
        doi: Digital Object Identifier (e.g., "10.1038/nrn2787").
        base_url: API base URL (injectable for testing).
        session: Optional requests.Session for connection reuse.

    Returns:
        Paper object with metadata from OpenAlex.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status (e.g. 404).
    """
    url = f"{base_url}/works/https://doi.org/{doi}"

    http = session or requests.Session()
    try:
        response = _request_with_retry(http, url, {})
    finally:
        if session is None:
            http.close()

    logger.debug("Retrieved work by DOI: %s", doi)
    return _parse_openalex_work(response.json())
