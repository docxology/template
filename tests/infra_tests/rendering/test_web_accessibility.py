"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

from infrastructure.rendering.web_renderer import WebRenderer


def test_accessibility_postprocess_adds_landmarks_without_synthesizing_alt(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><head></head><body><figure><img src="plot.png" '
        'alt="very long raw \\delta caption"><figcaption aria-hidden="true">'
        "Figure 1: Paired effect $\\delta$ and likelihood \\(A_k\\) across seeds. Extra detail with math."
        "</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, language="en-GB")

    content = html_file.read_text(encoding="utf-8")
    assert '<html lang="en-GB">' in content
    assert content.index('class="skip-link"') < content.index('<main id="main-content"')
    assert '<a class="skip-link" href="#main-content">Skip to main content</a>' in content
    assert '<main id="main-content" tabindex="-1">' in content
    assert "aria-hidden" not in content
    assert 'alt="very long raw \\delta caption"' in content
    assert 'alt="Figure 1: Paired effect delta and likelihood A_k across seeds."' not in content

    WebRenderer._enhance_accessibility(html_file, language="en-GB")
    content = html_file.read_text(encoding="utf-8")
    assert content.count('class="skip-link"') == 1
    assert content.count('<main id="main-content"') == 1


def test_accessibility_main_starts_after_toc_so_skip_link_bypasses_it(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        "<html><body><header><h1>Title</h1></header>"
        '<nav id="TOC"><a href="#section">Section</a></nav>'
        '<h1 id="section">Section</h1><p>Content</p></body></html>',
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert content.index('class="skip-link"') < content.index('<nav id="TOC">')
    assert content.index("</nav>") < content.index('<main id="main-content"')
    assert content.index('<main id="main-content"') < content.index('<h1 id="section">')


def test_accessibility_wraps_wide_tables_without_body_scroll_idempotently(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        "<html><body><table><caption>Exact seed-level values</caption>"
        "<thead><tr><th>Seed</th></tr></thead><tbody><tr><td>1</td></tr></tbody>"
        "</table></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file)
    WebRenderer._enhance_accessibility(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert content.count('class="table-scroll"') == 1
    assert 'role="region"' in content
    assert 'tabindex="0"' in content
    assert 'aria-label="Scrollable table: Exact seed-level values"' in content
    assert content.count('data-responsive-table="true"') == 1
