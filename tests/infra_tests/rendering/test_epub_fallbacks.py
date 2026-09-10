"""EPUB renderer fallback/error-path tests (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.epub_renderer import (
    EpubRenderResult,
    render_epub,
)
from ._ebook_fallbacks_helpers import (
    needs_pandoc,
    SAMPLE_MD,
    _MINIMAL_MD,
)


class TestEpubRendererFallbacks:
    """EPUB renderer error branches — real subprocess, no mocks."""

    def test_missing_combined_md_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_epub raises FileNotFoundError when the source markdown is absent."""
        out = tmp_path / "out.epub"
        with pytest.raises(FileNotFoundError, match="Combined markdown not found"):
            render_epub(tmp_path / "nonexistent.md", out)

    def test_missing_bibliography_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_epub raises FileNotFoundError when a bibliography path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.epub"
        with pytest.raises(FileNotFoundError, match="Bibliography not found"):
            render_epub(src, out, bibliography=tmp_path / "missing.bib")

    def test_missing_cover_image_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_epub raises FileNotFoundError when a cover image path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.epub"
        with pytest.raises(FileNotFoundError, match="Cover image not found"):
            render_epub(src, out, cover_image=tmp_path / "missing.png")

    def test_missing_pandoc_binary_raises_rendering_error(self, tmp_path: Path) -> None:
        """When the pandoc binary is absent from PATH, RenderingError is raised."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.epub"
        with pytest.raises(RenderingError, match="pandoc binary not found"):
            render_epub(src, out, pandoc_path="/nonexistent/pandoc-binary")

    @needs_pandoc
    def test_nonzero_exit_raises_rendering_error(self, tmp_path: Path) -> None:
        """render_epub raises RenderingError when pandoc exits non-zero.

        Uses a real unknown-flag to trigger pandoc's exit code 6.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.epub"
        with pytest.raises(RenderingError, match="pandoc EPUB render failed"):
            render_epub(src, out, extra_args=["--this-flag-does-not-exist"])

    @needs_pandoc
    def test_creates_nested_parent_dir(self, tmp_path: Path) -> None:
        """render_epub creates missing parent directories for the output path."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "deep" / "nested" / "dir" / "out.epub"
        result = render_epub(src, out)
        assert isinstance(result, EpubRenderResult)
        assert out.exists()
        assert out.parent.is_dir()

    @needs_pandoc
    def test_successful_render_returns_valid_result(self, tmp_path: Path) -> None:
        """A successful render returns an EpubRenderResult with correct metadata."""
        src = tmp_path / "combined.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out.epub"
        result = render_epub(src, out, title="Test Title", author="Test Author", language="en-US")
        assert isinstance(result, EpubRenderResult)
        assert result.output_path == out
        assert out.exists()
        assert result.size_bytes == out.stat().st_size
        assert result.size_bytes > 0

    @needs_pandoc
    def test_source_checked_before_pandoc_binary(self, tmp_path: Path) -> None:
        """FileNotFoundError for the source takes priority over the pandoc check."""
        out = tmp_path / "out.epub"
        with pytest.raises(FileNotFoundError, match="Combined markdown not found"):
            render_epub(tmp_path / "missing.md", out, pandoc_path="/nonexistent/pandoc")
