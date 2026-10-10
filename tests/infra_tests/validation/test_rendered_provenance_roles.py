"""Real-file published versus coherent-derived provenance and audit roles."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
from infrastructure.validation.publication.audit import _build_publication_audit, build_publication_audit
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    validate_current_rendered_provenance,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)
from tests.infra_tests.validation.test_publication_audit import _write_snapshot_audit_fixture


def _renew(root: Path, project: Path) -> None:
    snapshot_current_artifact_manifest(project / "output")
    _write_green_validation_report(root, project)
    write_rendered_provenance_receipt(root, PROJECT)


def _publish(root: Path, project: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    _renew(root, project)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    assert validate_rendered_provenance(root, PROJECT).valid


def test_coherent_derived_output_keeps_published_index_strict(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    _publish(tmp_path, project)
    published = (project / RECEIPT_RELATIVE_PATH).read_bytes()
    write_doc(project / "output/data/result.json", '{"count": 8}\n')
    _renew(tmp_path, project)

    strict = validate_rendered_provenance(tmp_path, PROJECT)
    derived = validate_current_rendered_provenance(tmp_path, PROJECT)

    assert (project / RECEIPT_RELATIVE_PATH).read_bytes() != published
    assert [issue.code for issue in strict.issues] == ["CLEAN_INDEX_INCOMPLETE"]
    assert derived.valid
    # The current route did not stage or rewrite any published index evidence.
    assert not validate_rendered_provenance(tmp_path, PROJECT).valid


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("source", "VALIDATION_INPUTS_DRIFT"),
        ("artifact", "ARTIFACT_MANIFEST_INVALID"),
        ("contradictory-report", "VALIDATION_REPORT_INCONSISTENT"),
        ("missing-consumption", "UNCONSUMED_MANUSCRIPT"),
        ("missing-receipt", "MISSING"),
    ],
)
def test_both_roles_refuse_actual_stale_or_incomplete_evidence(
    tmp_path: Path,
    change: str,
    expected: str,
) -> None:
    project = _green_project(tmp_path)
    _publish(tmp_path, project)
    if change == "source":
        write_doc(project / "src/stub.py", '"""Changed after genuine snapshot validation."""\n')
    elif change == "artifact":
        write_doc(project / "output/data/result.json", '{"count": 9}\n')
    elif change == "contradictory-report":
        path = project / "output/reports/validation_report.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        report["checks"]["Rendered structure"] = False
        write_doc(path, json.dumps(report) + "\n")
    elif change == "missing-consumption":
        source = project / "manuscript/02_unconsumed.md"
        write_doc(source, "# Additional methods\n\nThis canonical input was never hydrated.\n")
        subprocess.run(["git", "add", str(source)], cwd=tmp_path, check=True)
    else:
        (project / RECEIPT_RELATIVE_PATH).unlink()

    for validate in (validate_rendered_provenance, validate_current_rendered_provenance):
        result = validate(tmp_path, PROJECT)
        assert not result.valid
        assert expected in {issue.code for issue in result.issues}


def test_current_audit_reuses_full_checkers_for_coherent_derived_files(tmp_path: Path) -> None:
    project = _write_snapshot_audit_fixture(tmp_path)
    _publish(tmp_path, project)
    write_doc(project / "output/data/result.json", '{"status": "updated"}\n')
    _renew(tmp_path, project)

    published = build_publication_audit(tmp_path, [PROJECT], rendered=True, include_drift=False)
    current = _build_publication_audit(
        tmp_path,
        [PROJECT],
        rendered=True,
        include_drift=False,
        require_figure_accessibility=True,
        current_rendered=True,
    )

    assert current.findings == ()
    assert {finding.diagnostic_code for finding in published.findings} == {
        "METHODS.STAGE_PROVENANCE_UNAVAILABLE",
        "PUBLICATION.RENDERED_PROVENANCE_CLEAN_INDEX_INCOMPLETE",
    }


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("skill", "PUBLICATION.PROJECT_SKILL_MISSING"),
        ("methods", "METHODS.STAGE_SCRIPT_MISSING"),
        ("figure", "PUBLICATION.FIGURE_REGISTRY"),
        ("placeholder", "PUBLICATION.PLACEHOLDER_TOKEN"),
    ],
)
def test_current_audit_retains_source_methods_figure_and_placeholder_failures(
    tmp_path: Path,
    change: str,
    expected: str,
) -> None:
    project = _write_snapshot_audit_fixture(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    if change == "skill":
        (project / ".agents/skills/template-test/SKILL.md").unlink()
    elif change == "methods":
        # A coherent rendered receipt cannot waive a missing declared method script.
        (tmp_path / "scripts/pipeline/stage_02_analysis.py").unlink()
        _renew(tmp_path, project)
        assert validate_current_rendered_provenance(tmp_path, PROJECT).valid
    elif change == "figure":
        write_doc(project / "output/manuscript/03_results.md", "![Figure](../figures/absent.png){#fig:absent}\n")
    else:
        with (project / "output/web/_combined_manuscript.md").open("a", encoding="utf-8") as stream:
            stream.write("\n{{UNRESOLVED}}\n")

    current = _build_publication_audit(
        tmp_path,
        [PROJECT],
        rendered=True,
        include_drift=False,
        require_figure_accessibility=True,
        current_rendered=True,
    )

    assert expected in {finding.diagnostic_code for finding in current.blocking_findings}
