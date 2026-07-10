"""Tests for infrastructure.rendering._combined_exports — branch coverage.

Covers fixture-driven branches for:
- combined_source_files: existing/missing path, transmission-bookend classification
- resolve_combined_markdown: manuscript/output dir layout, pdf/tex candidates, empty/missing
- resolve_bibliography: bib present vs absent
- render_combined_docx: no combined-md early return; bibliography/crossref/metadata paths
- render_combined_epub: no combined-md early return; bibliography present vs absent
- render_combined_outputs: enable_* toggles; RenderingError and OSError paths
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.publishing.transmission_bookends import BEGIN_FILENAME, END_FILENAME
from infrastructure.rendering._combined_exports import (
    combined_source_files,
    render_combined_docx,
    render_combined_epub,
    render_combined_outputs,
    resolve_bibliography,
    resolve_combined_markdown,
    rewrite_pdf_figure_refs_to_raster,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_reporter(tmp_path: Path) -> DiagnosticReporter:
    """Build a DiagnosticReporter backed by tmp_path."""
    return DiagnosticReporter("test_project")


def _make_manager(tmp_path: Path, **overrides: object) -> RenderManager:
    """Create a RenderManager with all output dirs under tmp_path."""
    cfg = RenderingConfig(
        pdf_dir=str(tmp_path / "output/pdf"),
        docx_dir=str(tmp_path / "output/docx"),
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
        output_dir=str(tmp_path / "output"),
    )
    for attr, val in overrides.items():
        setattr(cfg, attr, val)
    return RenderManager(config=cfg)


# ---------------------------------------------------------------------------
# combined_source_files
# ---------------------------------------------------------------------------


def test_combined_source_files_includes_existing_path(tmp_path: Path) -> None:
    """A file that exists on disk is always included regardless of bookend status."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")

    result = combined_source_files([existing])

    assert result == [existing]


def test_combined_source_files_excludes_missing_bookend(tmp_path: Path) -> None:
    """A missing transmission bookend (by filename) is excluded from the output list."""
    missing_bookend = tmp_path / BEGIN_FILENAME
    # Do NOT create the file — it is missing AND is_transmission_bookend => exclude

    result = combined_source_files([missing_bookend])

    assert result == []


def test_combined_source_files_includes_missing_non_bookend(tmp_path: Path) -> None:
    """A missing non-bookend file is still included (caller is responsible for it)."""
    missing_regular = tmp_path / "05_discussion.md"
    # Do NOT create the file — missing AND NOT is_transmission_bookend => include

    result = combined_source_files([missing_regular])

    assert result == [missing_regular]


def test_combined_source_files_mixed_list(tmp_path: Path) -> None:
    """Mixed list: existing, missing-regular, and missing-bookend handled correctly."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")
    missing_regular = tmp_path / "02_methods.md"
    missing_end_bookend = tmp_path / END_FILENAME  # missing

    result = combined_source_files([existing, missing_regular, missing_end_bookend])

    assert existing in result
    assert missing_regular in result
    assert missing_end_bookend not in result


# ---------------------------------------------------------------------------
# resolve_combined_markdown
# ---------------------------------------------------------------------------


def test_resolve_combined_markdown_pdf_candidate(tmp_path: Path) -> None:
    """Returns the pdf/_combined_manuscript.md when it exists and is non-empty."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    pdf_candidate = project_root / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("# Combined\n\nSome content.\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == pdf_candidate


def test_resolve_combined_markdown_tex_candidate_fallback(tmp_path: Path) -> None:
    """Returns tex/_combined_manuscript.md when the pdf candidate is absent."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    tex_candidate = project_root / "output" / "tex" / "_combined_manuscript.md"
    tex_candidate.parent.mkdir(parents=True)
    tex_candidate.write_text("# Combined TeX\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == tex_candidate


def test_resolve_combined_markdown_returns_none_when_both_missing(tmp_path: Path) -> None:
    """Returns None when neither pdf nor tex combined markdown exists."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    result = resolve_combined_markdown(manuscript_dir)

    assert result is None


def test_resolve_combined_markdown_empty_file_skipped(tmp_path: Path) -> None:
    """An empty _combined_manuscript.md is skipped; None returned if no non-empty candidate."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    pdf_candidate = project_root / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("")  # empty

    result = resolve_combined_markdown(manuscript_dir)

    assert result is None


def test_resolve_combined_markdown_other_dir_layout(tmp_path: Path) -> None:
    """When manuscript_dir is NOT inside an 'output' dir, project_root = parent."""
    # Layout: tmp_path/manuscript -> project_root = tmp_path
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    pdf_candidate = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("# Content\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == pdf_candidate


# ---------------------------------------------------------------------------
# resolve_bibliography
# ---------------------------------------------------------------------------


def test_resolve_bibliography_returns_first_bib(tmp_path: Path) -> None:
    """Returns the first (sorted) .bib file when one or more are present."""
    bib1 = tmp_path / "references.bib"
    bib2 = tmp_path / "zotero.bib"
    bib1.write_text("@article{a,title={A}}\n")
    bib2.write_text("@article{b,title={B}}\n")

    result = resolve_bibliography(tmp_path)

    # sorted order: references.bib < zotero.bib
    assert result == bib1


def test_resolve_bibliography_returns_none_when_no_bib(tmp_path: Path) -> None:
    """Returns None when no .bib files are present in the manuscript dir."""
    result = resolve_bibliography(tmp_path)

    assert result is None


# ---------------------------------------------------------------------------
# render_combined_docx
# ---------------------------------------------------------------------------


def test_render_combined_docx_skips_when_no_combined_md(tmp_path: Path) -> None:
    """render_combined_docx returns early (no error) when no combined markdown exists."""
    manager = _make_manager(tmp_path)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No combined markdown => early return, no exception
    render_combined_docx(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_epub_skips_when_no_combined_md(tmp_path: Path) -> None:
    """render_combined_epub returns early (no error) when no combined markdown exists."""
    manager = _make_manager(tmp_path)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_docx_with_bibliography(tmp_path: Path) -> None:
    """render_combined_docx adds citeproc args when a .bib file is present."""
    # Set up project structure with combined markdown and bib
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    # Place combined markdown where resolve_combined_markdown will find it
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Test combined\n\nContent here.\n")

    # Add a bib file
    bib = manuscript_dir / "references.bib"
    bib.write_text("@article{test, title={Test}}\n")

    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)

    # Should not raise — may fail pandoc call (missing docx template etc.) but
    # that is caught inside render_combined_docx and logged as a warning.
    render_combined_docx(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_epub_with_bibliography(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Combined EPUB test\n\nContent.\n")

    bib = manuscript_dir / "references.bib"
    bib.write_text("@article{x, title={X}}\n")
    (manuscript_dir / "config.yaml").write_text(
        "paper:\n  title: Test EPUB\nauthors:\n  - name: Ada Lovelace\nmetadata:\n  language: en-GB\n"
    )

    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)
    captured: dict[str, object] = {}

    def fake_render_epub(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_path=Path("test.epub"), size_bytes=1024)

    monkeypatch.setattr("infrastructure.rendering.epub_renderer.render_epub", fake_render_epub)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)

    assert captured["bibliography"] is None
    assert captured["title"] == "Test EPUB"
    assert captured["author"] == "Ada Lovelace"
    assert captured["language"] == "en-GB"
    extra_args = captured["extra_args"]
    assert isinstance(extra_args, list)
    assert "--citeproc" in extra_args
    assert f"--bibliography={bib}" in extra_args


def test_render_combined_epub_without_bibliography(tmp_path: Path) -> None:
    """render_combined_epub uses bibliography=None when no .bib file is present."""
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Combined EPUB test\n\nContent.\n")

    # No .bib file present
    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)


# ---------------------------------------------------------------------------
# render_combined_outputs — config toggle branches
# ---------------------------------------------------------------------------


class _FailingRenderManager(RenderManager):
    """RenderManager subclass that raises on render calls to exercise error paths."""

    def __init__(self, cfg: RenderingConfig, *, raise_with: Exception) -> None:
        super().__init__(config=cfg)
        self._raise_with = raise_with

    def render_combined_pdf(self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project") -> Path:  # type: ignore[override]
        """Always raises the configured exception."""
        raise self._raise_with

    def render_combined_web(self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project") -> Path:  # type: ignore[override]
        """Always raises the configured exception."""
        raise self._raise_with


def test_render_combined_outputs_pdf_disabled_skips(tmp_path: Path) -> None:
    """When enable_pdf is False, the PDF render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No exception expected
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_disabled_skips(tmp_path: Path) -> None:
    """When enable_html is False, the HTML render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_pdf_rendering_error_with_rendered_count(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count>0 logs the individual-PDF note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("simulated combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # Must not propagate — caught and logged
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=3)

    # The diagnostic event should be recorded
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_rendering_error_zero_rendered(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count=0 does NOT log the individual note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    # Error still recorded despite rendered_count=0
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_oserror_with_existing_combined_md(tmp_path: Path) -> None:
    """An OSError during PDF render logs stderr/stdout attrs and stats the combined-md if present."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )

    class _OSErrWithAttrs(OSError):
        stderr = "err output"
        stdout = "std output"

    err = _OSErrWithAttrs("disk full")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create the combined markdown so the stat-log branch is exercised
    tex_dir = tmp_path / "output" / "tex"
    tex_dir.mkdir(parents=True)
    (tex_dir / "_combined_manuscript.md").write_text("content\n")

    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_rendering_error_recorded(tmp_path: Path) -> None:
    """A RenderingError during HTML render is caught and recorded on the reporter."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=True,
        enable_docx=False,
        enable_epub=False,
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("html render failed")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    assert len(reporter.events) >= 1


def test_render_combined_outputs_docx_enabled_delegates(tmp_path: Path) -> None:
    """When enable_docx=True, render_combined_outputs calls render_combined_docx (no error when no combined md)."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=True,
        enable_epub=False,
        docx_dir=str(tmp_path / "output/docx"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No combined markdown → render_combined_docx returns early; no exception
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_epub_enabled_delegates(tmp_path: Path) -> None:
    """When enable_epub=True, render_combined_outputs calls render_combined_epub (no error when no combined md)."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=False,
        enable_epub=True,
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


# ---------------------------------------------------------------------------
# rewrite_pdf_figure_refs_to_raster
# ---------------------------------------------------------------------------
# Regression coverage for a real failure: a combined manuscript's .pdf figure
# refs (correct for LaTeX) silently fail to embed in EPUB/MOBI/DOCX (PDF is
# not a valid inline-image media type there) — confirmed via epubcheck
# (RSC-007) on a real book, and the underlying cause of a real KDP "couldn't
# convert your HTML file to Kindle format" rejection.


def test_rewrite_pdf_figure_refs_swaps_to_png_when_sibling_exists(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "timeline_dark.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![Caption](../figures/timeline_dark.pdf){#fig-timeline}\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/timeline_dark.png" in result
    assert ".pdf" not in result


def test_rewrite_pdf_figure_refs_prefers_png_over_jpg(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.png").write_bytes(b"fake-png")
    (tmp_path / "figures" / "x.jpg").write_bytes(b"fake-jpg")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    result = rewrite_pdf_figure_refs_to_raster("![c](../figures/x.pdf)\n", combined_md)

    assert "../figures/x.png" in result


def test_rewrite_pdf_figure_refs_falls_back_to_jpg(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.jpg").write_bytes(b"fake-jpg")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    result = rewrite_pdf_figure_refs_to_raster("![c](../figures/x.pdf)\n", combined_md)

    assert "../figures/x.jpg" in result


def test_rewrite_pdf_figure_refs_leaves_unmatched_ref_untouched(tmp_path: Path) -> None:
    """No raster sibling on disk: leave the .pdf ref as-is (surfaces as a normal missing-resource error)."""
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![c](../figures/nonexistent.pdf)\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert result == text


def test_rewrite_pdf_figure_refs_ignores_non_pdf_images(tmp_path: Path) -> None:
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![c](../figures/already_raster.png)\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert result == text


def test_rewrite_pdf_figure_refs_handles_nested_citation_brackets(tmp_path: Path) -> None:
    """Regression: captions with inline citations like [@cite1; @cite2] nest brackets
    inside the alt text — a naive [^\\]]* class can't skip the inner ']' and silently
    fails to match at all, leaving the .pdf ref untouched (confirmed via epubcheck on
    a real manuscript: 3 of 7 figures kept failing after the first version of this fix
    specifically because their captions ended in a citation group)."""
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "historic_ratio_dark.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = (
        "![Caption with sources [@flandreau1996bimetallism; @laughlin1898bimetallism]."
        "](../figures/historic_ratio_dark.pdf){#fig-historic-ratio}\n"
    )
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/historic_ratio_dark.png" in result
    assert ".pdf" not in result


def test_rewrite_pdf_figure_refs_handles_multiple_refs(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "a.png").write_bytes(b"fake-png")
    (tmp_path / "figures" / "b.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![one](../figures/a.pdf){#fig-a}\n\ntext between\n\n![two](../figures/b.pdf){#fig-b}\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/a.png" in result
    assert "../figures/b.png" in result
    assert ".pdf" not in result
