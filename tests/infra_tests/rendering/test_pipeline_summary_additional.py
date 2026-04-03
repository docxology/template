"""Tests for infrastructure.rendering._pipeline_summary — additional coverage."""

from infrastructure.rendering._pipeline_summary import (
    _check_citations_used,
    log_rendering_summary,
)


class TestCheckCitationsUsed:
    def test_latex_cite(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"Some text \cite{smith2020} more text.")
        assert _check_citations_used(tmp_path) is True

    def test_citep(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"Text \citep{jones2021} end.")
        assert _check_citations_used(tmp_path) is True

    def test_citet(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"As shown by \citet{lee2022}.")
        assert _check_citations_used(tmp_path) is True

    def test_citeauthor(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"\citeauthor{brown2023} argued.")
        assert _check_citations_used(tmp_path) is True

    def test_citeyear(self, tmp_path):
        (tmp_path / "paper.md").write_text(r"In \citeyear{white2024}.")
        assert _check_citations_used(tmp_path) is True

    def test_bibtex_reference(self, tmp_path):
        (tmp_path / "paper.md").write_text("See @smith2020 for details.")
        assert _check_citations_used(tmp_path) is True

    def test_no_citations(self, tmp_path):
        (tmp_path / "paper.md").write_text("Plain text without any citations.")
        assert _check_citations_used(tmp_path) is False

    def test_empty_dir(self, tmp_path):
        assert _check_citations_used(tmp_path) is False

    def test_supplemental_dir(self, tmp_path):
        sup = tmp_path / "supplemental"
        sup.mkdir()
        (sup / "extra.md").write_text(r"Extra \cite{ref1} content.")
        assert _check_citations_used(tmp_path) is True

    def test_unreadable_file(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_bytes(b"\xff\xfe\x80\x81")
        # Should not crash
        result = _check_citations_used(tmp_path)
        assert isinstance(result, bool)


class TestLogRenderingSummary:
    def test_full_summary(self):
        summary = {
            "project": "demo",
            "combined_pdf": {"name": "demo_combined.pdf", "size_kb": 1024.5, "path": "/tmp/demo.pdf"},
            "combined_html": {"name": "index.html", "size_kb": 50.0, "path": "/tmp/index.html"},
            "individual_pdfs": [
                {"name": "01_intro.pdf", "size_kb": 200.0},
                {"name": "02_methods.pdf", "size_kb": 300.0},
            ],
            "web_outputs": [{"name": "section1.html", "size_kb": 10.0}],
            "slides": [{"name": "presentation.pdf", "size_kb": 500.0}],
            "total_size_kb": 2084.5,
        }
        # Should not raise
        log_rendering_summary(summary)

    def test_empty_summary(self):
        summary = {
            "project": "empty",
            "combined_pdf": None,
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        }
        log_rendering_summary(summary)

    def test_pdf_only_summary(self):
        summary = {
            "project": "test",
            "combined_pdf": {"name": "test.pdf", "size_kb": 100.0, "path": "/tmp/test.pdf"},
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 100.0,
        }
        log_rendering_summary(summary)
