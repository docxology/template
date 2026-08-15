"""Real-filesystem regressions for format-aware Stage 4/5 gates."""

from __future__ import annotations

import zipfile

from infrastructure.validation.output.pipeline import (
    _build_core_checks,
    execute_validation_pipeline,
    verify_outputs_exist,
)
from infrastructure.validation.output.render_formats import (
    enabled_render_formats,
    load_effective_rendering_config,
    remove_disabled_render_outputs,
    validate_enabled_render_outputs,
)


def _minimal_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\nstartxref\n0\n%%EOF\n"


def _html_only_project(tmp_path):
    project_root = tmp_path / "projects" / "active" / "demo"
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
    return project_root


def test_stage4_html_only_accepts_clean_tree(tmp_path) -> None:
    _html_only_project(tmp_path)

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert "PDF validation" not in checks
    assert "Transmission bookends" not in checks
    assert checks["Enabled render outputs"]() is True


def test_stage4_html_only_full_stage_succeeds_without_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)
    recorded_checks = {}

    def report_writer(check_results, *_args, **_kwargs):
        recorded_checks.update(check_results)
        return {"timestamp": "1970-01-01T00:00:00Z"}

    assert execute_validation_pipeline("demo", repo_root=tmp_path, report_writer=report_writer) == 0
    assert recorded_checks["Output structure"] is True


def test_stage4_html_only_detailed_structure_does_not_invent_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)

    valid, details = verify_outputs_exist("demo", repo_root=tmp_path, require_pdf=False)

    assert valid is True
    assert details["structure"]["missing_files"] == []
    assert details["structure"]["directory_structure"]["combined_pdf"]["required"] is False


def test_stage4_html_only_rejects_stale_disabled_pdf(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    stale_pdf = project_root / "output" / "pdf" / "old_section.pdf"
    stale_pdf.parent.mkdir(parents=True)
    stale_pdf.write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert checks["Enabled render outputs"]() is False


def test_stage4_pdf_requires_canonical_combined_pdf(tmp_path) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n",
        encoding="utf-8",
    )
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "other_valid.pdf").write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in _build_core_checks("demo", repo_root=tmp_path)}

    assert checks["PDF validation"]() is True
    assert checks["Enabled render outputs"]() is False


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
