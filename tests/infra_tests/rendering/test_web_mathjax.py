"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.rendering.web_renderer import (
    _MATHJAX_INTEGRITY,
    _MATHJAX_URL,
    WebRenderer,
)


class TestMathJaxIntegration:
    """Test MathJax integration."""

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
