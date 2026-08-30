"""Branch-gap tests for infrastructure/rendering/_pipeline_summary.py.

Covers the measured uncovered branches: combined HTML validation,
rendering-config error paths, unreadable slide sources, structurally
invalid DOCX/EPUB packages, and the PDF render-override contract.
All fixtures are real files built with reportlab/zipfile — no mocks.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from infrastructure.rendering._pipeline_summary import (
    _manuscript_dir_for_verify,
    _rendering_config_for_verify,
    _verify_combined_html,
    _verify_docx_output,
    _verify_epub_output,
    _verify_slide_outputs,
    verify_render_outputs,
)

PROJECT = "templates/test_proj"


def _make_pdf(path: Path, pages: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for i in range(pages):
        for j in range(500):
            pdf.drawString(72, 720 - j, f"content p{i + 1} L{j} " * 5)
        pdf.showPage()
    pdf.save()


def _make_accessible_reveal(path: Path) -> None:
    path.write_text(
        "<!doctype html><html><head><style data-template-accessible-slides>"
        "html, body { overflow-x: hidden; }</style></head>"
        '<body><nav aria-label="Presentation companion"></nav>'
        '<div aria-label="Presentation slides"><section aria-roledescription="slide">'
        "<h2>Current</h2></section></div><script>keyboard: true</script></body></html>",
        encoding="utf-8",
    )


def _scaffold_project(tmp_path: Path) -> Path:
    project = tmp_path / "projects" / "templates" / "test_proj"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    return project


def _make_docx(path: Path, *, corrupt: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        if corrupt:
            archive.writestr("unrelated.txt", "not a docx")
        else:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document/>")


def _make_epub(path: Path, *, corrupt: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if corrupt:
        path.write_bytes(b"%PDF-not-a-zip")
        return
    container = (
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="EPUB/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    package = (
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        '<manifest><item id="chapter" href="chapter.xhtml" '
        'media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="chapter"/></spine></package>'
    )
    chapter = '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Current.</p></body></html>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("EPUB/content.opf", package)
        archive.writestr("EPUB/chapter.xhtml", chapter)


class TestManuscriptDirForVerify:
    def test_prefers_injected_copy_when_populated(self, tmp_path: Path) -> None:
        source = tmp_path / "manuscript"
        injected = tmp_path / "output" / "manuscript"
        source.mkdir(parents=True)
        injected.mkdir(parents=True)
        (injected / "01_a.md").write_text("# A\n", encoding="utf-8")
        assert _manuscript_dir_for_verify(tmp_path) == injected

    def test_empty_injected_copy_falls_back_to_source(self, tmp_path: Path) -> None:
        (tmp_path / "output" / "manuscript").mkdir(parents=True)
        resolved = _manuscript_dir_for_verify(tmp_path)
        assert resolved.name == "manuscript"


class TestRenderingConfigForVerify:
    def test_malformed_yaml_raises_value_error(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        (project / "manuscript" / "config.yaml").write_text("render: [broken\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Could not read rendering configuration"):
            _rendering_config_for_verify(project)

    def test_non_mapping_config_raises_value_error(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        (project / "manuscript" / "config.yaml").write_text("- just\n- a list\n", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            _rendering_config_for_verify(project)


class TestVerifyCombinedHtml:
    def test_missing_html_fails(self, tmp_path: Path) -> None:
        assert _verify_combined_html(tmp_path) is False

    def test_empty_html_fails(self, tmp_path: Path) -> None:
        target = tmp_path / "output" / "web" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_text("", encoding="utf-8")
        assert _verify_combined_html(tmp_path) is False

    def test_non_standalone_html_fails(self, tmp_path: Path) -> None:
        target = tmp_path / "output" / "web" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_text("<p>fragment without document element</p>", encoding="utf-8")
        assert _verify_combined_html(tmp_path) is False

    def test_invalid_utf8_html_fails(self, tmp_path: Path) -> None:
        target = tmp_path / "output" / "web" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"\xff\xfe<html>")
        assert _verify_combined_html(tmp_path) is False

    def test_valid_doctype_html_passes(self, tmp_path: Path) -> None:
        target = tmp_path / "output" / "web" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_text("<!DOCTYPE html>\n<html><body>combined</body></html>", encoding="utf-8")
        assert _verify_combined_html(tmp_path) is True


class TestVerifySlideOutputs:
    def test_unreadable_slide_source_is_reported(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        source = project / "manuscript" / "01_intro.md"
        source.write_bytes(b"\xff\xfe\x00bad")
        result = _verify_slide_outputs(project)
        assert result is False

    def test_structurally_invalid_deck_fails(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        deck = project / "output" / "slides" / "01_intro_slides.pdf"
        deck.parent.mkdir(parents=True)
        deck.write_bytes(b"%PDF-1.4\n%%EOF\n")
        assert _verify_slide_outputs(project) is False

    def test_archive_profile_preserves_pdf_only_contract(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_pdf(project / "output" / "slides" / "01_intro_slides.pdf")

        assert _verify_slide_outputs(project, slides_profile="archive") is True

    def test_accessible_profile_requires_matching_reveal_output(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_pdf(project / "output" / "slides" / "01_intro_slides.pdf")

        assert _verify_slide_outputs(project, slides_profile="accessible") is False

    def test_accessible_profile_accepts_exact_valid_pair(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        slides = project / "output" / "slides"
        _make_pdf(slides / "01_intro_slides.pdf")
        _make_accessible_reveal(slides / "01_intro_slides.html")

        assert _verify_slide_outputs(project, slides_profile="accessible") is True


class TestPackageVerification:
    def test_docx_missing_package_fails(self, tmp_path: Path) -> None:
        assert _verify_docx_output(_scaffold_project(tmp_path), "test_proj") is False

    def test_docx_corrupt_zip_fails(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_docx(project / "output" / "docx" / "test_proj_combined.docx", corrupt=True)
        assert _verify_docx_output(project, "test_proj") is False

    def test_docx_valid_package_passes(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_docx(project / "output" / "docx" / "test_proj_combined.docx")
        assert _verify_docx_output(project, "test_proj") is True

    def test_epub_missing_package_fails(self, tmp_path: Path) -> None:
        assert _verify_epub_output(_scaffold_project(tmp_path), "test_proj") is False

    def test_epub_not_a_zip_fails(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_epub(project / "output" / "epub" / "test_proj_combined.epub", corrupt=True)
        assert _verify_epub_output(project, "test_proj") is False

    def test_epub_valid_package_passes(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        _make_epub(project / "output" / "epub" / "test_proj_combined.epub")
        assert _verify_epub_output(project, "test_proj") is True


class TestRenderOverrideAndConfigErrors:
    def test_pdf_override_script_routes_to_pdf_only_contract(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        scripts = project / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "_render_pdf_override.py").write_text("# override\n", encoding="utf-8")
        # No PDF outputs exist, so the legacy PDF-only contract must fail closed.
        assert verify_render_outputs(PROJECT, repo_root=tmp_path) is False

    def test_unreadable_config_fails_closed(self, tmp_path: Path) -> None:
        project = _scaffold_project(tmp_path)
        config = project / "manuscript" / "config.yaml"
        config.write_text("render: [broken\n", encoding="utf-8")
        assert verify_render_outputs(PROJECT, repo_root=tmp_path) is False
