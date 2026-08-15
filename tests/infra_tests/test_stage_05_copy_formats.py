"""End-to-end Stage 05 regressions for configured publication formats."""

from __future__ import annotations

from pathlib import Path

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


@pytest.mark.parametrize("with_stale_pdf", [False, True])
def test_html_only_copy_stage_succeeds_without_publishing_pdf(tmp_path, with_stale_pdf: bool) -> None:
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
    assert (copied / "web" / "index.html").is_file()
    assert not (copied / "demo_combined.pdf").exists()
    assert not (copied / "pdf").exists()
    if with_stale_pdf:
        assert (project_root / "output" / "pdf" / "demo_combined.pdf").is_file()


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
    assert (copied / "demo_combined.pdf").is_file()
    assert (copied / "pdf" / "demo_combined.pdf").is_file()
    assert not (copied / "web" / "index.html").exists()
    assert not (copied / "slides").exists()
