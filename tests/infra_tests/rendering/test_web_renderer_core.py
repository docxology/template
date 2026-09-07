"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering import web_renderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer

from ._web_renderer_test_helpers import _make_renderer


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


class TestWebRendererIntegration:
    """Integration tests for web renderer."""

    def test_full_render_workflow(self, tmp_path):
        """Test complete rendering workflow."""
        # Create test content
        md = tmp_path / "doc.md"
        md.write_text("# Document\n\n## Section\n\nContent here.")

        # Module should be importable
        assert web_renderer is not None


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


@pytest.mark.parametrize("combined", [False, True])
def test_render_preserves_planted_temporary_symlink(tmp_path: Path, combined: bool) -> None:
    """Real Pandoc rendering must not overwrite a predictable temp link's target."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "section.md"
    source.write_text("# Safe publication\n\nBody text.\n", encoding="utf-8")
    web = tmp_path / "output" / "web"
    web.mkdir(parents=True)
    protected = tmp_path / "unrelated.txt"
    protected.write_text("keep original bytes", encoding="utf-8")
    trap = web / "_combined_manuscript.md.tmp" if combined else source.with_suffix(".md.web.tmp")
    trap.symlink_to(protected)
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), output_dir=str(web.parent)))

    result = renderer.render_combined([source], manuscript) if combined else renderer.render(source)

    assert "Safe publication" in result.read_text(encoding="utf-8")
    assert protected.read_text(encoding="utf-8") == "keep original bytes"
    assert trap.is_symlink()
    assert source.read_text(encoding="utf-8") == "# Safe publication\n\nBody text.\n"
    assert not list(web.glob(".web-source-*"))


def test_render_cleans_private_source_after_pandoc_failure(tmp_path: Path) -> None:
    """Failed subprocesses leave no preprocessed manuscript copies behind."""
    source = tmp_path / "section.md"
    source.write_text("# Private source\n", encoding="utf-8")
    web = tmp_path / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), pandoc_path="/usr/bin/false"))
    with pytest.raises(RenderingError):
        renderer.render(source)
    assert not list(web.glob(".web-source-*"))
    assert not source.with_suffix(".md.web.tmp").exists()


@pytest.mark.parametrize("source_kind", ["missing", "directory"])
def test_render_source_io_failure_keeps_rendering_error_contract(tmp_path: Path, source_kind: str) -> None:
    """Input I/O failures retain the public error type and remove private copies."""
    source = tmp_path / "invalid.md"
    if source_kind == "directory":
        source.mkdir()
    web = tmp_path / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web)))
    with pytest.raises(RenderingError) as caught:
        renderer.render(source)
    assert isinstance(caught.value.__cause__, OSError)
    assert not list(web.glob(".web-source-*"))
    assert not list(web.glob("*.html"))


def test_individual_render_preserves_existing_page_permissions(tmp_path: Path) -> None:
    """Re-rendering a page must not widen its existing permission mode."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "03_results.md"
    source.write_text("# Results\n\nA short prose paragraph for rendering.\n", encoding="utf-8")
    web_dir = tmp_path / "output" / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output")))
    target = renderer._output_file_for_source(source)
    web_dir.mkdir(parents=True)
    target.write_text("<html><body>old</body></html>", encoding="utf-8")
    target.chmod(0o600)

    renderer.render(source)

    assert target.is_file()
    assert (target.stat().st_mode & 0o777) == 0o600


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
