"""Tests for the full-text resolver/downloader (no mocks; real HTTP via pytest-httpserver)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from literature.fulltext_download import (
    assess_fulltext_availability,
    download_fulltext,
    resolve_fulltext_url,
)
from literature.models import Paper

pytest_httpserver = pytest.importorskip("pytest_httpserver")


def _paper(**kw) -> Paper:
    base = {"title": "Modafinil and wakefulness", "doi": "10.5555/modafinil.0001"}
    base.update(kw)
    return Paper(**base)


def test_resolve_prefers_existing_pdf_url() -> None:
    p = _paper(pdf_url="https://example.org/a.pdf")
    assert resolve_fulltext_url(p) == "https://example.org/a.pdf"


def test_resolve_returns_none_without_doi_or_email() -> None:
    assert resolve_fulltext_url(_paper(doi=None)) is None
    assert resolve_fulltext_url(_paper(), unpaywall_email=None) is None


def test_resolve_via_unpaywall_best_oa_location(httpserver) -> None:
    payload = {
        "best_oa_location": {"url_for_pdf": "https://oa.example.org/full.pdf", "url": "https://oa.example.org/landing"},
        "oa_locations": [],
    }
    httpserver.expect_request("/v2/10.5555/modafinil.0001").respond_with_data(
        json.dumps(payload), content_type="application/json"
    )
    url = resolve_fulltext_url(
        _paper(),
        unpaywall_email="me@example.org",
        unpaywall_base_url=httpserver.url_for("/v2/"),
        delay_override=0,
    )
    assert url == "https://oa.example.org/full.pdf"


def test_resolve_via_unpaywall_falls_back_to_oa_locations(httpserver) -> None:
    payload = {
        "best_oa_location": None,
        "oa_locations": [{"url": "https://oa.example.org/loc.pdf"}],
    }
    httpserver.expect_request("/v2/10.5555/modafinil.0001").respond_with_data(
        json.dumps(payload), content_type="application/json"
    )
    url = resolve_fulltext_url(
        _paper(),
        unpaywall_email="me@example.org",
        unpaywall_base_url=httpserver.url_for("/v2/"),
        delay_override=0,
    )
    assert url == "https://oa.example.org/loc.pdf"


def test_resolve_unpaywall_no_oa(httpserver) -> None:
    httpserver.expect_request("/v2/10.5555/modafinil.0001").respond_with_data(
        json.dumps({"best_oa_location": None, "oa_locations": []}), content_type="application/json"
    )
    url = resolve_fulltext_url(
        _paper(),
        unpaywall_email="me@example.org",
        unpaywall_base_url=httpserver.url_for("/v2/"),
        delay_override=0,
    )
    assert url is None


def test_resolve_unpaywall_http_error_returns_none(httpserver) -> None:
    httpserver.expect_request("/v2/10.5555/modafinil.0001").respond_with_data("nope", status=404)
    url = resolve_fulltext_url(
        _paper(),
        unpaywall_email="me@example.org",
        unpaywall_base_url=httpserver.url_for("/v2/"),
        delay_override=0,
    )
    assert url is None


def test_download_writes_pdf_bytes(httpserver, tmp_path: Path) -> None:
    pdf_bytes = b"%PDF-1.4 fake modafinil full text"
    httpserver.expect_request("/full.pdf").respond_with_data(pdf_bytes, content_type="application/pdf")
    p = _paper(pdf_url=httpserver.url_for("/full.pdf"))
    out = download_fulltext(p, tmp_path, delay_override=0)
    assert out is not None
    assert out.exists()
    assert out.read_bytes() == pdf_bytes
    # deterministic filename derived from canonical id (doi:10.5555/modafinil.0001)
    assert out.name == "doi_10.5555_modafinil.0001.pdf"


def test_download_explicit_url_skips_resolve(httpserver, tmp_path: Path) -> None:
    httpserver.expect_request("/x.pdf").respond_with_data(b"bytes", content_type="application/pdf")
    out = download_fulltext(_paper(doi=None), tmp_path, url=httpserver.url_for("/x.pdf"), delay_override=0)
    assert out is not None and out.read_bytes() == b"bytes"


def test_download_no_url_returns_none(tmp_path: Path) -> None:
    assert download_fulltext(_paper(doi=None), tmp_path, delay_override=0) is None


def test_download_http_error_returns_none(httpserver, tmp_path: Path) -> None:
    httpserver.expect_request("/missing.pdf").respond_with_data("no", status=404)
    out = download_fulltext(_paper(pdf_url=httpserver.url_for("/missing.pdf")), tmp_path, delay_override=0)
    assert out is None


def test_download_retries_on_transient_then_succeeds(httpserver, tmp_path: Path) -> None:
    httpserver.expect_ordered_request("/r.pdf").respond_with_data("busy", status=503)
    httpserver.expect_ordered_request("/r.pdf").respond_with_data(b"PDFOK", content_type="application/pdf")
    out = download_fulltext(_paper(pdf_url=httpserver.url_for("/r.pdf")), tmp_path, delay_override=0)
    assert out is not None and out.read_bytes() == b"PDFOK"


class _RaisingSession:
    """A real (non-mock) session whose GET always raises, to exercise the error path."""

    def get(self, *args, **kwargs):  # noqa: ANN002, ANN003
        import requests

        raise requests.ConnectionError("no network")


def test_request_exception_path_returns_none(tmp_path: Path) -> None:
    out = download_fulltext(
        _paper(doi=None),
        tmp_path,
        url="https://example.org/x.pdf",
        session=_RaisingSession(),
        delay_override=0,
    )
    assert out is None


def test_resolve_exception_path_returns_none() -> None:
    url = resolve_fulltext_url(
        _paper(),
        unpaywall_email="me@example.org",
        session=_RaisingSession(),
        delay_override=0,
    )
    assert url is None


def test_assess_fulltext_availability_counts() -> None:
    papers = [
        Paper(title="a", pdf_url="u1", is_open_access=True, full_text_source="repository"),
        Paper(title="b", is_open_access=True, full_text_source="publisher"),
        Paper(title="c", is_open_access=False),
        Paper(title="d"),  # unknown OA
    ]
    stats = assess_fulltext_availability(papers)
    assert stats["total"] == 4
    assert stats["has_pdf_url"] == 1
    assert stats["is_open_access"] == 2
    assert stats["not_open_access"] == 1
    assert stats["unknown_open_access"] == 1
    assert stats["pct_with_pdf_url"] == 25.0
    assert stats["by_source"] == {"repository": 1, "publisher": 1}


def test_assess_empty_corpus() -> None:
    stats = assess_fulltext_availability([])
    assert stats["total"] == 0
    assert stats["pct_with_pdf_url"] == 0.0
    assert stats["by_source"] == {}
