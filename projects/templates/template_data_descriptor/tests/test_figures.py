"""Tests for figure-data preparers (no mocks; no matplotlib needed)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from data_descriptor import (
    FileInventoryRow,
    FileVerification,
    ProvenanceStep,
    SchemaRow,
    build_descriptor_report,
    demo_broken_descriptor,
    descriptor_figure_specs_for_data,
    file_inventory_rows,
    provenance_steps,
    schema_table_rows,
    severity_counts,
    validate_descriptor,
    verify_descriptor_files,
    verification_table_rows,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_descriptor.json").read_text(encoding="utf-8")),
    )


class TestSchemaTableRows:
    """Schema rows carry every field with a compact constraint label."""

    def test_rows_cover_all_fields_in_order(self) -> None:
        rows = schema_table_rows(load_fixture())
        assert all(isinstance(row, SchemaRow) for row in rows)
        assert [row.name for row in rows] == [
            "sample_id",
            "subject_id",
            "group",
            "value",
            "collected_on",
            "instrument",
        ]

    def test_constraint_labels_are_rendered(self) -> None:
        rows = {row.name: row for row in schema_table_rows(load_fixture())}
        assert "pattern ^S[0-9]{3}$" in rows["sample_id"].constraint
        assert "control" in rows["group"].constraint and "treatment" in rows["group"].constraint
        assert rows["value"].constraint == "[0, 1]"
        assert rows["value"].unit == "normalized_score"
        assert rows["value"].nullable == "no"
        assert rows["collected_on"].constraint == ""

    def test_non_list_fields_returns_empty(self) -> None:
        assert schema_table_rows({"fields": "not-a-list"}) == ()

    def test_non_mapping_field_is_skipped(self) -> None:
        rows = schema_table_rows({"fields": ["not-a-mapping", {"name": "x", "type": "string", "nullable": True}]})
        assert [row.name for row in rows] == ["x"]
        assert rows[0].nullable == "yes"

    def test_bad_constraints_shape_yields_empty_label(self) -> None:
        rows = schema_table_rows({"fields": [{"name": "x", "type": "string", "constraints": "bad"}]})
        assert rows[0].constraint == ""


class TestFileInventoryRows:
    """File-inventory rows mirror the declared file list."""

    def test_rows_match_files(self) -> None:
        rows = file_inventory_rows(load_fixture())
        assert all(isinstance(row, FileInventoryRow) for row in rows)
        assert [row.path for row in rows] == ["fixtures/measurements.csv", "fixtures/subjects.csv"]
        assert [row.rows for row in rows] == [12, 6]
        assert {row.media_type for row in rows} == {"text/csv"}

    def test_non_list_files_returns_empty(self) -> None:
        assert file_inventory_rows({"files": "not-a-list"}) == ()

    def test_non_mapping_file_is_skipped(self) -> None:
        rows = file_inventory_rows({"files": ["bad", {"path": "a.csv", "rows": 2, "media_type": "text/csv"}]})
        assert [row.path for row in rows] == ["a.csv"]


class TestProvenanceSteps:
    """Provenance steps are ordered and indexed."""

    def test_steps_are_ordered(self) -> None:
        steps = provenance_steps(load_fixture())
        assert all(isinstance(step, ProvenanceStep) for step in steps)
        assert [step.step for step in steps] == ["collect", "clean", "validate", "package"]
        assert [step.index for step in steps] == [0, 1, 2, 3]

    def test_non_list_provenance_returns_empty(self) -> None:
        assert provenance_steps({"provenance": "not-a-list"}) == ()

    def test_non_mapping_step_is_skipped(self) -> None:
        steps = provenance_steps({"provenance": ["bad", {"step": "collect", "agent": "a"}]})
        assert [step.step for step in steps] == ["collect"]


class TestSeverityCountsAndDemo:
    """Severity counts and the demonstration perturbation."""

    def test_clean_fixture_has_no_findings(self) -> None:
        assert severity_counts(load_fixture()) == {"error": 0, "warning": 0}

    def test_demo_broken_descriptor_triggers_findings(self) -> None:
        broken = demo_broken_descriptor(load_fixture())
        counts = severity_counts(broken)
        assert counts["error"] > 0
        assert counts["warning"] > 0

    def test_demo_broken_does_not_mutate_original(self) -> None:
        descriptor = load_fixture()
        demo_broken_descriptor(descriptor)
        assert validate_descriptor(descriptor) == ()
        assert "license" in descriptor


class TestVerificationTableRows:
    """Verification display rows expose actual status without script logic."""

    def test_verified_and_absent_rows(self) -> None:
        checks = (
            FileVerification("a.csv", "verified", "sha256:a", "sha256:a", 2, 2, True, True),
            FileVerification("b.csv", "absent", "sha256:b", "", 3, -1, False, False),
        )

        assert verification_table_rows(checks) == (
            ("a.csv", "2", "2", "match", "verified"),
            ("b.csv", "3", "—", "absent", "absent"),
        )


class TestFigureAltText:
    """Registry descriptions follow descriptor inputs and fail truthful on empties."""

    @staticmethod
    def _specs_for(
        descriptor: dict[str, Any],
        checks: tuple[FileVerification, ...],
    ):
        report = build_descriptor_report(descriptor)
        return {
            spec.label: spec
            for spec in descriptor_figure_specs_for_data(
                descriptor,
                checks,
                readiness_score=report.readiness_score,
            )
        }

    def test_alternate_descriptor_changes_all_data_descriptions(self) -> None:
        shipped = load_fixture()
        shipped_specs = self._specs_for(
            shipped,
            verify_descriptor_files(shipped, PROJECT_ROOT / "data"),
        )
        alternate = json.loads(json.dumps(shipped))
        alternate["fields"] = alternate["fields"][:2]
        alternate["files"] = [
            {
                "path": "fixtures/alternate.csv",
                "media_type": "text/csv",
                "rows": 99,
                "checksum": "sha256:alternate",
            }
        ]
        alternate["provenance"] = [{"step": "inspect", "agent": "reviewer"}]
        alternate.pop("license")
        alternate_checks = (
            FileVerification(
                "fixtures/alternate.csv",
                "row_mismatch",
                "sha256:alternate",
                "sha256:observed",
                99,
                98,
                False,
                False,
            ),
        )

        alternate_specs = self._specs_for(alternate, alternate_checks)

        assert all(alternate_specs[label].alt_text != shipped_specs[label].alt_text for label in alternate_specs)
        assert "2-row data dictionary" in alternate_specs["fig:schema_overview"].alt_text
        assert "fixtures/alternate.csv: 99" in alternate_specs["fig:file_inventory"].alt_text
        assert "inspect (reviewer)" in alternate_specs["fig:provenance_flow"].alt_text
        assert "status row_mismatch" in alternate_specs["fig:checksum_verification"].alt_text
        assert "synthetic" in alternate_specs["fig:quality_gate"].alt_text

    def test_empty_descriptor_reports_absence_instead_of_fixture_numbers(self) -> None:
        specs = self._specs_for({}, ())

        assert "Empty data-dictionary table" in specs["fig:schema_overview"].alt_text
        assert "Empty file-inventory bar chart" in specs["fig:file_inventory"].alt_text
        assert "Empty provenance-flow panel" in specs["fig:provenance_flow"].alt_text
        assert "Empty descriptor-to-file verification table" in specs["fig:checksum_verification"].alt_text
