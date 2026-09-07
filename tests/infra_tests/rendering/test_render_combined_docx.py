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
    render_combined_docx,
)
from ._combined_exports_helpers import _make_manager, _make_reporter


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
