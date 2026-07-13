"""Tests for the bioRxiv/medRxiv API client.

Uses pytest-httpserver to serve realistic bioRxiv/medRxiv ``details`` JSON
locally (no mocks). Covers the pure helpers (``_extract_year``,
``_extract_authors``, ``_build_pdf_url``, ``_matches_query``,
``_parse_biorxiv_paper``) field-by-field, cursor-based pagination (including
the "full page -> fetch next" and "short page -> stop" transitions), the
client-side keyword filter, the empty-collection contract, and the graceful
malformed-JSON / HTTP-error contracts of ``search_biorxiv``.

Assertions are bound to independently hand-computed expected values rather
than echoing whatever the function returns.
"""

from __future__ import annotations

import requests
from pytest_httpserver import HTTPServer

from literature.biorxiv_client import (
    BIORXIV_API_URL,
    BIORXIV_PAGE_SIZE,
    _build_pdf_url,
    _extract_authors,
    _extract_year,
    _matches_query,
    _parse_biorxiv_paper,
    search_biorxiv,
)
from literature.models import Author, Paper

# ---------------------------------------------------------------------------
# Sample bioRxiv ``collection`` entries
# ---------------------------------------------------------------------------

PAPER_MATCHING = {
    "doi": "10.1101/2020.01.01.000001",
    "title": "Active inference and free energy in neural populations",
    "authors": "Friston K;Parr T",
    "date": "2020-01-01",
    "abstract": "We study active inference in cortical microcircuits.",
    "category": "neuroscience",
    "server": "biorxiv",
}

PAPER_NON_MATCHING = {
    "doi": "10.1101/2020.02.02.000002",
    "title": "Photosynthesis rates in tropical understory plants",
    "authors": "Smith J",
    "date": "2020-02-02",
    "abstract": "We measured chlorophyll density across canopy layers.",
    "category": "plant biology",
    "server": "biorxiv",
}

PAPER_SPARSE = {
    "doi": "",
    "title": "A sparse record with no active inference content either",
    "authors": "",
    "date": "",
    "abstract": "",
    "category": "",
    "server": "biorxiv",
}


# ---------------------------------------------------------------------------
# _extract_year (pure)
# ---------------------------------------------------------------------------


def test_extract_year_full_date() -> None:
    assert _extract_year("2020-01-01") == 2020


def test_extract_year_none() -> None:
    assert _extract_year(None) is None


def test_extract_year_empty_string() -> None:
    assert _extract_year("") is None


def test_extract_year_invalid() -> None:
    assert _extract_year("not-a-date") is None


def test_extract_year_non_string() -> None:
    assert _extract_year(20200101) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _extract_authors (pure) — semicolon-separated string
# ---------------------------------------------------------------------------


def test_extract_authors_splits_semicolons() -> None:
    authors = _extract_authors("Friston K;Parr T")
    assert authors == [Author(name="Friston K"), Author(name="Parr T")]


def test_extract_authors_single_author() -> None:
    authors = _extract_authors("Smith J")
    assert authors == [Author(name="Smith J")]


def test_extract_authors_strips_whitespace() -> None:
    authors = _extract_authors(" Friston K ; Parr T ")
    assert [a.name for a in authors] == ["Friston K", "Parr T"]


def test_extract_authors_drops_empty_parts() -> None:
    authors = _extract_authors("Friston K;;Parr T;")
    assert [a.name for a in authors] == ["Friston K", "Parr T"]


def test_extract_authors_empty_string() -> None:
    assert _extract_authors("") == []


def test_extract_authors_non_string() -> None:
    assert _extract_authors(["Friston K", "Parr T"]) == []
    assert _extract_authors(None) == []


# ---------------------------------------------------------------------------
# _build_pdf_url (pure)
# ---------------------------------------------------------------------------


def test_build_pdf_url_biorxiv() -> None:
    url = _build_pdf_url("biorxiv", "10.1101/2020.01.01.000001")
    assert url == "https://www.biorxiv.org/content/10.1101/2020.01.01.000001v1.full.pdf"


def test_build_pdf_url_medrxiv() -> None:
    url = _build_pdf_url("medrxiv", "10.1101/2020.01.01.000001")
    assert url == "https://www.medrxiv.org/content/10.1101/2020.01.01.000001v1.full.pdf"


def test_build_pdf_url_no_doi() -> None:
    assert _build_pdf_url("biorxiv", None) is None
    assert _build_pdf_url("biorxiv", "") is None


# ---------------------------------------------------------------------------
# _matches_query (pure)
# ---------------------------------------------------------------------------


def test_matches_query_all_terms_present() -> None:
    assert _matches_query(PAPER_MATCHING, ["active", "inference"]) is True


def test_matches_query_case_insensitive() -> None:
    # PAPER_MATCHING's text is lower-cased internally by _matches_query, but
    # terms themselves are expected pre-lowered by the caller (search_biorxiv
    # lower-cases the query before calling) — an upper-case item title/abstract
    # still matches lower-cased terms.
    item = {"title": "ACTIVE INFERENCE STUDY", "abstract": "Free Energy Principle"}
    assert _matches_query(item, ["active", "inference"]) is True


def test_matches_query_missing_term() -> None:
    assert _matches_query(PAPER_NON_MATCHING, ["active", "inference"]) is False


def test_matches_query_empty_terms_matches_everything() -> None:
    assert _matches_query(PAPER_NON_MATCHING, []) is True


def test_matches_query_checks_abstract_too() -> None:
    item = {"title": "Unrelated title", "abstract": "mentions active inference here"}
    assert _matches_query(item, ["active", "inference"]) is True


# ---------------------------------------------------------------------------
# _parse_biorxiv_paper (pure) — field by field
# ---------------------------------------------------------------------------


def test_parse_matching_paper_all_fields() -> None:
    paper = _parse_biorxiv_paper(PAPER_MATCHING, "biorxiv")

    assert isinstance(paper, Paper)
    assert paper.title == "Active inference and free energy in neural populations"
    assert paper.abstract == "We study active inference in cortical microcircuits."
    assert paper.year == 2020
    assert paper.doi == "10.1101/2020.01.01.000001"
    assert paper.venue is None
    assert paper.pdf_url == "https://www.biorxiv.org/content/10.1101/2020.01.01.000001v1.full.pdf"
    assert paper.full_text_source == "biorxiv"
    assert paper.is_preprint is True  # full_text_source="biorxiv" is a preprint hint

    assert len(paper.authors) == 2
    assert paper.authors[0] == Author(name="Friston K")
    assert paper.authors[1].name == "Parr T"


def test_parse_paper_medrxiv_server() -> None:
    item = dict(PAPER_MATCHING, server="medrxiv")
    paper = _parse_biorxiv_paper(item, "medrxiv")
    assert paper.full_text_source == "medrxiv"
    assert paper.pdf_url == "https://www.medrxiv.org/content/10.1101/2020.01.01.000001v1.full.pdf"


def test_parse_sparse_paper_fallbacks() -> None:
    paper = _parse_biorxiv_paper(PAPER_SPARSE, "biorxiv")
    assert paper.doi is None  # empty string -> None
    assert paper.pdf_url is None
    assert paper.year is None
    assert paper.authors == []
    assert paper.abstract == ""


def test_parse_paper_missing_title_is_empty_string() -> None:
    paper = _parse_biorxiv_paper({}, "biorxiv")
    assert paper.title == ""
    assert paper.authors == []
    assert paper.year is None
    assert paper.doi is None


# ---------------------------------------------------------------------------
# search_biorxiv (HTTP via pytest-httpserver)
# ---------------------------------------------------------------------------


def test_search_biorxiv_single_page_filters_to_matching_only(httpserver: HTTPServer) -> None:
    page = {
        "collection": [PAPER_MATCHING, PAPER_NON_MATCHING],
        "messages": [{"status": "ok"}],
    }
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json(page)

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=10)

    assert len(papers) == 1
    assert papers[0].title == "Active inference and free energy in neural populations"
    assert papers[0].doi == "10.1101/2020.01.01.000001"
    assert [a.name for a in papers[0].authors] == ["Friston K", "Parr T"]
    assert papers[0].year == 2020


def test_search_biorxiv_medrxiv_server_hits_correct_path(httpserver: HTTPServer) -> None:
    page = {"collection": [PAPER_MATCHING], "messages": []}
    httpserver.expect_request(
        f"/details/medrxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json(page)

    papers = search_biorxiv(
        "active inference",
        base_url=httpserver.url_for(""),
        max_results=10,
        server="medrxiv",
    )
    assert len(papers) == 1
    assert papers[0].full_text_source == "medrxiv"


def test_search_biorxiv_empty_collection_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json({"collection": [], "messages": []})

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=10)
    assert papers == []


def test_search_biorxiv_malformed_json_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_data("not json", content_type="application/json")

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=10)
    assert papers == []


def test_search_biorxiv_http_error_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_data("", status=500)

    papers = search_biorxiv(
        "active inference",
        base_url=httpserver.url_for(""),
        max_results=10,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_biorxiv_connection_error_returns_empty() -> None:
    # Unroutable port: requests raises ConnectionError, which must be swallowed.
    papers = search_biorxiv(
        "active inference",
        base_url="http://127.0.0.1:1",
        max_results=10,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_biorxiv_non_dict_payload_stops(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json(["not", "a", "dict"])

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=10)
    assert papers == []


def test_search_biorxiv_non_list_collection_stops(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json({"collection": "not a list", "messages": []})

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=10)
    assert papers == []


def test_search_biorxiv_uses_injected_session(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json({"collection": [], "messages": []})

    with requests.Session() as session:
        papers = search_biorxiv(
            "active inference", base_url=httpserver.url_for(""), max_results=10, session=session
        )
    assert papers == []


def test_search_biorxiv_paginates_two_pages(httpserver: HTTPServer) -> None:
    # Page one returns exactly BIORXIV_PAGE_SIZE (100) matching raw items
    # -> triggers a second-page fetch at cursor=100. Page two returns fewer
    # than 100 raw items -> the loop stops after page two.
    assert BIORXIV_PAGE_SIZE == 100
    page_one_items = [
        {
            "doi": f"10.1101/2020.01.01.{i:06d}",
            "title": "Active inference study",
            "authors": "Author One",
            "date": "2020-01-01",
            "abstract": "active inference content",
            "category": "neuroscience",
            "server": "biorxiv",
        }
        for i in range(100)
    ]
    page_two_items = [
        {
            "doi": "10.1101/2020.02.02.000200",
            "title": "Active inference follow-up study",
            "authors": "Author Two",
            "date": "2020-02-02",
            "abstract": "active inference content continued",
            "category": "neuroscience",
            "server": "biorxiv",
        }
    ]

    httpserver.expect_ordered_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json({"collection": page_one_items, "messages": []})
    httpserver.expect_ordered_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/100/json"
    ).respond_with_json({"collection": page_two_items, "messages": []})

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=200)

    assert len(papers) == 101
    assert papers[-1].title == "Active inference follow-up study"


def test_search_biorxiv_stops_once_max_results_reached(httpserver: HTTPServer) -> None:
    # A full page of matches is returned but max_results caps the client at 2
    # before a second page would be requested.
    page_items = [
        {
            "doi": f"10.1101/2020.01.01.{i:06d}",
            "title": "Active inference study",
            "authors": "Author One",
            "date": "2020-01-01",
            "abstract": "active inference content",
            "category": "neuroscience",
            "server": "biorxiv",
        }
        for i in range(100)
    ]
    httpserver.expect_request(
        f"/details/biorxiv/{2013}-01-01/{2099}-12-31/0/json"
    ).respond_with_json({"collection": page_items, "messages": []})

    papers = search_biorxiv("active inference", base_url=httpserver.url_for(""), max_results=2)
    assert len(papers) == 2


def test_default_api_url_constant() -> None:
    assert BIORXIV_API_URL == "https://api.biorxiv.org"
