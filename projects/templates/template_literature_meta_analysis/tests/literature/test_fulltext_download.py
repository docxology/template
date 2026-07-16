"""Tests for the full-text resolver/downloader (no mocks; real HTTP via pytest-httpserver)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from literature.corpus import Corpus
from literature.fulltext_download import (
    assess_fulltext_availability,
    assess_fulltext_extraction,
    download_and_extract_fulltext,
    download_fulltext,
    extract_figures,
    extract_fulltext_text,
    resolve_fulltext_url,
)
from literature.models import Paper

pytest_httpserver = pytest.importorskip("pytest_httpserver")
reportlab = pytest.importorskip("reportlab")
PIL = pytest.importorskip("PIL")

from PIL import Image  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

KNOWN_TEXT_SUBSTRING = "modafinil-extraction-fixture-known-substring-42"


def _build_text_only_pdf(path: Path) -> None:
    """Write a real, text-only PDF (no embedded raster images) via reportlab."""
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 700, f"Full text extraction fixture: {KNOWN_TEXT_SUBSTRING}")
    c.drawString(72, 680, "A second line of body text for good measure.")
    c.showPage()
    c.save()


def _build_image_pdf(path: Path, tmp_path: Path) -> None:
    """Write a real PDF with one embedded raster image (a tiny solid-color PNG)."""
    img_path = tmp_path / "tiny_swatch.png"
    Image.new("RGB", (10, 10), color=(120, 40, 200)).save(img_path)

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 700, "Page with one embedded figure.")
    c.drawImage(str(img_path), 72, 600, width=10, height=10)
    c.showPage()
    c.save()


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
        "oa_locations": [{"url_for_pdf": "https://oa.example.org/loc.pdf"}],
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


def test_resolve_unpaywall_rejects_landing_only_location(httpserver) -> None:
    payload = {
        "best_oa_location": {"url": "https://oa.example.org/landing"},
        "oa_locations": [{"url": "https://oa.example.org/other-landing"}],
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

    assert url is None


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
    httpserver.expect_request("/x.pdf").respond_with_data(b"%PDF-bytes", content_type="application/pdf")
    out = download_fulltext(_paper(doi=None), tmp_path, url=httpserver.url_for("/x.pdf"), delay_override=0)
    assert out is not None and out.read_bytes() == b"%PDF-bytes"


def test_download_no_url_returns_none(tmp_path: Path) -> None:
    assert download_fulltext(_paper(doi=None), tmp_path, delay_override=0) is None


def test_download_http_error_returns_none(httpserver, tmp_path: Path) -> None:
    httpserver.expect_request("/missing.pdf").respond_with_data("no", status=404)
    out = download_fulltext(_paper(pdf_url=httpserver.url_for("/missing.pdf")), tmp_path, delay_override=0)
    assert out is None


def test_download_retries_on_transient_then_succeeds(httpserver, tmp_path: Path) -> None:
    httpserver.expect_ordered_request("/r.pdf").respond_with_data("busy", status=503)
    httpserver.expect_ordered_request("/r.pdf").respond_with_data(b"%PDF-OK", content_type="application/pdf")
    out = download_fulltext(_paper(pdf_url=httpserver.url_for("/r.pdf")), tmp_path, delay_override=0)
    assert out is not None and out.read_bytes() == b"%PDF-OK"


def test_download_rejects_html_with_http_200(httpserver, tmp_path: Path) -> None:
    httpserver.expect_request("/landing").respond_with_data(
        "<html>publisher landing page</html>",
        content_type="text/html",
    )

    out = download_fulltext(
        _paper(pdf_url=httpserver.url_for("/landing")),
        tmp_path,
        delay_override=0,
    )

    assert out is None
    assert list(tmp_path.glob("*.pdf")) == []


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
    assert stats["by_source"] == {"repository": 1}


def test_assess_empty_corpus() -> None:
    stats = assess_fulltext_availability([])
    assert stats["total"] == 0
    assert stats["pct_with_pdf_url"] == 0.0
    assert stats["by_source"] == {}


# ---------------------------------------------------------------------------
# extract_fulltext_text / extract_figures (real PDFs built with reportlab)
# ---------------------------------------------------------------------------


def test_extract_fulltext_text_from_text_only_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "text_only.pdf"
    _build_text_only_pdf(pdf_path)

    text = extract_fulltext_text(pdf_path)
    assert text is not None
    assert KNOWN_TEXT_SUBSTRING in text


def test_extract_figures_from_text_only_pdf_is_empty(tmp_path: Path) -> None:
    pdf_path = tmp_path / "text_only.pdf"
    _build_text_only_pdf(pdf_path)

    figures = extract_figures(pdf_path, tmp_path / "figures", stem="paper")
    assert figures == []


def test_extract_figures_from_image_pdf_writes_openable_image(tmp_path: Path) -> None:
    pdf_path = tmp_path / "with_image.pdf"
    _build_image_pdf(pdf_path, tmp_path)

    dest_dir = tmp_path / "figures"
    figures = extract_figures(pdf_path, dest_dir, stem="paper")

    assert len(figures) >= 1
    for fig_path in figures:
        assert fig_path.exists()
        assert fig_path.stat().st_size > 0
        assert fig_path.parent == dest_dir
        # Real, openable image bytes -- not just a non-empty file.
        with Image.open(fig_path) as im:
            im.verify()


def test_extract_fulltext_text_corrupt_pdf_returns_none(tmp_path: Path) -> None:
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"not a pdf")

    assert extract_fulltext_text(pdf_path) is None


def test_extract_figures_corrupt_pdf_returns_empty_list(tmp_path: Path) -> None:
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"not a pdf")

    assert extract_figures(pdf_path, tmp_path / "figures", stem="paper") == []


# ---------------------------------------------------------------------------
# download_and_extract_fulltext (end-to-end via pytest-httpserver)
# ---------------------------------------------------------------------------


def test_download_and_extract_fulltext_end_to_end(httpserver, tmp_path: Path) -> None:
    pdf_bytes_path = tmp_path / "_source.pdf"
    _build_text_only_pdf(pdf_bytes_path)
    pdf_bytes = pdf_bytes_path.read_bytes()

    httpserver.expect_request("/full.pdf").respond_with_data(pdf_bytes, content_type="application/pdf")
    p = _paper(pdf_url=httpserver.url_for("/full.pdf"))

    dest_dir = tmp_path / "dest"
    result = download_and_extract_fulltext(p, dest_dir, delay_override=0)

    assert result["pdf_path"] is not None
    assert result["pdf_path"].exists()
    assert result["pdf_path"].read_bytes() == pdf_bytes

    assert result["text_path"] is not None
    assert result["text_path"].exists()
    assert KNOWN_TEXT_SUBSTRING in result["text_path"].read_text(encoding="utf-8")

    assert result["figure_paths"] == []


def test_download_and_extract_fulltext_no_pdf_returns_none_fields(tmp_path: Path) -> None:
    result = download_and_extract_fulltext(_paper(doi=None), tmp_path, delay_override=0)
    assert result == {"pdf_path": None, "text_path": None, "figure_paths": []}


def test_download_and_extract_fulltext_idempotent(httpserver, tmp_path: Path) -> None:
    pdf_bytes_path = tmp_path / "_source.pdf"
    _build_text_only_pdf(pdf_bytes_path)
    pdf_bytes = pdf_bytes_path.read_bytes()

    httpserver.expect_request("/full2.pdf").respond_with_data(pdf_bytes, content_type="application/pdf")
    p = _paper(pdf_url=httpserver.url_for("/full2.pdf"))

    dest_dir = tmp_path / "dest"
    first = download_and_extract_fulltext(p, dest_dir, delay_override=0)
    second = download_and_extract_fulltext(p, dest_dir, delay_override=0)

    assert first["pdf_path"] == second["pdf_path"]
    assert first["text_path"] == second["text_path"]
    assert first["figure_paths"] == second["figure_paths"] == []


# ---------------------------------------------------------------------------
# assess_fulltext_extraction (filesystem-aware sibling of assess_corpus)
# ---------------------------------------------------------------------------


def test_assess_fulltext_extraction_counts_text_and_figures(tmp_path: Path) -> None:
    p1 = Paper(title="Has both", doi="10.1/one")
    p2 = Paper(title="Has text only", doi="10.1/two")
    p3 = Paper(title="Has neither", doi="10.1/three")
    corpus = Corpus([p1, p2, p3])

    (tmp_path / f"{_safe_filename_for(p1)}.txt").write_text("body", encoding="utf-8")
    (tmp_path / f"{_safe_filename_for(p2)}.txt").write_text("body", encoding="utf-8")
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()
    (figures_dir / f"{_safe_filename_for(p1)}_fig1.png").write_bytes(b"\x89PNG")

    stats = assess_fulltext_extraction(corpus, tmp_path)
    assert stats["total_papers"] == 3
    assert stats["with_extracted_text"] == 2
    assert stats["without_extracted_text"] == 1
    assert stats["with_extracted_figures"] == 1
    assert stats["without_extracted_figures"] == 2


def test_assess_fulltext_extraction_empty_dir(tmp_path: Path) -> None:
    corpus = Corpus([Paper(title="Lonely paper", doi="10.1/lonely")])
    stats = assess_fulltext_extraction(corpus, tmp_path / "does_not_exist")
    assert stats["total_papers"] == 1
    assert stats["with_extracted_text"] == 0
    assert stats["with_extracted_figures"] == 0
    assert stats["percent_with_extracted_text"] == 0.0


def _safe_filename_for(paper: Paper) -> str:
    from literature.fulltext_download import _safe_filename

    return _safe_filename(paper.canonical_id)
