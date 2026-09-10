"""Render-format environment overrides and slides deck/accessibility gates."""

from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from infrastructure.validation.output.render_formats import (
    enabled_render_formats,
    load_effective_rendering_config,
    validate_enabled_render_outputs,
)
from tests.infra_tests.validation._render_formats_helpers import _minimal_pdf, _html_only_project


def _write_valid_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawString(72, 720, "Current slide output")
    pdf.showPage()
    pdf.save()


def _write_accessible_reveal(path: Path) -> None:
    path.write_text(
        "<!doctype html><html><head><title>Current — presentation</title>"
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
        "<style data-template-accessible-slides>html, body { overflow-x: hidden; }</style></head>"
        '<body><a class="skip-link" href="#main-content">Skip to main content</a>'
        '<nav class="slide-reader-nav" aria-label="Presentation companion"></nav>'
        '<main id="main-content"><h1>Current presentation</h1>'
        '<div aria-label="Presentation slides"><section aria-roledescription="slide" '
        'aria-labelledby="current-heading"><h2 id="current-heading">Current</h2>'
        "<p>Visible slide body.</p></section></div>"
        "<script data-template-interactive-keyboard-guard>/* keyboard guard */</script>"
        "<script>Reveal.initialize({scrollActivationWidth: null, keyboard: true});</script>"
        "</main></body></html>",
        encoding="utf-8",
    )


def test_enable_pdf_environment_override_remains_strict(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    config = load_effective_rendering_config(project_root, env={"ENABLE_PDF": "1"})

    formats = enabled_render_formats(config)

    assert formats == {"html", "pdf"}
    assert validate_enabled_render_outputs(project_root / "output", "demo", formats) is False


def test_legacy_pdf_override_forces_same_pdf_only_contract_in_later_stages(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    override = project_root / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("raise SystemExit(0)\n", encoding="utf-8")

    config = load_effective_rendering_config(
        project_root,
        env={"ENABLE_HTML": "1", "ENABLE_SLIDES": "1", "ENABLE_DOCX": "1"},
    )

    assert enabled_render_formats(config) == {"pdf"}


def test_slides_enabled_requires_at_least_one_current_deck(tmp_path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_intro.md").write_text(
        "<!-- render:skip-beamer -->\n# Intro\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"slides"},
            manuscript_dir=manuscript_dir,
        )
        is False
    )


def test_slides_enabled_rejects_deck_for_deleted_source(tmp_path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_current.md").write_text("# Current\n", encoding="utf-8")
    slides_dir = tmp_path / "output" / "slides"
    slides_dir.mkdir(parents=True)
    (slides_dir / "01_current_slides.pdf").write_bytes(_minimal_pdf())
    (slides_dir / "00_deleted_slides.pdf").write_bytes(_minimal_pdf())

    assert (
        validate_enabled_render_outputs(
            tmp_path / "output",
            "demo",
            {"slides"},
            manuscript_dir=manuscript_dir,
        )
        is False
    )


def test_archive_slides_preserve_pdf_only_validation_contract(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_current.md").write_text("# Current\n", encoding="utf-8")
    slides = tmp_path / "output" / "slides"
    _write_valid_pdf(slides / "01_current_slides.pdf")

    assert validate_enabled_render_outputs(
        tmp_path / "output",
        "demo",
        {"slides"},
        manuscript_dir=manuscript_dir,
        slides_profile="archive",
    )


def test_accessible_slides_reject_missing_reveal_pair_member(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_current.md").write_text("# Current\n", encoding="utf-8")
    slides = tmp_path / "output" / "slides"
    _write_valid_pdf(slides / "01_current_slides.pdf")

    assert not validate_enabled_render_outputs(
        tmp_path / "output",
        "demo",
        {"slides"},
        manuscript_dir=manuscript_dir,
        slides_profile="accessible",
    )


def test_accessible_slides_accept_exact_stable_pair(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "01_current.md").write_text("# Current\n", encoding="utf-8")
    slides = tmp_path / "output" / "slides"
    _write_valid_pdf(slides / "01_current_slides.pdf")
    _write_accessible_reveal(slides / "01_current_slides.html")

    assert validate_enabled_render_outputs(
        tmp_path / "output",
        "demo",
        {"slides"},
        manuscript_dir=manuscript_dir,
        slides_profile="accessible",
    )
