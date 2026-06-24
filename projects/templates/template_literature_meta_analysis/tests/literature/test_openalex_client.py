"""Tests for OpenAlex API client.

Uses pytest-httpserver to serve realistic OpenAlex JSON responses locally.
Tests search_openalex, get_work_by_doi, and _reconstruct_abstract.
"""

import pytest
import requests
from pytest_httpserver import HTTPServer

from literature.openalex_client import (
    _reconstruct_abstract,
    get_work_by_doi,
    search_openalex,
)
from literature.models import Paper


# ---------------------------------------------------------------------------
# Sample OpenAlex API responses
# ---------------------------------------------------------------------------

SEARCH_RESPONSE = {
    "meta": {"count": 2, "db_response_time_ms": 42, "page": 1, "per_page": 25},
    "results": [
        {
            "id": "https://openalex.org/W2140",
            "display_name": "The free-energy principle: a unified brain theory?",
            "publication_year": 2010,
            "doi": "https://doi.org/10.1038/nrn2787",
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Karl Friston",
                        "orcid": "https://orcid.org/0000-0001-7984-8909",
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I1",
                            "display_name": "University College London",
                        }
                    ],
                }
            ],
            "cited_by_count": 3500,
            "abstract_inverted_index": {
                "The": [0],
                "free": [1],
                "energy": [2],
                "principle": [3],
                "provides": [4],
                "a": [5],
                "unified": [6],
                "account": [7],
                "of": [8],
                "brain": [9],
                "function.": [10],
            },
            "primary_location": {
                "source": {
                    "id": "https://openalex.org/S1",
                    "display_name": "Nature Reviews Neuroscience",
                }
            },
            "open_access": {
                "is_oa": True,
                "oa_url": "https://europepmc.org/articles/pmc2996528",
            },
            "best_oa_location": {
                "pdf_url": "https://europepmc.org/articles/pmc2996528?pdf=render",
                "url": "https://europepmc.org/articles/pmc2996528",
                "source": {
                    "type": "repository",
                    "display_name": "Europe PMC",
                },
            },
        },
        {
            "id": "https://openalex.org/W5678",
            "display_name": "Active Inference and Learning",
            "publication_year": 2016,
            "doi": "https://doi.org/10.1016/j.neubiorev.2016.06.022",
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A2",
                        "display_name": "Karl Friston",
                        "orcid": None,
                    },
                    "institutions": [],
                },
                {
                    "author": {
                        "id": "https://openalex.org/A3",
                        "display_name": "Thomas FitzGerald",
                        "orcid": None,
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I2",
                            "display_name": "Max Planck Institute",
                        }
                    ],
                },
            ],
            "cited_by_count": 200,
            "abstract_inverted_index": None,
            "primary_location": None,
            "open_access": {
                "is_oa": False,
            },
        },
    ],
}

SINGLE_WORK_RESPONSE = {
    "id": "https://openalex.org/W2140",
    "display_name": "The free-energy principle: a unified brain theory?",
    "publication_year": 2010,
    "doi": "https://doi.org/10.1038/nrn2787",
    "authorships": [
        {
            "author": {
                "id": "https://openalex.org/A1",
                "display_name": "Karl Friston",
                "orcid": "https://orcid.org/0000-0001-7984-8909",
            },
            "institutions": [
                {
                    "id": "https://openalex.org/I1",
                    "display_name": "University College London",
                }
            ],
        }
    ],
    "cited_by_count": 3500,
    "abstract_inverted_index": {
        "The": [0],
        "free-energy": [1],
        "principle.": [2],
    },
    "primary_location": {
        "source": {
            "display_name": "Nature Reviews Neuroscience",
        }
    },
}

EMPTY_SEARCH_RESPONSE = {
    "meta": {"count": 0, "db_response_time_ms": 10, "page": 1, "per_page": 25},
    "results": [],
}


# ---------------------------------------------------------------------------
# _reconstruct_abstract tests
# ---------------------------------------------------------------------------


class TestReconstructAbstract:
    """Tests for the inverted index abstract reconstruction."""

    def test_simple_reconstruction(self):
        """Simple inverted index produces correct text."""
        inverted_index = {"The": [0], "free": [1], "energy": [2]}
        assert _reconstruct_abstract(inverted_index) == "The free energy"

    def test_word_appearing_multiple_times(self):
        """Words appearing at multiple positions are correctly placed."""
        inverted_index = {
            "the": [0, 4],
            "cat": [1],
            "sat": [2],
            "on": [3],
            "mat": [5],
        }
        result = _reconstruct_abstract(inverted_index)
        assert result == "the cat sat on the mat"

    def test_empty_inverted_index(self):
        """Empty inverted index returns empty string."""
        assert _reconstruct_abstract({}) == ""

    def test_none_inverted_index(self):
        """None inverted index returns empty string."""
        assert _reconstruct_abstract(None) == ""

    def test_single_word(self):
        """Single word in inverted index."""
        assert _reconstruct_abstract({"Hello": [0]}) == "Hello"

    def test_complex_abstract(self):
        """Reconstruct a more realistic abstract snippet."""
        inverted_index = {
            "Active": [0],
            "inference": [1, 7],
            "is": [2],
            "a": [3],
            "corollary": [4],
            "of": [5],
            "the": [6],
            "framework.": [8],
        }
        result = _reconstruct_abstract(inverted_index)
        assert result == "Active inference is a corollary of the inference framework."

    def test_preserves_punctuation(self):
        """Punctuation attached to words is preserved."""
        inverted_index = {
            "Hello,": [0],
            "world!": [1],
        }
        assert _reconstruct_abstract(inverted_index) == "Hello, world!"


# ---------------------------------------------------------------------------
# search_openalex tests
# ---------------------------------------------------------------------------


class TestSearchOpenalex:
    """Tests for the OpenAlex search function."""

    def test_search_returns_papers(self, httpserver: HTTPServer):
        """Search returns correctly parsed Paper objects."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="free energy principle",
            max_results=10,
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert len(papers) == 2
        assert isinstance(papers[0], Paper)

    def test_search_first_result_fields(self, httpserver: HTTPServer):
        """First result has correct field values."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="free energy principle",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        p = papers[0]
        assert p.title == "The free-energy principle: a unified brain theory?"
        assert p.year == 2010
        assert p.doi == "10.1038/nrn2787"  # https://doi.org/ prefix stripped
        assert p.openalex_id == "https://openalex.org/W2140"
        assert p.citation_count == 3500
        assert p.venue == "Nature Reviews Neuroscience"
        assert p.is_open_access is True
        assert p.pdf_url == "https://europepmc.org/articles/pmc2996528?pdf=render"
        assert p.full_text_source == "repository"

    def test_search_authors_parsed(self, httpserver: HTTPServer):
        """Authors with affiliation and ORCID are parsed."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="free energy principle",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert len(papers[0].authors) == 1
        assert papers[0].authors[0].name == "Karl Friston"
        assert papers[0].authors[0].affiliation == "University College London"
        assert papers[0].authors[0].orcid == "0000-0001-7984-8909"

    def test_search_abstract_reconstructed(self, httpserver: HTTPServer):
        """Abstract is reconstructed from inverted index."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="free energy principle",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert "free energy principle provides" in papers[0].abstract.lower()

    def test_search_null_abstract(self, httpserver: HTTPServer):
        """Paper with null abstract_inverted_index has empty abstract."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="active inference",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert papers[1].abstract == ""

    def test_search_null_venue(self, httpserver: HTTPServer):
        """Paper with no primary_location has venue=None."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="active inference",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert papers[1].venue is None
        assert papers[1].is_open_access is False
        assert papers[1].pdf_url is None

    def test_search_empty_results(self, httpserver: HTTPServer):
        """Empty search results return empty list."""
        httpserver.expect_request("/works").respond_with_json(EMPTY_SEARCH_RESPONSE)

        papers = search_openalex(
            query="nonexistent topic xyz",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_http_error(self, httpserver: HTTPServer):
        """HTTP error after retries is swallowed and returns empty list."""
        httpserver.expect_request("/works").respond_with_data("Service Unavailable", status=503)

        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers == []

    def test_search_with_session(self, httpserver: HTTPServer):
        """Search works with a provided session."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        session = requests.Session()
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            session=session,
            delay_override=lambda _: None,
        )
        session.close()

        assert len(papers) == 2

    def test_search_multiple_authors(self, httpserver: HTTPServer):
        """Second result with multiple authors parsed correctly."""
        httpserver.expect_request("/works").respond_with_json(SEARCH_RESPONSE)

        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )

        p = papers[1]
        assert len(p.authors) == 2
        assert p.authors[0].name == "Karl Friston"
        assert p.authors[0].affiliation is None  # no institutions
        assert p.authors[1].name == "Thomas FitzGerald"
        assert p.authors[1].affiliation == "Max Planck Institute"


# ---------------------------------------------------------------------------
# get_work_by_doi tests
# ---------------------------------------------------------------------------


class TestGetWorkByDoi:
    """Tests for DOI-based work retrieval."""

    def test_get_work(self, httpserver: HTTPServer):
        """get_work_by_doi returns a Paper with correct fields."""
        httpserver.expect_request("/works/https://doi.org/10.1038/nrn2787").respond_with_json(SINGLE_WORK_RESPONSE)

        paper = get_work_by_doi(
            doi="10.1038/nrn2787",
            base_url=httpserver.url_for(""),
        )

        assert isinstance(paper, Paper)
        assert paper.title == "The free-energy principle: a unified brain theory?"
        assert paper.doi == "10.1038/nrn2787"
        assert paper.year == 2010
        assert paper.citation_count == 3500
        assert paper.venue == "Nature Reviews Neuroscience"

    def test_get_work_abstract(self, httpserver: HTTPServer):
        """Abstract is reconstructed from inverted index in DOI lookup."""
        httpserver.expect_request("/works/https://doi.org/10.1038/nrn2787").respond_with_json(SINGLE_WORK_RESPONSE)

        paper = get_work_by_doi(
            doi="10.1038/nrn2787",
            base_url=httpserver.url_for(""),
        )

        assert paper.abstract == "The free-energy principle."

    def test_get_work_not_found(self, httpserver: HTTPServer):
        """404 response raises exception."""
        httpserver.expect_request("/works/https://doi.org/10.9999/nonexistent").respond_with_data(
            '{"error": "Not found"}', status=404
        )

        with pytest.raises(Exception):
            get_work_by_doi(
                doi="10.9999/nonexistent",
                base_url=httpserver.url_for(""),
            )

    def test_get_work_canonical_id(self, httpserver: HTTPServer):
        """Paper from DOI lookup has doi: canonical_id."""
        httpserver.expect_request("/works/https://doi.org/10.1038/nrn2787").respond_with_json(SINGLE_WORK_RESPONSE)

        paper = get_work_by_doi(
            doi="10.1038/nrn2787",
            base_url=httpserver.url_for(""),
        )

        assert paper.canonical_id == "doi:10.1038/nrn2787"

    def test_get_work_with_session(self, httpserver: HTTPServer):
        """get_work_by_doi works with a provided session."""
        httpserver.expect_request("/works/https://doi.org/10.1038/nrn2787").respond_with_json(SINGLE_WORK_RESPONSE)

        session = requests.Session()
        paper = get_work_by_doi(
            doi="10.1038/nrn2787",
            base_url=httpserver.url_for(""),
            session=session,
        )
        session.close()

        assert paper.title == "The free-energy principle: a unified brain theory?"

    def test_get_work_orcid_parsed(self, httpserver: HTTPServer):
        """ORCID URL prefix is stripped from author ORCID."""
        httpserver.expect_request("/works/https://doi.org/10.1038/nrn2787").respond_with_json(SINGLE_WORK_RESPONSE)

        paper = get_work_by_doi(
            doi="10.1038/nrn2787",
            base_url=httpserver.url_for(""),
        )

        assert paper.authors[0].orcid == "0000-0001-7984-8909"


class TestOpenAlexPaginationAndRetry:
    """Tests for cursor pagination and retry logic."""

    def test_cursor_pagination(self, httpserver: HTTPServer):
        """search_openalex follows cursor pagination."""
        # Page 1: full page, next_cursor="c2"
        page1 = {
            "meta": {"count": 250, "next_cursor": "c2", "per_page": 200},
            "results": [{"id": f"W{i}", "title": f"Work {i}"} for i in range(200)],
        }
        # Page 2: remaining 50, next_cursor="c3"
        page2 = {
            "meta": {"count": 250, "next_cursor": "c3", "per_page": 50},
            "results": [{"id": f"W{i + 200}", "title": f"Work {i + 200}"} for i in range(50)],
        }

        # Initial request uses cursor="*" and per_page=200 (capped)
        httpserver.expect_request(
            "/works", query_string={"search": "test", "per_page": "200", "cursor": "*"}
        ).respond_with_json(page1)

        # Next request uses cursor="c2" and per_page=50 (remaining)
        httpserver.expect_request(
            "/works", query_string={"search": "test", "per_page": "50", "cursor": "c2"}
        ).respond_with_json(page2)

        papers = search_openalex(
            query="test",
            max_results=250,
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert len(papers) == 250
        assert papers[0].title == "Work 0"
        assert papers[249].title == "Work 249"

    def test_retry_on_error(self, httpserver: HTTPServer):
        """search retries on 429/500/503 (up to 1 time) and recovers."""
        # Fail once then succeed
        httpserver.expect_ordered_request("/works").respond_with_data("Error", status=503)
        httpserver.expect_ordered_request("/works").respond_with_json(
            {"meta": {}, "results": [{"id": "W1", "title": "Success"}]}
        )

        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert len(papers) == 1
        assert papers[0].title == "Success"


# ---------------------------------------------------------------------------
# Open access and full-text parsing edge cases
# ---------------------------------------------------------------------------


class TestOpenAlexOAParsing:
    """Tests for PDF URL and full_text_source resolution branches."""

    def test_oa_url_is_pdf(self, httpserver: HTTPServer):
        """oa_url ending in .pdf is used directly as pdf_url."""
        response = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "https://openalex.org/W9000",
                    "display_name": "OA Paper",
                    "publication_year": 2023,
                    "doi": None,
                    "authorships": [],
                    "cited_by_count": 10,
                    "abstract_inverted_index": None,
                    "primary_location": None,
                    "open_access": {
                        "is_oa": True,
                        "oa_url": "https://arxiv.org/pdf/2301.00001.pdf",
                    },
                    "best_oa_location": {},
                }
            ],
        }
        httpserver.expect_request("/works").respond_with_json(response)
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers[0].pdf_url == "https://arxiv.org/pdf/2301.00001.pdf"

    def test_journal_source_type(self, httpserver: HTTPServer):
        """best_oa_location with 'journal' source type → 'publisher'."""
        response = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "https://openalex.org/W9001",
                    "display_name": "Journal Paper",
                    "publication_year": 2023,
                    "doi": None,
                    "authorships": [],
                    "cited_by_count": 5,
                    "abstract_inverted_index": None,
                    "primary_location": None,
                    "open_access": {"is_oa": True},
                    "best_oa_location": {
                        "pdf_url": "https://journal.org/paper.pdf",
                        "source": {"type": "journal", "display_name": "Some Journal"},
                    },
                }
            ],
        }
        httpserver.expect_request("/works").respond_with_json(response)
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers[0].pdf_url == "https://journal.org/paper.pdf"
        assert papers[0].full_text_source == "publisher"

    def test_unknown_source_type_fallback(self, httpserver: HTTPServer):
        """Unknown source type defaults to 'openalex'."""
        response = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "https://openalex.org/W9002",
                    "display_name": "Unknown Source Paper",
                    "publication_year": 2023,
                    "doi": None,
                    "authorships": [],
                    "cited_by_count": 0,
                    "abstract_inverted_index": None,
                    "primary_location": None,
                    "open_access": {"is_oa": True},
                    "best_oa_location": {
                        "pdf_url": "https://other.org/paper.pdf",
                        "source": {"type": "other", "display_name": "Other"},
                    },
                }
            ],
        }
        httpserver.expect_request("/works").respond_with_json(response)
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers[0].full_text_source == "openalex"

    def test_referenced_works_parsed(self, httpserver: HTTPServer):
        """referenced_works URLs are parsed to openalex: prefixed IDs."""
        response = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "https://openalex.org/W9003",
                    "display_name": "Referencing Paper",
                    "publication_year": 2024,
                    "doi": "https://doi.org/10.1000/refs",
                    "authorships": [],
                    "cited_by_count": 0,
                    "abstract_inverted_index": None,
                    "primary_location": None,
                    "open_access": {"is_oa": False},
                    "referenced_works": [
                        "https://openalex.org/W1111",
                        "https://openalex.org/W2222",
                    ],
                }
            ],
        }
        httpserver.expect_request("/works").respond_with_json(response)
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers[0].references == ["openalex:W1111", "openalex:W2222"]

    def test_venue_from_primary_location(self, httpserver: HTTPServer):
        """Venue is extracted from primary_location.source.display_name."""
        response = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "https://openalex.org/W9004",
                    "display_name": "Venue Paper",
                    "publication_year": 2024,
                    "doi": None,
                    "authorships": [],
                    "cited_by_count": 0,
                    "abstract_inverted_index": None,
                    "primary_location": {
                        "source": {
                            "display_name": "Frontiers in Neuroscience",
                        }
                    },
                    "open_access": {"is_oa": False},
                }
            ],
        }
        httpserver.expect_request("/works").respond_with_json(response)
        papers = search_openalex(
            query="test",
            base_url=httpserver.url_for(""),
            delay_override=lambda _: None,
        )
        assert papers[0].venue == "Frontiers in Neuroscience"
