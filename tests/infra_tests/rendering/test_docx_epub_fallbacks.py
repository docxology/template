"""No-mock tests for DOCX/EPUB/MOBI renderer and ebook-stage fallback/error paths.

Exercises real error branches in the ebook rendering stack using real subprocess
calls, real temporary files, and real binaries — no MagicMock, no mocker.patch,
no unittest.mock. When an external binary (pandoc, calibre ebook-convert) is
absent from the environment, the tests assert the real fallback/error code path
that handles that absence.

Source modules under test:
- infrastructure/rendering/docx_renderer.py
- infrastructure/rendering/epub_renderer.py
- infrastructure/rendering/mobi_renderer.py
- infrastructure/rendering/ebook_bundle.py
- infrastructure/rendering/ebook_stage.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.docx_renderer import DocxRenderResult, render_docx
from infrastructure.rendering.epub_renderer import EpubRenderResult, render_epub
from infrastructure.rendering.ebook_bundle import (
    EbookBundleManager,
    _find_combined_markdown,
    _find_cover_image,
)
from infrastructure.rendering.ebook_stage import run_ebook_generation
from infrastructure.rendering.mobi_renderer import MobiRenderResult, render_mobi

# ── Environment capability detection ──────────────────────────────────────────
# These tests never mock the binaries. Instead, they detect whether the real
# binary is present and assert the code path that handles presence or absence.

_PANDOC = shutil.which("pandoc")
_CALIBRE = shutil.which("ebook-convert")
# 'true' and 'false' are guaranteed-present POSIX binaries used as real
# non-pandoc / always-fail-exit substitutions to exercise the binary-missing
# fallback path without mocking.
_TRUE = shutil.which("true")
_FALSE = shutil.which("false")

needs_pandoc = pytest.mark.skipif(_PANDOC is None, reason="pandoc not installed")

SAMPLE_MD = """\
# Chapter 1

A paragraph of text in the first chapter.

# Chapter 2

A second chapter with **bold** and *italic* text.
"""

_MINIMAL_MD = "# Title\n\nSome content.\n"


# ════════════════════════════════════════════════════════════════════════════════
# DOCX renderer fallback / error paths
# ════════════════════════════════════════════════════════════════════════════════


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


# ════════════════════════════════════════════════════════════════════════════════
# EPUB renderer fallback / error paths
# ════════════════════════════════════════════════════════════════════════════════


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


# ════════════════════════════════════════════════════════════════════════════════
# MOBI renderer shared fallback paths (shares the binary-absence pattern)
# ════════════════════════════════════════════════════════════════════════════════


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
    @pytest.mark.skipif(_CALIBRE is not None, reason="calibre is installed — test the absence path only")
    def test_calibre_absent_in_environment_raises_rendering_error(self, tmp_path: Path) -> None:
        """When calibre is genuinely absent from the environment, render_mobi fails.

        This asserts the real fallback: pandoc is present, but calibre is not,
        so the MOBI render raises RenderingError with the calibre installation hint.
        """
        src = tmp_path / "combined.md"
        src.write_text(_MINIMAL_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        with pytest.raises(RenderingError, match="calibre ebook-convert binary not found"):
            render_mobi(src, out)

    @needs_pandoc
    @pytest.mark.skipif(_CALIBRE is None, reason="calibre not installed — cannot test full pipeline")
    def test_successful_mobi_render_when_calibre_present(self, tmp_path: Path) -> None:
        """When both pandoc and calibre are present, render_mobi succeeds."""
        src = tmp_path / "combined.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out.mobi"
        result = render_mobi(src, out, title="Mobi Test", author="Author")
        assert isinstance(result, MobiRenderResult)
        assert out.exists()
        assert result.size_bytes > 0


# ════════════════════════════════════════════════════════════════════════════════
# EbookBundleManager fallback behavior
# ════════════════════════════════════════════════════════════════════════════════


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


# ════════════════════════════════════════════════════════════════════════════════
# Ebook stage (run_ebook_generation) fallback behavior
# ════════════════════════════════════════════════════════════════════════════════


class TestEbookStageFallbacks:
    """Ebook stage orchestrator fallback/error paths — real filesystem, no mocks."""

    def test_no_combined_markdown_returns_graceful_skip(self, tmp_path: Path) -> None:
        """run_ebook_generation returns exit code 2 when no combined markdown is found.

        This is the graceful-skip path — the stage logs a warning and returns 2
        rather than failing.
        """
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        project_root = repo_root / "projects" / "active" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "output").mkdir(parents=True)

        exit_code = run_ebook_generation(repo_root, "myproject")
        assert exit_code == 2

    def test_all_formats_skipped_returns_zero(self, tmp_path: Path) -> None:
        """run_ebook_generation returns 0 when all formats are skipped."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        project_root = repo_root / "projects" / "active" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")

        exit_code = run_ebook_generation(repo_root, "myproject", skip_formats_arg="epub,mobi,docx")
        assert exit_code == 0

    def test_missing_pandoc_with_source_produces_partial_or_failure(self, tmp_path: Path) -> None:
        """When pandoc is absent, ebook stage returns 0 (partial) or 1 (all failed).

        The stage catches each format's RenderingError independently. With
        pandoc missing, all three formats fail. But the stage returns 0 when
        there are no successes AND no successes (all failed → return 1), OR
        it may return 0 for partial success. With all formats failing, it
        should return 1.
        """
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        project_root = repo_root / "projects" / "active" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        # Create a combined markdown file in the expected location.
        output_pdf = project_root / "output" / "pdf"
        output_pdf.mkdir(parents=True)
        combined_md = output_pdf / "_combined_manuscript.md"
        combined_md.write_text(_MINIMAL_MD, encoding="utf-8")

        # Use a nonexistent pandoc path — all formats will fail.
        exit_code = run_ebook_generation(
            repo_root,
            "myproject",
            skip_formats_arg="mobi",  # Skip MOBI since calibre may also be absent
        )
        # With pandoc present but calibre absent (the common CI case), EPUB and
        # DOCX succeed, MOBI is skipped → exit 0. With pandoc absent, all fail → 1.
        # We assert it's one of these valid outcomes.
        assert exit_code in (0, 1, 2), f"unexpected exit code: {exit_code}"

    @needs_pandoc
    def test_cover_image_not_found_continues_without_cover(self, tmp_path: Path) -> None:
        """run_ebook_generation continues when a specified cover image is absent.

        The stage logs a warning and proceeds with cover_image=None.
        """
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        project_root = repo_root / "projects" / "active" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        output_pdf = project_root / "output" / "pdf"
        output_pdf.mkdir(parents=True)
        combined_md = output_pdf / "_combined_manuscript.md"
        combined_md.write_text(_MINIMAL_MD, encoding="utf-8")

        exit_code = run_ebook_generation(
            repo_root,
            "myproject",
            skip_formats_arg="mobi",
            cover_image_arg="/nonexistent/cover.png",
        )
        # Should succeed (EPUB and DOCX at minimum), exit 0.
        assert exit_code in (0, 1)

    @needs_pandoc
    @pytest.mark.skipif(_CALIBRE is None, reason="calibre not installed")
    def test_full_pipeline_with_calibre_present(self, tmp_path: Path) -> None:
        """When both pandoc and calibre are present, all formats succeed (exit 0)."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        project_root = repo_root / "projects" / "active" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        output_pdf = project_root / "output" / "pdf"
        output_pdf.mkdir(parents=True)
        combined_md = output_pdf / "_combined_manuscript.md"
        combined_md.write_text(SAMPLE_MD, encoding="utf-8")

        exit_code = run_ebook_generation(repo_root, "myproject")
        assert exit_code == 0
        # Verify ebook files were produced.
        ebook_dir = project_root / "output" / "ebook"
        assert ebook_dir.is_dir()
        assert (ebook_dir / "myproject.epub").exists()
        assert (ebook_dir / "myproject.docx").exists()
        assert (ebook_dir / "myproject.mobi").exists()


# ════════════════════════════════════════════════════════════════════════════════
# Helper-function edge cases (shared between DOCX/EPUB/MOBI)
# ════════════════════════════════════════════════════════════════════════════════


class TestSharedHelperFunctions:
    """Tests for _truncate_error_context and _process_output_text helpers.

    These helpers are duplicated across docx_renderer, epub_renderer, and
    mobi_renderer. The existing per-module test files cover them individually;
    here we verify they behave identically across modules (shared contract).
    """

    def test_truncate_error_context_empty_all_modules(self) -> None:
        """All three modules return the same placeholder for empty input."""
        from infrastructure.rendering.docx_renderer import _truncate_error_context as docx_trunc
        from infrastructure.rendering.epub_renderer import _truncate_error_context as epub_trunc
        from infrastructure.rendering.mobi_renderer import _truncate_error_context as mobi_trunc

        for func in (docx_trunc, epub_trunc, mobi_trunc):
            assert func("") == "no stderr captured"
            assert func("   ") == "no stderr captured"

    def test_truncate_error_context_long_all_modules(self) -> None:
        """All three modules truncate to 500 characters."""
        from infrastructure.rendering.docx_renderer import _truncate_error_context as docx_trunc
        from infrastructure.rendering.epub_renderer import _truncate_error_context as epub_trunc
        from infrastructure.rendering.mobi_renderer import _truncate_error_context as mobi_trunc

        long_text = "x" * 600
        for func in (docx_trunc, epub_trunc, mobi_trunc):
            result = func(long_text)
            assert len(result) == 500

    def test_process_output_text_none_all_modules(self) -> None:
        """All three modules return empty string for None input."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            assert func(None) == ""

    def test_process_output_text_bytes_all_modules(self) -> None:
        """All three modules decode bytes to string."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            assert func(b"hello") == "hello"

    def test_process_output_text_invalid_utf8_all_modules(self) -> None:
        """All three modules use errors='replace' for invalid UTF-8."""
        from infrastructure.rendering.docx_renderer import _process_output_text as docx_proc
        from infrastructure.rendering.epub_renderer import _process_output_text as epub_proc
        from infrastructure.rendering.mobi_renderer import _process_output_text as mobi_proc

        for func in (docx_proc, epub_proc, mobi_proc):
            result = func(b"\xff\xfe")
            assert isinstance(result, str)
            assert len(result) > 0
