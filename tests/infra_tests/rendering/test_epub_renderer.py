"""Tests for EPUB renderer - no mocks, runs real pandoc."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest

from infrastructure.rendering.epub_renderer import EpubRenderResult, render_epub


pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc not installed",
)


SAMPLE_MD = """---
title: "EPUB Renderer Smoke Test"
author: Template Test
lang: en
---

# Chapter 1

A paragraph of text in the first chapter.

# Chapter 2

A second chapter with **bold** and *italic* text.
"""


def test_render_epub_produces_nonempty_file(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    result = render_epub(src, out)

    assert isinstance(result, EpubRenderResult)
    assert result.output_path == out
    assert out.exists()
    assert out.stat().st_size > 1024
    assert result.size_bytes == out.stat().st_size
    assert result.duration_seconds >= 0.0


def test_render_epub_contains_title(tmp_path: Path) -> None:
    """EPUB is a ZIP; verify pandoc emitted title metadata."""
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    with zipfile.ZipFile(out) as zip_file:
        names = zip_file.namelist()
        opf_name = next((name for name in names if name.endswith(".opf")), None)
        assert opf_name is not None, f"no .opf manifest found in EPUB: {names}"
        opf = zip_file.read(opf_name).decode("utf-8")
    assert "<dc:title>EPUB Renderer Smoke Test</dc:title>" in opf or "EPUB Renderer Smoke Test" in opf


def test_render_epub_missing_source_raises(tmp_path: Path) -> None:
    out = tmp_path / "out.epub"
    with pytest.raises(FileNotFoundError):
        render_epub(tmp_path / "missing.md", out)


def _opf_text(epub_path: Path) -> str:
    with zipfile.ZipFile(epub_path) as zip_file:
        names = zip_file.namelist()
        opf_name = next((name for name in names if name.endswith(".opf")), None)
        assert opf_name is not None, f"no .opf manifest found in EPUB: {names}"
        return zip_file.read(opf_name).decode("utf-8")


# Frontmatter-free source: real combined-manuscript markdown has no YAML
# frontmatter (title/author/language live only in the project's separate
# manuscript/config.yaml), which is exactly the gap that let a real EPUB
# ship with no dc:title/dc:creator and an invalid dc:language ("C", the
# POSIX locale name) — see 07_ebook_generation.py's _load_manuscript_metadata.
_NO_FRONTMATTER_MD = "# Chapter 1\n\nA paragraph with no YAML frontmatter at all.\n"


def test_render_epub_without_metadata_args_omits_title_and_creator(tmp_path: Path) -> None:
    """Regression: source markdown with no frontmatter must not silently ship untitled."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    opf = _opf_text(out)
    assert "<dc:title>" not in opf
    assert "<dc:creator" not in opf


def test_render_epub_metadata_args_populate_title_and_creator(tmp_path: Path) -> None:
    """title=/author=/language= must reach the OPF even with frontmatter-free source."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out, title="Explicit Title", author="Explicit Author", language="en-US")

    opf = _opf_text(out)
    assert ">Explicit Title</dc:title>" in opf
    assert ">Explicit Author</dc:creator>" in opf
    assert "<dc:language>en-US</dc:language>" in opf


def test_render_epub_default_language_is_not_locale_dependent(tmp_path: Path) -> None:
    """Without an explicit language=, must default to 'en', never fall through to the host locale."""
    src = tmp_path / "combined.md"
    src.write_text(_NO_FRONTMATTER_MD, encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out)

    opf = _opf_text(out)
    assert "<dc:language>en</dc:language>" in opf


# 1x1 PNG — smallest real image, used to assert media embedding.
_PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_render_epub_embeds_figures_via_resource_path(tmp_path: Path) -> None:
    """Relative ``figures/<name>`` refs must embed when resource-path is the parent.

    Regression: pandoc silently drops images (no error) when the resource-path
    does not make ``figures/x.png`` resolvable. See _combined_exports.py.
    """
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.png").write_bytes(_PNG_1x1)
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\n![cap](figures/x.png)\n", encoding="utf-8")
    out = tmp_path / "out.epub"

    render_epub(src, out, extra_args=["--resource-path=" + str(tmp_path)])

    with zipfile.ZipFile(out) as zip_file:
        media = [n for n in zip_file.namelist() if n.lower().endswith(".png")]
    assert media, "expected the figure to be embedded in the EPUB"
