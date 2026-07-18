"""State-changing publishing preflight tests."""

from pathlib import Path
import hashlib

import pytest

from infrastructure.publishing.preflight import publishing_preflight


def _public_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "projects/templates/template_code_project"
    pdf = project / "output/pdf/template_code_project_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-1.7\n")
    return project, pdf


def test_preflight_emits_exact_payload_and_redacted_sources(tmp_path: Path) -> None:
    _project, pdf = _public_project(tmp_path)
    result = publishing_preflight(
        tmp_path,
        "templates/template_code_project",
        [pdf],
        {"github": "environment", "zenodo": "cli"},
    )
    assert result["payload"] == [
        {
            "path": "output/pdf/template_code_project_combined.pdf",
            "bytes": 9,
            "sha256": hashlib.sha256(b"%PDF-1.7\n").hexdigest(),
        }
    ]
    assert result["credential_sources"] == {"github": "environment", "zenodo": "cli"}


def test_preflight_refuses_local_only_project(tmp_path: Path) -> None:
    project = tmp_path / "projects/working/private"
    project.mkdir(parents=True)
    payload = project / "paper.pdf"
    payload.write_bytes(b"pdf")
    with pytest.raises(ValueError, match="local-only"):
        publishing_preflight(tmp_path, "working/private", [payload], {})


def test_preflight_refuses_payload_outside_project(tmp_path: Path) -> None:
    _project, _pdf = _public_project(tmp_path)
    outside = tmp_path / "output/templates/template_code_project/paper.pdf"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"pdf")
    with pytest.raises(ValueError, match="outside canonical project tree"):
        publishing_preflight(tmp_path, "templates/template_code_project", [outside], {})


def test_preflight_refuses_duplicate_payload_entries(tmp_path: Path) -> None:
    _project, pdf = _public_project(tmp_path)
    with pytest.raises(ValueError, match="duplicated"):
        publishing_preflight(tmp_path, "templates/template_code_project", [pdf, pdf], {})


def test_preflight_refuses_untrusted_credential_label_that_could_leak_a_secret(tmp_path: Path) -> None:
    _project, pdf = _public_project(tmp_path)
    with pytest.raises(ValueError, match="credential name"):
        publishing_preflight(
            tmp_path,
            "templates/template_code_project",
            [pdf],
            {"ghp_secret_material_must_not_be_logged": "environment"},
        )


def test_preflight_refuses_invalid_pdf_signature(tmp_path: Path) -> None:
    _project, pdf = _public_project(tmp_path)
    pdf.write_bytes(b"not a pdf")
    with pytest.raises(ValueError, match="not a PDF"):
        publishing_preflight(tmp_path, "templates/template_code_project", [pdf], {})
