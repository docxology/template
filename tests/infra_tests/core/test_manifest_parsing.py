"""Manifest parsing, roundtrip, and aggregate-mode inheritance regressions."""

from __future__ import annotations

from pathlib import Path

import json

import pytest

from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    STABLE_OUTPUT_INVENTORY_MODE,
    aggregate_artifact_manifests,
    artifact_manifest_from_payload,
    compute_sha256,
    snapshot_current_artifact_manifest,
)
from infrastructure.validation.output.artifacts import current_project_manifest_if_valid, read_artifact_manifest


def test_legacy_manifest_reader_defaults_to_strict_shippable_mode(tmp_path: Path) -> None:
    manifest_path = tmp_path / "artifact_manifest.json"
    manifest_path.write_text('{"entries": [], "issues": []}\n', encoding="utf-8")

    manifest = read_artifact_manifest(manifest_path)

    assert manifest.inventory_mode == STABLE_OUTPUT_INVENTORY_MODE
    assert manifest.to_dict()["inventory_mode"] == STABLE_OUTPUT_INVENTORY_MODE


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("contract_match", "false"),
        ("size_bytes", 1.5),
        ("stage_num", "1"),
        ("sha256", "A" * 64),
        ("path", "output\\data\\result.json"),
        ("path", "output/data/../secret.json"),
        ("path", "output//data.json"),
        ("path", "output/C:/secret.json"),
        ("path", "output/data/nul\0.json"),
        ("timestamp", 0),
    ],
)
def test_manifest_parser_rejects_coerced_or_noncanonical_entry_fields(
    field: str,
    invalid: object,
) -> None:
    entry: dict[str, object] = {
        "path": "output/data/result.json",
        "size_bytes": 3,
        "sha256": "0" * 64,
        "stage_num": 1,
        "stage_name": "Analysis",
        "contract_match": False,
        "timestamp": "",
    }
    entry[field] = invalid

    with pytest.raises(ValueError):
        artifact_manifest_from_payload({"entries": [entry], "issues": []})


def test_manifest_parser_rejects_non_string_issues() -> None:
    with pytest.raises(ValueError, match="list of strings"):
        artifact_manifest_from_payload({"entries": [], "issues": [7]})


def test_manifest_parser_preserves_nul_safe_newline_path() -> None:
    payload = {
        "entries": [
            {
                "path": "output/data/line\nbreak.json",
                "size_bytes": 3,
                "sha256": "0" * 64,
                "stage_num": 1,
                "stage_name": "Analysis",
                "contract_match": True,
                "timestamp": "",
            }
        ],
        "issues": [],
    }

    parsed = artifact_manifest_from_payload(payload)

    assert parsed.entries[0].path == "output/data/line\nbreak.json"


def test_local_manifest_roundtrip_preserves_inventory_mode(tmp_path: Path) -> None:
    output = tmp_path / "private-project" / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"result": 1}\n', encoding="utf-8")

    written = snapshot_current_artifact_manifest(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    loaded = read_artifact_manifest(output / "reports" / "artifact_manifest.json")

    assert written.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert loaded == written
    assert (
        current_project_manifest_if_valid(
            output,
            output.parent,
            expected_inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
        )
        == written
    )
    assert current_project_manifest_if_valid(output, output.parent) is None


def test_local_aggregate_inherits_unspecified_legacy_stage_mode_but_rejects_explicit_conflict(
    tmp_path: Path,
) -> None:
    project = tmp_path / "private-project"
    output = project / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"result": 1}\n', encoding="utf-8")
    stage_path = output / ".pipeline" / "artifacts" / "stage-01-analysis.json"
    stage_path.parent.mkdir(parents=True)
    payload = {
        "entries": [
            {
                "path": "output/data/result.json",
                "size_bytes": result.stat().st_size,
                "sha256": compute_sha256(result),
                "stage_num": 1,
                "stage_name": "Analysis",
                "contract_match": True,
                "timestamp": "",
            }
        ],
        "issues": [],
    }
    stage_path.write_text(json.dumps(payload), encoding="utf-8")

    inherited = aggregate_artifact_manifests(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert inherited.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert inherited.issues == ()

    payload["inventory_mode"] = STABLE_OUTPUT_INVENTORY_MODE
    stage_path.write_text(json.dumps(payload), encoding="utf-8")
    contradictory = aggregate_artifact_manifests(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert contradictory.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert contradictory.issues == (
        "stage artifact manifest inventory mode mismatch: "
        "stage-01-analysis.json: expected stable-local-output-v1, found stable-shippable-output-v1",
    )
