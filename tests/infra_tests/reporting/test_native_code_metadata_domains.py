"""Contextual metadata DATA controls; no fabricated native owner or clock."""

from __future__ import annotations

import copy
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_code_metadata_domains import (
    INVENTORY,
    OBSERVATION,
    PROJECT,
    SOURCE,
    VARIABLES,
    _registered_metadata_origin,
    validate_metadata_observation,
)
from infrastructure.reporting.native_code_scalar_domains import code_consumed_value_meaning
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ACTUAL = "3.14.0 (main, Oct 1 2026, 12:00:00) [Clang]"


def _data() -> tuple[dict, dict]:
    observation = {
        "artifact_census": [
            {
                "category": category,
                "parent_is_dir": True,
                "parent_is_symlink": False,
                "records": [
                    {"path": f"output/{category}/{name}", "kind": "regular", "is_file": True} for name in names
                ],
            }
            for category, names in INVENTORY.items()
        ],
        "timestamp": {
            "source_date_epoch": " 0 ",
            "before_utc": "2026-10-10T01:00:00.100000+00:00",
            "after_utc": "2026-10-10T01:00:00.200000+00:00",
            "returned_utc": "1970-01-01T00:00:00Z",
        },
        "runtime": {
            "python_version": "3.14.0",
            "python_runtime_version": ACTUAL,
            "numpy_version": "2.3.3",
            "system": "Linux",
            "machine": "x86_64",
        },
    }
    values = {
        "ARTIFACT_FIGURES": "7",
        "ARTIFACT_DATA_FILES": "3",
        "ARTIFACT_REPORTS": "6",
        "ARTIFACT_TOTAL": "16",
        "GENERATION_TIMESTAMP": "1970-01-01T00:00:00Z",
        "PYTHON_VERSION": "3.14.0",
        "NUMPY_VERSION": "2.3.3",
        "PLATFORM": "Linux x86_64",
    }
    return observation, values


def test_complete_sixteen_name_census_and_source_epoch() -> None:
    observation, variables = _data()
    assert (
        validate_metadata_observation(
            observation, variables, actual_python_runtime=ACTUAL, deadline=time.monotonic() + 10
        )
        == variables
    )


def test_absent_and_directory_artifacts_are_not_counted() -> None:
    observation, variables = _data()
    records = observation["artifact_census"][0]["records"]
    records[0].update(kind="absent", is_file=False)
    records[1].update(kind="directory", is_file=False)
    variables.update(ARTIFACT_FIGURES="5", ARTIFACT_TOTAL="14")
    assert (
        validate_metadata_observation(
            observation, variables, actual_python_runtime=ACTUAL, deadline=time.monotonic() + 10
        )
        == variables
    )


@pytest.mark.parametrize("mutation", ["omitted", "reordered", "type", "symlink", "count", "bool-count", "parent"])
def test_census_roster_type_or_formatter_drift_refuses(mutation: str) -> None:
    observation, variables = _data()
    row = observation["artifact_census"][0]
    if mutation == "omitted":
        row["records"].pop()
    elif mutation == "reordered":
        row["records"].reverse()
    elif mutation == "type":
        row["records"][0]["kind"] = "directory"
    elif mutation == "symlink":
        row["records"][0]["kind"] = "symlink"
    elif mutation == "count":
        variables["ARTIFACT_TOTAL"] = "17"
    elif mutation == "bool-count":
        row["records"][0]["is_file"] = 1
    else:
        row["parent_is_symlink"] = True
    with pytest.raises(ValueError, match="Code metadata"):
        validate_metadata_observation(
            observation, variables, actual_python_runtime=ACTUAL, deadline=time.monotonic() + 10
        )


def test_each_wall_clock_run_uses_its_actual_context() -> None:
    for returned, system, machine in (
        ("2026-10-10T01:00:00Z", "Linux", "x86_64"),
        ("2026-10-10T01:00:01Z", "Darwin", "arm64"),
    ):
        observation, variables = _data()
        observation["timestamp"].update(
            source_date_epoch="", before_utc=returned, after_utc=returned, returned_utc=returned
        )
        observation["runtime"].update(system=system, machine=machine)
        variables.update(GENERATION_TIMESTAMP=returned, PLATFORM=system + " " + machine)
        assert (
            validate_metadata_observation(
                observation, variables, actual_python_runtime=ACTUAL, deadline=time.monotonic() + 10
            )
            == variables
        )


@pytest.mark.parametrize(
    "mutation", ["epoch", "out-of-interval", "non-utc", "backwards", "actual-runtime", "numpy", "platform"]
)
def test_actual_timestamp_runtime_or_payload_drift_refuses(mutation: str) -> None:
    observation, variables = _data()
    if mutation == "epoch":
        observation["timestamp"]["source_date_epoch"] = "1"
    elif mutation == "out-of-interval":
        observation["timestamp"].update(source_date_epoch="", returned_utc="2026-10-10T01:00:01Z")
    elif mutation == "non-utc":
        observation["timestamp"]["before_utc"] = "2026-10-10T02:00:00+01:00"
    elif mutation == "backwards":
        observation["timestamp"]["after_utc"] = "2026-10-09T01:00:00+00:00"
    elif mutation == "actual-runtime":
        observation["runtime"]["python_runtime_version"] = "other process"
    elif mutation == "numpy":
        variables["NUMPY_VERSION"] = "different"
    else:
        variables["PLATFORM"] = "Darwin arm64"
    with pytest.raises(ValueError, match="Code metadata"):
        validate_metadata_observation(
            observation, variables, actual_python_runtime=ACTUAL, deadline=time.monotonic() + 10
        )


def _origin_data(root: Path) -> tuple:
    for name in (OBSERVATION, VARIABLES):
        path = root / PROJECT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}")
    reader = SnapshotReader(root)
    observation, variables = (reader.read(PROJECT + "/" + name) for name in (OBSERVATION, VARIABLES))
    actor = {"source": SOURCE, "source_sha256": "a" * 64, "function": "generate_variables", "line": 1}
    written = {
        "path": OBSERVATION,
        "sha256": observation.sha256,
        "bytes": 2,
        "ordinal": 1,
        "native_identity": [1, 2, 2, 3, 4],
        "producer": actor,
        "prior_registered_read_count": 4,
    }
    read = {
        "path": OBSERVATION,
        "sha256": observation.sha256,
        "bytes": 2,
        "ordinal": 5,
        "native_identity": [1, 2, 2, 3, 4],
        "consumer": dict(actor),
    }
    final = {
        "path": VARIABLES,
        "sha256": variables.sha256,
        "bytes": 2,
        "ordinal": 2,
        "producer": {**actor, "function": "save_variables"},
        "prior_registered_read_count": 5,
    }
    stage = {
        "analysis_nonce": "DATA",
        "observed_process": {},
        "native_stage_original": {},
        "registered_returned_reads": {"records": [read], "completed_writes": {"records": [written, final]}},
    }
    return stage, observation, variables


def test_completed_metadata_write_read_and_variable_temporal_chain(tmp_path: Path) -> None:
    stage, observation, variables = _origin_data(tmp_path)
    origin, missing = _registered_metadata_origin(
        stage, observation, variables, source_sha256="a" * 64, deadline=time.monotonic() + 10
    )
    assert missing is None and origin is not None
    assert origin["observation_completed_write"]["ordinal"] < origin["variables_completed_write"]["ordinal"]


@pytest.mark.parametrize(
    "mutation", ["inode", "producer", "source-body", "prior-read", "late-read", "write-order", "payload"]
)
def test_metadata_temporal_or_source_body_drift_refuses(tmp_path: Path, mutation: str) -> None:
    stage, observation, variables = _origin_data(tmp_path)
    events = stage["registered_returned_reads"]
    write, final = events["completed_writes"]["records"]
    read = events["records"][0]
    if mutation == "inode":
        read["native_identity"][1] = 99
    elif mutation == "producer":
        write["producer"]["function"] = "declared"
    elif mutation == "source-body":
        read["consumer"]["source_sha256"] = "b" * 64
    elif mutation == "prior-read":
        read["ordinal"] = 4
    elif mutation == "late-read":
        read["ordinal"] = 6
    elif mutation == "write-order":
        final["ordinal"] = 1
    else:
        write["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="temporal chain"):
        _registered_metadata_origin(
            stage, observation, variables, source_sha256="a" * 64, deadline=time.monotonic() + 10
        )


def _meaning() -> dict:
    occurrence = {
        "source": {"path": PROJECT + "/manuscript/section.md"},
        "consumed": {"path": PROJECT + "/output/manuscript/section.md"},
        "ordinal": 1,
        "source_start_byte": 0,
        "source_end_byte": 24,
        "output_start_byte": 0,
        "output_end_byte": 20,
        "replacement_sha256": "a" * 64,
    }
    rows = []
    for key in ("GENERATION_TIMESTAMP", "RESULT_MIN_ITERATIONS"):
        rows.append(
            {
                "key": key,
                "json_pointer": "/" + key,
                "config_pointers": [],
                "csv_cells": [],
                "payload_sha256": "a" * 64,
                "fixed_source_transform": "Source:" + key,
                "selected_occurrences": [copy.deepcopy(occurrence)],
            }
        )
    return {"values": rows}


def test_contextual_payload_lengths_allow_only_per_run_offsets_to_differ() -> None:
    original, current = _meaning(), _meaning()
    current["values"][0]["payload_sha256"] = "b" * 64
    for row in current["values"]:
        row["selected_occurrences"][0].update(output_start_byte=4, output_end_byte=28, replacement_sha256="c" * 64)
    assert code_consumed_value_meaning(original, deadline=time.monotonic() + 10) == code_consumed_value_meaning(
        current, deadline=time.monotonic() + 10
    )


@pytest.mark.parametrize(
    "mutation", ["scientific-payload", "source-ordinal", "source-span", "source-path", "consumed-path"]
)
def test_contextual_meaning_preserves_science_and_complete_source_identity(mutation: str) -> None:
    original, current = _meaning(), _meaning()
    row = current["values"][1]
    if mutation == "scientific-payload":
        row["payload_sha256"] = "b" * 64
    else:
        occurrence = row["selected_occurrences"][0]
        if mutation == "source-ordinal":
            occurrence["ordinal"] = 2
        elif mutation == "source-span":
            occurrence["source_end_byte"] = 25
        elif mutation == "source-path":
            occurrence["source"]["path"] += "x"
        else:
            occurrence["consumed"]["path"] += "x"
    assert code_consumed_value_meaning(original, deadline=time.monotonic() + 10) != code_consumed_value_meaning(
        current, deadline=time.monotonic() + 10
    )
