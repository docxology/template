"""DOCX renderer fallback/error-path tests (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.docx_renderer import (
    DocxRenderResult,
    render_docx,
)
from ._ebook_fallbacks_helpers import (
    needs_pandoc,
    SAMPLE_MD,
    _MINIMAL_MD,
)


class TestDocxRendererFallbacks:
    """DOCX renderer error branches — real subprocess, no mocks."""

    def test_missing_combined_md_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_docx raises FileNotFoundError when the source markdown is absent."""
        out = tmp_path / "out.docx"
        with pytest.raises(FileNotFoundError, match="Combined markdown not found"):
            render_docx(tmp_path / "nonexistent.md", out)

    def test_missing_bibliography_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_docx raises FileNotFoundError when a bibliography path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.docx"
        with pytest.raises(FileNotFoundError, match="Bibliography not found"):
            render_docx(src, out, bibliography=tmp_path / "missing.bib")

    def test_missing_reference_doc_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_docx raises FileNotFoundError when a reference DOCX path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.docx"
        with pytest.raises(FileNotFoundError, match="Reference DOCX not found"):
            render_docx(src, out, reference_doc=tmp_path / "missing.docx")

    def test_missing_pandoc_binary_raises_rendering_error(self, tmp_path: Path) -> None:
        """When the pandoc binary is absent from PATH, RenderingError is raised.

        Uses a real nonexistent path — ``shutil.which`` returns None, exercising
        the genuine binary-absence fallback, not a mock.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.docx"
        with pytest.raises(RenderingError, match="pandoc binary not found"):
            render_docx(src, out, pandoc_path="/nonexistent/pandoc-binary")

    @needs_pandoc
    def test_nonzero_exit_raises_rendering_error(self, tmp_path: Path) -> None:
        """render_docx raises RenderingError when pandoc exits non-zero.

        A non-DOCX file passed as ``--reference-doc`` causes pandoc to fail with
        a real non-zero exit code (exit 1 — "Did not find end of central
        directory signature"). This exercises the ``returncode != 0`` branch
        with a real subprocess, not a mock.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        # A plain text file is not a valid DOCX ZIP — pandoc will fail.
        fake_ref = tmp_path / "not_a_docx.docx"
        fake_ref.write_text("this is not a ZIP/DOCX", encoding="utf-8")
        out = tmp_path / "out.docx"
        with pytest.raises(RenderingError, match="pandoc DOCX render failed"):
            render_docx(src, out, reference_doc=fake_ref)

    @needs_pandoc
    def test_invalid_extra_arg_raises_rendering_error(self, tmp_path: Path) -> None:
        """render_docx raises RenderingError when pandoc rejects an unknown flag.

        Pandoc exits with code 6 on unknown options — a real non-zero exit
        that exercises the error branch without any mocking.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.docx"
        with pytest.raises(RenderingError, match="pandoc DOCX render failed"):
            render_docx(src, out, extra_args=["--this-flag-does-not-exist"])

    @needs_pandoc
    def test_creates_nested_parent_dir(self, tmp_path: Path) -> None:
        """render_docx creates missing parent directories for the output path."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "deep" / "nested" / "dir" / "out.docx"
        result = render_docx(src, out)
        assert isinstance(result, DocxRenderResult)
        assert out.exists()
        assert out.parent.is_dir()
        assert result.output_path == out

    @needs_pandoc
    def test_successful_render_returns_valid_result(self, tmp_path: Path) -> None:
        """A successful render returns a DocxRenderResult with correct metadata."""
        src = tmp_path / "combined.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out.docx"
        result = render_docx(src, out, title="Test Title", author="Test Author")
        assert isinstance(result, DocxRenderResult)
        assert result.output_path == out
        assert out.exists()
        assert result.size_bytes == out.stat().st_size
        assert result.size_bytes > 0
        assert result.duration_seconds >= 0.0

    @needs_pandoc
    def test_source_checked_before_pandoc_binary(self, tmp_path: Path) -> None:
        """FileNotFoundError for the source takes priority over the pandoc check.

        The source-file existence check happens before the binary check in
        render_docx, so a missing source with a missing pandoc binary still
        raises FileNotFoundError, not RenderingError.
        """
        out = tmp_path / "out.docx"
        with pytest.raises(FileNotFoundError, match="Combined markdown not found"):
            render_docx(tmp_path / "missing.md", out, pandoc_path="/nonexistent/pandoc")
