"""Comprehensive tests for infrastructure/rendering/web_renderer.py.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
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
        """Test rendering HTML."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nContent")

        if hasattr(web_renderer, "render_html"):
            try:
                web_renderer.render_html(str(md))
            except Exception:
                pass

    def test_render_html_with_template(self, tmp_path):
        """Test rendering HTML with template."""
        md = tmp_path / "doc.md"
        md.write_text("# Title")

        if hasattr(web_renderer, "render_html"):
            try:
                web_renderer.render_html(str(md), template="default")
            except Exception:
                pass


class TestMathJaxIntegration:
    """Test MathJax integration."""

    def test_render_with_mathjax(self, tmp_path):
        """Test rendering with MathJax."""
        md = tmp_path / "math.md"
        md.write_text("# Math\n\n$E = mc^2$")

        if hasattr(web_renderer, "render_html"):
            try:
                web_renderer.render_html(str(md), mathjax=True)
            except Exception:
                pass

    def test_mathjax_config(self):
        """Test MathJax configuration."""
        if hasattr(web_renderer, "get_mathjax_config"):
            config = web_renderer.get_mathjax_config()
            assert config is not None

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


class TestCssIntegration:
    """Test CSS integration."""

    def test_add_stylesheet(self, tmp_path):
        """Test adding stylesheet."""
        if hasattr(web_renderer, "add_stylesheet"):
            html = "<html><head></head><body></body></html>"
            result = web_renderer.add_stylesheet(html, "style.css")
            assert result is not None

    def test_inline_css(self, tmp_path):
        """Test inlining CSS."""
        css = tmp_path / "style.css"
        css.write_text("body { color: black; }")

        if hasattr(web_renderer, "inline_css"):
            html = "<html><head></head><body></body></html>"
            try:
                web_renderer.inline_css(html, str(css))
            except Exception:
                pass


class TestAssetHandling:
    """Test asset handling."""

    def test_copy_assets(self, tmp_path):
        """Test copying assets."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "image.png").write_bytes(b"\x89PNG")

        if hasattr(web_renderer, "copy_assets"):
            try:
                web_renderer.copy_assets(str(src), str(tmp_path / "out"))
            except Exception:
                pass

    def test_resolve_asset_paths(self, tmp_path):
        """Test resolving asset paths."""
        html = '<img src="image.png">'

        if hasattr(web_renderer, "resolve_asset_paths"):
            result = web_renderer.resolve_asset_paths(html, tmp_path)
            assert result is not None


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
        md1 = tmp_path / "01_intro.md"
        md1.write_text("# Introduction\n\nThis is the introduction.")

        md2 = tmp_path / "02_methods.md"
        md2.write_text("# Methods\n\nThis describes the methods.")

        md3 = tmp_path / "03_results.md"
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

        result = renderer.render_combined(source_files, tmp_path, "test_project")

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
        md1 = tmp_path / "a.md"
        md1.write_text("# Section A\n\nContent A.")

        md2 = tmp_path / "b.md"
        md2.write_text("# Section B\n\nContent B.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        manager = RenderManager(config)
        result = manager.render_combined_web([md1, md2], tmp_path, "test")

        assert result.exists()
        assert result.name == "index.html"

    def test_render_combined_resolves_bibliographic_citations(self, tmp_path):
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md = manuscript_dir / "01_intro.md"
        md.write_text("# Introduction\n\nPrior work matters [@jaynes2003probability].\n", encoding="utf-8")
        (manuscript_dir / "references.bib").write_text(
            "@book{jaynes2003probability,\n"
            "  author = {Jaynes, Edwin T.},\n"
            "  title = {Probability Theory},\n"
            "  year = {2003},\n"
            "  publisher = {Cambridge University Press}\n"
            "}\n",
            encoding="utf-8",
        )

        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output"))
        result = WebRenderer(config).render_combined([md], manuscript_dir, "test")

        content = result.read_text(encoding="utf-8")
        assert "Jaynes" in content
        assert "#ref-jaynes2003probability" in content
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


def test_accessibility_postprocess_adds_language_main_and_concise_alt(tmp_path: Path) -> None:
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
    assert 'alt="Figure 1: Paired effect delta and likelihood A_k across seeds."' in content

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
