"""Enabled-format inventory identity gates and Stage 5 disabled-output filtering."""

from __future__ import annotations
import subprocess
import zipfile
from pathlib import Path
from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory
from infrastructure.validation.output.render_formats import (
    remove_disabled_render_outputs,
    validate_enabled_render_outputs,
)
from tests.infra_tests.validation._render_formats_helpers import _minimal_pdf, _write_epub


def test_enabled_format_stability_accepts_relative_output_and_supplied_inventory(tmp_path, monkeypatch) -> None:
    """Relative callers and absolute inventory paths must share one identity."""
    monkeypatch.chdir(tmp_path)
    output_dir = Path("output")
    pdf = output_dir / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    inventory = collect_stable_output_inventory(output_dir)

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is True
    )


def test_enabled_docx_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """A valid ignored DOCX package must fail the release inventory gate."""
    output_dir = tmp_path / "output"
    docx = output_dir / "docx" / "demo_combined.docx"
    docx.parent.mkdir(parents=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/docx/*.docx\n", encoding="utf-8")

    assert validate_enabled_render_outputs(output_dir, "demo", {"docx"}) is False


def test_enabled_epub_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """A valid ignored EPUB package must fail the release inventory gate."""
    output_dir = tmp_path / "output"
    epub = output_dir / "epub" / "demo_combined.epub"
    _write_epub(epub)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/epub/*.epub\n", encoding="utf-8")

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_stage5_filter_removes_disabled_outputs_but_preserves_authored_web(tmp_path) -> None:
    output_dir = tmp_path / "output" / "active" / "demo"
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "index.html").write_text("<!doctype html><html><body>Current</body></html>\n", encoding="utf-8")
    (web_dir / "dashboard.html").write_text("<!doctype html><html><body>Dashboard</body></html>\n", encoding="utf-8")
    for directory, filename in (
        ("pdf", "old.pdf"),
        ("slides", "old_slides.pdf"),
        ("docx", "demo_combined.docx"),
        ("epub", "demo_combined.epub"),
    ):
        path = output_dir / directory / filename
        path.parent.mkdir(parents=True)
        path.write_bytes(b"stale")
    (output_dir / "demo_combined.pdf").write_bytes(_minimal_pdf())

    removed = remove_disabled_render_outputs(output_dir, "active/demo", {"html"})

    assert removed
    assert not (output_dir / "demo_combined.pdf").exists()
    assert not (output_dir / "pdf").exists()
    assert not (output_dir / "slides").exists()
    assert not (output_dir / "docx").exists()
    assert not (output_dir / "epub").exists()
    assert (web_dir / "index.html").is_file()
    assert (web_dir / "dashboard.html").is_file()
    assert validate_enabled_render_outputs(output_dir, "active/demo", {"html"}) is True


def test_stage5_filter_preserves_cross_format_composition_evidence(tmp_path) -> None:
    output_dir = tmp_path / "output" / "active" / "demo"
    web_dir = output_dir / "web"
    reports_dir = output_dir / "reports"
    web_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    combined = web_dir / "_combined_manuscript.md"
    composition = reports_dir / "manuscript_composition.json"
    combined.write_text("# Current combined source\n", encoding="utf-8")
    composition.write_text('{"combined_path":"output/web/_combined_manuscript.md"}\n', encoding="utf-8")
    (web_dir / "index.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")
    (web_dir / "manuscript__01_intro.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")
    (web_dir / "favicon.ico").write_bytes(b"stale renderer favicon")

    remove_disabled_render_outputs(output_dir, "active/demo", {"docx"})

    assert combined.is_file()
    assert composition.is_file()
    assert not (web_dir / "index.html").exists()
    assert not (web_dir / "manuscript__01_intro.html").exists()
    assert not (web_dir / "favicon.ico").exists()


def test_disabled_html_rejects_renderer_owned_stale_favicon(tmp_path) -> None:
    output_dir = tmp_path / "output"
    docx = output_dir / "docx" / "demo_combined.docx"
    docx.parent.mkdir(parents=True)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    favicon = output_dir / "web" / "favicon.ico"
    favicon.parent.mkdir(parents=True)
    favicon.write_bytes(b"stale renderer favicon")

    assert validate_enabled_render_outputs(output_dir, "demo", {"docx"}) is False
