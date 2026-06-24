"""PubMed E-utilities search client.

Provides a keyless adapter for PubMed's E-utilities search and fetch
endpoints. PMID identifiers are retrieved from ``esearch.fcgi`` and then
resolved to article metadata via ``efetch.fcgi``. All search errors are
handled gracefully and return an empty result set.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET  # noqa: S405 — used only for type hints / ParseError
from typing import Callable, Optional

from defusedxml.ElementTree import fromstring as _safe_fromstring

import requests

from .models import Author, Paper

logger = logging.getLogger(__name__)

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

MAX_RETRIES = 1
RETRY_BASE_SECONDS = 1.0
# Max PMIDs per efetch GET request — keeps the ``id`` query string under the
# server URI length limit (large idlists otherwise return HTTP 414).
EFETCH_BATCH_SIZE = 200


def _normalized_element_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    text = "".join(element.itertext())
    return " ".join(text.split())


def _request_with_retry(
    http: requests.Session,
    url: str,
    params: dict[str, object],
    *,
    delay_override: Optional[Callable[[float], None]] = None,
    max_retries: int = MAX_RETRIES,
) -> requests.Response:
    sleep_fn = delay_override or time.sleep

    for attempt in range(max_retries + 1):
        try:
            response = http.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt >= max_retries:
                raise
            sleep_fn(RETRY_BASE_SECONDS * (attempt + 1))

    raise requests.HTTPError("PubMed retries exhausted")  # pragma: no cover


def _parse_pubmed_article(xml_element: ET.Element) -> Paper:
    title = _normalized_element_text(xml_element.find(".//Article/ArticleTitle"))

    abstract_segments = []
    for abstract_text in xml_element.findall(".//Article/Abstract/AbstractText"):
        segment = _normalized_element_text(abstract_text)
        if segment:
            abstract_segments.append(segment)
    abstract = " ".join(abstract_segments)

    authors: list[Author] = []
    for author_element in xml_element.findall(".//Article/AuthorList/Author"):
        collective_name = _normalized_element_text(author_element.find("CollectiveName"))
        if collective_name:
            authors.append(Author(name=collective_name))
            continue

        fore_name = _normalized_element_text(author_element.find("ForeName"))
        last_name = _normalized_element_text(author_element.find("LastName"))
        author_name = " ".join(part for part in (fore_name, last_name) if part)
        if author_name:
            authors.append(Author(name=author_name))

    year: Optional[int] = None
    year_text = _normalized_element_text(xml_element.find(".//Article/Journal/JournalIssue/PubDate/Year"))
    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            year = None

    venue_text = _normalized_element_text(xml_element.find(".//Article/Journal/Title"))
    venue = venue_text or None

    doi_text = _normalized_element_text(xml_element.find(".//PubmedData/ArticleIdList/ArticleId[@IdType='doi']"))
    doi = doi_text or None

    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        venue=venue,
    )


def search_pubmed(
    query: str,
    *,
    esearch_url: str = PUBMED_ESEARCH_URL,
    efetch_url: str = PUBMED_EFETCH_URL,
    max_results: int = 100,
    session: Optional[requests.Session] = None,
    delay_override: Optional[Callable[[float], None]] = None,
) -> list[Paper]:
    http = session or requests.Session()

    try:
        esearch_response = _request_with_retry(
            http,
            esearch_url,
            {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            },
            delay_override=delay_override,
        )

        try:
            esearch_payload = esearch_response.json()
        except ValueError as exc:
            raise ValueError("PubMed esearch returned invalid JSON") from exc

        if not isinstance(esearch_payload, dict):
            raise ValueError("PubMed esearch payload is not a JSON object")

        esearch_result = esearch_payload.get("esearchresult")
        if not isinstance(esearch_result, dict):
            raise ValueError("PubMed esearch payload missing esearchresult")

        idlist = esearch_result.get("idlist")
        if not isinstance(idlist, list):
            raise ValueError("PubMed esearch payload missing idlist")

        pmids = [pmid.strip() for pmid in idlist if isinstance(pmid, str) and pmid.strip()]
        if not pmids:
            return []

        # efetch is a GET; passing hundreds of PMIDs in one ``id`` query string
        # overruns the server URI limit (HTTP 414). Fetch in bounded batches and
        # concatenate the parsed articles.
        papers: list[Paper] = []
        for start in range(0, len(pmids), EFETCH_BATCH_SIZE):
            batch = pmids[start : start + EFETCH_BATCH_SIZE]
            efetch_response = _request_with_retry(
                http,
                efetch_url,
                {
                    "db": "pubmed",
                    "id": ",".join(batch),
                    "retmode": "xml",
                },
                delay_override=delay_override,
            )
            try:
                root = _safe_fromstring(efetch_response.text)
            except ET.ParseError as exc:
                raise ValueError("PubMed efetch returned invalid XML") from exc
            for article in root.findall(".//PubmedArticle"):
                papers.append(_parse_pubmed_article(article))
        return papers
    except Exception as exc:  # noqa: BLE001 -- safety net: any engine error degrades to an empty result set
        logger.warning("PubMed search failed for query %r: %s", query, exc)
        return []
    finally:
        if session is None:
            http.close()
