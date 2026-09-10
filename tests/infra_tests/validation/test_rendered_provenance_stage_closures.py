"""Rendered publication provenance: stage source/config closure drift and trackable publication surfaces."""

from __future__ import annotations
import subprocess
from pathlib import Path
import pytest
from infrastructure.validation.publication.rendered_provenance import (
    RenderedProvenanceError,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("relative_path", "replacement", "fingerprint"),
    [
        (
            "infrastructure/research/runtime_prompt.md",
            "Changed runtime research prompt.\n",
            "stage",
        ),
        (
            "infrastructure/rendering/layout.template",
            "<article>{{ manuscript }}</article>\n",
            "stage",
        ),
        (
            "infrastructure/validation/output/runtime_gate.py",
            "REQUIRE_CURRENT_OUTPUT = False\n",
            "stage",
        ),
        (
            "scripts/__init__.py",
            '"""Changed stage bootstrap."""\n',
            "stage",
        ),
        (
            "projects/templates/template_test/src/stub.py",
            '"""Changed project source."""\n',
            "source",
        ),
        (
            "projects/templates/template_test/manuscript/config.yaml",
            "paper:\n  title: Changed title\n",
            "config",
        ),
        (
            ".gitignore",
            "# changed release ignore semantics\n*.never-created\n",
            "config",
        ),
    ],
)
def test_complete_stage_source_and_config_closures_detect_drift(
    tmp_path: Path,
    relative_path: str,
    replacement: str,
    fingerprint: str,
) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    write_doc(tmp_path / relative_path, replacement)
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert getattr(before, fingerprint) != getattr(after, fingerprint)
    _write_green_validation_report(tmp_path, project)
    issue_codes = {issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues}
    assert f"{fingerprint.upper()}_FINGERPRINT_DRIFT" in issue_codes
    assert "VALIDATION_REPORT_DRIFT" in issue_codes


def test_staged_new_non_python_runtime_asset_participates_in_stage_closure(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    runtime_asset = tmp_path / "infrastructure" / "rendering" / "new_runtime_asset.template"
    write_doc(runtime_asset, "<aside>new behavior</aside>\n")
    subprocess.run(["git", "add", str(runtime_asset)], cwd=tmp_path, check=True)
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert after.stage.file_count == before.stage.file_count + 1
    assert after.stage != before.stage
    with pytest.raises(RenderedProvenanceError, match="exact current rendered snapshot") as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_INPUTS_DRIFT"


def test_advanced_publication_surfaces_are_trackable_but_intermediates_stay_ignored() -> None:
    project = "projects/templates/template_advanced_literature_review/output"
    stable = (
        f"{project}/manuscript/00_abstract.md",
        f"{project}/figures/figure_registry.json",
        f"{project}/web/_combined_manuscript.md",
        f"{project}/pdf/template_advanced_literature_review_combined.pdf",
        f"{project}/slides/00_abstract_slides.pdf",
        f"{project}/reports/artifact_manifest.json",
        f"{project}/reports/manuscript_composition.json",
        f"{project}/reports/rendered_provenance.json",
        f"{project}/reports/validation_report.json",
    )
    for relative in stable:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", "--no-index", relative],
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 1, relative

    transient = subprocess.run(
        [
            "git",
            "check-ignore",
            "--quiet",
            "--no-index",
            f"{project}/pdf/_combined_manuscript.tex",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert transient.returncode == 0
