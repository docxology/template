"""Per-run integrity of the eight Source-selected Code metadata roles.

The existing genuine join admits each completed Source stage before calling
this DATA predicate. Contextual labels describe that run; they do not establish
scientific recurrence, native occurrence positions or cross-host equality.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PROJECT = "projects/templates/template_code_project"
SOURCE = PROJECT + "/src/template_code_project/core/manuscript_variables.py"
OBSERVATION = "output/data/manuscript_metadata.json"
VARIABLES = "output/data/manuscript_variables.json"
HYDRATION = "hydration:scripts/z_generate_manuscript_variables.py"
INVENTORY = {
    "figures": (
        "algorithm_complexity.png",
        "benchmark_timings.png",
        "convergence_plot.png",
        "convergence_rate_comparison.png",
        "performance_benchmark.png",
        "stability_analysis.png",
        "step_size_sensitivity.png",
    ),
    "data": ("convergence_plot.json", "dashboard_payload.json", "optimization_results.csv"),
    "reports": (
        "benchmark_report.json",
        "dashboard_invariants.txt",
        "dashboard_summary.txt",
        "output_validation.json",
        "performance_benchmark.json",
        "stability_analysis.json",
    ),
}
METADATA_KEYS = frozenset(
    {
        "ARTIFACT_FIGURES",
        "ARTIFACT_DATA_FILES",
        "ARTIFACT_REPORTS",
        "ARTIFACT_TOTAL",
        "GENERATION_TIMESTAMP",
        "PYTHON_VERSION",
        "NUMPY_VERSION",
        "PLATFORM",
    }
)


def _fields(value: object, names: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError("Code metadata observation differs from its fixed Source fields")
    return value


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Code metadata timestamp lacks its actual bounded UTC value")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Code metadata timestamp lacks its actual bounded UTC value") from error
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Code metadata timestamp is not UTC")
    return parsed


def _text(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048 or "\0" in value:
        raise ValueError("Code metadata lost its bounded actual Source string")
    return value


def validate_metadata_observation(
    observation: dict[str, Any],
    variables: dict[str, Any],
    *,
    actual_python_runtime: str,
    deadline: float,
) -> dict[str, str]:
    """Recompute the census/formatter and check actual contextual Source calls.

    actual_python_runtime comes from the independently authenticated completed
    hydration leaf. NumPy/platform labels are actual captured Source-call DATA,
    not a declaration of complete provider-library or clock custody.
    """
    remaining(deadline)
    _fields(observation, {"artifact_census", "timestamp", "runtime"})
    census = observation["artifact_census"]
    if not isinstance(census, list) or len(census) != len(INVENTORY):
        raise ValueError("Code metadata census lost its complete sixteen-name Source roster")
    counts: dict[str, int] = {}
    for category, row in zip(INVENTORY, census, strict=True):
        remaining(deadline)
        _fields(row, {"category", "parent_is_dir", "parent_is_symlink", "records"})
        if (
            row["category"] != category
            or type(row["parent_is_dir"]) is not bool
            or row["parent_is_symlink"] is not False
            or not isinstance(row["records"], list)
            or len(row["records"]) != len(INVENTORY[category])
        ):
            raise ValueError("Code metadata census differs from its confined actual category")
        count = 0
        for name, entry in zip(INVENTORY[category], row["records"], strict=True):
            remaining(deadline)
            _fields(entry, {"path", "kind", "is_file"})
            if (
                entry["path"] != f"output/{category}/{name}"
                or entry["kind"] not in {"absent", "regular", "directory"}
                or type(entry["is_file"]) is not bool
                or entry["is_file"] != (entry["kind"] == "regular")
                or (row["parent_is_dir"] is False and entry["kind"] != "absent")
            ):
                raise ValueError("Code metadata census lost its actual name/type observation")
            count += int(entry["is_file"])
        counts[category] = count
    timestamp = _fields(observation["timestamp"], {"source_date_epoch", "before_utc", "after_utc", "returned_utc"})
    raw_epoch = timestamp["source_date_epoch"]
    returned = _text(timestamp["returned_utc"])
    before, after = _utc(timestamp["before_utc"]), _utc(timestamp["after_utc"])
    if not isinstance(raw_epoch, str) or len(raw_epoch) > 64 or before > after:
        raise ValueError("Code metadata timestamp lost its Source environment/call interval")
    if raw_epoch.strip().isdigit():
        try:
            expected_time = datetime.fromtimestamp(int(raw_epoch.strip()), tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except (OverflowError, OSError, ValueError) as error:
            raise ValueError("Code metadata timestamp has an unsupported Source epoch") from error
        if returned != expected_time:
            raise ValueError("Code metadata timestamp differs from its Source epoch formatter")
    elif (
        not isinstance(returned, str)
        or len(returned) != 20
        or _utc(returned).strftime("%Y-%m-%dT%H:%M:%SZ") != returned
        or not before.replace(microsecond=0) <= _utc(returned) <= after.replace(microsecond=0)
    ):
        raise ValueError("Code metadata timestamp differs from its actual UTC call interval")
    runtime_fields = _fields(
        observation["runtime"], {"python_version", "python_runtime_version", "numpy_version", "system", "machine"}
    )
    runtime = {key: _text(value) for key, value in runtime_fields.items()}
    if (
        not isinstance(actual_python_runtime, str)
        or not runtime["python_version"]
        or not runtime["numpy_version"]
        or runtime["python_runtime_version"] != actual_python_runtime
        or not actual_python_runtime.startswith((runtime["python_version"] + " ", runtime["python_version"] + "+ "))
    ):
        raise ValueError("Code metadata runtime differs from its actual completed hydration process")
    expected = {
        "ARTIFACT_FIGURES": str(counts["figures"]),
        "ARTIFACT_DATA_FILES": str(counts["data"]),
        "ARTIFACT_REPORTS": str(counts["reports"]),
        "ARTIFACT_TOTAL": str(sum(counts.values())),
        "GENERATION_TIMESTAMP": returned,
        "PYTHON_VERSION": runtime["python_version"],
        "NUMPY_VERSION": runtime["numpy_version"],
        "PLATFORM": runtime["system"] + " " + runtime["machine"],
    }
    if any(variables.get(key) != value for key, value in expected.items()):
        raise ValueError("Code metadata token differs from its actual Source observation/formatter")
    remaining(deadline)
    return expected


def _registered_metadata_origin(
    stage: dict[str, Any],
    observation: ArtifactSnapshot,
    variables: ArtifactSnapshot,
    *,
    source_sha256: str,
    deadline: float,
) -> tuple[dict[str, Any] | None, str | None]:
    """Use actual completed write/read order, never boundary file appearance."""
    remaining(deadline)
    events = stage["registered_returned_reads"]
    writes = events["completed_writes"]["records"]
    observed = [row for row in writes if row["path"] == OBSERVATION]
    consumed = [row for row in events["records"] if row["path"] == OBSERVATION]
    variable_writes = [row for row in writes if row["path"] == VARIABLES]
    if len(observed) != 1 or len(consumed) != 1 or not variable_writes:
        return None, "missing-completed-observation-write-read-or-variables-write"
    written, read, final = observed[0], consumed[0], variable_writes[-1]
    if (
        any(
            actor["source"] != SOURCE or actor["source_sha256"] != source_sha256 or actor["function"] != function
            for actor, function in (
                (written["producer"], "generate_variables"),
                (read["consumer"], "generate_variables"),
                (final["producer"], "save_variables"),
            )
        )
        or (written["sha256"], written["bytes"]) != (observation.sha256, len(observation.content))
        or (read["sha256"], read["bytes"], read["native_identity"])
        != (written["sha256"], written["bytes"], written["native_identity"])
        or (final["sha256"], final["bytes"]) != (variables.sha256, len(variables.content))
        or written["ordinal"] >= final["ordinal"]
        or not written["prior_registered_read_count"] < read["ordinal"] <= final["prior_registered_read_count"]
    ):
        raise ValueError("Code metadata lost its actual Source completed write/read/variables temporal chain")
    return {
        "hydration_nonce": stage["analysis_nonce"],
        "hydration_process": stage["observed_process"],
        "native_stage_original": stage["native_stage_original"],
        "observation_completed_write": written,
        "observation_returned_read": read,
        "variables_completed_write": final,
    }, None


def selected_metadata_domains(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    variables: ArtifactSnapshot,
    decoded: dict[str, Any],
    selected_keys: frozenset[str],
    *,
    deadline: float,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None, list[str]]:
    """Return checked per-run roles to the existing genuine complete Code join."""
    # Source admission/closing are the enclosing join's genuine operation;
    # this helper never constructs ownership from graph or companion DATA.
    if not selected_keys or not selected_keys <= METADATA_KEYS:
        raise ValueError("Code metadata selection differs from its eight fixed Source roles")
    stages = [row for row in analysis["ordered_stages"] if row["stage_key"] == HYDRATION]
    if len(stages) != 1:
        raise ValueError("Code metadata lacks the actual completed hydration stage")
    stage = stages[0]
    observation = reader.read(PROJECT + "/" + OBSERVATION, max_bytes=1024 * 1024)
    binding = stage["leaf"]
    leaf = reader.read(binding["path"], max_bytes=64 * 1024 * 1024)
    if leaf.sha256 != binding["sha256"] or len(leaf.content) != binding["bytes"]:
        raise ValueError("Code metadata hydration leaf changed after actual role authentication")
    actual = leaf.json_object()["worker"]["completion"]["actual_runtime"]["python_version"]
    expected = validate_metadata_observation(
        observation.json_object(), decoded, actual_python_runtime=actual, deadline=deadline
    )
    origin, missing = _registered_metadata_origin(
        stage,
        observation,
        variables,
        source_sha256=hashlib.sha256(source.reference.read(SOURCE)).hexdigest(),
        deadline=deadline,
    )
    domains = {}
    for key in sorted(selected_keys):
        remaining(deadline)
        payload = expected[key]
        domains[key] = {
            "key": key,
            "json_pointer": "/" + key,
            "payload": payload,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "config_pointers": [],
            "csv_cells": [],
            "observation": {
                "path": observation.relative,
                "sha256": observation.sha256,
                "bytes": len(observation.content),
            },
            "fixed_source_transform": "Source-code-observed-metadata-role:" + key,
            "claim_boundary": "Source metadata integrity; scientific meaning and native location remain separate",
        }
    residuals = ["consumed-value-metadata-" + missing + ":" + key for key in sorted(selected_keys)] if missing else []
    return domains, origin, residuals
