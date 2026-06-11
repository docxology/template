"""HTTP-backend tests using pytest-httpserver (no mocks).

These tests bring up a real local HTTP server, point each backend at it, and
assert end-to-end behaviour.
"""

from __future__ import annotations


import pytest
from pytest_httpserver import HTTPServer

from infrastructure.search.literature.backends import (
    ArxivBackend,
    BackendError,
    CrossrefBackend,
    PaperclipBackend,
    UrllibHttpClient,
)
from infrastructure.search.literature.models import SearchQuery


# ---------------------------------------------------------------------------
# Crossref
# ---------------------------------------------------------------------------


CROSSREF_PAYLOAD = {
    "status": "ok",
    "message": {
        "items": [
            {
                "DOI": "10.1126/science.1213847",
                "title": ["Reproducible research in computational science"],
                "author": [{"given": "Roger D", "family": "Peng"}],
                "issued": {"date-parts": [[2011, 12]]},
                "container-title": ["Science"],
                "type": "journal-article",
                "volume": "334",
                "issue": "6060",
                "page": "1226-1227",
                "publisher": "AAAS",
                "abstract": "<jats:p>An <jats:i>interesting</jats:i> paper.</jats:p>",
                "subject": ["Computational science", "Reproducibility"],
                "score": 12.5,
                "URL": "https://doi.org/10.1126/science.1213847",
            }
        ]
    },
}


def test_crossref_parses_real_payload(httpserver: HTTPServer):
    httpserver.expect_request("/works").respond_with_json(CROSSREF_PAYLOAD)
    backend = CrossrefBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/works"),
    )
    results = backend.search(SearchQuery(text="reproducible research"))
    assert len(results) == 1
    p = results[0]
    assert p.id == "doi:10.1126/science.1213847"
    assert p.title == "Reproducible research in computational science"
    assert p.authors == ["Roger D Peng"]
    assert p.year == 2011
    assert p.doi == "10.1126/science.1213847"
    assert p.venue == "Science"
    assert p.venue_type == "journal"
    assert p.volume == "334"
    assert p.issue == "6060"
    assert p.pages == "1226-1227"
    assert p.publisher == "AAAS"
    # JATS XML stripped from abstract.
    assert "<jats:p>" not in (p.abstract or "")
    assert "interesting" in (p.abstract or "")
    assert p.score == 12.5
    assert p.source == "crossref"


def test_crossref_passes_year_filter_to_api(httpserver: HTTPServer):
    httpserver.expect_request(
        "/works",
        query_string={
            "query": "x",
            "rows": "10",
            "filter": "from-pub-date:2010,until-pub-date:2020-12-31",
        },
    ).respond_with_json({"message": {"items": []}})
    backend = CrossrefBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/works"),
    )
    results = backend.search(SearchQuery(text="x", year_min=2010, year_max=2020))
    assert results == []


def test_crossref_non_200_raises(httpserver: HTTPServer):
    httpserver.expect_request("/works").respond_with_data("internal error", status=500)
    backend = CrossrefBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/works"),
    )
    with pytest.raises(BackendError, match="HTTP 500"):
        backend.search(SearchQuery(text="x"))


def test_crossref_non_json_raises(httpserver: HTTPServer):
    httpserver.expect_request("/works").respond_with_data("<html>not json</html>", content_type="text/html")
    backend = CrossrefBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/works"),
    )
    with pytest.raises(BackendError, match="non-JSON"):
        backend.search(SearchQuery(text="x"))


def test_crossref_missing_authors_handled(httpserver: HTTPServer):
    httpserver.expect_request("/works").respond_with_json(
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1/x",
                        "title": ["Anon"],
                        "issued": {"date-parts": [[2024]]},
                        "type": "journal-article",
                    }
                ]
            }
        }
    )
    backend = CrossrefBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/works"),
    )
    results = backend.search(SearchQuery(text="anon"))
    assert results[0].authors == []
    assert results[0].year == 2024


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------


ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>arXiv Query: search_query=all:adam</title>
  <entry>
    <id>http://arxiv.org/abs/1412.6980v9</id>
    <published>2014-12-22T16:34:33Z</published>
    <title>
      Adam: A Method for Stochastic Optimization
    </title>
    <summary>
      We introduce Adam, an algorithm for first-order
      gradient-based optimization of stochastic
      objective functions.
    </summary>
    <author><name>Diederik P. Kingma</name></author>
    <author><name>Jimmy Ba</name></author>
    <arxiv:doi>10.48550/arXiv.1412.6980</arxiv:doi>
  </entry>
</feed>
"""


def test_arxiv_parses_atom_response(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data(ARXIV_ATOM, content_type="application/atom+xml")
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
    )
    results = backend.search(SearchQuery(text="adam"))
    assert len(results) == 1
    p = results[0]
    assert p.id == "arxiv:1412.6980"
    assert p.title.startswith("Adam: A Method")
    assert p.year == 2014
    assert p.authors == ["Diederik P. Kingma", "Jimmy Ba"]
    assert p.source == "arxiv"
    assert p.venue == "arXiv"
    assert p.venue_type == "preprint"
    assert p.doi == "10.48550/arXiv.1412.6980"
    assert p.pdf_url == "https://arxiv.org/pdf/1412.6980.pdf"
    # Whitespace collapsed in title and summary.
    assert "\n" not in p.title
    assert p.abstract is not None
    assert "first-order" in p.abstract


def test_arxiv_id_extraction_preserves_old_style_category() -> None:
    """Old-style (pre-2007) arXiv IDs keep their category prefix (ARX-1).

    The previous extractor dropped the category (cs/0309040 -> 0309040),
    producing a wrong Paper.id and a 404 pdf URL.
    """
    from infrastructure.search.literature.arxiv_backend import _arxiv_id_from_url

    assert _arxiv_id_from_url("http://arxiv.org/abs/2401.12345v2") == "2401.12345"
    assert _arxiv_id_from_url("http://arxiv.org/abs/cs/0309040v1") == "cs/0309040"
    assert _arxiv_id_from_url("http://arxiv.org/abs/hep-ph/9901001") == "hep-ph/9901001"
    assert _arxiv_id_from_url("2401.12345") == "2401.12345"


def test_arxiv_year_filter_applied_post_fetch(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data(ARXIV_ATOM, content_type="application/atom+xml")
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
    )
    results = backend.search(SearchQuery(text="adam", year_min=2020))
    assert results == []  # 2014 entry filtered out


def test_arxiv_non_xml_raises(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data("not xml at all")
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
    )
    with pytest.raises(BackendError, match="non-XML"):
        backend.search(SearchQuery(text="x"))


def test_arxiv_non_200_raises(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data("err", status=503)
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
    )
    with pytest.raises(BackendError, match="HTTP 503"):
        backend.search(SearchQuery(text="x"))


def test_arxiv_fetch_by_id_retries_on_429_then_succeeds(httpserver: HTTPServer):
    """Throttled responses are retried with exponential backoff until arXiv answers."""
    httpserver.expect_ordered_request("/api/query").respond_with_data("slow down", status=429)
    httpserver.expect_ordered_request("/api/query").respond_with_data("slow down", status=429)
    httpserver.expect_ordered_request("/api/query").respond_with_data(
        ARXIV_ATOM, content_type="application/atom+xml"
    )
    delays: list[float] = []
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
        retry_base_delay=0.01,
        sleeper=delays.append,
    )
    paper = backend.fetch_by_id("1412.6980")
    assert paper is not None
    assert paper.title.startswith("Adam: A Method")
    assert delays == [0.01, 0.02]  # exponential backoff actually applied


def test_arxiv_fetch_by_id_429_exhausts_retries(httpserver: HTTPServer):
    """Persistent throttling still raises BackendError after max_retries attempts."""
    for _ in range(4):  # initial request + 3 retries
        httpserver.expect_ordered_request("/api/query").respond_with_data("slow down", status=429)
    delays: list[float] = []
    backend = ArxivBackend(
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/api/query"),
        retry_base_delay=0.01,
        sleeper=delays.append,
    )
    with pytest.raises(BackendError, match="HTTP 429"):
        backend.fetch_by_id("1412.6980")
    assert len(delays) == 3


# ---------------------------------------------------------------------------
# Paperclip
# ---------------------------------------------------------------------------


def test_paperclip_requires_api_key():
    with pytest.raises(ValueError, match="api_key"):
        PaperclipBackend(api_key="")


# Paperclip uses an MCP-style JSON-RPC envelope. Newer responses return a
# `structuredContent.papers` list; older responses return CLI-style text in
# `content[].text`. We test both shapes.

PAPERCLIP_STRUCTURED_ENVELOPE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "structuredContent": {
            "papers": [
                {
                    "id": "arxiv:2501.12948",
                    "title": "DeepSeek-R1: A study of GRPO",
                    "authors": ["Author A", "Author B"],
                    "year": 2025,
                    "abstract": "We train DeepSeek-R1 using GRPO.",
                    "doi": None,
                    "venue": "arXiv",
                    "venue_type": "preprint",
                    "score": 0.91,
                }
            ]
        }
    },
}


def test_paperclip_sends_x_api_key_header(httpserver: HTTPServer):
    """The adapter must POST with X-API-Key (matching the SDK)."""
    httpserver.expect_request("/papers", method="POST", headers={"X-API-Key": "test-key"}).respond_with_json(
        PAPERCLIP_STRUCTURED_ENVELOPE
    )
    backend = PaperclipBackend(
        api_key="test-key",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    results = backend.search(SearchQuery(text="grpo"))
    assert len(results) == 1
    assert results[0].id == "arxiv:2501.12948"
    assert results[0].source == "paperclip"
    assert results[0].score == 0.91


def test_paperclip_posts_mcp_tools_call_payload(httpserver: HTTPServer):
    """Paperclip requests must use the repo-owned MCP-style JSON-RPC contract."""
    expected_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "paperclip",
            "arguments": {
                "command": "search 'active inference' -n 3 --since 2020",
                "description": "search 'active inference' -n 3 --since 2020",
                "skip_truncation": True,
            },
        },
    }
    httpserver.expect_request(
        "/mcp",
        method="POST",
        headers={"X-API-Key": "test-key", "Content-Type": "application/json"},
        json=expected_payload,
    ).respond_with_json(PAPERCLIP_STRUCTURED_ENVELOPE)
    backend = PaperclipBackend(
        api_key="test-key",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/mcp"),
    )

    results = backend.search(SearchQuery(text="active inference", max_results=3, year_min=2020))

    assert len(results) == 1
    assert results[0].source == "paperclip"


def test_paperclip_parses_structured_papers(httpserver: HTTPServer):
    httpserver.expect_request("/papers", method="POST").respond_with_json(PAPERCLIP_STRUCTURED_ENVELOPE)
    backend = PaperclipBackend(
        api_key="k",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    results = backend.search(SearchQuery(text="x"))
    assert len(results) == 1
    assert results[0].title.startswith("DeepSeek")


def test_paperclip_falls_back_to_text_content(httpserver: HTTPServer):
    """When result.content is text-only, parse titles from the CLI-style output."""
    text_envelope = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Found 2 papers\n"
                        "  1. Convex Optimization\n"
                        "     doi:10.1017/CBO9780511804441\n"
                        "  2. Adam: A method for stochastic optimization\n"
                        "     arxiv:1412.6980\n"
                    ),
                }
            ]
        },
    }
    httpserver.expect_request("/papers", method="POST").respond_with_json(text_envelope)
    backend = PaperclipBackend(
        api_key="k",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    results = backend.search(SearchQuery(text="x"))
    assert len(results) == 2
    assert any("Convex" in p.title for p in results)
    assert any(p.id.startswith("arxiv:") or p.id.startswith("doi:") for p in results)


def test_paperclip_non_200_raises(httpserver: HTTPServer):
    httpserver.expect_request("/papers", method="POST").respond_with_data("nope", status=401)
    backend = PaperclipBackend(
        api_key="bad",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    with pytest.raises(BackendError, match="HTTP 401"):
        backend.search(SearchQuery(text="x"))


def test_paperclip_mcp_error_envelope_raises(httpserver: HTTPServer):
    httpserver.expect_request("/papers", method="POST").respond_with_json(
        {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": "Internal error"}}
    )
    backend = PaperclipBackend(
        api_key="k",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    with pytest.raises(BackendError, match="MCP error"):
        backend.search(SearchQuery(text="x"))


def test_paperclip_skips_malformed_records(httpserver: HTTPServer):
    envelope = {
        "result": {
            "structuredContent": {
                "papers": [
                    {"id": "x"},  # missing title -> skipped
                    PAPERCLIP_STRUCTURED_ENVELOPE["result"]["structuredContent"]["papers"][0],
                ]
            }
        }
    }
    httpserver.expect_request("/papers", method="POST").respond_with_json(envelope)
    backend = PaperclipBackend(
        api_key="k",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/papers"),
    )
    results = backend.search(SearchQuery(text="x"))
    assert len(results) == 1
    assert results[0].title.startswith("DeepSeek")


# Regression: live MCP service emits CLI-style text with rich metadata
# rows (`<internal_id> · <venue> · <YYYY-MM-DD>`), an authors line, a
# DOI URL, and a quoted abstract. The text parser must extract all of
# these into Paper fields and canonicalise arxiv-shaped internal ids
# back to the `arxiv:<id>` form the rest of the codebase expects.
PAPERCLIP_LIVE_TEXT = (
    "Found 3 papers  [s_48a6feb1]\n\n"
    "  1. The Neural Correlates of Ambiguity and Risk in Human Decision-Making"
    " under an Active Inference Framework\n"
    "     Shuo Zhang, Yan Tian, Quanying Liu *, Haiyan Wu *\n"
    "     bio_271f14126cad · bioRxiv · 2023-09-18\n"
    "     https://doi.org/10.1101/2023.09.18.558250\n"
    '     "This study investigated how the brain represents and resolves'
    " ambiguity and risk in decision-making using an active inference"
    ' framework."\n\n'
    "  2. Whence the Expected Free Energy?\n"
    "     Beren Millidge, Alexander Tschantz, Christopher L Buckley\n"
    "     arx_2004.08128 · arXiv · 2020-04-17\n"
    '     "EFE origins in active inference."\n\n'
    "  3. Free Energy Projective Simulation (FEPS)\n"
    "     Jos\\'ephine Pazem, Marius Krumm, Alexander Q. Vining\n"
    "     arx_2411.14991 · arXiv · 2024-11-22\n"
    '     "FEPS models interpretable active inference agents."\n'
)


def test_paperclip_parses_live_cli_format_with_full_metadata(httpserver: HTTPServer):
    """End-to-end parse of the production CLI-style text envelope."""
    envelope = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [{"type": "text", "text": PAPERCLIP_LIVE_TEXT}],
            "isError": False,
        },
    }
    httpserver.expect_request("/mcp", method="POST").respond_with_json(envelope)
    backend = PaperclipBackend(
        api_key="k",
        http_client=UrllibHttpClient(),
        base_url=httpserver.url_for("/mcp"),
    )
    results = backend.search(SearchQuery(text="active inference"))
    assert len(results) == 3

    p1 = results[0]
    assert p1.id == "doi:10.1101/2023.09.18.558250"
    assert p1.title.startswith("The Neural Correlates")
    assert p1.authors == ["Shuo Zhang", "Yan Tian", "Quanying Liu", "Haiyan Wu"]
    assert p1.venue == "bioRxiv"
    assert p1.venue_type == "preprint"
    assert p1.year == 2023
    assert p1.doi == "10.1101/2023.09.18.558250"
    assert p1.url == "https://doi.org/10.1101/2023.09.18.558250"
    assert p1.abstract is not None and "active inference" in p1.abstract

    p2 = results[1]
    # arx_2004.08128 → canonical arxiv:2004.08128
    assert p2.id == "arxiv:2004.08128"
    assert p2.title == "Whence the Expected Free Energy?"
    assert p2.authors == ["Beren Millidge", "Alexander Tschantz", "Christopher L Buckley"]
    assert p2.venue == "arXiv"
    assert p2.venue_type == "preprint"
    assert p2.year == 2020
    assert p2.doi is None  # arXiv records have no DOI line in this format
    assert p2.abstract == "EFE origins in active inference."

    p3 = results[2]
    assert p3.id == "arxiv:2411.14991"
    assert p3.year == 2024


def test_paperclip_default_base_url_is_mcp():
    """The class default points at /mcp, not the legacy /papers HTML route."""
    backend = PaperclipBackend(api_key="k")
    assert backend.base_url == "https://paperclip.gxl.ai/mcp"
