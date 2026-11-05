"""Specific validation-input drift diagnostics without widening provenance custody."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    RenderedSnapshotError,
    build_current_rendered_snapshot,
    read_committed_validation_report,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import PROJECT, _green_project


@pytest.mark.parametrize("label", ("stage", "source", "config", "output"))
def test_report_drift_names_the_changed_fingerprint(tmp_path: Path, label: str) -> None:
    project = _green_project(tmp_path)
    current = build_current_rendered_snapshot(tmp_path, PROJECT)
    report_path = project / "output/reports/validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["validated_inputs"]["fingerprints"][label]["sha256"] = "0" * 64
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RenderedSnapshotError) as error:
        read_committed_validation_report(tmp_path, PROJECT, current)

    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert str(error.value).endswith(f"(changed: fingerprints.{label})")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("schema_version", "unrecognized"),
        ("artifact_manifest", {}),
        ("composition_manifest", {}),
        ("combined_manuscript", {}),
        ("consumed_manuscript", []),
        ("fingerprints", "invalid fingerprint mapping"),
    ],
)
def test_report_drift_names_changed_commitment_without_echoing_values(
    tmp_path: Path, field: str, replacement: object
) -> None:
    project = _green_project(tmp_path)
    current = build_current_rendered_snapshot(tmp_path, PROJECT)
    report_path = project / "output/reports/validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["validated_inputs"][field] = replacement
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RenderedSnapshotError) as error:
        read_committed_validation_report(tmp_path, PROJECT, current)

    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert str(error.value).endswith(f"(changed: {field})")
    assert "invalid fingerprint mapping" not in str(error.value)


@pytest.mark.parametrize("nested", (False, True))
def test_foreign_report_fields_remain_refused_without_echoing_their_names(tmp_path: Path, nested: bool) -> None:
    project = _green_project(tmp_path)
    current = build_current_rendered_snapshot(tmp_path, PROJECT)
    report_path = project / "output/reports/validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    target = payload["validated_inputs"]
    if nested:
        target = target["fingerprints"]
    target["NEVER_ECHO_UNTRUSTED_FIELD"] = "untrusted value"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RenderedSnapshotError) as error:
        read_committed_validation_report(tmp_path, PROJECT, current)

    assert error.value.code == "VALIDATION_INPUTS_DRIFT"
    assert str(error.value).endswith(f"(changed: {'fingerprints.fields' if nested else 'fields'})")
    assert "NEVER_ECHO_UNTRUSTED_FIELD" not in str(error.value)
    assert "untrusted value" not in str(error.value)


def test_actual_stage_drift_reaches_provenance_finding_without_rewriting_evidence(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt_path = project / RECEIPT_RELATIVE_PATH
    report_path = project / "output/reports/validation_report.json"
    before = receipt_path.read_bytes(), report_path.read_bytes()
    write_doc(tmp_path / "infrastructure/validation/output/runtime_gate.py", "REQUIRE_CURRENT_OUTPUT = False\n")

    validation = validate_rendered_provenance(tmp_path, PROJECT)

    assert [issue.code for issue in validation.issues] == ["VALIDATION_INPUTS_DRIFT"]
    assert validation.issues[0].message.endswith("(changed: fingerprints.stage)")
    assert (receipt_path.read_bytes(), report_path.read_bytes()) == before


def test_equivalent_physical_roots_share_the_complete_validation_commitment(tmp_path: Path) -> None:
    original = tmp_path / "original"
    _green_project(original)
    write_rendered_provenance_receipt(original, PROJECT)
    copied = tmp_path / "separate-copy"
    shutil.copytree(original, copied)
    assert original.stat().st_ino != copied.stat().st_ino
    first = build_current_rendered_snapshot(original, PROJECT)
    second = build_current_rendered_snapshot(copied, PROJECT)

    assert first.validated_inputs_dict() == second.validated_inputs_dict()
    assert read_committed_validation_report(original, PROJECT, first) == read_committed_validation_report(
        copied, PROJECT, second
    )
    assert validate_rendered_provenance(original, PROJECT).valid
    assert validate_rendered_provenance(copied, PROJECT).valid
