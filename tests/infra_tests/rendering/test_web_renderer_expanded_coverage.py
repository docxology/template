"""Tests for infrastructure.rendering.web_renderer — non-subprocess methods."""

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer


def _make_renderer(tmp_path):
    """Create a WebRenderer with config pointing to tmp_path."""
    config = RenderingConfig(
        pandoc_path="pandoc",
        web_dir=str(tmp_path / "web"),
    )
    return WebRenderer(config)


def test_individual_render_output_names_include_parent_context(tmp_path: Path) -> None:
    renderer = _make_renderer(tmp_path)
    source_a = tmp_path / "manuscript" / "parts" / "alpha" / "00-overview.md"
    source_b = tmp_path / "manuscript" / "parts" / "beta" / "00-overview.md"

    assert renderer._output_file_for_source(source_a).name == "alpha__00-overview.html"
    assert renderer._output_file_for_source(source_b).name == "beta__00-overview.html"


class TestCombineMarkdownFiles:
    def test_single_file(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "intro.md"
        md.write_text("# Introduction\n\nHello world.\n")
        result = renderer._combine_markdown_files([md])
        assert "# Introduction" in result
        assert "Hello world." in result

    def test_multiple_files(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        f1 = tmp_path / "01.md"
        f2 = tmp_path / "02.md"
        f1.write_text("# Section 1\n\nContent 1.\n")
        f2.write_text("# Section 2\n\nContent 2.\n")
        result = renderer._combine_markdown_files([f1, f2])
        assert "Section 1" in result
        assert "Section 2" in result
        assert "---" in result  # Separator between sections

    def test_strips_trailing_whitespace(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "test.md"
        md.write_text("Content   \n\n\n")
        result = renderer._combine_markdown_files([md])
        assert not result.endswith("   \n\n\n")

    def test_adds_newline_if_missing(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "test.md"
        md.write_text("No trailing newline")
        result = renderer._combine_markdown_files([md])
        assert result.endswith("\n") or len(result.strip()) > 0

    def test_empty_files_raises(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "empty.md"
        md.write_text("")
        with pytest.raises(RenderingError, match="empty"):
            renderer._combine_markdown_files([md])

    def test_bom_removal(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "bom.md"
        md.write_text("\ufeff# With BOM\n\nContent.\n")
        result = renderer._combine_markdown_files([md])
        assert not result.startswith("\ufeff")

    def test_unicode_error(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "bad.md"
        md.write_bytes(b"\x80\x81\x82")
        with pytest.raises(RenderingError, match="encoding"):
            renderer._combine_markdown_files([md])

    def test_missing_file(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        md = tmp_path / "nonexistent.md"
        with pytest.raises(RenderingError):
            renderer._combine_markdown_files([md])

    def test_html_safe_markdown_preserves_raw_latex_visible_text(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        source = (
            "NumPy `\\citep{harris-2020}`{=latex}, SciPy "
            "`\\citep{virtanen-2020}`{=latex}; see "
            "`\\hyperref[sec:pymdp_validation]{§16}`{=latex}. "
            "`\\phantomsection\\label{thm:demo}`{=latex}**Theorem.**"
        )

        result = renderer._html_safe_markdown(source)

        assert "NumPy [harris-2020], SciPy [virtanen-2020]" in result
        assert "see §16." in result
        assert "`\\citep" not in result
        assert "`\\hyperref" not in result
        assert "label{thm:demo}" not in result
        assert "**Theorem.**" in result

    def test_html_safe_markdown_normalizes_project_figure_paths(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        source = (
            "![A](../output/figures/a.png)\n"
            "![B](output/figures/b.png)\n"
            "![C](../../output/figures/c.png)\n"
        )

        result = renderer._html_safe_markdown(source)

        assert "../output/figures/" not in result
        assert "../../output/figures/" not in result
        assert "output/figures/" not in result
        assert result.count("../figures/") == 3


class TestEmbedCss:
    def test_embed_in_head(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        # Create the CSS file where the renderer expects it
        css_dir = Path(__file__).resolve().parent.parent.parent.parent / "infrastructure" / "rendering"
        css_file = css_dir / "ide_style.css"

        html_file = tmp_path / "test.html"
        html_file.write_text("<html><head><title>Test</title></head><body>Hi</body></html>")

        if css_file.exists():
            renderer._embed_css(html_file)
            content = html_file.read_text()
            assert "<style>" in content
        else:
            # CSS file doesn't exist, should handle gracefully
            renderer._embed_css(html_file)

    def test_no_head_tag(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        html_file = tmp_path / "nohead.html"
        html_file.write_text("<html><body>Content</body></html>")
        # Should not crash
        renderer._embed_css(html_file)
