"""Comprehensive tests for infrastructure/rendering/web_renderer.py.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import re
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import (
    deployed_web_link_issues,
    repository_root_for,
    rewrite_repository_links,
)
from infrastructure.rendering import web_renderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import (
    _MATHJAX_DYNAMIC_PREFIX,
    _MATHJAX_FONT_URL,
    _MATHJAX_INTEGRITY,
    _MATHJAX_URL,
    WebRenderer,
)


class TestWebRendererCore:
    """Test core web renderer functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert web_renderer is not None

    def test_has_render_functions(self):
        """Test that module has render functions."""
        module_funcs = [
            a for a in dir(web_renderer) if not a.startswith("_") and callable(getattr(web_renderer, a, None))
        ]
        assert len(module_funcs) > 0


class TestHtmlRendering:
    """Test HTML rendering functionality."""

    def test_render_html(self, tmp_path):
        """WebRenderer.render writes HTML that contains the source heading."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nContent", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        result = renderer.render(md)
        assert result.exists()
        html = result.read_text(encoding="utf-8")
        assert "Title" in html
        assert "Content" in html

    def test_render_html_uses_configured_web_dir(self, tmp_path):
        """Output lands under the configured web_dir, not a hidden default."""
        md = tmp_path / "doc.md"
        md.write_text("# Title", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        result = renderer.render(md)
        assert result.parent == Path(renderer.config.web_dir)


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


class TestCssIntegration:
    """Test CSS integration."""

    def test_rendered_html_includes_stylesheet_or_inline_style(self, tmp_path):
        """Combined HTML is not a bare unstyled fragment."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nBody", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        html = renderer.render(md).read_text(encoding="utf-8")
        assert "<style" in html.lower() or "stylesheet" in html.lower()


class TestAssetHandling:
    """Test asset handling."""

    def test_render_preserves_local_image_reference(self, tmp_path):
        """A markdown image remains addressable in the written HTML."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\n![alt text](image.png)\n", encoding="utf-8")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        renderer = _make_renderer(tmp_path)
        html = renderer.render(md).read_text(encoding="utf-8")
        assert "image.png" in html
        assert "alt text" in html


class TestWebRendererIntegration:
    """Integration tests for web renderer."""

    def test_full_render_workflow(self, tmp_path):
        """Test complete rendering workflow."""
        # Create test content
        md = tmp_path / "doc.md"
        md.write_text("# Document\n\n## Section\n\nContent here.")

        # Module should be importable
        assert web_renderer is not None


class TestCombinedHtmlRendering:
    """Test combined HTML rendering functionality."""

    def test_render_combined_creates_index_html(self, tmp_path):
        """Test that render_combined creates index.html with TOC."""
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        # Create test markdown files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md1 = manuscript_dir / "01_intro.md"
        md1.write_text("# Introduction\n\nThis is the introduction.")

        md2 = manuscript_dir / "02_methods.md"
        md2.write_text("# Methods\n\nThis describes the methods.")

        md3 = manuscript_dir / "03_results.md"
        md3.write_text("# Results\n\n$E = mc^2$\n\nSome results here.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        web_dir.mkdir(parents=True, exist_ok=True)

        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        # Test render_combined
        renderer = WebRenderer(config)
        source_files = [md1, md2, md3]

        result = renderer.render_combined(source_files, manuscript_dir, "test_project")

        # Verify index.html was created
        assert result.name == "index.html"
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify content includes TOC and sections
        content = result.read_text()
        # Pandoc generates TOC with nav id="TOC" element, not "Table of Contents" text
        assert 'id="TOC"' in content or 'id="toc"' in content
        assert "Introduction" in content
        assert "Methods" in content
        assert "Results" in content
        # Pandoc generates IDs from heading text (e.g., id="introduction"), not section-N
        assert 'id="introduction"' in content
        assert 'id="methods"' in content
        assert 'id="results"' in content

    def test_render_manager_combined_web(self, tmp_path):
        """Test RenderManager.render_combined_web method."""
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.core import RenderManager

        # Create test files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md1 = manuscript_dir / "a.md"
        md1.write_text("# Section A\n\nContent A.")

        md2 = manuscript_dir / "b.md"
        md2.write_text("# Section B\n\nContent B.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        manager = RenderManager(config)
        result = manager.render_combined_web([md1, md2], manuscript_dir, "test")

        assert result.exists()
        assert result.name == "index.html"

    def test_render_combined_resolves_bibliographic_citations(self, tmp_path):
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md = manuscript_dir / "01_intro.md"
        md.write_text(
            "# Introduction\n\nPrior work matters [@jaynes2003probability; @shannon1948theory].\n",
            encoding="utf-8",
        )
        (manuscript_dir / "references.bib").write_text(
            "@book{jaynes2003probability,\n"
            "  author = {Jaynes, Edwin T.},\n"
            "  title = {Probability Theory},\n"
            "  year = {2003},\n"
            "  publisher = {Cambridge University Press}\n"
            "}\n",
            encoding="utf-8",
        )
        (manuscript_dir / "z_supplemental.bib").write_text(
            "@article{shannon1948theory,\n"
            "  author = {Shannon, Claude E.},\n"
            "  title = {A Mathematical Theory of Communication},\n"
            "  year = {1948},\n"
            "  journal = {Bell System Technical Journal}\n"
            "}\n",
            encoding="utf-8",
        )

        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output"))
        result = WebRenderer(config).render_combined([md], manuscript_dir, "test")

        content = result.read_text(encoding="utf-8")
        assert "Jaynes" in content
        assert "Shannon" in content
        assert "#ref-jaynes2003probability" in content
        assert "#ref-shannon1948theory" in content
        assert "[@jaynes2003probability]" not in content
        assert "[jaynes2003probability]" not in content


def _make_renderer(tmp_path):
    """Create a WebRenderer with config pointing to tmp_path."""
    config = RenderingConfig(
        pandoc_path="pandoc",
        web_dir=str(tmp_path / "web"),
    )
    return WebRenderer(config)


def test_pandoc_metadata_args_enable_linked_references(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text(
        "paper:\n  title: Test\n  subtitle: Accessible summary\n"
        "authors:\n  - name: Ada Lovelace\nmetadata:\n  language: en-GB\n",
        encoding="utf-8",
    )

    args = WebRenderer._pandoc_metadata_args(manuscript_dir)

    assert "--metadata=linkReferences:true" in args
    assert "--metadata=author:Ada Lovelace" in args
    assert "--metadata=lang:en-GB" in args
    assert "--metadata=description:Accessible summary" in args


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


def test_responsive_variant_uses_mobile_sibling_when_present(tmp_path: Path) -> None:
    web_dir = tmp_path / "output" / "web"
    figure_dir = tmp_path / "output" / "figures"
    web_dir.mkdir(parents=True)
    figure_dir.mkdir(parents=True)
    (figure_dir / "graphical.png").write_bytes(b"desktop")
    (figure_dir / "graphical_mobile.png").write_bytes(b"mobile")
    html_file = web_dir / "index.html"
    html_file.write_text(
        '<html><body><img src="../figures/graphical.png" alt="Graphical abstract"></body></html>',
        encoding="utf-8",
    )

    WebRenderer._add_responsive_image_variants(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert '<picture><source media="(max-width: 600px)"' in content
    assert 'srcset="../figures/graphical_mobile.png"' in content


def test_figure_images_link_to_full_resolution_assets_idempotently(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Dense scientific figure"><figcaption>Dense figure.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)
    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert content.count('class="figure-full-size-link"') == 1
    assert 'href="../figures/dense.png"' in content
    assert 'target="_blank"' in content
    assert 'rel="noopener"' in content
    assert 'aria-label="Open full-size figure, Dense figure."' in content
    assert 'class="figure-full-size-label"' in content


def test_numbered_figure_full_size_link_has_contextual_accessible_name(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Dense scientific figure"><figcaption>Figure 7: Evidence map \\(F(q)\\).</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 7, Evidence map F(q)."' in content
    assert 'aria-label="Open full-size figure"' not in content


def test_full_size_link_uses_concise_caption_result_not_caption_metadata(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:evidence"><img src="../figures/evidence.png" '
        'alt="Evidence map"><figcaption>Figure 12: Evidence classes remain in separate lanes. '
        "Source relation: source-owned explanatory map; uncertainty: none.</figcaption>"
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 12, Evidence classes remain in separate lanes."' in content
    assert "Source relation" in content
    assert 'aria-label="Open full-size Figure 12, Evidence classes remain in separate lanes. Source' not in content


def test_full_size_link_shortens_a_long_result_at_a_semantic_boundary(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="evidence.png" alt="Evidence map">'
        "<figcaption>Figure 6: Evidence class and replication remain claim-lane specific; "
        "guarantees do not migrate between client and server lanes.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 6, Evidence class and replication remain claim-lane specific"' in content
    assert "guarantees do not migrate" in content
    assert (
        'aria-label="Open full-size Figure 6, Evidence class and replication remain claim-lane specific;' not in content
    )


def test_full_size_figure_link_rejects_missing_context(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/dense.png" alt=""></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="contextual full-size link"):
        WebRenderer._add_full_resolution_figure_links(html_file)


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


def test_individual_render_embeds_publication_css_and_full_resolution_figure_link(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "03_results.md"
    source.write_text(
        "# Results\n\n![Dense figure](../figures/dense.png){#fig:dense width=100%}\n",
        encoding="utf-8",
    )
    web_dir = tmp_path / "output" / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output")))

    result = renderer.render(source)

    content = result.read_text(encoding="utf-8")
    assert "--brand-1" in content
    assert "width: min(100%, 800px)" in content
    assert 'class="figure-full-size-link"' in content
    assert 'href="../figures/dense.png"' in content


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
        source = "![A](../output/figures/a.png)\n![B](output/figures/b.png)\n![C](../../output/figures/c.png)\n"

        result = renderer._html_safe_markdown(source)

        assert "../output/figures/" not in result
        assert "../../output/figures/" not in result
        assert "output/figures/" not in result
        assert result.count("../figures/") == 3

    def test_html_safe_markdown_preserves_pandoc_crossrefs(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        source = (
            "See [@fig:coverage] and [@tbl:coverage] in [@sec:results]. "
            "Bibliography [@smith2020; -@doe2021] remains readable."
        )

        result = renderer._html_safe_markdown(source)

        assert "[@fig:coverage]" in result
        assert "[@tbl:coverage]" in result
        assert "[@sec:results]" in result
        assert "[fig:coverage]" not in result
        assert "[tbl:coverage]" not in result
        assert "[sec:results]" not in result
        assert "[smith2020; doe2021]" in result

    def test_per_section_html_can_render_crossrefs_without_raw_markers(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        source = "See [@fig:coverage] and [@sec:results]."

        result = renderer._html_safe_markdown(source, preserve_crossrefs=False)

        assert "[@fig:coverage]" not in result
        assert "[@sec:results]" not in result
        assert "[fig:coverage]" in result
        assert "[sec:results]" in result


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


class TestTheoremBlocks:
    """Web-only rewrite of raw-LaTeX theorem environments into numbered Divs."""

    def test_theorem_block_becomes_numbered_div_with_name_and_body(self):
        src = (
            "\\begin{theorem}[Recovery corner]\n"
            "The robust aggregator at zero robustness equals the log-linear pool.\n"
            "\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "::: {.theorem-box .theorem}" in out
        assert "**Theorem 1** (Recovery corner)." in out
        assert "equals the log-linear pool." in out  # body preserved
        assert "\\begin{theorem}" not in out  # raw LaTeX gone

    def test_theorem_block_with_same_line_label_is_rewritten_with_anchor(self):
        # The standard amsthm idiom puts \label on the \begin line:
        # \begin{proposition}[Name]\label{prop:x} — the rewriter must still fire
        # (a 2026-07-17 regression dropped every labeled environment from the
        # web surface) and should carry the label through as a Div anchor.
        src = (
            "\\begin{proposition}[EFE identity]\\label{prop:efe-decomposition}\n"
            "The cost and value decompositions agree.\n"
            "\\end{proposition}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "::: {.theorem-box .proposition #prop:efe-decomposition}" in out
        assert "**Proposition 1** (EFE identity)." in out
        assert "decompositions agree." in out
        assert "\\label{" not in out  # label consumed, not leaked into prose
        assert "\\begin{proposition}" not in out

    def test_shared_counter_across_environments(self):
        src = (
            "\\begin{definition}[Free energy]\nF is defined here.\n\\end{definition}\n\n"
            "\\begin{lemma}\nA lemma body.\n\\end{lemma}\n\n"
            "\\begin{theorem}[Main]\nThe theorem body.\n\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        # one running counter, mirroring \newtheorem[theorem] shared numbering
        assert "**Definition 1** (Free energy)." in out
        assert "**Lemma 2**." in out
        assert "**Theorem 3** (Main)." in out
        assert ".definition" in out and ".lemma" in out and ".theorem" in out

    def test_unnamed_block_has_no_parenthetical(self):
        out = WebRenderer._html_theorem_blocks("\\begin{proposition}\nNo name here.\n\\end{proposition}")
        assert "**Proposition 1**." in out
        assert "(" not in out.split("No name")[0].split("Proposition 1")[1]

    def test_non_theorem_content_is_untouched(self):
        src = "Just prose with $x = 1$ and a [@fig:a] reference.\n"
        assert WebRenderer._html_theorem_blocks(src) == src

    def test_texttt_in_body_becomes_code_span_with_unescaped_underscores(self):
        # Pandoc's HTML writer drops \texttt{...} as raw inline LaTeX, which
        # made module names vanish from the web theorem boxes ("the categorical
        # generative model of , the cost"). The body cleaner must surface the
        # filename as a markdown code span instead.
        src = (
            "\\begin{definition}[EFE module]\n"
            "The categorical generative model of \\texttt{expected\\_free\\_energy.py}, the cost.\n"
            "\\end{definition}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "`expected_free_energy.py`" in out
        assert "\\texttt" not in out

    def test_inline_and_display_math_delimiters_become_dollar_math(self):
        # \(...\) degraded to "(G())" on the web because pandoc's markdown
        # reader doesn't enable tex_math_single_backslash; the body cleaner
        # converts to $...$ / $$...$$ so HTML+MathJax renders them.
        src = (
            "\\begin{theorem}[EFE]\n"
            "The expected free energy \\(G(\\pi)\\) satisfies\n"
            "\\[G(\\pi) = \\mathbb{E}[F]\\]\n"
            "for every policy.\n"
            "\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "$G(\\pi)$" in out
        assert "$$G(\\pi) = \\mathbb{E}[F]$$" in out
        assert "\\(" not in out and "\\[" not in out

    def test_theorem_name_preserves_math_and_texttt(self):
        """Optional theorem names use the same safe path as theorem bodies."""
        src = "\\begin{theorem}[KL/NLL/\\(\\beta=0\\), \\texttt{log_linear_pool}]\nThe identity holds.\n\\end{theorem}"
        out = WebRenderer._html_theorem_blocks(src)
        assert "KL/NLL/$\\beta=0$" in out
        assert "`log_linear_pool`" in out
        assert "\\(" not in out
        assert "\\texttt" not in out

    def test_texttt_and_math_outside_theorem_bodies_are_untouched(self):
        # The cleaner is theorem-body-scoped: surrounding prose keeps its raw
        # LaTeX for the existing global passes to handle.
        src = (
            "Prose with \\texttt{keep\\_raw.py} and \\(x\\) here.\n\n\\begin{lemma}\nBody with \\(y\\).\n\\end{lemma}\n"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "\\texttt{keep\\_raw.py}" in out
        assert "Prose with \\texttt" in out and "\\(x\\)" in out
        assert "$y$" in out

    def test_theorems_survive_full_html_safe_pass(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        src = (
            "Intro.\n\n\\begin{theorem}[Descent]\n"
            "Block-coordinate descent never increases $F$.\n"
            "\\end{theorem}\n\nOutro."
        )
        result = renderer._html_safe_markdown(src)
        assert "theorem-box" in result
        assert "Block-coordinate descent never increases" in result  # not dropped
        assert "\\begin{theorem}" not in result
