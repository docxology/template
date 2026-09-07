"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import re

from infrastructure.rendering.web_renderer import (
    _MATHJAX_DYNAMIC_PREFIX,
    _MATHJAX_FONT_URL,
    _MATHJAX_INTEGRITY,
    _MATHJAX_URL,
    WebRenderer,
)

from ._web_renderer_test_helpers import _make_renderer


class TestMathJaxIntegration:
    """Test MathJax integration."""

    def test_render_with_mathjax(self, tmp_path):
        """Rendered math pages keep the equation and the pinned MathJax URL."""
        md = tmp_path / "math.md"
        md.write_text("# Math\n\n$E = mc^2$", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        result = renderer.render(md)
        html = result.read_text(encoding="utf-8")
        assert "E = mc^2" in html or "E = mc" in html
        assert _MATHJAX_URL in html

    def test_mathjax_config(self):
        """Pinned MathJax constants stay non-empty and point at a https URL."""
        assert _MATHJAX_URL.startswith("https://")
        assert _MATHJAX_INTEGRITY.startswith("sha")
        assert _MATHJAX_FONT_URL.startswith("https://")

    def test_harden_mathjax_script_adds_sri_to_pinned_url(self, tmp_path):
        html = tmp_path / "math.html"
        html.write_text(
            f'<html><head><script src="{_MATHJAX_URL}"></script></head><body></body></html>',
            encoding="utf-8",
        )

        WebRenderer._harden_mathjax_script(html)

        content = html.read_text(encoding="utf-8")
        assert f'src="{_MATHJAX_URL}"' in content
        assert f'integrity="{_MATHJAX_INTEGRITY}"' in content
        assert 'crossorigin="anonymous"' in content
        assert _MATHJAX_FONT_URL in content
        assert _MATHJAX_DYNAMIC_PREFIX in content
        assert content.index(_MATHJAX_FONT_URL) < content.index(_MATHJAX_URL)
        assert "aria-roledescription" in content
        assert "mathematical expression" in content
        assert 'displayOverflow: "linebreak"' in content
        assert 'width: "100%"' in content
        assert "lineleading: 0.5" in content

    def test_harden_mathjax_script_overwrites_wrong_sri_and_removes_duplicate_loader(self, tmp_path):
        html = tmp_path / "math.html"
        html.write_text(
            "<html><head>"
            f'<script src="{_MATHJAX_URL}" integrity="sha384-AAAA" crossorigin="use-credentials"></script>'
            f'<script defer src="{_MATHJAX_URL}?bypass=1">ignored</script>'
            "</head><body></body></html>",
            encoding="utf-8",
        )

        WebRenderer._harden_mathjax_script(html)

        content = html.read_text(encoding="utf-8")
        assert content.count(_MATHJAX_URL) == 1
        assert content.count(f'integrity="{_MATHJAX_INTEGRITY}"') == 1
        assert content.count('crossorigin="anonymous"') == 1
        assert "sha384-AAAA" not in content
        assert "use-credentials" not in content

    def test_harden_mathjax_script_replaces_untrusted_config_before_loader(self, tmp_path):
        html = tmp_path / "math.html"
        html.write_text(
            "<html><head>"
            f'<script src="{_MATHJAX_URL}"></script>'
            "<script data-template-mathjax-config></script>"
            "</head><body></body></html>",
            encoding="utf-8",
        )

        WebRenderer._harden_mathjax_script(html)

        content = html.read_text(encoding="utf-8")
        assert content.count("data-template-mathjax-config") == 1
        assert "window.MathJax.chtml" in content
        assert content.index("data-template-mathjax-config") < content.index(_MATHJAX_URL)

    def test_harden_mathjax_script_removes_line_owned_attributes_without_whitespace_residue(self, tmp_path):
        """Canonicalization removes a Pandoc-formatted source line cleanly."""
        html = tmp_path / "math.html"
        html.write_text(
            "<html><head>\n"
            '<script defer=""\n'
            "  \n"
            f'  type="text/javascript" nonce="alpha beta" src="{_MATHJAX_URL}"\n'
            f'  integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"></script>\n'
            "</head><body></body></html>\n",
            encoding="utf-8",
        )

        WebRenderer._harden_mathjax_script(html)
        WebRenderer._harden_mathjax_script(html)

        content = html.read_text(encoding="utf-8")
        assert re.search(r"(?m)^[ \t]+$", content) is None
        assert '<script defer=""\n  type="text/javascript" nonce="alpha beta"' in content
        assert content.count(f'src="{_MATHJAX_URL}"') == 1
