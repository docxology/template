"""Rendered publication provenance: receipt and snapshot attestation lifecycle over a green project."""

from __future__ import annotations
import json
import subprocess
from pathlib import Path
import pytest
from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    snapshot_current_artifact_manifest,
)
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    RenderedProvenanceError,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    RenderedSnapshotError,
    _output_records,
    build_current_rendered_snapshot,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)


def test_receipt_is_deterministic_and_current_for_green_real_files(tmp_path: Path) -> None:
    project = _green_project(tmp_path)

    first = write_rendered_provenance_receipt(tmp_path, PROJECT)
    first_bytes = (project / RECEIPT_RELATIVE_PATH).read_bytes()
    second = write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert first == second
    assert (project / RECEIPT_RELATIVE_PATH).read_bytes() == first_bytes
    assert first.evidence_mode == "validated-co-snapshot-fingerprint-bridge"
    assert first.stage.file_count == 6
    assert first.source.file_count >= 3
    assert first.config.file_count >= 3
    assert first.output.file_count >= 4
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_rendered_snapshot_accepts_explicit_stable_local_manifest(tmp_path: Path) -> None:
    """A blanket-ignored lifecycle output compares within its authorized mode."""
    project = tmp_path / "private" / "demo"
    result = project / "output" / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"count": 7}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    (project / ".gitignore").write_text("output/\n", encoding="utf-8")
    snapshot_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    records, manifest = _output_records(
        project,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [record.key for record in records] == ["output/data/result.json"]
    assert manifest.path == "output/reports/artifact_manifest.json"


def test_rendered_snapshot_rejects_manifest_from_another_inventory_mode(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["inventory_mode"] = STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(RenderedSnapshotError) as exc_info:
        build_current_rendered_snapshot(tmp_path, PROJECT)

    assert exc_info.value.code == "ARTIFACT_MANIFEST_INVALID"
    assert "artifact inventory mode mismatch" in str(exc_info.value)


def test_clean_index_requires_every_manifest_and_evidence_path(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    untracked = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in untracked.issues] == ["CLEAN_INDEX_INCOMPLETE"]
    assert "rendered_provenance.json" in untracked.issues[0].message

    subprocess.run(
        ["git", "add", str(project / RECEIPT_RELATIVE_PATH)],
        cwd=tmp_path,
        check=True,
    )
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_historical_green_report_cannot_reattest_changed_source(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()

    write_doc(project / "src" / "stub.py", '"""Changed after validation."""\n')

    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert receipt_path.read_bytes() == old_receipt


def test_internally_contradictory_validation_report_fails_closed(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()
    report_path = project / "output" / "reports" / "validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["checks"]["Rendered structure"] = False
    write_doc(report_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["VALIDATION_REPORT_INCONSISTENT"]
    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "VALIDATION_REPORT_INCONSISTENT"
    assert receipt_path.read_bytes() == old_receipt


def test_extra_stable_output_is_rejected_until_manifest_attests_it(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    old_receipt = receipt_path.read_bytes()

    write_doc(project / "output" / "web" / "unattested-runtime.js", "export const value = 1;\n")
    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["ARTIFACT_MANIFEST_INCOMPLETE"]
    assert "output/web/unattested-runtime.js" in validation.issues[0].message
    with pytest.raises(RenderedProvenanceError) as error:
        write_rendered_provenance_receipt(tmp_path, PROJECT)
    assert error.value.code == "ARTIFACT_MANIFEST_INCOMPLETE"
    assert receipt_path.read_bytes() == old_receipt


def test_runtime_history_is_nonstable_but_unattested_report_still_fails(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    write_doc(
        project / "output" / "reports" / ".history" / "telemetry-123.json",
        '{"runtime": true}\n',
    )
    assert validate_rendered_provenance(tmp_path, PROJECT).valid

    write_doc(project / "output" / "reports" / "unattested_quality_report.json", '{"quality": "green"}\n')
    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["ARTIFACT_MANIFEST_INCOMPLETE"]
    assert "output/reports/unattested_quality_report.json" in validation.issues[0].message


def test_report_and_receipt_are_fixed_points_over_ignored_runtime_state(tmp_path: Path) -> None:
    """Regenerating validation evidence must ignore machine-local residue."""
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    report_path = project / "output" / "reports" / "validation_report.json"
    receipt_path = project / RECEIPT_RELATIVE_PATH
    baseline_report = report_path.read_bytes()
    baseline_receipt = receipt_path.read_bytes()

    ignored_files = {
        "pdf/build.aux": b"latex auxiliary",
        "reports/.history/telemetry-123.json": b"{}\n",
        "reports/snapshots/stage.json": b"{}\n",
        "logs/pipeline.log": b"runtime log\n",
        "figures/.partial.png": b"atomic leftover",
    }
    for relative, payload in ignored_files.items():
        path = project / "output" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    for relative in ("slides", "simulations", "llm"):
        (project / "output" / relative).mkdir(parents=True, exist_ok=True)

    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)

    assert report_path.read_bytes() == baseline_report
    assert receipt_path.read_bytes() == baseline_receipt
    assert validate_rendered_provenance(tmp_path, PROJECT).valid


def test_manifest_and_validation_report_digests_are_bound_separately(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    write_doc(manifest_path, json.dumps(manifest_payload, separators=(",", ":")) + "\n")
    _write_green_validation_report(tmp_path, project)

    manifest_codes = {issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues}
    assert "ARTIFACT_MANIFEST_DRIFT" in manifest_codes
    assert "VALIDATION_REPORT_DRIFT" in manifest_codes

    write_rendered_provenance_receipt(tmp_path, PROJECT)
    report_path = project / "output" / "reports" / "validation_report.json"
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    report_payload["recommendations"].append({"action": "Review deterministic evidence."})
    write_doc(report_path, json.dumps(report_payload, indent=2, sort_keys=True) + "\n")

    assert [issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues] == [
        "VALIDATION_REPORT_DRIFT"
    ]
