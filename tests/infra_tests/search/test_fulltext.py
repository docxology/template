"""Tests for fulltext / abstract fetchers (no mocks; pytest-httpserver)."""

from __future__ import annotations

from pathlib import Path

from pytest_httpserver import HTTPServer

from infrastructure.search.literature import (
    AbstractFetcher,
    FulltextFetcher,
    Paper,
    enrich_papers,
    write_corpus,
)
from infrastructure.search.literature.fulltext import _safe_id

ARXIV_SUMMARY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1412.6980v9</id>
    <summary>
      We introduce Adam, an algorithm for first-order
      gradient-based optimization of stochastic objective functions.
    </summary>
  </entry>
</feed>
"""


class TestAbstractFetcher:
    def test_skipped_when_already_present(self):
        p = Paper(id="x", title="T", abstract="present")
        fetcher = AbstractFetcher()
        result = fetcher.fetch(p)
        assert result.status == "skipped"

    def test_arxiv_hit_populates_abstract(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/api/query").respond_with_data(
            ARXIV_SUMMARY_XML, content_type="application/atom+xml"
        )
        p = Paper(id="arxiv:1412.6980", title="Adam")
        fetcher = AbstractFetcher(
            arxiv_base_url=httpserver.url_for("/api/query"),
            cache_dir=tmp_path,
        )
        result = fetcher.fetch(p)
        assert result.status == "hit"
        assert "first-order" in p.abstract
        assert result.path is not None and result.path.exists()

    def test_cached_read_skips_network(self, httpserver: HTTPServer, tmp_path: Path):
        # Pre-populate cache; HTTP server should never be called.
        cache_path = tmp_path / f"abs_{_safe_id('arxiv:1234')}.txt"
        cache_path.write_text("cached abstract", encoding="utf-8")
        fetcher = AbstractFetcher(
            arxiv_base_url=httpserver.url_for("/never-called"),
            cache_dir=tmp_path,
        )
        p = Paper(id="arxiv:1234", title="x")
        result = fetcher.fetch(p)
        assert result.status == "cached"
        assert p.abstract == "cached abstract"

    def test_force_refetches(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/api/query").respond_with_data(
            ARXIV_SUMMARY_XML, content_type="application/atom+xml"
        )
        p = Paper(id="arxiv:1412.6980", title="x", abstract="stale")
        fetcher = AbstractFetcher(
            arxiv_base_url=httpserver.url_for("/api/query"),
            cache_dir=tmp_path,
        )
        result = fetcher.fetch(p, force=True)
        assert result.status == "hit"
        assert "first-order" in p.abstract

    def test_skipped_for_unsupported_id(self):
        p = Paper(id="random:abc", title="x")
        result = AbstractFetcher().fetch(p)
        assert result.status == "skipped"
        assert "no abstract source" in (result.message or "")

    def test_arxiv_non_200(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/query").respond_with_data("err", status=503)
        fetcher = AbstractFetcher(arxiv_base_url=httpserver.url_for("/api/query"))
        result = fetcher.fetch(Paper(id="arxiv:1", title="x"))
        assert result.status == "error"
        assert "503" in (result.message or "")

    def test_fetch_all_returns_one_per_paper(self):
        papers = [
            Paper(id="x:1", title="T", abstract="A"),
            Paper(id="x:2", title="T2", abstract="B"),
        ]
        results = AbstractFetcher().fetch_all(papers)
        assert len(results) == 2
        assert all(r.status == "skipped" for r in results)


class TestFulltextFetcher:
    def test_skipped_when_present(self):
        p = Paper(id="arxiv:1", title="x", fulltext="here")
        result = FulltextFetcher().fetch(p)
        assert result.status == "skipped"

    def test_skipped_when_no_url(self):
        p = Paper(id="random:1", title="x")
        result = FulltextFetcher().fetch(p)
        assert result.status == "skipped"

    def test_arxiv_pdf_url_resolution(self, httpserver: HTTPServer, tmp_path: Path):
        # Tiny synthetic PDF bytes — pypdf may or may not parse them; we
        # only assert the request was made and the file was cached.
        httpserver.expect_request("/pdf/1.pdf").respond_with_data(
            b"%PDF-1.4\n%fake\n", content_type="application/pdf"
        )
        fetcher = FulltextFetcher(cache_dir=tmp_path)
        # Override the URL to point at our local server.
        p = Paper(id="arxiv:1", title="x", pdf_url=httpserver.url_for("/pdf/1.pdf"))
        result = fetcher.fetch(p)
        # Without pypdf installed, status will be "error" with the cached
        # PDF path; with pypdf, it may be "error" (parse failure on the
        # synthetic PDF) — in either case the PDF must have been written.
        assert (tmp_path / f"{_safe_id('arxiv:1')}.pdf").exists()

    def test_non_200_returns_error(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/pdf").respond_with_data("nope", status=404)
        fetcher = FulltextFetcher(cache_dir=tmp_path)
        p = Paper(id="x:1", title="t", pdf_url=httpserver.url_for("/pdf"))
        result = fetcher.fetch(p)
        assert result.status == "error"
        assert "404" in (result.message or "")

    def test_uses_paper_pdf_url_attribute(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/p.pdf").respond_with_data(
            b"%PDF-1.4\n", content_type="application/pdf"
        )
        fetcher = FulltextFetcher(cache_dir=tmp_path)
        p = Paper(id="x:1", title="t", pdf_url=httpserver.url_for("/p.pdf"))
        fetcher.fetch(p)
        assert (tmp_path / f"{_safe_id('x:1')}.pdf").exists()

    def test_cached_text_short_circuits(self, tmp_path: Path):
        text_path = tmp_path / f"{_safe_id('arxiv:1')}.txt"
        text_path.write_text("cached body", encoding="utf-8")
        fetcher = FulltextFetcher(cache_dir=tmp_path)
        p = Paper(id="arxiv:1", title="x")
        result = fetcher.fetch(p)
        assert result.status == "cached"
        assert p.fulltext == "cached body"


class TestEnrichPipeline:
    def test_enrich_papers_runs_both_fetchers(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/api/query").respond_with_data(
            ARXIV_SUMMARY_XML, content_type="application/atom+xml"
        )
        httpserver.expect_request("/p.pdf").respond_with_data(
            b"%PDF-1.4\n", content_type="application/pdf"
        )
        p = Paper(
            id="arxiv:1412.6980",
            title="Adam",
            pdf_url=httpserver.url_for("/p.pdf"),
        )
        results = enrich_papers(
            [p],
            abstracts=AbstractFetcher(
                arxiv_base_url=httpserver.url_for("/api/query"),
                cache_dir=tmp_path / "abs",
            ),
            fulltext=FulltextFetcher(cache_dir=tmp_path / "ft"),
        )
        # One result per fetcher.
        assert len(results) == 2
        assert any(r.status == "hit" and "first-order" in (r.paper.abstract or "")
                   for r in results)


class TestWriteCorpus:
    def test_round_trip(self, tmp_path: Path):
        papers = [
            Paper(id="x:1", title="A", year=2020),
            Paper(id="x:2", title="B", year=2021, abstract="abs"),
        ]
        out = write_corpus(papers, tmp_path / "corpus.json")
        assert out.exists()
        # Check via LocalBackend round-trip.
        from infrastructure.search.literature import LocalBackend, SearchQuery
        backend = LocalBackend(out)
        results = backend.search(SearchQuery(text="A B"))
        assert len(results) == 2
