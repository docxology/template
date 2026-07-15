"""Europe PMC REST API client.

Provides a keyless engine adapter over the Europe PMC ``search`` endpoint
(https://www.ebi.ac.uk/europepmc/webservices/rest/search). Mirrors the shape
of the sibling adapters (``pubmed_client``, ``crossref_client``): a
module-level ``EUROPEPMC_API_URL`` constant, pure per-field parser helpers, a
pure ``_parse_europepmc_result`` record parser, and a ``search_europepmc``
entry point built on the shared ``literature.http.request_with_retry`` helper.

The Europe PMC ``search`` response wraps results as
``{"resultList": {"result": [ ...result objects... ]}}``. Result objects
expose (all optional) ``pmid``, ``pmcid``, ``doi``, ``title``,
``authorList.author`` (list of ``{fullName}`` or ``{firstName, lastName}``),
``pubYear``, ``journalInfo.journal.title``, ``abstractText``,
``isOpenAccess`` (``"Y"``/``"N"``), and ``fullTextUrlList.fullTextUrl`` (list of
``{url, documentStyle, availability}`` — an entry whose ``documentStyle`` is
``"pdf"`` (case-insensitive) is preferred for ``pdf_url``, else the first
entry's URL is used).

All functions accept an injectable ``base_url`` for testing with
pytest-httpserver. ``search_europepmc`` is graceful: on any network error,
JSON-decode error, or unexpected payload shape it logs a warning and returns
``[]`` -- it never raises to the caller.

API reference: https://europepmc.org/RestfulWebService
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import requests

from literature.http import request_with_retry

from .models import Author, Paper

logger = logging.getLogger(__name__)

# Default API base URL (the search endpoint is f"{base_url}/search").
EUROPEPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

# Europe PMC's documented per-request pageSize ceiling.
EUROPEPMC_MAX_PAGE_SIZE = 1000


def _extract_authors(item: dict) -> list[Author]:
    """Build the author list from a Europe PMC result's ``authorList`` field.

    Each author entry has either a ``fullName`` or ``firstName``/``lastName``.
    Authors with no resolvable name are skipped.

    Args:
        item: Europe PMC result object.

    Returns:
        List of Author objects (possibly empty).
    """
    authors: list[Author] = []
    author_list = item.get("authorList") or {}
    if not isinstance(author_list, dict):
        return authors
    for entry in author_list.get("author", []) or []:
        if not isinstance(entry, dict):
            continue

        full_name = entry.get("fullName")
        if full_name:
            name = str(full_name).strip()
        else:
            first = str(entry.get("firstName") or "").strip()
            last = str(entry.get("lastName") or "").strip()
            name = f"{first} {last}".strip()

        if name:
            authors.append(Author(name=name))
    return authors


def _extract_year(item: dict) -> Optional[int]:
    """Extract the publication year from a Europe PMC result's ``pubYear`` field.

    ``pubYear`` may be a string or an int, or absent entirely.

    Args:
        item: Europe PMC result object.

    Returns:
        Year as an int, or None if it cannot be resolved.
    """
    year_raw = item.get("pubYear")
    if year_raw is None:
        return None
    try:
        return int(year_raw)
    except (TypeError, ValueError):
        return None


def _extract_venue(item: dict) -> Optional[str]:
    """Extract the journal title from ``journalInfo.journal.title``.

    Args:
        item: Europe PMC result object.

    Returns:
        Journal title string, or None if missing.
    """
    journal_info = item.get("journalInfo")
    if not isinstance(journal_info, dict):
        return None
    journal = journal_info.get("journal")
    if not isinstance(journal, dict):
        return None
    title = journal.get("title")
    return str(title) if title else None


def _extract_pdf_url(item: dict) -> Optional[str]:
    """Extract a full-text PDF URL from ``fullTextUrlList.fullTextUrl``.

    Prefers an entry whose ``documentStyle`` is ``"pdf"`` (case-insensitive);
    falls back to the first entry's URL when no PDF-styled entry is present.

    Args:
        item: Europe PMC result object.

    Returns:
        A URL string, or None if no full-text URLs are present.
    """
    url_list = item.get("fullTextUrlList")
    if not isinstance(url_list, dict):
        return None
    entries = url_list.get("fullTextUrl")
    if not isinstance(entries, list) or not entries:
        return None

    dict_entries = [entry for entry in entries if isinstance(entry, dict)]
    if not dict_entries:
        return None

    for entry in dict_entries:
        if str(entry.get("documentStyle", "")).strip().lower() == "pdf":
            url = entry.get("url")
            if url:
                return str(url)

    fallback_url = dict_entries[0].get("url")
    return str(fallback_url) if fallback_url else None


def _extract_open_access(item: dict) -> Optional[bool]:
    """Translate the Europe PMC ``isOpenAccess`` ``"Y"``/``"N"`` flag to bool.

    Args:
        item: Europe PMC result object.

    Returns:
        True for ``"Y"``, False for ``"N"``, None if missing or unrecognized.
    """
    flag = item.get("isOpenAccess")
    if flag is None:
        return None
    flag_str = str(flag).strip().upper()
    if flag_str == "Y":
        return True
    if flag_str == "N":
        return False
    return None


def _parse_europepmc_result(item: dict) -> Paper:
    """Parse a single Europe PMC ``resultList.result`` object into a Paper.

    Args:
        item: Dictionary representing one Europe PMC result.

    Returns:
        Paper populated from the Europe PMC fields. Pure: performs no I/O.
    """
    title = item.get("title") or ""
    abstract = item.get("abstractText") or ""
    authors = _extract_authors(item)
    year = _extract_year(item)
    doi = item.get("doi") or None
    pmid = item.get("pmid") or None
    venue = _extract_venue(item)
    pdf_url = _extract_pdf_url(item)
    is_open_access = _extract_open_access(item)

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        pmid=pmid,
        venue=venue,
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        full_text_source="europepmc",
    )


def search_europepmc(
    query: str,
    *,
    max_results: int = 100,
    base_url: str = EUROPEPMC_API_URL,
    session: Optional[requests.Session] = None,
    delay_override: Optional[Callable[[float], None]] = None,
) -> list[Paper]:
    """Search Europe PMC for works matching a free-text query.

    Issues a single GET against ``f"{base_url}/search"`` with ``pageSize``
    capped at both ``max_results`` and Europe PMC's documented 1000-result
    ceiling. Graceful by contract: any network error, non-200 status,
    JSON-decode failure, or unexpected payload shape is logged and an empty
    list is returned -- this function never raises to the caller.

    Args:
        query: Free-text search query (Europe PMC query syntax).
        max_results: Maximum number of results to retrieve.
        base_url: API base URL (injectable for testing). The search endpoint
            is ``f"{base_url}/search"``.
        session: Optional requests.Session for connection reuse.
        delay_override: Optional sleep function (test injection).

    Returns:
        List of Paper objects (possibly empty).
    """
    http = session or requests.Session()
    try:
        response = request_with_retry(
            http,
            "GET",
            f"{base_url}/search",
            params={
                "query": query,
                "pageSize": min(max_results, EUROPEPMC_MAX_PAGE_SIZE),
                "format": "json",
                "resultType": "core",
            },
            delay_override=delay_override,
        )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("Europe PMC search returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("Europe PMC search payload is not a JSON object")

        result_list = payload.get("resultList")
        if not isinstance(result_list, dict):
            raise ValueError("Europe PMC search payload missing resultList")

        results = result_list.get("result")
        if not isinstance(results, list):
            raise ValueError("Europe PMC search payload missing result list")

        papers = [_parse_europepmc_result(item) for item in results if isinstance(item, dict)]
        logger.info("Europe PMC search complete: %d papers for query %r", len(papers), query[:80])
        return papers[:max_results]
    except Exception as exc:  # noqa: BLE001 -- safety net: any engine error degrades to an empty result set
        logger.warning("Europe PMC search failed for query %r: %s", query, exc)
        return []
    finally:
        if session is None:
            http.close()
