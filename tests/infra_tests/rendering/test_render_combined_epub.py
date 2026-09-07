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

import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.rendering._combined_exports import (
    render_combined_epub,
)
from ._combined_exports_helpers import _make_manager, _make_reporter, _epub_package_identifiers


# ---------------------------------------------------------------------------
# render_combined_epub
# ---------------------------------------------------------------------------


def test_render_combined_epub_skips_when_no_combined_md(tmp_path: Path) -> None:
    """render_combined_epub returns early (no error) when no combined markdown exists."""
    manager = _make_manager(tmp_path)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)


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
    supplemental_bib = manuscript_dir / "z_supplemental.bib"
    supplemental_bib.write_text("@article{y, title={Y}}\n")
    (manuscript_dir / "cover.png").write_bytes(b"cover fixture")
    (manuscript_dir / "config.yaml").write_text(
        "paper:\n"
        "  title: Test EPUB\n"
        "  cover:\n"
        "    image: cover.png\n"
        "    alt: A source-owned cover description.\n"
        "authors:\n"
        "  - name: Ada Lovelace\n"
        "metadata:\n"
        "  language: en-GB\n"
    )

    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)
    captured: dict[str, object] = {}

    def fake_render_epub(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_path=Path("test.epub"), size_bytes=1024)

    render_combined_epub(
        manager,
        manuscript_dir,
        "myproject",
        reporter,
        epub_renderer=fake_render_epub,
    )

    assert captured["bibliography"] is None
    assert captured["title"] == "Test EPUB"
    assert captured["author"] == "Ada Lovelace"
    assert captured["language"] == "en-GB"
    assert captured["cover_image"] == manuscript_dir / "cover.png"
    assert captured["cover_alt"] == "A source-owned cover description."
    extra_args = captured["extra_args"]
    assert isinstance(extra_args, list)
    assert "--citeproc" in extra_args
    assert f"--bibliography={bib}" in extra_args
    assert f"--bibliography={supplemental_bib}" in extra_args
    assert extra_args.index(f"--bibliography={bib}") < extra_args.index(f"--bibliography={supplemental_bib}")


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


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_render_combined_epub_identifier_tracks_effective_bibliography(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production bibliography extras participate in effective-package identity."""

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    combined_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir(parents=True)
    combined_md.write_text("# Evidence\n\nThe result follows prior work [@binding2026].\n", encoding="utf-8")
    bibliography = manuscript_dir / "references.bib"
    bibliography.write_text(
        "@article{binding2026,\n"
        "  author={Binder, Ada},\n"
        "  title={First Effective Bibliography Revision},\n"
        "  journal={Determinism Quarterly},\n"
        "  year={2026}\n"
        "}\n",
        encoding="utf-8",
    )
    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)
    output = tmp_path / "output" / "epub" / "myproject_combined.epub"

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)
    first_package_id, first_navigation_id = _epub_package_identifiers(output)
    with zipfile.ZipFile(output) as archive:
        first_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith((".xhtml", ".html"))
        )
    assert first_package_id == first_navigation_id
    assert "First Effective Bibliography Revision" in first_text

    bibliography.write_text(
        "@article{binding2026,\n"
        "  author={Binder, Ada},\n"
        "  title={Second Effective Bibliography Revision},\n"
        "  journal={Determinism Quarterly},\n"
        "  year={2026}\n"
        "}\n",
        encoding="utf-8",
    )
    render_combined_epub(manager, manuscript_dir, "myproject", reporter)
    changed_package_id, changed_navigation_id = _epub_package_identifiers(output)

    assert changed_package_id == changed_navigation_id
    assert changed_package_id != first_package_id
