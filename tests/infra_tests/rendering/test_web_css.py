"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from ._web_renderer_test_helpers import _make_renderer


class TestCssIntegration:
    """Test CSS integration."""

    def test_rendered_html_includes_stylesheet_or_inline_style(self, tmp_path):
        """Combined HTML is not a bare unstyled fragment."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nBody", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        html = renderer.render(md).read_text(encoding="utf-8")
        assert "<style" in html.lower() or "stylesheet" in html.lower()


class TestEmbedCss:
    def test_embed_in_head(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        css_dir = Path(__file__).resolve().parent.parent.parent.parent / "infrastructure" / "rendering"
        css_file = css_dir / "ide_style.css"

        html_file = tmp_path / "test.html"
        html_file.write_text("<html><head><title>Test</title></head><body>Hi</body></html>")

        if css_file.exists():
            renderer._embed_css(html_file)
            content = html_file.read_text()
            assert "<style>" in content
        else:
            renderer._embed_css(html_file)

    def test_no_head_tag(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        html_file = tmp_path / "nohead.html"
        html_file.write_text("<html><body>Content</body></html>")
        renderer._embed_css(html_file)

    def test_embed_includes_shared_design_tokens(self, tmp_path):
        """Embedded CSS carries the shared --brand-1 token + a prefers-color-scheme block."""
        renderer = _make_renderer(tmp_path)
        css_file = (
            Path(__file__).resolve().parent.parent.parent.parent / "infrastructure" / "rendering" / "ide_style.css"
        )
        if not css_file.exists():
            pytest.skip("ide_style.css not present")
        html_file = tmp_path / "doc.html"
        html_file.write_text("<html><head><title>T</title></head><body>Hi</body></html>")
        renderer._embed_css(html_file)
        content = html_file.read_text()
        assert "--brand-1" in content
        assert "prefers-color-scheme" in content
        assert 'mjx-container[display="true"]' in content
        assert "color: #b91c1c" in content
        assert "text-decoration: underline" in content
        assert "text-decoration: none" not in content
        assert "min-height: 28px" in content
        assert "#TOC a" in content
        assert ".figure-full-size-link" in content
        assert "cursor: zoom-in" in content
        assert "width: min(1080px, calc(100vw - 3rem))" in content
        assert "overflow-x: clip" in content
        assert ".table-scroll" in content
        assert "overflow-x: auto" in content
        assert "white-space: pre-wrap" in content
        assert "pre > code.sourceCode > span" in content
        assert "pre.sourceCode code span" in content
        assert 'mjx-container[display="true"] { max-width: 100%; overflow: visible; }' in content
        assert ".figure-exact-values" in content
