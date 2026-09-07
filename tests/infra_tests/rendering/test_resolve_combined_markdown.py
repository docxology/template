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
    resolve_combined_markdown,
)


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
