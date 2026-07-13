"""Tests for the SovietRxiv / RussiaRxiv API client.

Uses pytest-httpserver to serve realistic SovietRxiv ``PaperList`` JSON locally
(no mocks). Covers the pure parser ``_parse_sovietrxiv_paper`` field-by-field,
the ``_extract_year`` and ``_extract_authors`` helpers, cursor-based
pagination, the polite ``X-API-Email`` header, and the graceful empty /
HTTP-error contracts of ``search_sovietrxiv``.

Assertions are bound to independently hand-computed expected values rather
than echoing whatever the function returns.
"""

from __future__ import annotations

import requests
from pytest_httpserver import HTTPServer

from literature.sovietrxiv_client import (
    CHINARXIV_API_URL,
    SOVIETRXIV_API_URL,
    _extract_authors,
    _extract_year,
    _parse_sovietrxiv_paper,
    search_sovietrxiv,
)
from literature.models import Author, Paper


# ---------------------------------------------------------------------------
# Sample SovietRxiv ``PaperList`` responses
# ---------------------------------------------------------------------------

# Paper 1: full record — title, abstract, two authors, date, subjects,
# has_full_text, has_pdf, source_url, english_pdf_url, source, publication.
PAPER_FULL = {
    "id": "202312.00001",
    "title": "On the stability of differential equations with delay",
    "authors": ["Anna Ivanova", "Boris Petrov"],
    "abstract": "We study the stability of solutions to delay differential equations.",
    "abstract_source": "source",
    "date": "1985-03-15",
    "subjects": ["Mathematics", "Differential Equations"],
    "has_full_text": True,
    "has_figures": False,
    "has_pdf": True,
    "source_language": "ru",
    "source_url": "https://mathnet.ru/12345",
    "source": "russiarxiv",
    "publication": "matematicheskii_sbornik",
    "publication_title": "Matematicheskii Sbornik",
    "english_pdf_url": "https://russiarxiv.org/pdf/202312.00001",
}

# Paper 2: sparse record — no abstract, one author, no date, no PDF, no subjects.
PAPER_SPARSE = {
    "id": "199001.00002",
    "title": "A Sparse SovietRxiv Record",
    "authors": ["Single Author"],
    "abstract_source": "none",
    "source": "chinaxiv",
}

SEARCH_RESPONSE = {
    "total": 2,
    "limit": 100,
    "next_cursor": None,
    "data": [PAPER_FULL, PAPER_SPARSE],
}

EMPTY_RESPONSE = {
    "total": 0,
    "limit": 100,
    "next_cursor": None,
    "data": [],
}


# ---------------------------------------------------------------------------
# _extract_year (pure)
# ---------------------------------------------------------------------------


def test_extract_year_full_date() -> None:
    assert _extract_year("1985-03-15") == 1985


def test_extract_year_year_only() -> None:
    assert _extract_year("1990") == 1990


def test_extract_year_year_month() -> None:
    assert _extract_year("2001-07") == 2001


def test_extract_year_none() -> None:
    assert _extract_year(None) is None


def test_extract_year_empty() -> None:
    assert _extract_year("") is None


def test_extract_year_invalid() -> None:
    assert _extract_year("not-a-date") is None


def test_extract_year_non_string() -> None:
    assert _extract_year(12345) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _extract_authors (pure)
# ---------------------------------------------------------------------------


def test_extract_authors_list_of_strings() -> None:
    authors = _extract_authors(["Alice", "Bob"])
    assert authors == [Author(name="Alice"), Author(name="Bob")]


def test_extract_authors_skips_empty() -> None:
    authors = _extract_authors(["Alice", "", "  ", "Bob"])
    assert [a.name for a in authors] == ["Alice", "Bob"]


def test_extract_authors_empty_list() -> None:
    assert _extract_authors([]) == []


def test_extract_authors_non_list() -> None:
    assert _extract_authors("not a list") == []
    assert _extract_authors(None) is not None and _extract_authors(None) == []
    assert _extract_authors({"a": 1}) == []


def test_extract_authors_skips_non_strings() -> None:
    assert _extract_authors(["Alice", 42, None, {"name": "Bob"}]) == [Author(name="Alice")]


# ---------------------------------------------------------------------------
# _parse_sovietrxiv_paper (pure) — full record, field by field
# ---------------------------------------------------------------------------


def test_parse_full_paper_all_fields() -> None:
    paper = _parse_sovietrxiv_paper(PAPER_FULL)

    assert isinstance(paper, Paper)
    assert paper.title == "On the stability of differential equations with delay"
    assert paper.abstract == "We study the stability of solutions to delay differential equations."
    assert paper.year == 1985
    assert paper.doi is None  # SovietRxiv does not expose DOIs in the summary schema
    assert paper.venue == "Matematicheskii Sbornik"
    assert paper.citation_count == 0  # Not provided by the API
    assert paper.pdf_url == "https://russiarxiv.org/pdf/202312.00001"
    assert paper.is_open_access is True  # has_pdf=True -> True
    assert paper.full_text_source == "sovietrxiv"  # has_full_text=True

    # Authors: two, as plain strings.
    assert len(paper.authors) == 2
    assert paper.authors[0] == Author(name="Anna Ivanova")
    assert paper.authors[1].name == "Boris Petrov"
    assert paper.authors[1].affiliation is None  # No affiliation data

    # Untouched id fields.
    assert paper.arxiv_id is None
    assert paper.s2_id is None
    assert paper.openalex_id is None
    assert paper.references == []


def test_parse_sparse_paper_fallbacks() -> None:
    paper = _parse_sovietrxiv_paper(PAPER_SPARSE)

    assert paper.title == "A Sparse SovietRxiv Record"
    assert paper.abstract == ""  # No abstract field -> empty
    assert paper.year is None  # No date
    assert paper.doi is None
    # No publication_title/publication, source="chinaxiv" -> venue fallback
    assert paper.venue == "SovietRxiv (chinaxiv)"
    assert paper.citation_count == 0
    assert paper.pdf_url is None  # No source_url or english_pdf_url
    assert paper.is_open_access is None  # has_pdf not a bool -> None
    assert paper.full_text_source is None  # has_full_text not present

    # Single author preserved.
    assert len(paper.authors) == 1
    assert paper.authors[0].name == "Single Author"
    assert paper.authors[0].affiliation is None


def test_parse_paper_missing_title_is_empty_string() -> None:
    paper = _parse_sovietrxiv_paper({"id": "123"})
    assert paper.title == ""
    assert paper.authors == []
    assert paper.year is None


def test_parse_paper_empty_authors_list() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "authors": []})
    assert paper.authors == []


def test_parse_paper_missing_authors_key() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X"})
    assert paper.authors == []


def test_parse_paper_publication_fallback_to_source() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "source": "russiarxiv"})
    assert paper.venue == "SovietRxiv (russiarxiv)"


def test_parse_paper_no_source_no_publication_venue_none() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X"})
    assert paper.venue is None


def test_parse_paper_has_pdf_false_is_open_access_false() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "has_pdf": False})
    assert paper.is_open_access is False


def test_parse_paper_has_pdf_non_bool_is_open_access_none() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "has_pdf": "yes"})
    assert paper.is_open_access is None


def test_parse_paper_has_full_text_sets_full_text_source() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "has_full_text": True})
    assert paper.full_text_source == "sovietrxiv"


def test_parse_paper_has_full_text_false_sets_none() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "has_full_text": False})
    assert paper.full_text_source is None


def test_parse_paper_source_url_as_pdf_url() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "source_url": "https://example.com/orig.pdf"})
    assert paper.pdf_url == "https://example.com/orig.pdf"


def test_parse_paper_english_pdf_url_preferred_over_source_url() -> None:
    paper = _parse_sovietrxiv_paper(
        {
            "title": "X",
            "source_url": "https://example.com/orig.pdf",
            "english_pdf_url": "https://example.com/en.pdf",
        }
    )
    assert paper.pdf_url == "https://example.com/en.pdf"


def test_parse_paper_invalid_date_returns_none_pub_date() -> None:
    paper = _parse_sovietrxiv_paper({"title": "X", "date": "invalid"})
    assert paper.publication_date is None
    assert paper.year is None


def test_parse_paper_valid_date_sets_pub_date() -> None:
    from datetime import date as date_type

    paper = _parse_sovietrxiv_paper({"title": "X", "date": "1990-06-15"})
    assert paper.publication_date == date_type(1990, 6, 15)
    assert paper.year == 1990


def test_parse_paper_publication_title_preferred_over_publication() -> None:
    paper = _parse_sovietrxiv_paper(
        {
            "title": "X",
            "publication": "key_form",
            "publication_title": "Display Title",
        }
    )
    assert paper.venue == "Display Title"


# ---------------------------------------------------------------------------
# search_sovietrxiv (HTTP via pytest-httpserver)
# ---------------------------------------------------------------------------


def test_search_sovietrxiv_parses_items(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/api/v1/papers").respond_with_json(SEARCH_RESPONSE)

    papers = search_sovietrxiv("differential equations", base_url=httpserver.url_for(""), max_results=5)

    assert len(papers) == 2
    assert papers[0].title == "On the stability of differential equations with delay"
    assert papers[0].year == 1985
    assert papers[0].authors[0].name == "Anna Ivanova"
    assert papers[1].title == "A Sparse SovietRxiv Record"
    assert papers[1].year is None


def test_search_sovietrxiv_sends_api_email_header(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        "/api/v1/papers",
        headers={"X-API-Email": "user@example.com"},
    ).respond_with_json(SEARCH_RESPONSE)

    papers = search_sovietrxiv(
        "test",
        base_url=httpserver.url_for(""),
        max_results=5,
        api_email="user@example.com",
    )
    # The strict header match above proves X-API-Email was sent; sanity-check
    # parsing still works.
    assert len(papers) == 2


def test_search_sovietrxiv_omits_email_header_when_absent(httpserver: HTTPServer) -> None:
    # Request without X-API-Email header must still succeed.
    httpserver.expect_request("/api/v1/papers").respond_with_json(SEARCH_RESPONSE)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=5)
    assert len(papers) == 2


def test_search_sovietrxiv_empty_result_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/api/v1/papers").respond_with_json(EMPTY_RESPONSE)

    papers = search_sovietrxiv("nothing", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_search_sovietrxiv_http_error_returns_empty(httpserver: HTTPServer) -> None:
    # 500 is retried once (delay injected to keep fast), then surfaces as
    # HTTPError, which search_sovietrxiv must swallow -> [].
    httpserver.expect_request("/api/v1/papers").respond_with_data("", status=500)

    papers = search_sovietrxiv(
        "boom",
        base_url=httpserver.url_for(""),
        max_results=5,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_sovietrxiv_connection_error_returns_empty() -> None:
    # Unroutable port: requests raises ConnectionError, which must be swallowed.
    papers = search_sovietrxiv(
        "x",
        base_url="http://127.0.0.1:1",
        max_results=5,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_sovietrxiv_malformed_json_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/api/v1/papers").respond_with_data("not json", content_type="application/json")
    papers = search_sovietrxiv("x", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_search_sovietrxiv_paginates_two_pages(httpserver: HTTPServer) -> None:
    # page_size=1 forces a 1-result window. Page one has next_cursor set so
    # the client requests page two. Page two has next_cursor=None -> stop.
    page_one = {
        "total": 2,
        "limit": 1,
        "next_cursor": "cursor_abc",
        "data": [{"id": "001", "title": "First"}],
    }
    page_two = {
        "total": 2,
        "limit": 1,
        "next_cursor": None,
        "data": [{"id": "002", "title": "Second"}],
    }

    httpserver.expect_ordered_request(
        "/api/v1/papers",
        query_string="q=test&limit=1",
    ).respond_with_json(page_one)
    httpserver.expect_ordered_request(
        "/api/v1/papers",
        query_string="q=test&limit=1&cursor=cursor_abc",
    ).respond_with_json(page_two)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=10, page_size=1)

    assert [p.title for p in papers] == ["First", "Second"]


def test_search_sovietrxiv_final_page_caps_limit(httpserver: HTTPServer) -> None:
    # page_size=5 but max_results=3 -> the first (and only) page must request
    # limit=3, not 5, so the total never exceeds max_results.
    page = {
        "total": 3,
        "limit": 3,
        "next_cursor": None,
        "data": [{"id": str(i), "title": f"Paper {i}"} for i in range(3)],
    }
    httpserver.expect_request(
        "/api/v1/papers",
        query_string="q=test&limit=3",
    ).respond_with_json(page)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=3, page_size=5)
    assert len(papers) == 3


def test_search_sovietrxiv_respects_max_results_cap(httpserver: HTTPServer) -> None:
    # A full page of 2 is returned but max_results=1 -> only 1 page requested
    # (limit=1), and the result is capped at 1.
    one_item = {
        "total": 1,
        "limit": 1,
        "next_cursor": None,
        "data": [{"id": "001", "title": "Only"}],
    }
    httpserver.expect_request(
        "/api/v1/papers",
        query_string="q=test&limit=1",
    ).respond_with_json(one_item)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=1)
    assert len(papers) == 1
    assert papers[0].title == "Only"


def test_search_sovietrxiv_stops_on_empty_page(httpserver: HTTPServer) -> None:
    # If the API returns an empty data array, the client must stop paging.
    empty_page = {"total": 0, "limit": 100, "next_cursor": "cursor_abc", "data": []}
    httpserver.expect_request("/api/v1/papers").respond_with_json(empty_page)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=10)
    assert papers == []


def test_search_sovietrxiv_stops_when_next_cursor_missing(httpserver: HTTPServer) -> None:
    # If next_cursor is null/missing, the client must stop after page one.
    page = {
        "total": 1,
        "limit": 100,
        "next_cursor": None,
        "data": [{"id": "001", "title": "Done"}],
    }
    httpserver.expect_request("/api/v1/papers").respond_with_json(page)

    papers = search_sovietrxiv("test", base_url=httpserver.url_for(""), max_results=10)
    assert len(papers) == 1


def test_search_sovietrxiv_uses_injected_session(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/api/v1/papers").respond_with_json(EMPTY_RESPONSE)
    with requests.Session() as session:
        papers = search_sovietrxiv("x", base_url=httpserver.url_for(""), max_results=5, session=session)
    assert papers == []


def test_search_sovietrxiv_sends_source_filter(httpserver: HTTPServer) -> None:
    httpserver.expect_request(
        "/api/v1/papers",
        query_string="q=test&limit=5&source=russiarxiv",
    ).respond_with_json(SEARCH_RESPONSE)

    papers = search_sovietrxiv(
        "test",
        base_url=httpserver.url_for(""),
        max_results=5,
        source="russiarxiv",
    )
    # The strict query_string match above proves source was sent.
    assert len(papers) == 2


def test_search_sovietrxiv_non_dict_payload_stops(httpserver: HTTPServer) -> None:
    # A non-dict JSON payload (e.g. a bare list) must not crash; the client
    # stops and returns [].
    httpserver.expect_request("/api/v1/papers").respond_with_json(["not", "a", "dict"])
    papers = search_sovietrxiv("x", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_search_sovietrxiv_non_list_data_stops(httpserver: HTTPServer) -> None:
    # If "data" is not a list, the client must stop gracefully.
    bad_payload = {"total": 1, "limit": 100, "next_cursor": None, "data": "not a list"}
    httpserver.expect_request("/api/v1/papers").respond_with_json(bad_payload)
    papers = search_sovietrxiv("x", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_default_api_url_constant() -> None:
    assert SOVIETRXIV_API_URL == "https://russiarxiv.org"
    assert CHINARXIV_API_URL == "https://chinaxiv.org"
