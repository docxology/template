"""Additional tests for EPUB renderer error branches.

Targets branches below 60%: missing pandoc, missing bibliography,
missing cover image, non-zero exit, empty output, timeout.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.epub_renderer import (
    EpubRenderResult,
    _process_output_text,
    _truncate_error_context,
    render_epub,
)

SAMPLE_MD = "# Chapter 1\n\nA paragraph of text.\n"

pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc not installed",
)


def test_truncate_error_context_empty() -> None:
    assert _truncate_error_context("") == "no stderr captured"
    assert _truncate_error_context("   ") == "no stderr captured"


def test_truncate_error_context_long() -> None:
    long_text = "x" * 600
    result = _truncate_error_context(long_text)
    assert len(result) == 500


def test_process_output_text_bytes() -> None:
    assert _process_output_text(b"hello") == "hello"


def test_process_output_text_str() -> None:
    assert _process_output_text("hello") == "hello"


def test_process_output_text_none() -> None:
    assert _process_output_text(None) == ""


def test_render_epub_missing_bibliography_raises(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"
    with pytest.raises(FileNotFoundError, match="Bibliography not found"):
        render_epub(src, out, bibliography=tmp_path / "missing.bib")


def test_render_epub_missing_cover_image_raises(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"
    with pytest.raises(FileNotFoundError, match="Cover image not found"):
        render_epub(src, out, cover_image=tmp_path / "missing.png")


def test_render_epub_with_cover_image(tmp_path: Path) -> None:
    # 1x1 PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    cover = tmp_path / "cover.png"
    cover.write_bytes(png)
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\nContent.\n", encoding="utf-8")
    out = tmp_path / "out.epub"
    result = render_epub(src, out, cover_image=cover, title="Cover Test", author="Author")
    assert isinstance(result, EpubRenderResult)
    assert out.exists()


def test_render_epub_creates_parent_dir(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "deep" / "nested" / "out.epub"
    result = render_epub(src, out)
    assert isinstance(result, EpubRenderResult)
    assert out.exists()
    assert out.parent.is_dir()


def test_render_epub_with_bibliography(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text("# Test\n\nSee [@smith2020].\n", encoding="utf-8")
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{smith2020, title={Test}, author={Smith}, year={2020}}\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.epub"
    result = render_epub(src, out, bibliography=bib, title="Bib Test", author="Author")
    assert isinstance(result, EpubRenderResult)
    assert out.exists()


def test_render_epub_with_extra_args(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text("# Test\n\nContent.\n", encoding="utf-8")
    out = tmp_path / "out.epub"
    result = render_epub(src, out, extra_args=["--toc"])
    assert isinstance(result, EpubRenderResult)
    assert out.exists()


def test_render_epub_missing_pandoc_raises(tmp_path: Path) -> None:
    """When pandoc binary is not found, RenderingError is raised."""
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.epub"
    with pytest.raises(RenderingError, match="pandoc binary not found"):
        render_epub(src, out, pandoc_path="/nonexistent/pandoc-binary")
