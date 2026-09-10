"""EbookBundleManager fallback behavior tests (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.rendering.ebook_bundle import (
    EbookBundleManager,
    _find_combined_markdown,
    _find_cover_image,
)
from ._ebook_fallbacks_helpers import (
    _CALIBRE,
    needs_pandoc,
    SAMPLE_MD,
    _MINIMAL_MD,
)


class TestEbookBundleManagerFallbacks:
    """EbookBundleManager error isolation and graceful degradation — no mocks."""

    def test_missing_combined_md_raises_file_not_found(self, tmp_path: Path) -> None:
        """generate_all raises FileNotFoundError when combined_md does not exist."""
        manager = EbookBundleManager()
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "output" / "ebook"
        with pytest.raises(FileNotFoundError, match="Combined markdown not found"):
            manager.generate_all(
                project_root=project_root,
                combined_md=tmp_path / "nonexistent.md",
                output_dir=output_dir,
            )

    def test_missing_pandoc_produces_no_formats_but_metadata(self, tmp_path: Path) -> None:
        """When pandoc is absent, all format renders fail but metadata is still produced.

        EbookBundleManager isolates each format failure — a missing pandoc binary
        causes EPUB/MOBI/DOCX to fail silently (logged), but the metadata package
        (ONIX/JSON/OPF) is still generated because it does not depend on pandoc.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "output" / "ebook"

        manager = EbookBundleManager(pandoc_path="/nonexistent/pandoc")
        outputs = manager.generate_all(
            project_root=project_root,
            combined_md=src,
            output_dir=output_dir,
        )
        # No ebook format outputs (pandoc is missing).
        assert "epub" not in outputs
        assert "mobi" not in outputs
        assert "docx" not in outputs
        # Metadata package is still produced — it doesn't need pandoc.
        assert "onix_xml" in outputs
        assert "metadata_json" in outputs
        assert "opf" in outputs
        assert outputs["onix_xml"].exists()
        assert outputs["metadata_json"].exists()
        assert outputs["opf"].exists()

    @needs_pandoc
    @pytest.mark.skipif(_CALIBRE is not None, reason="calibre is installed — test the absence path only")
    def test_calibre_absent_skips_mobi_but_produces_others(self, tmp_path: Path) -> None:
        """When calibre is absent, MOBI fails but EPUB and DOCX still succeed.

        This is the real graceful-degradation path: the manager catches each
        format's RenderingError independently.
        """
        src = tmp_path / "combined.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "output" / "ebook"

        manager = EbookBundleManager()
        outputs = manager.generate_all(
            project_root=project_root,
            combined_md=src,
            output_dir=output_dir,
        )
        # EPUB and DOCX succeed (pandoc present), MOBI fails (calibre absent).
        assert "epub" in outputs
        assert "docx" in outputs
        assert "mobi" not in outputs
        assert outputs["epub"].exists()
        assert outputs["docx"].exists()
        # Metadata is also produced.
        assert "onix_xml" in outputs

    @needs_pandoc
    def test_skip_mobi_skips_mobi_generation(self, tmp_path: Path) -> None:
        """skip_mobi=True prevents MOBI generation entirely (no calibre call)."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "output" / "ebook"

        manager = EbookBundleManager(skip_mobi=True)
        outputs = manager.generate_all(
            project_root=project_root,
            combined_md=src,
            output_dir=output_dir,
        )
        assert "mobi" not in outputs
        assert "epub" in outputs
        assert "docx" in outputs

    @needs_pandoc
    def test_skip_docx_skips_docx_generation(self, tmp_path: Path) -> None:
        """skip_docx=True prevents DOCX generation entirely."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "output" / "ebook"

        manager = EbookBundleManager(skip_docx=True)
        outputs = manager.generate_all(
            project_root=project_root,
            combined_md=src,
            output_dir=output_dir,
        )
        assert "docx" not in outputs
        assert "epub" in outputs

    def test_generate_from_project_no_combined_md_returns_empty(self, tmp_path: Path) -> None:
        """generate_from_project returns empty dict when no combined markdown is found.

        This is the graceful-skip path — the method logs a warning and returns
        an empty dict rather than raising.
        """
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        (project_root / "output").mkdir()
        manager = EbookBundleManager()
        outputs = manager.generate_from_project(project_root)
        assert outputs == {}

    def test_find_combined_markdown_returns_none_for_empty_project(self, tmp_path: Path) -> None:
        """_find_combined_markdown returns None when no combined markdown exists."""
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        (project_root / "output").mkdir()
        assert _find_combined_markdown(project_root) is None

    def test_find_combined_markdown_finds_combined_md(self, tmp_path: Path) -> None:
        """_find_combined_markdown finds an existing combined.md in output/."""
        project_root = tmp_path / "myproject"
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True)
        combined = output_dir / "combined.md"
        combined.write_text("# Title", encoding="utf-8")
        result = _find_combined_markdown(project_root)
        assert result is not None
        assert result == combined

    def test_find_cover_image_returns_none_when_absent(self, tmp_path: Path) -> None:
        """_find_cover_image returns None when no cover image exists."""
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        assert _find_cover_image(project_root) is None

    def test_find_cover_image_finds_manuscript_cover(self, tmp_path: Path) -> None:
        """_find_cover_image finds cover.png in manuscript/ directory."""
        project_root = tmp_path / "myproject"
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir(parents=True)
        cover = manuscript_dir / "cover.png"
        cover.write_bytes(b"fake-png")
        result = _find_cover_image(project_root)
        assert result is not None
        assert result == cover

    @needs_pandoc
    def test_generate_all_creates_output_dir(self, tmp_path: Path) -> None:
        """generate_all creates the output directory if it does not exist."""
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        project_root = tmp_path / "myproject"
        project_root.mkdir()
        output_dir = tmp_path / "deep" / "nested" / "ebook"

        manager = EbookBundleManager(skip_mobi=True)
        outputs = manager.generate_all(
            project_root=project_root,
            combined_md=src,
            output_dir=output_dir,
        )
        assert output_dir.is_dir()
        assert "epub" in outputs
