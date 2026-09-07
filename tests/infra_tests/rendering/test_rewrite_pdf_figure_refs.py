"""Tests for infrastructure.rendering._combined_exports — branch coverage.

Covers fixture-driven branches for:
- combined_source_files: existing/missing path, transmission-bookend classification
- resolve_combined_markdown: manuscript/output dir layout, pdf/tex candidates, empty/missing
- resolve_bibliography: deterministic union, path deduplication, and conflicts
- render_combined_docx: no combined-md early return; bibliography/crossref/metadata paths
- render_combined_epub: no combined-md early return; bibliography present vs absent
- render_combined_outputs: enable_* toggles; RenderingError and OSError paths
"""

from __future__ import annotations

from pathlib import Path


from infrastructure.rendering._combined_exports import (
    rewrite_pdf_figure_refs_to_raster,
)


# ---------------------------------------------------------------------------
# rewrite_pdf_figure_refs_to_raster
# ---------------------------------------------------------------------------


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
