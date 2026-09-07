"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import (
    deployed_web_link_issues,
    repository_root_for,
    rewrite_repository_links,
)


def test_repository_link_rewrite_resolves_manuscript_paths_and_preserves_web_pages(tmp_path: Path) -> None:
    """Public web output maps source links without rewriting local pages."""
    repository_root = repository_root_for(Path(__file__))
    source = repository_root / "projects/templates/template_code_project/manuscript/01_introduction.md"
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "other.html").write_text("<html></html>", encoding="utf-8")
    html_file = web_dir / "manuscript__01_introduction.html"
    html_file.write_text(
        '<a href="../../../../docs/_generated/COUNTS.md#coverage">Counts</a>'
        '<a href="../../../../infrastructure/rendering/web_renderer.py?view=source">Renderer</a>'
        '<a href="01_introduction.md?view=source#intro">Source</a>'
        '<a href="other.html#part">Local page</a>'
        '<a data-href="01_introduction.md">Metadata</a>'
        '<a href="https://example.org/?a=1&amp;b=2">External</a>'
        '<a href="#local">Fragment</a>',
        encoding="utf-8",
    )

    rewrite_repository_links(
        html_file,
        repository_root=repository_root,
        rendered_sources={source: html_file.name},
    )

    content = html_file.read_text(encoding="utf-8")
    assert 'href="https://github.com/docxology/template/blob/main/docs/_generated/COUNTS.md#coverage"' in content
    assert (
        'href="https://github.com/docxology/template/blob/main/infrastructure/rendering/web_renderer.py?view=source"'
        in content
    )
    assert 'href="manuscript__01_introduction.html?view=source#intro"' in content
    assert 'href="other.html#part"' in content
    assert 'data-href="01_introduction.md"' in content
    assert 'href="https://example.org/?a=1&amp;b=2"' in content
    assert 'href="#local"' in content


def test_repository_link_rewrite_preserves_safe_renderer_figure_assets(
    tmp_path: Path,
) -> None:
    repository_root = repository_root_for(Path(__file__))
    source = repository_root / "projects/templates/template_code_project/manuscript/01_introduction.md"
    output = tmp_path / "output"
    web_dir = output / "web"
    figures_dir = output / "figures"
    web_dir.mkdir(parents=True)
    figures_dir.mkdir()
    (figures_dir / "figure_exact_values.md").write_text("# Exact values\n", encoding="utf-8")
    html_file = web_dir / "index.html"
    html_file.write_text(
        '<a href="../figures/figure_exact_values.md#fig-values-dense">Exact values</a>',
        encoding="utf-8",
    )

    rewrite_repository_links(
        html_file,
        repository_root=repository_root,
        rendered_sources={source: html_file.name},
    )

    assert 'href="../figures/figure_exact_values.md#fig-values-dense"' in html_file.read_text(encoding="utf-8")


def test_repository_link_rewrite_rejects_unsafe_uri_schemes(tmp_path: Path) -> None:
    """Renderer-owned anchors fail closed for executable URI schemes."""
    repository_root = repository_root_for(Path(__file__))
    source = repository_root / "projects/templates/template_code_project/manuscript/01_introduction.md"
    html_file = tmp_path / "page.html"
    html_file.write_text('<a href="javascript:alert(1)">unsafe</a>', encoding="utf-8")

    with pytest.raises(RenderingError, match="unsupported URI scheme"):
        rewrite_repository_links(
            html_file,
            repository_root=repository_root,
            rendered_sources={source: html_file.name},
        )


def test_repository_link_rewrite_rejects_isolated_paths(tmp_path: Path) -> None:
    """Public-link rewriting never guesses a repository for an isolated render."""
    with pytest.raises(RenderingError, match="Could not locate public repository root"):
        repository_root_for(tmp_path / "isolated.html")


def test_deployed_web_link_issues_reports_missing_local_renderer_links(tmp_path: Path) -> None:
    """The deployed-web scan reports missing local anchors but accepts fragments."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "index.html").write_text(
        '<a href="missing.html">Missing</a><a href="#section">Section</a><a href="https://example.org">External</a>',
        encoding="utf-8",
    )
    (web_dir / "chapter__one.html").write_text('<a href="../outside.html">Outside</a>', encoding="utf-8")

    issues = deployed_web_link_issues(web_dir)

    assert len(issues) == 2
    assert any("missing.html" in issue for issue in issues)
    assert any("outside.html" in issue for issue in issues)


def test_deployed_web_link_issues_accepts_safe_sibling_figure_assets(tmp_path: Path) -> None:
    output = tmp_path / "output"
    web_dir = output / "web"
    figures_dir = output / "figures"
    web_dir.mkdir(parents=True)
    figures_dir.mkdir()
    (figures_dir / "dense.png").write_bytes(b"image")
    (figures_dir / "figure_exact_values.md").write_text("# Exact values\n", encoding="utf-8")
    (web_dir / "index.html").write_text(
        '<a href="../figures/dense.png">Figure</a>'
        '<a href="../figures/figure_exact_values.md#fig-values-dense">Exact values</a>',
        encoding="utf-8",
    )

    assert deployed_web_link_issues(web_dir) == ()


def test_deployed_web_link_issues_reports_missing_local_img_sources(tmp_path: Path) -> None:
    """The deployed-web scan fails closed on missing local image sources."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "figures").mkdir()
    (web_dir / "figures" / "present.png").write_bytes(b"image")
    (web_dir / "index.html").write_text(
        '<img src="figures/missing.png" alt="Missing">'
        '<img src="figures/present.png" alt="Present">'
        '<img src="https://example.org/remote.png" alt="Remote">'
        '<img src="data:image/png;base64,AAA=" alt="Inline">',
        encoding="utf-8",
    )

    issues = deployed_web_link_issues(web_dir)

    assert len(issues) == 1
    assert "img src" in issues[0]
    assert "figures/missing.png" in issues[0]


def test_deployed_web_link_issues_rejects_unsupported_img_schemes(tmp_path: Path) -> None:
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "index.html").write_text('<img src="javascript:alert(1)" alt="Bad">', encoding="utf-8")

    issues = deployed_web_link_issues(web_dir)

    assert len(issues) == 1
    assert "unsupported img src scheme" in issues[0]
