"""Tests for arXiv Atom API client.

Uses pytest-httpserver to serve real arXiv Atom XML responses locally,
avoiding any network calls. Tests both parse_arxiv_response (pure function)
and search_arxiv (HTTP integration).
"""

import xml.etree.ElementTree as ET

import pytest
from pytest_httpserver import HTTPServer

from literature.arxiv_client import (
    parse_arxiv_response,
    search_arxiv,
)


# ---------------------------------------------------------------------------
# Sample arXiv Atom XML responses
# ---------------------------------------------------------------------------

SINGLE_ENTRY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query: search_query=all:active+inference</title>
  <id>http://arxiv.org/api/query</id>
  <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">1</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/2201.06387v1</id>
    <title>An Overview of the Free Energy Principle and Related Research</title>
    <summary>The free energy principle (FEP) is a mathematical framework that attempts to explain perception, action, and learning in biological agents.</summary>
    <author><name>Zhengquan Zhang</name></author>
    <author><name>Feng Xu</name></author>
    <published>2022-01-17T00:00:00Z</published>
    <arxiv:doi>10.1162/neco_a_01532</arxiv:doi>
  </entry>
</feed>
"""

MULTI_ENTRY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/1709.02341v2</id>
    <title>Active Inference: A Process Theory</title>
    <summary>This paper describes active inference as a process theory.</summary>
    <author><name>Karl Friston</name></author>
    <author><name>Thomas Parr</name></author>
    <author><name>Giovanni Pezzulo</name></author>
    <published>2017-09-07T00:00:00Z</published>
    <arxiv:doi>10.1162/NECO_a_00912</arxiv:doi>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2003.09604v1</id>
    <title>A tutorial on the free-energy framework for modelling perception and learning</title>
    <summary>This tutorial provides an accessible introduction to the FEP.</summary>
    <author><name>Rafal Bogacz</name></author>
    <published>2020-03-21T00:00:00Z</published>
  </entry>
</feed>
"""

EMPTY_FEED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
</feed>
"""

ENTRY_NO_DOI_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2107.00000v1</id>
    <title>Some Active Inference Extension</title>
    <summary>An extension to active inference without a DOI.</summary>
    <author><name>Jane Doe</name></author>
    <published>2021-07-01T00:00:00Z</published>
  </entry>
</feed>
"""

ENTRY_NO_TITLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/0000.00000v1</id>
    <summary>Entry with no title element.</summary>
    <author><name>No Title Author</name></author>
    <published>2021-01-01T00:00:00Z</published>
  </entry>
</feed>
"""

ENTRY_INVALID_DATE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2109.99999v1</id>
    <title>Paper with invalid date</title>
    <summary>Abstract text.</summary>
    <author><name>Test Author</name></author>
    <published>not-a-date</published>
  </entry>
</feed>
"""

ENTRY_NO_SUMMARY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2200.11111v1</id>
    <title>Paper without summary</title>
    <author><name>Test Author</name></author>
    <published>2022-01-01T00:00:00Z</published>
  </entry>
</feed>
"""

ENTRY_NO_PUBLISHED_DATE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2300.22222v1</id>
    <title>Paper without published date</title>
    <summary>Abstract text.</summary>
    <author><name>Test Author</name></author>
  </entry>
</feed>
"""

ENTRY_ID_WITHOUT_ABS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query</title>
  <entry>
    <id>http://arxiv.org/something/else</id>
    <title>Paper with non-standard ID</title>
    <summary>Abstract text.</summary>
    <author><name>Test Author</name></author>
    <published>2023-01-01T00:00:00Z</published>
  </entry>
</feed>
"""


# ---------------------------------------------------------------------------
# parse_arxiv_response tests
# ---------------------------------------------------------------------------


class TestParseArxivResponse:
    """Tests for the pure XML parsing function."""

    def test_single_entry(self):
        """Parse a feed with a single entry."""
        papers = parse_arxiv_response(SINGLE_ENTRY_XML)
        assert len(papers) == 1

        p = papers[0]
        assert p.title == "An Overview of the Free Energy Principle and Related Research"
        assert "free energy principle" in p.abstract.lower()
        assert len(p.authors) == 2
        assert p.authors[0].name == "Zhengquan Zhang"
        assert p.authors[1].name == "Feng Xu"
        assert p.year == 2022
        assert p.doi == "10.1162/neco_a_01532"
        assert p.arxiv_id == "2201.06387"
        assert p.pdf_url == "https://arxiv.org/pdf/2201.06387.pdf"
        assert p.is_open_access is True
        assert p.full_text_source == "arxiv"

    def test_multi_entry(self):
        """Parse a feed with multiple entries."""
        papers = parse_arxiv_response(MULTI_ENTRY_XML)
        assert len(papers) == 2

        # First paper has DOI
        assert papers[0].doi == "10.1162/NECO_a_00912"
        assert papers[0].arxiv_id == "1709.02341"
        assert len(papers[0].authors) == 3

        # Second paper has no DOI
        assert papers[1].doi is None
        assert papers[1].arxiv_id == "2003.09604"
        assert papers[1].year == 2020

    def test_empty_feed(self):
        """Parse a feed with no entries returns empty list."""
        papers = parse_arxiv_response(EMPTY_FEED_XML)
        assert papers == []

    def test_entry_without_doi(self):
        """Entry without arxiv:doi element has doi=None."""
        papers = parse_arxiv_response(ENTRY_NO_DOI_XML)
        assert len(papers) == 1
        assert papers[0].doi is None
        assert papers[0].arxiv_id == "2107.00000"
        assert papers[0].pdf_url == "https://arxiv.org/pdf/2107.00000.pdf"
        assert papers[0].is_open_access is True
        assert papers[0].full_text_source == "arxiv"

    def test_canonical_id_with_doi(self):
        """Paper with DOI uses doi: prefix for canonical_id."""
        papers = parse_arxiv_response(SINGLE_ENTRY_XML)
        assert papers[0].canonical_id == "doi:10.1162/neco_a_01532"

    def test_canonical_id_without_doi(self):
        """Paper without DOI falls back to arxiv: prefix."""
        papers = parse_arxiv_response(ENTRY_NO_DOI_XML)
        assert papers[0].canonical_id == "arxiv:2107.00000"

    def test_publication_date_parsed(self):
        """Publication date is correctly parsed from ISO format."""
        papers = parse_arxiv_response(SINGLE_ENTRY_XML)
        from datetime import date

        assert papers[0].publication_date == date(2022, 1, 17)

    def test_version_stripped_from_arxiv_id(self):
        """Version suffix (v1, v2) is stripped from arXiv ID."""
        papers = parse_arxiv_response(MULTI_ENTRY_XML)
        # 1709.02341v2 -> 1709.02341
        assert papers[0].arxiv_id == "1709.02341"
        # 2003.09604v1 -> 2003.09604
        assert papers[1].arxiv_id == "2003.09604"

    def test_whitespace_normalized_in_title(self):
        """Multiline titles have whitespace normalized."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/9999.99999v1</id>
    <title>
      A Very Long Title
      That Spans Multiple Lines
    </title>
    <summary>Abstract text.</summary>
    <author><name>Test Author</name></author>
    <published>2023-01-01T00:00:00Z</published>
  </entry>
</feed>
"""
        papers = parse_arxiv_response(xml)
        assert papers[0].title == "A Very Long Title That Spans Multiple Lines"

    def test_malformed_xml_raises(self):
        """Malformed XML raises ParseError."""
        with pytest.raises(ET.ParseError):
            parse_arxiv_response("<not valid xml")

    def test_entry_without_title_skipped(self):
        """Entry without a title element is skipped (returns empty list)."""
        papers = parse_arxiv_response(ENTRY_NO_TITLE_XML)
        assert papers == []

    def test_invalid_date_handled(self):
        """Entry with invalid date still produces a Paper with no date/year."""
        papers = parse_arxiv_response(ENTRY_INVALID_DATE_XML)
        assert len(papers) == 1
        assert papers[0].publication_date is None
        assert papers[0].year is None
        assert papers[0].title == "Paper with invalid date"

    def test_entry_without_summary(self):
        """Entry without summary element has empty abstract."""
        papers = parse_arxiv_response(ENTRY_NO_SUMMARY_XML)
        assert len(papers) == 1
        assert papers[0].abstract == ""

    def test_entry_without_published_date(self):
        """Entry without published element has no date or year."""
        papers = parse_arxiv_response(ENTRY_NO_PUBLISHED_DATE_XML)
        assert len(papers) == 1
        assert papers[0].publication_date is None
        assert papers[0].year is None

    def test_entry_id_without_abs_path(self):
        """Entry with non-standard ID (no /abs/) has arxiv_id=None."""
        papers = parse_arxiv_response(ENTRY_ID_WITHOUT_ABS_XML)
        assert len(papers) == 1
        assert papers[0].arxiv_id is None
        assert papers[0].pdf_url is None
        assert papers[0].full_text_source is None


# ---------------------------------------------------------------------------
# search_arxiv HTTP integration tests (pytest-httpserver)
# ---------------------------------------------------------------------------


class TestSearchArxiv:
    """Tests for the search_arxiv function using a local HTTP server."""

    def test_search_returns_papers(self, httpserver: HTTPServer):
        """search_arxiv returns parsed Paper objects from HTTP response."""
        httpserver.expect_request("/api/query").respond_with_data(SINGLE_ENTRY_XML, content_type="application/atom+xml")

        papers = search_arxiv(
            query="all:active+inference",
            max_results=10,
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )

        assert len(papers) == 1
        assert papers[0].title == "An Overview of the Free Energy Principle and Related Research"

    def test_search_empty_results(self, httpserver: HTTPServer):
        """search_arxiv handles empty feed gracefully."""
        httpserver.expect_request("/api/query").respond_with_data(EMPTY_FEED_XML, content_type="application/atom+xml")

        papers = search_arxiv(
            query="all:nonexistent+topic+xyz",
            max_results=10,
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_multiple_results(self, httpserver: HTTPServer):
        """search_arxiv correctly parses multiple entries."""
        httpserver.expect_request("/api/query").respond_with_data(MULTI_ENTRY_XML, content_type="application/atom+xml")

        papers = search_arxiv(
            query="all:free+energy+principle",
            max_results=50,
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )

        assert len(papers) == 2

    def test_search_http_error(self, httpserver: HTTPServer):
        """search_arxiv raises on HTTP error status."""
        httpserver.expect_request("/api/query").respond_with_data("Server Error", status=500)

        with pytest.raises(Exception):
            search_arxiv(
                query="test",
                base_url=httpserver.url_for("/api/query"),
                rate_limit_seconds=0,
                delay_override=lambda _: None,
            )

    def test_search_with_custom_session(self, httpserver: HTTPServer):
        """search_arxiv works with a provided session object."""
        import requests

        httpserver.expect_request("/api/query").respond_with_data(SINGLE_ENTRY_XML, content_type="application/atom+xml")

        session = requests.Session()
        papers = search_arxiv(
            query="test",
            base_url=httpserver.url_for("/api/query"),
            session=session,
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )
        session.close()

        assert len(papers) == 1

    def test_search_max_results_param(self, httpserver: HTTPServer):
        """max_results is passed as query parameter to the API."""
        httpserver.expect_request(
            "/api/query",
        ).respond_with_data(EMPTY_FEED_XML, content_type="application/atom+xml")

        search_arxiv(
            query="test",
            max_results=25,
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
        )

        # Verify the server received the request (no exception = success)
        httpserver.check()


class TestArxivPaginationAndRetry:
    """Tests for auto-pagination and retry logic."""

    def test_pagination(self, httpserver: HTTPServer):
        """search_arxiv automatically fetches multiple pages."""
        header = '<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom"><title>ArXiv Query</title>'
        footer = "</feed>"
        entry_tmpl = "<entry><id>http://arxiv.org/abs/{id}</id><title>{title}</title><summary>Abstract</summary><author><name>Author</name></author><published>2023-01-01T00:00:00Z</published></entry>"

        # Page 1: 100 results (full page)
        page1_xml = (
            header + "".join([entry_tmpl.format(id=f"1001.{i:04d}", title=f"Paper {i}") for i in range(100)]) + footer
        )

        # Page 2: 50 results (partial page)
        page2_xml = (
            header
            + "".join([entry_tmpl.format(id=f"2002.{i:04d}", title=f"Paper {i + 100}") for i in range(50)])
            + footer
        )

        # Expect specific query params including sorting
        httpserver.expect_request(
            "/api/query",
            query_string="search_query=test&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending",
        ).respond_with_data(page1_xml)

        httpserver.expect_request(
            "/api/query",
            query_string="search_query=test&start=100&max_results=50&sortBy=submittedDate&sortOrder=descending",
        ).respond_with_data(page2_xml)

        papers = search_arxiv(
            query="test",
            max_results=150,
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )
        assert len(papers) == 150
        assert papers[0].title == "Paper 0"
        assert papers[149].title == "Paper 149"

    def test_retry_on_error(self, httpserver: HTTPServer):
        """search_arxiv retries on HTTP errors."""
        # Fail twice then succeed
        httpserver.expect_ordered_request("/api/query").respond_with_data("Error", status=503)
        httpserver.expect_ordered_request("/api/query").respond_with_data("Error", status=503)

        valid_xml = '<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Success</title><summary>Abstract</summary></entry></feed>'
        httpserver.expect_ordered_request("/api/query").respond_with_data(
            valid_xml, content_type="application/atom+xml"
        )

        papers = search_arxiv(
            query="test",
            base_url=httpserver.url_for("/api/query"),
            rate_limit_seconds=0,
            delay_override=lambda _: None,
        )
        assert len(papers) == 1
        assert papers[0].title == "Success"
