"""MOBI renderer shared fallback paths (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.mobi_renderer import (
    MobiRenderResult,
    render_mobi,
)
from ._ebook_fallbacks_helpers import (
    _CALIBRE,
    _TRUE,
    needs_pandoc,
    SAMPLE_MD,
    _MINIMAL_MD,
)


class TestMobiRendererFallbacks:
    """MOBI renderer error branches — exercises shared pandoc/calibre absence paths."""

    def test_missing_combined_md_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_mobi raises FileNotFoundError when the source markdown is absent."""
        out = tmp_path / "out.mobi"
        with pytest.raises(FileNotFoundError):
            render_mobi(tmp_path / "nonexistent.md", out)

    def test_missing_bibliography_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_mobi raises FileNotFoundError when a bibliography path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(FileNotFoundError, match="Bibliography not found"):
            render_mobi(src, out, bibliography=tmp_path / "missing.bib")

    def test_missing_cover_image_raises_file_not_found(self, tmp_path: Path) -> None:
        """render_mobi raises FileNotFoundError when a cover image path does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(FileNotFoundError, match="Cover image not found"):
            render_mobi(src, out, cover_image=tmp_path / "missing.png")

    def test_missing_pandoc_raises_rendering_error(self, tmp_path: Path) -> None:
        """render_mobi raises RenderingError when pandoc binary is not found."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(RenderingError, match="pandoc binary not found"):
            render_mobi(src, out, pandoc_path="/nonexistent/pandoc-binary")

    @pytest.mark.skipif(_TRUE is None, reason="'true' binary not available")
    def test_missing_calibre_raises_rendering_error(self, tmp_path: Path) -> None:
        """render_mobi raises RenderingError when calibre ebook-convert is not found.

        Uses 'true' as a real binary that ``shutil.which`` finds (satisfying the
        pandoc check) but that is not actually pandoc — so the calibre check is
        reached. The calibre binary is set to a nonexistent path, exercising the
        genuine binary-absence fallback for calibre.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(RenderingError, match="calibre ebook-convert binary not found"):
            render_mobi(
                src,
                out,
                pandoc_path=_TRUE,  # type: ignore[arg-type]
                calibre_path="/nonexistent/ebook-convert",
            )

    @needs_pandoc
    def test_missing_ebook_convert_raises_rendering_error(self, tmp_path: Path) -> None:
        """An unavailable ebook-convert binary fails closed with the install hint.

        Exercises the real ``shutil.which`` resolution with an explicitly
        unresolvable binary name, so the contract holds in every environment
        regardless of whether calibre is installed.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(RenderingError, match="calibre ebook-convert binary not found"):
            render_mobi(src, out, calibre_path="ebook-convert-not-installed-fixture")

    @needs_pandoc
    def test_mobi_render_environment_contract(self, tmp_path: Path) -> None:
        """render_mobi succeeds with calibre present and fails closed without it.

        Both branches are real production behavior: with calibre installed the
        full pandoc→EPUB→MOBI pipeline runs; without it the typed absence
        error fires. The test asserts whichever contract this environment
        supports, so the suite never skips.
        """
        src = tmp_path / "combined.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        if _CALIBRE is not None:
            result = render_mobi(src, out, title="Mobi Test", author="Author")
            assert isinstance(result, MobiRenderResult)
            assert out.exists()
            assert result.size_bytes > 0
        else:
            with pytest.raises(RenderingError, match="calibre ebook-convert binary not found"):
                render_mobi(src, out)
