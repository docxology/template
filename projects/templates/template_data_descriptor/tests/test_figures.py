"""Tests for figure-data preparers (no mocks; no matplotlib needed)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from data_descriptor import (
    FileInventoryRow,
    ProvenanceStep,
    SchemaRow,
    demo_broken_descriptor,
    file_inventory_rows,
    provenance_steps,
    schema_table_rows,
    severity_counts,
    validate_descriptor,
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
