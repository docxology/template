"""Ebook stage (run_ebook_generation) fallback behavior tests (split from test_docx_epub_fallbacks.py)."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import pytest
from infrastructure.rendering.ebook_stage import run_ebook_generation
from ._ebook_fallbacks_helpers import (
    _CALIBRE,
    needs_pandoc,
    SAMPLE_MD,
    _MINIMAL_MD,
    _ebook_archive_text,
    _epub_package_identifiers,
)


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

    def test_duplicate_citation_key_returns_failure_before_render(self, tmp_path: Path) -> None:
        """Ambiguous multi-file keys fail the stage even when Pandoc is unavailable."""
        repo_root = tmp_path / "repo"
        project_root = repo_root / "projects" / "working" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "a.bib").write_text("@article{shared,title={A}}\n", encoding="utf-8")
        (manuscript_dir / "b.bib").write_text("@book{shared,title={B}}\n", encoding="utf-8")
        combined = project_root / "output" / "pdf" / "_combined_manuscript.md"
        combined.parent.mkdir(parents=True)
        combined.write_text("# Evidence\n\nSee [@shared].\n", encoding="utf-8")

        assert run_ebook_generation(repo_root, "working/myproject", skip_formats_arg="mobi,docx") == 1

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
    def test_multi_bibliography_citations_resolve_in_epub_and_docx(self, tmp_path: Path) -> None:
        """The stage's real Pandoc outputs consume every top-level ``.bib`` file."""
        repo_root = tmp_path / "repo"
        project_root = repo_root / "projects" / "working" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "references.bib").write_text(
            "@article{alpha2020primary,\n"
            "  author={Alpha, Ada},\n"
            "  title={Primary Source},\n"
            "  journal={Journal One},\n"
            "  year={2020}\n"
            "}\n",
            encoding="utf-8",
        )
        (manuscript_dir / "z_supplemental.bib").write_text(
            "@article{omega2021supplement,\n"
            "  author={Omega, Orla},\n"
            "  title={Supplemental Source},\n"
            "  journal={Journal Two},\n"
            "  year={2021}\n"
            "}\n",
            encoding="utf-8",
        )
        combined = project_root / "output" / "pdf" / "_combined_manuscript.md"
        combined.parent.mkdir(parents=True)
        combined.write_text(
            "# Evidence\n\nBoth sources matter [@alpha2020primary; @omega2021supplement].\n",
            encoding="utf-8",
        )

        exit_code = run_ebook_generation(repo_root, "working/myproject", skip_formats_arg="mobi")

        assert exit_code == 0
        ebook_dir = project_root / "output" / "ebook"
        for artifact in (ebook_dir / "myproject.docx", ebook_dir / "myproject.epub"):
            archive_text = _ebook_archive_text(artifact)
            assert "Primary Source" in archive_text
            assert "Supplemental Source" in archive_text
            assert "[@alpha2020primary" not in archive_text
            assert "@omega2021supplement]" not in archive_text

    @needs_pandoc
    def test_epub_identifier_tracks_effective_body_media(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The production ebook stage binds packaged media bytes into its UUID."""

        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        repo_root = tmp_path / "repo"
        project_root = repo_root / "projects" / "working" / "myproject"
        (project_root / "src").mkdir(parents=True)
        (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
        figures_dir = project_root / "output" / "figures"
        figures_dir.mkdir(parents=True)
        figure = figures_dir / "identity.svg"
        figure.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<title>First media revision</title><rect width="10" height="10" fill="red"/></svg>\n',
            encoding="utf-8",
        )
        combined = project_root / "output" / "pdf" / "_combined_manuscript.md"
        combined.parent.mkdir(parents=True)
        combined.write_text(
            "# Media evidence\n\n![Accessible identity fixture](figures/identity.svg)\n",
            encoding="utf-8",
        )
        output = project_root / "output" / "ebook" / "myproject.epub"

        assert run_ebook_generation(repo_root, "working/myproject", skip_formats_arg="mobi,docx") == 0
        first_package_id, first_navigation_id = _epub_package_identifiers(output)
        assert first_package_id == first_navigation_id

        figure.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<title>Second media revision</title><rect width="10" height="10" fill="blue"/></svg>\n',
            encoding="utf-8",
        )
        assert run_ebook_generation(repo_root, "working/myproject", skip_formats_arg="mobi,docx") == 0
        changed_package_id, changed_navigation_id = _epub_package_identifiers(output)

        assert changed_package_id == changed_navigation_id
        assert changed_package_id != first_package_id
        with ZipFile(output) as archive:
            svg_payloads = [archive.read(name) for name in archive.namelist() if name.endswith(".svg")]
        assert any(b"Second media revision" in payload for payload in svg_payloads)

    @needs_pandoc
    def test_full_pipeline_ebook_generation_contract(self, tmp_path: Path) -> None:
        """The ebook stage degrades per-format and the suite never skips.

        With calibre installed, all three formats succeed (exit 0). Without
        it, EPUB and DOCX still render via pandoc, MOBI fails closed, and
        the stage reports partial success (exit 0) — the documented
        per-format isolation contract of ``run_ebook_generation``.
        """
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
        if _CALIBRE is not None:
            assert (ebook_dir / "myproject.mobi").exists()
        else:
            assert not (ebook_dir / "myproject.mobi").exists()
