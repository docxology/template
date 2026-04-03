"""Tests for infrastructure.rendering._pdf_figure_paths — comprehensive coverage."""


from infrastructure.rendering._pdf_figure_paths import (
    _normalize_path,
    _extract_filename,
    fix_figure_paths,
)


class TestNormalizePath:
    def test_basic_ascii(self):
        assert _normalize_path("figures/plot.png") == "figures/plot.png"

    def test_unicode_normalization(self):
        # NFC normalization should work
        result = _normalize_path("figures/caf\u00e9.png")
        assert "caf" in result


class TestExtractFilename:
    def test_output_figures_prefix(self):
        assert _extract_filename("../output/figures/plot.png") == "plot.png"

    def test_output_figures_no_dots(self):
        assert _extract_filename("output/figures/chart.pdf") == "chart.pdf"

    def test_relative_figures(self):
        assert _extract_filename("../figures/fig1.png") == "fig1.png"

    def test_dot_slash_figures(self):
        assert _extract_filename("./figures/fig2.png") == "fig2.png"

    def test_bare_slash_path(self):
        assert _extract_filename("some/deep/path/image.png") == "image.png"

    def test_backslash_path(self):
        assert _extract_filename("some\\path\\image.png") == "image.png"

    def test_bare_filename(self):
        assert _extract_filename("image.png") == "image.png"


class TestFixFigurePaths:
    def test_already_correct_format(self, tmp_path):
        tex = r"\includegraphics{../figures/plot.png}"
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert "../figures/plot.png" in result

    def test_fix_output_figures_path(self, tmp_path):
        tex = r"\includegraphics{../output/figures/plot.png}"
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "plot.png").write_bytes(b"PNG")
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert "../figures/plot.png" in result

    def test_fix_with_options(self, tmp_path):
        tex = r"\includegraphics[width=\textwidth]{../output/figures/chart.pdf}"
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "chart.pdf").write_bytes(b"PDF")
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert r"[width=\textwidth]" in result
        assert "../figures/chart.pdf" in result

    def test_missing_figure_file(self, tmp_path):
        tex = r"\includegraphics{../output/figures/missing.png}"
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        # Don't create the file
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert "../figures/missing.png" in result

    def test_multiple_figures(self, tmp_path):
        tex = (
            r"\includegraphics{../output/figures/fig1.png}" + "\n"
            r"\includegraphics{../output/figures/fig2.png}"
        )
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        (figures_dir / "fig1.png").write_bytes(b"PNG1")
        (figures_dir / "fig2.png").write_bytes(b"PNG2")
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert result.count("../figures/") == 2

    def test_fallback_output_figures(self, tmp_path):
        # Test the fallback string replacement for paths that regex misses
        tex = r"]{output/figures/plot.png}"
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert "]{../figures/plot.png}" in result

    def test_fallback_bare_figures(self, tmp_path):
        tex = r"]{figures/plot.png}"
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert "]{../figures/plot.png}" in result

    def test_no_figures(self, tmp_path):
        tex = "No figures here, just text."
        result = fix_figure_paths(tex, tmp_path / "manuscript", tmp_path / "pdf")
        assert result == tex
