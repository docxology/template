from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from data_descriptor import (
    build_descriptor_report,
    build_release_bundle_manifest,
    descriptor_fingerprint,
    summarize_field_constraints,
    validate_descriptor,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_fixture() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_descriptor.json").read_text(encoding="utf-8")),
    )


def test_valid_descriptor_builds_readiness_report() -> None:
    descriptor = load_fixture()

    report = build_descriptor_report(descriptor)

    assert report.valid is True
    assert report.readiness_score == 1.0
    assert report.field_count == 3
    assert report.file_count == 1
    assert report.schema_fingerprint == descriptor_fingerprint(descriptor)
    assert report.findings == ()


def test_schema_fingerprint_is_order_independent() -> None:
    descriptor = load_fixture()
    reordered = {**descriptor, "fields": list(reversed(descriptor["fields"]))}

    assert descriptor_fingerprint(descriptor) == descriptor_fingerprint(reordered)


def test_invalid_descriptor_reports_specific_errors_and_warnings() -> None:
    descriptor = load_fixture()
    descriptor.pop("license")
    descriptor["files"][0]["checksum"] = "sha256:not-valid"
    descriptor["files"][0]["rows"] = 0
    descriptor["fields"].append({"name": "value", "type": "opaque", "nullable": True})
    descriptor["primary_key"] = ["missing_id"]
    descriptor["provenance"] = [{"step": "collect", "agent": "fixture"}]

    findings = validate_descriptor(descriptor)
    codes = {finding.code for finding in findings}
    report = build_descriptor_report(descriptor)

    assert {"missing_top_level", "missing_license", "bad_checksum", "duplicate_field"} <= codes
    assert {"unknown_field_type", "nonpositive_rows", "thin_provenance"} <= codes
    assert "unknown_primary_key" in codes
    assert report.valid is False
    assert report.readiness_score < 1.0


def test_field_constraints_are_summarized_and_exported_to_release_manifest() -> None:
    descriptor = load_fixture()

    summaries = summarize_field_constraints(descriptor)
    manifest = build_release_bundle_manifest(descriptor)

    assert [summary.name for summary in summaries] == ["sample_id", "group", "value"]
    assert summaries[1].allowed_values_count == 2
    assert summaries[2].unit == "normalized_score"
    assert summaries[2].has_bounds is True
    assert manifest["valid"] is True
    assert manifest["release_boundary"] == "metadata-and-checksums-only"
    assert manifest["field_constraints"][2]["unit"] == "normalized_score"
    assert manifest["files"][0]["path"] == "measurements.csv"


def test_descriptor_reports_constraint_and_path_gaps() -> None:
    descriptor = load_fixture()
    descriptor["files"][0]["path"] = "../private/measurements.csv"
    descriptor["files"][0]["media_type"] = "application/octet-stream"
    descriptor["fields"][1]["constraints"] = {"allowed_values": []}
    descriptor["fields"][2].pop("unit")
    descriptor["fields"][2]["constraints"] = {"minimum": 10, "maximum": 1}

    codes = {finding.code for finding in validate_descriptor(descriptor)}

    assert "unsafe_file_path" in codes
    assert "unknown_media_type" in codes
    assert "bad_allowed_values" in codes
    assert "missing_unit" in codes
    assert "invalid_numeric_range" in codes


def test_descriptor_reports_missing_sections_and_file_key_gaps() -> None:
    empty = {"name": "broken", "version": "0.1.0", "license": "", "files": [], "fields": [], "provenance": []}
    descriptor = load_fixture()
    descriptor["files"] = [
        {
            "path": "",
            "media_type": "text/csv",
            "checksum": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "rows": 1,
        },
        {
            "path": "",
            "media_type": "text/csv",
            "checksum": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "rows": 1,
        },
        {
            "media_type": "text/csv",
            "checksum": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "rows": 1,
        },
    ]

    empty_codes = {finding.code for finding in validate_descriptor(empty)}
    file_codes = {finding.code for finding in validate_descriptor(descriptor)}

    assert {"missing_license", "missing_files", "missing_fields"} <= empty_codes
    assert "missing_file_key" in file_codes
    assert "missing_file_path" in file_codes
    assert "duplicate_file_path" in file_codes


def test_descriptor_reports_malformed_constraint_shapes_and_types() -> None:
    descriptor = load_fixture()
    descriptor["fields"] = [
        "not-a-mapping",
        {"name": "category", "type": "category", "nullable": False, "constraints": "not-a-mapping"},
        {
            "name": "numeric",
            "type": "number",
            "nullable": False,
            "constraints": {"minimum": "low", "maximum": "high"},
        },
        {
            "name": "event_date",
            "type": "date",
            "nullable": False,
            "constraints": {"minimum": 1, "pattern": "^2026-"},
        },
    ]

    summaries = summarize_field_constraints({"fields": "not-a-list"})
    mixed_summaries = summarize_field_constraints(descriptor)
    codes = {finding.code for finding in validate_descriptor(descriptor)}

    assert summaries == ()
    assert [summary.name for summary in mixed_summaries] == ["category", "numeric", "event_date"]
    assert {"invalid_field_entry", "bad_constraints", "missing_unit"} <= codes
    assert "bad_numeric_bound" in codes
    assert "bounds_on_non_numeric_field" in codes
    assert "pattern_on_non_text_field" in codes


def test_descriptor_rejects_non_mapping_file_and_field_entries() -> None:
    descriptor = {
        "name": "broken",
        "version": "0.1.0",
        "license": "CC0-1.0",
        "files": ["not-a-mapping"],
        "fields": ["not-a-mapping"],
        "provenance": [],
    }

    codes = {finding.code for finding in validate_descriptor(descriptor)}

    assert "invalid_file_entry" in codes
    assert "invalid_field_entry" in codes
    assert "missing_primary_key" in codes
