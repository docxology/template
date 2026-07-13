"""Tests for the Europe PMC API client.

Uses pytest-httpserver to serve realistic Europe PMC ``search`` JSON locally
(no mocks). Covers the pure parser ``_parse_europepmc_result`` field-by-field,
the per-field helper functions, and the graceful empty / malformed / HTTP-error
contracts of ``search_europepmc``.

Assertions are bound to independently hand-computed expected values rather
than echoing whatever the function returns.
"""

from __future__ import annotations

import requests
from pytest_httpserver import HTTPServer

from literature.europepmc_client import (
    EUROPEPMC_API_URL,
    _extract_authors,
    _extract_open_access,
    _extract_pdf_url,
    _extract_venue,
    _extract_year,
    _parse_europepmc_result,
    search_europepmc,
)
from literature.models import Author, Paper

# ---------------------------------------------------------------------------
# Sample Europe PMC ``search`` results
# ---------------------------------------------------------------------------

# Result 1: full record — pmid, pmcid, doi, title, two authors (fullName),
# year, venue, abstract, open access, and a PDF-styled full-text URL among
# several entries.
RESULT_FULL = {
    "pmid": "30123456",
    "pmcid": "PMC6123456",
    "doi": "10.1016/j.tics.2010.05.001",
    "title": "The free-energy principle: a unified brain theory?",
    "authorList": {
        "author": [
            {"fullName": "Friston K"},
            {"firstName": "Thomas", "lastName": "Parr"},
        ]
    },
    "pubYear": "2010",
    "journalInfo": {"journal": {"title": "Nature Reviews Neuroscience"}},
    "abstractText": "The free energy principle unifies perception and action.",
    "isOpenAccess": "Y",
    "fullTextUrlList": {
        "fullTextUrl": [
            {
                "url": "https://europepmc.org/article/MED/30123456",
                "documentStyle": "html",
                "availability": "Open access",
            },
            {
                "url": "https://europepmc.org/articles/PMC6123456/pdf",
                "documentStyle": "pdf",
                "availability": "Open access",
            },
        ]
    },
}

# Result 2: sparse record — no pmid/pmcid/doi, no authors, no year, no
# journal, no abstract, not open access, no full-text URLs.
RESULT_SPARSE = {
    "title": "A Sparse Europe PMC Record",
}

SEARCH_RESPONSE = {"resultList": {"result": [RESULT_FULL, RESULT_SPARSE]}}

EMPTY_RESPONSE = {"resultList": {"result": []}}


# ---------------------------------------------------------------------------
# Pure per-field helpers
# ---------------------------------------------------------------------------


class TestExtractAuthors:
    def test_full_name_and_first_last_name(self):
        item = {
            "authorList": {
                "author": [
                    {"fullName": "Friston K"},
                    {"firstName": "Thomas", "lastName": "Parr"},
                ]
            }
        }
        authors = _extract_authors(item)
        assert authors == [Author(name="Friston K"), Author(name="Thomas Parr")]

    def test_missing_author_list_returns_empty(self):
        assert _extract_authors({}) == []

    def test_author_list_wrong_type_returns_empty(self):
        assert _extract_authors({"authorList": "not-a-dict"}) == []

    def test_non_dict_author_entry_skipped(self):
        item = {"authorList": {"author": ["not-a-dict", {"fullName": "Real Name"}]}}
        assert [a.name for a in _extract_authors(item)] == ["Real Name"]

    def test_nameless_author_skipped(self):
        item = {"authorList": {"author": [{"firstName": "", "lastName": ""}, {"fullName": "Keep"}]}}
        assert [a.name for a in _extract_authors(item)] == ["Keep"]


class TestExtractYear:
    def test_string_year_parsed(self):
        assert _extract_year({"pubYear": "2019"}) == 2019

    def test_int_year_parsed(self):
        assert _extract_year({"pubYear": 2019}) == 2019

    def test_missing_year_is_none(self):
        assert _extract_year({}) is None

    def test_non_numeric_year_is_none(self):
        assert _extract_year({"pubYear": "Spring"}) is None


class TestExtractVenue:
    def test_venue_from_journal_info(self):
        item = {"journalInfo": {"journal": {"title": "Journal of Theoretical Biology"}}}
        assert _extract_venue(item) == "Journal of Theoretical Biology"

    def test_missing_journal_info_is_none(self):
        assert _extract_venue({}) is None

    def test_journal_info_wrong_type_is_none(self):
        assert _extract_venue({"journalInfo": "not-a-dict"}) is None

    def test_journal_wrong_type_is_none(self):
        assert _extract_venue({"journalInfo": {"journal": "not-a-dict"}}) is None


class TestExtractPdfUrl:
    def test_prefers_pdf_document_style(self):
        item = {
            "fullTextUrlList": {
                "fullTextUrl": [
                    {"url": "https://example.org/html", "documentStyle": "html"},
                    {"url": "https://example.org/pdf", "documentStyle": "PDF"},
                ]
            }
        }
        assert _extract_pdf_url(item) == "https://example.org/pdf"

    def test_falls_back_to_first_entry_when_no_pdf(self):
        item = {
            "fullTextUrlList": {
                "fullTextUrl": [
                    {"url": "https://example.org/html", "documentStyle": "html"},
                    {"url": "https://example.org/xml", "documentStyle": "xml"},
                ]
            }
        }
        assert _extract_pdf_url(item) == "https://example.org/html"

    def test_missing_url_list_is_none(self):
        assert _extract_pdf_url({}) is None

    def test_empty_url_list_is_none(self):
        assert _extract_pdf_url({"fullTextUrlList": {"fullTextUrl": []}}) is None

    def test_non_dict_entries_ignored(self):
        item = {"fullTextUrlList": {"fullTextUrl": ["not-a-dict"]}}
        assert _extract_pdf_url(item) is None


class TestExtractOpenAccess:
    def test_y_is_true(self):
        assert _extract_open_access({"isOpenAccess": "Y"}) is True

    def test_n_is_false(self):
        assert _extract_open_access({"isOpenAccess": "N"}) is False

    def test_missing_is_none(self):
        assert _extract_open_access({}) is None

    def test_unrecognized_value_is_none(self):
        assert _extract_open_access({"isOpenAccess": "maybe"}) is None


# ---------------------------------------------------------------------------
# _parse_europepmc_result (pure) — full record, field by field
# ---------------------------------------------------------------------------


class TestParseEuropePMCResult:
    def test_parse_full_result_all_fields(self):
        paper = _parse_europepmc_result(RESULT_FULL)

        assert isinstance(paper, Paper)
        assert paper.title == "The free-energy principle: a unified brain theory?"
        assert paper.abstract == "The free energy principle unifies perception and action."
        assert paper.doi == "10.1016/j.tics.2010.05.001"
        assert paper.pmid == "30123456"
        assert paper.year == 2010
        assert paper.venue == "Nature Reviews Neuroscience"
        assert paper.pdf_url == "https://europepmc.org/articles/PMC6123456/pdf"
        assert paper.is_open_access is True
        assert paper.full_text_source == "europepmc"

        assert len(paper.authors) == 2
        assert paper.authors[0] == Author(name="Friston K")
        assert paper.authors[1] == Author(name="Thomas Parr")

        # canonical_id derives from DOI (independent of the parser).
        assert paper.canonical_id == "doi:10.1016/j.tics.2010.05.001"

    def test_parse_sparse_result_fallbacks(self):
        paper = _parse_europepmc_result(RESULT_SPARSE)

        assert paper.title == "A Sparse Europe PMC Record"
        assert paper.abstract == ""
        assert paper.doi is None
        assert paper.pmid is None
        assert paper.year is None
        assert paper.venue is None
        assert paper.pdf_url is None
        assert paper.is_open_access is None
        assert paper.authors == []
        assert paper.full_text_source == "europepmc"

        # No doi/pmid/arxiv/s2/openalex -> falls back to a title hash.
        assert paper.canonical_id.startswith("title:")

    def test_parse_missing_title_is_empty_string(self):
        paper = _parse_europepmc_result({"doi": "10.1/x"})
        assert paper.title == ""
        assert paper.authors == []
        assert paper.year is None


# ---------------------------------------------------------------------------
# search_europepmc (HTTP via pytest-httpserver)
# ---------------------------------------------------------------------------


class TestSearchEuropePMC:
    def test_search_parses_multi_entry_response(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json(SEARCH_RESPONSE)

        papers = search_europepmc("active inference", base_url=httpserver.url_for(""), max_results=10)

        assert len(papers) == 2
        assert papers[0].pmid == "30123456"
        assert papers[0].doi == "10.1016/j.tics.2010.05.001"
        assert papers[0].year == 2010
        assert papers[0].pdf_url == "https://europepmc.org/articles/PMC6123456/pdf"
        assert papers[0].is_open_access is True
        assert papers[0].full_text_source == "europepmc"
        assert papers[1].title == "A Sparse Europe PMC Record"
        assert papers[1].pmid is None

    def test_search_sends_expected_query_params(self, httpserver: HTTPServer):
        httpserver.expect_request(
            "/search",
            query_string="query=modafinil&pageSize=50&format=json&resultType=core",
        ).respond_with_json(EMPTY_RESPONSE)

        papers = search_europepmc("modafinil", base_url=httpserver.url_for(""), max_results=50)
        assert papers == []

    def test_search_caps_page_size_at_1000(self, httpserver: HTTPServer):
        httpserver.expect_request(
            "/search",
            query_string="query=q&pageSize=1000&format=json&resultType=core",
        ).respond_with_json(EMPTY_RESPONSE)

        papers = search_europepmc("q", base_url=httpserver.url_for(""), max_results=5000)
        assert papers == []

    def test_search_empty_result_list_returns_empty(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json(EMPTY_RESPONSE)

        papers = search_europepmc("nothing", base_url=httpserver.url_for(""), max_results=5)
        assert papers == []

    def test_search_respects_max_results_cap(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json(SEARCH_RESPONSE)

        papers = search_europepmc("active inference", base_url=httpserver.url_for(""), max_results=1)
        assert len(papers) == 1
        assert papers[0].pmid == "30123456"

    def test_search_http_error_returns_empty(self, httpserver: HTTPServer):
        # 500 is retried, then surfaces as HTTPError, which search_europepmc
        # must swallow -> [].
        httpserver.expect_request("/search").respond_with_data("", status=500)

        papers = search_europepmc(
            "boom",
            base_url=httpserver.url_for(""),
            max_results=5,
            delay_override=lambda _s: None,
        )
        assert papers == []

    def test_search_connection_error_returns_empty(self):
        # Unroutable port: requests raises ConnectionError, which must be swallowed.
        papers = search_europepmc(
            "x",
            base_url="http://127.0.0.1:1",
            max_results=5,
            delay_override=lambda _s: None,
        )
        assert papers == []

    def test_search_malformed_json_returns_empty(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_data("not json", content_type="application/json")
        papers = search_europepmc("x", base_url=httpserver.url_for(""), max_results=5)
        assert papers == []

    def test_search_missing_result_list_returns_empty(self, httpserver: HTTPServer):
        """Response JSON without a 'resultList' key never raises -> []."""
        httpserver.expect_request("/search").respond_with_json({"header": {}})

        papers = search_europepmc("no result list", base_url=httpserver.url_for(""), max_results=5)
        assert papers == []

    def test_search_result_list_not_dict_returns_empty(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json({"resultList": "not-a-dict"})

        papers = search_europepmc("bad resultList", base_url=httpserver.url_for(""), max_results=5)
        assert papers == []

    def test_search_result_not_list_returns_empty(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json({"resultList": {"result": "not-a-list"}})

        papers = search_europepmc("bad result", base_url=httpserver.url_for(""), max_results=5)
        assert papers == []

    def test_search_non_dict_result_entries_skipped(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json(
            {"resultList": {"result": ["not-a-dict", RESULT_SPARSE]}}
        )

        papers = search_europepmc("mixed", base_url=httpserver.url_for(""), max_results=5)
        assert len(papers) == 1
        assert papers[0].title == "A Sparse Europe PMC Record"

    def test_search_uses_injected_session(self, httpserver: HTTPServer):
        httpserver.expect_request("/search").respond_with_json(EMPTY_RESPONSE)
        with requests.Session() as session:
            papers = search_europepmc("x", base_url=httpserver.url_for(""), max_results=5, session=session)
        assert papers == []

    def test_default_api_url_constant(self):
        assert EUROPEPMC_API_URL == "https://www.ebi.ac.uk/europepmc/webservices/rest"
