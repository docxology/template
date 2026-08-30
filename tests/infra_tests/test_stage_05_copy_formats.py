"""End-to-end Stage 05 regressions for configured publication formats."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import zipfile

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from scripts.pipeline.stage_05_copy import execute_copy_stage


def _write_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = canvas.Canvas(str(path), pagesize=letter)
    document.drawString(72, 720, "Current custom-rendered manuscript")
    document.showPage()
    document.save()


def _write_epub(path: Path) -> None:
    """Write a minimal well-formed EPUB package."""

    path.parent.mkdir(parents=True, exist_ok=True)
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


def _write_accessible_reveal(path: Path) -> None:
    path.write_text(
        "<!doctype html><html><head><style data-template-accessible-slides>"
        "html, body { overflow-x: hidden; }</style></head>"
        '<body><nav aria-label="Presentation companion"></nav>'
        '<div aria-label="Presentation slides"><section aria-roledescription="slide">'
        "<h2>Current</h2></section></div><script>keyboard: true</script></body></html>",
        encoding="utf-8",
    )


@pytest.mark.parametrize("with_stale_pdf", [False, True])
def test_html_only_copy_stage_succeeds_without_publishing_pdf(tmp_path, caplog, with_stale_pdf: bool) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n\nCurrent prose.\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: false\n    html: true\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    web_dir = project_root / "output" / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "index.html").write_text("<!doctype html><html><body>Current</body></html>\n", encoding="utf-8")
    if with_stale_pdf:
        stale_pdf = project_root / "output" / "pdf" / "demo_combined.pdf"
        stale_pdf.parent.mkdir(parents=True)
        stale_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    assert execute_copy_stage("active/demo", repo_root=tmp_path) == 0

    copied = tmp_path / "output" / "active" / "demo"
    copied_html = copied / "web" / "index.html"
    assert copied_html.is_file()
    assert copied_html.read_bytes() == (web_dir / "index.html").read_bytes()
    assert not (copied / "demo_combined.pdf").exists()
    assert not (copied / "pdf").exists()
    source_stats = project_root / "output" / "reports" / "output_statistics.json"
    copied_stats = copied / "reports" / "output_statistics.json"
    source_text = project_root / "output" / "reports" / "output_statistics.txt"
    copied_text = copied / "reports" / "output_statistics.txt"
    assert source_stats.read_bytes() == copied_stats.read_bytes()
    assert source_text.read_bytes() == copied_text.read_bytes()
    stats = json.loads(source_stats.read_text(encoding="utf-8"))
    assert stats["inventory_mode"] == "stable-local-output-v1"
    assert stats["inventory_scope"] == "stage5-delivery-mirror"
    assert stats["inventory_root"] == "output/active/demo"
    assert stats["directories"]["pdf"]["exists"] is False
    assert stats["directories"]["web"]["file_count"] == 1
    assert not any(
        name in {"pdf/ directory", "slides/ directory", "docx/ directory", "epub/ directory"}
        or name.endswith(("_combined.pdf", "_combined.docx", "_combined.epub"))
        or name == "slides/*_slides.pdf"
        for name in stats["missing_expected_files"]
    )
    assert stats["total_files"] == sum(info["file_count"] for info in stats["directories"].values())
    physical_total = sum(1 for path in copied.rglob("*") if path.is_file())
    physical_reports = sum(1 for path in (copied / "reports").rglob("*") if path.is_file())
    assert f"Physical local mirror: {physical_total} files" in caplog.text
    assert f"• Reports: {physical_reports}" in caplog.text
    assert "slides/ has no stable artifacts" not in caplog.text
    assert "docx/ has no stable artifacts" not in caplog.text
    assert "epub/ has no stable artifacts" not in caplog.text
    if with_stale_pdf:
        assert (project_root / "output" / "pdf" / "demo_combined.pdf").is_file()
    else:
        first_total = physical_total
        first_reports = physical_reports
        caplog.clear()
        assert execute_copy_stage("active/demo", repo_root=tmp_path) == 0
        repeat_total = sum(1 for path in copied.rglob("*") if path.is_file())
        repeat_reports = sum(1 for path in (copied / "reports").rglob("*") if path.is_file())
        assert (repeat_total, repeat_reports) == (first_total, first_reports)
        assert f"Physical local mirror: {repeat_total} files" in caplog.text
        assert f"• Reports: {repeat_reports}" in caplog.text


def test_legacy_pdf_override_copy_stage_uses_pdf_only_contract(tmp_path) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    # The legacy override remains PDF-only even when ordinary format toggles
    # would otherwise request HTML and slides.
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: false\n    html: true\n    slides: true\n",
        encoding="utf-8",
    )
    override = project_root / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("raise SystemExit(0)\n", encoding="utf-8")
    _write_pdf(project_root / "output" / "pdf" / "demo_combined.pdf")

    assert execute_copy_stage("active/demo", repo_root=tmp_path) == 0

    copied = tmp_path / "output" / "active" / "demo"
    root_alias = copied / "demo_combined.pdf"
    canonical_pdf = copied / "pdf" / "demo_combined.pdf"
    assert root_alias.is_file()
    assert canonical_pdf.is_file()
    assert root_alias.read_bytes() == canonical_pdf.read_bytes()
    assert not (copied / "web" / "index.html").exists()
    assert not (copied / "slides").exists()


@pytest.mark.parametrize(("with_reveal", "expected_status"), [(False, 1), (True, 0)])
def test_accessible_slide_copy_requires_exact_pair(tmp_path: Path, with_reveal: bool, expected_status: int) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    manuscript = project_root / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_intro.md").write_text("# Intro\n\nCurrent evidence.\n", encoding="utf-8")
    (manuscript / "config.yaml").write_text(
        "render:\n"
        "  formats:\n"
        "    pdf: false\n"
        "    html: false\n"
        "    slides: true\n"
        "    docx: false\n"
        "    epub: false\n"
        "  slides:\n"
        "    profile: accessible\n",
        encoding="utf-8",
    )
    slides = project_root / "output" / "slides"
    _write_pdf(slides / "01_intro_slides.pdf")
    if with_reveal:
        _write_accessible_reveal(slides / "01_intro_slides.html")

    assert execute_copy_stage("active/demo", repo_root=tmp_path) == expected_status


def test_copy_stage_maps_ignored_delivery_tree_to_source_inventory(tmp_path, caplog) -> None:
    """Root ``output/`` ignores must not erase stable copy-validation facts."""
    project_root = tmp_path / "projects" / "active" / "demo"
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    _write_pdf(project_root / "output" / "pdf" / "demo_combined.pdf")
    (project_root / "output" / "pdf" / "_combined_manuscript.tex").write_text(
        "ignored intermediate\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text(
        "/output/\nprojects/active/demo/output/pdf/_combined_manuscript.*\n",
        encoding="utf-8",
    )

    with caplog.at_level("INFO"):
        assert execute_copy_stage("active/demo", repo_root=tmp_path) == 0

    assert "pdf/ valid (1 files" in caplog.text
    assert "✓ pdf: 1 files" in caplog.text
    assert "pdf/ has no stable artifacts" not in caplog.text


def test_docx_epub_copy_statistics_match_enabled_formats(tmp_path) -> None:
    """Enabled package formats are counted without disabled-format warnings."""
    project_root = tmp_path / "projects" / "active" / "demo"
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: false\n    html: false\n    slides: false\n    docx: true\n    epub: true\n",
        encoding="utf-8",
    )
    docx = project_root / "output" / "docx" / "demo_combined.docx"
    docx.parent.mkdir(parents=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    epub = project_root / "output" / "epub" / "demo_combined.epub"
    _write_epub(epub)

    assert execute_copy_stage("active/demo", repo_root=tmp_path) == 0

    stats = json.loads((project_root / "output" / "reports" / "output_statistics.json").read_text(encoding="utf-8"))
    assert stats["directories"]["docx"]["file_count"] == 1
    assert stats["directories"]["epub"]["file_count"] == 1
    assert stats["missing_expected_files"] == [
        "figures/ directory",
        "data/ directory",
        "reports/ directory",
    ]
