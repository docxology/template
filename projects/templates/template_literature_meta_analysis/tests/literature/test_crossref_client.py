"""Tests for the Crossref API client.

Uses pytest-httpserver to serve realistic Crossref ``works`` JSON locally
(no mocks). Covers the pure parser ``_parse_crossref_work`` field-by-field,
JATS abstract stripping, missing-field fallbacks, pagination, the polite
``mailto`` parameter, and the graceful empty / HTTP-error contracts of
``search_crossref``.

Assertions are bound to independently hand-computed expected values rather
than echoing whatever the function returns.
"""

from __future__ import annotations


import requests
from pytest_httpserver import HTTPServer

from literature.crossref_client import (
    CROSSREF_API_URL,
    _parse_crossref_work,
    _strip_jats,
    search_crossref,
)
from literature.models import Author, Paper


# ---------------------------------------------------------------------------
# Sample Crossref ``works`` responses
# ---------------------------------------------------------------------------

# Work 1: full record — DOI, JATS abstract, two authors, year, venue,
# citation count, URL.
WORK_FULL = {
    "DOI": "10.1038/nrn2787",
    "title": ["The free-energy principle: a unified brain theory?"],
    "abstract": (
        "<jats:p>The free energy principle &amp; active inference unify "
        "<jats:italic>perception</jats:italic> and action.</jats:p>"
    ),
    "author": [
        {
            "given": "Karl",
            "family": "Friston",
            "affiliation": [{"name": "University College London"}],
        },
        {
            "given": "Thomas",
            "family": "Parr",
            "affiliation": [],
        },
    ],
    "issued": {"date-parts": [[2010, 2, 1]]},
    "container-title": ["Nature Reviews Neuroscience"],
    "is-referenced-by-count": 3500,
    "URL": "https://doi.org/10.1038/nrn2787",
}

# Work 2: sparse record — no abstract, organizational author, missing year,
# missing venue, missing citation count, no URL.
WORK_SPARSE = {
    "DOI": "10.5555/sparse",
    "title": ["A Sparse Crossref Record"],
    "author": [{"name": "Active Inference Institute"}],
    "issued": {"date-parts": [[]]},
}

SEARCH_RESPONSE = {"message": {"items": [WORK_FULL, WORK_SPARSE]}}

EMPTY_RESPONSE = {"message": {"items": []}}

# Expected de-JATS'd abstract, computed by hand: tags removed, "&amp;"
# unescaped to "&", whitespace collapsed.
EXPECTED_ABSTRACT = "The free energy principle & active inference unify perception and action."


# ---------------------------------------------------------------------------
# _strip_jats (pure)
# ---------------------------------------------------------------------------


def test_strip_jats_removes_tags_unescapes_and_collapses() -> None:
    raw = (
        "<jats:p>The free energy principle &amp; active inference unify "
        "<jats:italic>perception</jats:italic> and action.</jats:p>"
    )
    assert _strip_jats(raw) == EXPECTED_ABSTRACT


def test_strip_jats_empty_returns_empty() -> None:
    assert _strip_jats("") == ""


def test_strip_jats_entities_lt_gt_quot() -> None:
    raw = "<p>a &lt; b &gt; c &quot;d&quot;</p>"
    # Hand-computed: tags -> spaces, entities unescaped, whitespace collapsed.
    assert _strip_jats(raw) == 'a < b > c "d"'


# ---------------------------------------------------------------------------
# _parse_crossref_work (pure) — full record, field by field
# ---------------------------------------------------------------------------


def test_parse_full_work_all_fields() -> None:
    paper = _parse_crossref_work(WORK_FULL)

    assert isinstance(paper, Paper)
    assert paper.title == "The free-energy principle: a unified brain theory?"
    assert paper.abstract == EXPECTED_ABSTRACT
    assert paper.doi == "10.1038/nrn2787"
    assert paper.year == 2010
    assert paper.venue == "Nature Reviews Neuroscience"
    assert paper.citation_count == 3500
    assert paper.pdf_url == "https://doi.org/10.1038/nrn2787"

    # Authors: two, with names assembled from given+family.
    assert len(paper.authors) == 2
    assert paper.authors[0] == Author(name="Karl Friston", affiliation="University College London")
    assert paper.authors[1].name == "Thomas Parr"
    # Empty affiliation list -> None affiliation.
    assert paper.authors[1].affiliation is None

    # canonical_id derives from DOI (independent of the parser).
    assert paper.canonical_id == "doi:10.1038/nrn2787"

    # Untouched id fields.
    assert paper.arxiv_id is None
    assert paper.s2_id is None
    assert paper.openalex_id is None
    assert paper.references == []


def test_parse_sparse_work_fallbacks() -> None:
    paper = _parse_crossref_work(WORK_SPARSE)

    assert paper.title == "A Sparse Crossref Record"
    assert paper.abstract == ""
    assert paper.doi == "10.5555/sparse"
    assert paper.year is None  # date-parts [[]] is unresolvable
    assert paper.venue is None
    assert paper.citation_count == 0  # missing -> default 0
    assert paper.pdf_url is None  # no URL

    # Organizational author preserved via "name".
    assert len(paper.authors) == 1
    assert paper.authors[0].name == "Active Inference Institute"
    assert paper.authors[0].affiliation is None


def test_parse_work_missing_title_is_empty_string() -> None:
    paper = _parse_crossref_work({"DOI": "10.1/x"})
    assert paper.title == ""
    assert paper.authors == []
    assert paper.year is None


def test_parse_work_family_only_author() -> None:
    paper = _parse_crossref_work({"title": ["X"], "author": [{"family": "Doe"}]})
    assert paper.authors[0].name == "Doe"


def test_parse_work_skips_nameless_author() -> None:
    paper = _parse_crossref_work({"title": ["X"], "author": [{"given": "", "family": ""}, {"family": "Real"}]})
    assert len(paper.authors) == 1
    assert paper.authors[0].name == "Real"


def test_parse_work_non_int_citation_count_defaults_zero() -> None:
    paper = _parse_crossref_work({"title": ["X"], "is-referenced-by-count": None})
    assert paper.citation_count == 0


def test_parse_work_missing_date_parts_key() -> None:
    paper = _parse_crossref_work({"title": ["X"], "issued": {}})
    assert paper.year is None


def test_parse_work_non_int_year_in_date_parts() -> None:
    paper = _parse_crossref_work({"title": ["X"], "issued": {"date-parts": [["2010"]]}})
    assert paper.year is None  # string year is not accepted


def test_parse_work_empty_title_list_elements() -> None:
    paper = _parse_crossref_work({"title": [""], "container-title": [""]})
    assert paper.title == ""
    assert paper.venue is None


def test_parse_work_non_dict_author_entry_ignored() -> None:
    paper = _parse_crossref_work({"title": ["X"], "author": ["not-a-dict", {"family": "Keep"}]})
    assert [a.name for a in paper.authors] == ["Keep"]


def test_parse_work_affiliation_without_name_is_none() -> None:
    # affiliation entry is present but has no "name" key -> affiliation None.
    paper = _parse_crossref_work({"title": ["X"], "author": [{"family": "Doe", "affiliation": [{"id": "1"}]}]})
    assert paper.authors[0].affiliation is None


def test_parse_work_affiliation_non_dict_is_none() -> None:
    paper = _parse_crossref_work({"title": ["X"], "author": [{"family": "Doe", "affiliation": ["a string"]}]})
    assert paper.authors[0].affiliation is None


# ---------------------------------------------------------------------------
# search_crossref (HTTP via pytest-httpserver)
# ---------------------------------------------------------------------------


def test_search_crossref_parses_items(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

    papers = search_crossref("active inference", base_url=httpserver.url_for(""), max_results=5)

    assert len(papers) == 2
    assert papers[0].doi == "10.1038/nrn2787"
    assert papers[0].abstract == EXPECTED_ABSTRACT
    assert papers[0].year == 2010
    assert papers[0].citation_count == 3500
    assert papers[1].doi == "10.5555/sparse"
    assert papers[1].citation_count == 0


def test_search_crossref_sends_mailto_when_provided(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works", query_string="query=ai&rows=5&offset=0&mailto=x%40y.z").respond_with_json(
        SEARCH_RESPONSE
    )

    papers = search_crossref("ai", base_url=httpserver.url_for(""), max_results=5, mailto="x@y.z")
    # The strict query_string match above proves mailto was sent; sanity-check
    # parsing still works.
    assert len(papers) == 2


def test_search_crossref_omits_mailto_when_absent(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works", query_string="query=ai&rows=5&offset=0").respond_with_json(SEARCH_RESPONSE)

    papers = search_crossref("ai", base_url=httpserver.url_for(""), max_results=5)
    assert len(papers) == 2


def test_search_crossref_empty_result_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works").respond_with_json(EMPTY_RESPONSE)

    papers = search_crossref("nothing", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_search_crossref_http_error_returns_empty(httpserver: HTTPServer) -> None:
    # 500 is retried once (delay injected to keep fast), then surfaces as
    # HTTPError, which search_crossref must swallow -> [].
    httpserver.expect_request("/works").respond_with_data("", status=500)

    papers = search_crossref(
        "boom",
        base_url=httpserver.url_for(""),
        max_results=5,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_crossref_connection_error_returns_empty() -> None:
    # Unroutable port: requests raises ConnectionError, which must be swallowed.
    papers = search_crossref(
        "x",
        base_url="http://127.0.0.1:1",
        max_results=5,
        delay_override=lambda _s: None,
    )
    assert papers == []


def test_search_crossref_malformed_json_returns_empty(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works").respond_with_data("not json", content_type="application/json")
    papers = search_crossref("x", base_url=httpserver.url_for(""), max_results=5)
    assert papers == []


def test_search_crossref_paginates_two_pages(httpserver: HTTPServer) -> None:
    # rows_per_page=2 forces a 2-row window. Page one is FULL (2 == rows) so the
    # client requests page two at offset=2. Page two returns 1 (< 2) -> stop.
    # Total = 3 distinct DOIs, proving the offset advanced across requests.
    page_one = {
        "message": {
            "items": [
                {"DOI": "10.1/a", "title": ["A"]},
                {"DOI": "10.1/b", "title": ["B"]},
            ]
        }
    }
    page_two = {"message": {"items": [{"DOI": "10.1/c", "title": ["C"]}]}}

    httpserver.expect_ordered_request("/works", query_string="query=q&rows=2&offset=0").respond_with_json(page_one)
    httpserver.expect_ordered_request("/works", query_string="query=q&rows=2&offset=2").respond_with_json(page_two)

    papers = search_crossref("q", base_url=httpserver.url_for(""), max_results=10, rows_per_page=2)

    assert [p.doi for p in papers] == ["10.1/a", "10.1/b", "10.1/c"]


def test_search_crossref_final_page_caps_rows(httpserver: HTTPServer) -> None:
    # rows_per_page=5 but max_results=3 -> the first (and only) page must request
    # rows=3, not 5, so the total never exceeds max_results.
    page = {"message": {"items": [{"DOI": f"10.1/{i}", "title": [str(i)]} for i in range(3)]}}
    httpserver.expect_request("/works", query_string="query=q&rows=3&offset=0").respond_with_json(page)

    papers = search_crossref("q", base_url=httpserver.url_for(""), max_results=3, rows_per_page=5)
    assert len(papers) == 3


def test_search_crossref_respects_max_results_cap(httpserver: HTTPServer) -> None:
    # A full page of 2 is returned but max_results=1 -> only 1 page requested
    # (rows=1), and the result is capped at 1.
    one_item = {"message": {"items": [{"DOI": "10.1/a", "title": ["A"]}]}}
    httpserver.expect_request("/works", query_string="query=q&rows=1&offset=0").respond_with_json(one_item)

    papers = search_crossref("q", base_url=httpserver.url_for(""), max_results=1)
    assert len(papers) == 1
    assert papers[0].doi == "10.1/a"


def test_search_crossref_uses_injected_session(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/works").respond_with_json(EMPTY_RESPONSE)
    with requests.Session() as session:
        papers = search_crossref("x", base_url=httpserver.url_for(""), max_results=5, session=session)
    assert papers == []


def test_default_api_url_constant() -> None:
    assert CROSSREF_API_URL == "https://api.crossref.org"
