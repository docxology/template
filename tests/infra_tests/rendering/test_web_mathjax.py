"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import pytest

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

    @pytest.mark.parametrize("before_loader", ["<head>", "<head>\n  "], ids=["compact", "indented"])
    @pytest.mark.parametrize("closing_tag", ["</script>", "</script >"], ids=["plain", "with-whitespace"])
    def test_harden_mathjax_script_is_byte_stable(self, tmp_path, before_loader, closing_tag):
        html = tmp_path / "math.html"
        following = "</head><body><p>Manuscript text.</p></body></html>"
        html.write_text(
            f'<html>{before_loader}<script src="{_MATHJAX_URL}">{closing_tag}{following}',
            encoding="utf-8",
        )

        WebRenderer._harden_mathjax_script(html)
        first = html.read_bytes()
        assert first.startswith(f"<html>{before_loader}<script ".encode())
        assert first.endswith(following.encode())
        assert first.count(f'integrity="{_MATHJAX_INTEGRITY}"'.encode()) == 1
        assert first.count(f'src="{_MATHJAX_URL}"'.encode()) == 1

        WebRenderer._harden_mathjax_script(html)
        assert html.read_bytes() == first

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
