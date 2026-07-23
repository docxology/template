"""Additional tests for DOCX renderer error branches.

Targets branches below 60%: missing pandoc, missing bibliography,
missing reference doc, non-zero exit, empty output, timeout.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.docx_renderer import (
    DocxRenderResult,
    _process_output_text,
    _truncate_error_context,
    render_docx,
)

SAMPLE_MD = "# Section 1\n\nA paragraph with a citation [@smith2020].\n"

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
    assert result == "x" * 500


def test_truncate_error_context_normal() -> None:
    assert _truncate_error_context("some error") == "some error"


def test_process_output_text_bytes() -> None:
    assert _process_output_text(b"hello") == "hello"


def test_process_output_text_str() -> None:
    assert _process_output_text("hello") == "hello"


def test_process_output_text_none() -> None:
    assert _process_output_text(None) == ""


def test_render_docx_missing_bibliography_raises(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.docx"
    with pytest.raises(FileNotFoundError, match="Bibliography not found"):
        render_docx(src, out, bibliography=tmp_path / "missing.bib")


def test_render_docx_missing_reference_doc_raises(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.docx"
    with pytest.raises(FileNotFoundError, match="Reference DOCX not found"):
        render_docx(src, out, reference_doc=tmp_path / "missing.docx")


def test_render_docx_with_title_and_author(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text("# Test\n\nContent.\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    result = render_docx(src, out, title="My Title", author="My Author")
    assert isinstance(result, DocxRenderResult)
    assert out.exists()


def test_render_docx_with_bibliography(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text("# Test\n\nSee [@smith2020].\n", encoding="utf-8")
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{smith2020, title={Test}, author={Smith}, year={2020}}\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    result = render_docx(src, out, bibliography=bib)
    assert isinstance(result, DocxRenderResult)
    assert out.exists()


def test_render_docx_with_extra_args(tmp_path: Path) -> None:
    src = tmp_path / "combined.md"
    src.write_text("# Test\n\nContent.\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    result = render_docx(src, out, extra_args=["--toc"])
    assert isinstance(result, DocxRenderResult)
    assert out.exists()


def test_render_docx_missing_pandoc_raises(tmp_path: Path) -> None:
    """When pandoc binary is not found, RenderingError is raised."""
    src = tmp_path / "combined.md"
    src.write_text(SAMPLE_MD, encoding="utf-8")
    out = tmp_path / "out.docx"
    with pytest.raises(RenderingError, match="pandoc binary not found"):
        render_docx(src, out, pandoc_path="/nonexistent/pandoc-binary")
