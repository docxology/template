"""Real-filesystem regressions for Stage 4 HTML-only and PDF render gates."""

from __future__ import annotations
import subprocess
from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory, output_inventory_mode_for_project
from infrastructure.project.discovery import resolve_project_root
from infrastructure.validation.output.pipeline import (
    _build_core_checks,
    execute_validation_pipeline,
    verify_outputs_exist,
)
from infrastructure.validation.output.render_formats import validate_enabled_render_outputs
from tests.infra_tests.validation._render_formats_helpers import _minimal_pdf, _html_only_project


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

    valid, details = verify_outputs_exist(
        "demo",
        repo_root=tmp_path,
        require_pdf=False,
        enabled_formats={"html"},
    )

    assert valid is True
    assert details["structure"]["missing_files"] == []
    assert details["structure"]["directory_structure"]["combined_pdf"]["required"] is False
    assert details["structure"]["directory_structure"]["slides"]["required"] is False
    assert details["structure"]["directory_structure"]["docx"]["required"] is False
    assert details["structure"]["directory_structure"]["epub"]["required"] is False
    assert not any(
        name in message
        for message in details["issues_by_severity"]["info"]
        for name in ("pdf/", "slides/", "docx/", "epub/")
    )


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


def test_enabled_pdf_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """Structural validity cannot substitute for a shippable PDF."""
    output_dir = tmp_path / "output"
    pdf = output_dir / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/pdf/*.pdf\n", encoding="utf-8")

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"pdf"},
            pdf_validator=lambda: True,
        )
        is False
    )


def test_managed_external_project_accepts_valid_ignored_local_pdf(tmp_path) -> None:
    """A lifecycle sidecar's blanket output ignore is local scope, not absence."""
    repo_root = tmp_path / "template"
    external_project = tmp_path / "private" / "demo"
    manuscript = external_project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    pdf = external_project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=external_project, check=True, capture_output=True)
    (external_project / ".gitignore").write_text("output/\n", encoding="utf-8")
    managed_link = repo_root / "projects" / "working" / "demo"
    managed_link.parent.mkdir(parents=True)
    managed_link.symlink_to(external_project, target_is_directory=True)

    resolved = resolve_project_root(repo_root, "working/demo")
    inventory = collect_stable_output_inventory(
        resolved / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, resolved),
    )

    assert resolved == external_project.resolve()
    assert inventory.mode == "stable-local-output-v1"
    assert pdf.absolute() in inventory.files
    checks = {check.name: check.run for check in _build_core_checks("working/demo", repo_root=repo_root)}
    assert checks["Enabled render outputs"]() is True
    assert (
        validate_enabled_render_outputs(
            resolved / "output",
            "working/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is True
    )


def test_public_template_blanket_ignore_cannot_downgrade_shippable_gate(tmp_path) -> None:
    """A public ignore-policy regression must expose an empty release inventory."""
    repo_root = tmp_path / "template"
    project = repo_root / "projects" / "templates" / "demo"
    pdf = project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text("projects/templates/demo/output/\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, project),
    )

    assert inventory.mode == "stable-shippable-output-v1"
    assert inventory.files == ()
    assert (
        validate_enabled_render_outputs(
            project / "output",
            "templates/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is False
    )
