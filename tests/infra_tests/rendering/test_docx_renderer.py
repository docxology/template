"""Tests for DOCX renderer - no mocks, runs real pandoc."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest

from infrastructure.rendering.docx_renderer import DocxRenderResult, render_docx


pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc not installed",
)


SAMPLE_MD = """---
title: "DOCX Renderer Smoke Test"
author: Template Test
---

# Section 1

This is a paragraph with a citation [@smith2020].

## Subsection

- bullet a
- bullet b

> blockquote line

```python
print("code block")
```
"""


def test_render_docx_produces_nonempty_file(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.docx"

    result = render_docx(src, out)

    assert isinstance(result, DocxRenderResult)
    assert result.output_path == out
    assert out.exists()
    assert out.stat().st_size > 1024
    assert result.size_bytes == out.stat().st_size
    assert result.duration_seconds >= 0.0


def test_render_docx_is_valid_zip(tmp_path: Path) -> None:
    """DOCX is a ZIP archive; verify pandoc emitted a valid structure."""
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.docx"

    render_docx(src, out)

    with zipfile.ZipFile(out) as zip_file:
        names = zip_file.namelist()
    assert "word/document.xml" in names
    assert "[Content_Types].xml" in names


def test_render_docx_missing_source_raises(tmp_path: Path) -> None:
    out = tmp_path / "out.docx"
    with pytest.raises(FileNotFoundError):
        render_docx(tmp_path / "missing.md", out)


def test_render_docx_creates_parent(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "deep" / "nested" / "out.docx"

    render_docx(src, out)

    assert out.exists()
    assert out.parent.is_dir()
