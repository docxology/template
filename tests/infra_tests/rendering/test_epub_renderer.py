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
