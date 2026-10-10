"""Selected Code SDK objective-stability meanings under the existing join.

These report projections are DATA. The caller already authenticates the actual
Source stage and all returned reads/writes. The SDK branch is distinct from the
project's gradient-descent fallback and from its stability heatmap.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_value_predicate import ScalarQuadraticConfig, _objective
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

STABILITY_KEYS = frozenset({"STABILITY_SCORE", "STABILITY_FUNCTION"})
PROJECT = "projects/templates/template_code_project"
SRC = PROJECT + "/src/template_code_project"
REPORT = "output/reports/stability_analysis.json"
VARIABLES = "output/data/manuscript_variables.json"
HYDRATION = "hydration:scripts/z_generate_manuscript_variables.py"
SDK_MODULE = "scientific/stability.py"


def validate_sdk_stability_report(
    config: ScalarQuadraticConfig,
    report: dict[str, Any],
    variables: dict[str, Any],
    selected_keys: frozenset[str],
    *,
    deadline: float,
) -> dict[str, str]:
    """Independently evaluate the exact first-four configured scalar inputs.

    The fixed SDK scores objective values, not optimization trajectories. Only
    the explicitly finite scalar Source contract is implemented here; overflow
    or exception behavior stays a refusal rather than a substituted default.
    """
    remaining(deadline)
    scores = []
    for point in config.stability_starting_points[:4]:
        remaining(deadline)
        value = _objective(config, point)
        if not math.isfinite(value):
            raise ValueError("selected Code SDK stability requires finite configured objective evaluations")
        magnitude = abs(value)
        scores.append(0.3 if magnitude > 1e10 or 0 < magnitude < 1e-10 else 1.0)
    score = sum(scores) / len(scores)
    expected = {
        "function_name": "quadratic_function",
        "stability_score": score,
        "expected_behavior": "Stable numerical behavior across input range",
        "actual_behavior": f"Stability score: {score:.2f}",
        "recommendations": ["Consider adding input validation and error handling"] if score < 0.8 else [],
    }
    if type(report.get("stability_score")) not in (int, float) or report != expected or set(report) != set(expected):
        raise ValueError("selected Code report differs from the independent SDK objective-stability contract")
    values = {"STABILITY_SCORE": f"{score:.2f}", "STABILITY_FUNCTION": "quadratic_function"}
    for key in sorted(selected_keys):
        remaining(deadline)
        if key not in STABILITY_KEYS or variables.get(key) != values[key]:
            raise ValueError("selected Code stability token differs from the actual report formatter")
    return {key: values[key] for key in sorted(selected_keys)}


def _registered_report_origin(
    analysis: dict[str, Any],
    config: ArtifactSnapshot,
    report: ArtifactSnapshot,
    variables: ArtifactSnapshot,
    *,
    deadline: float,
) -> tuple[dict[str, Any] | None, str | None]:
    written = None
    producer = None
    hydration = None
    for stage in analysis["ordered_stages"]:
        remaining(deadline)
        if stage["stage_key"] == HYDRATION:
            hydration = stage
            break
        for row in stage["registered_returned_reads"]["completed_writes"]["records"]:
            remaining(deadline)
            if row["path"] == REPORT:
                written, producer = row, stage
    if written is None or producer is None or hydration is None:
        return None, "missing-completed-report-write-or-hydration-stage"
    config_reads = [
        row
        for row in producer["registered_returned_reads"]["records"]
        if row["path"] == "manuscript/config.yaml"
        and row["consumer"]["source"] == SRC + "/core/experiment_config.py"
        and row["consumer"]["function"] == "load_experiment_config"
        and row["ordinal"] <= written["prior_registered_read_count"]
    ]
    reads = hydration["registered_returned_reads"]["records"]
    report_reads = [
        row
        for row in reads
        if row["path"] == REPORT
        and row["consumer"]["source"] == SRC + "/core/manuscript_variables.py"
        and row["consumer"]["function"] == "_load_json_report"
    ]
    variable_writes = [
        row for row in hydration["registered_returned_reads"]["completed_writes"]["records"] if row["path"] == VARIABLES
    ]
    if not config_reads or len(report_reads) != 1 or not variable_writes:
        return None, "missing-exact-config-report-read-or-variable-write"
    consumed, variable_write = report_reads[0], variable_writes[-1]
    if (
        written["producer"]["source"] != SRC + "/analysis/scientific_reports.py"
        or written["producer"]["function"] != "run_stability_analysis"
        or (written["sha256"], written["bytes"]) != (report.sha256, len(report.content))
        or any((row["sha256"], row["bytes"]) != (config.sha256, len(config.content)) for row in config_reads)
        or (consumed["sha256"], consumed["bytes"], consumed["native_identity"])
        != (written["sha256"], written["bytes"], written["native_identity"])
        or variable_write["producer"]["source"] != SRC + "/core/manuscript_variables.py"
        or variable_write["producer"]["function"] != "save_variables"
        or (variable_write["sha256"], variable_write["bytes"]) != (variables.sha256, len(variables.content))
        or consumed["ordinal"] > variable_write["prior_registered_read_count"]
    ):
        raise ValueError("selected stability report lost its exact Source write/read/variable temporal chain")
    return {
        "producer_stage": producer["stage_key"],
        "producer_nonce": producer["analysis_nonce"],
        "producer_process": producer["observed_process"],
        "producer_config_reads": config_reads,
        "report_completed_write": written,
        "native_stage_original": producer["native_stage_original"],
        "hydration_nonce": hydration["analysis_nonce"],
        "hydration_process": hydration["observed_process"],
        "report_read": consumed,
        "variables_completed_write": variable_write,
    }, None


def _sdk_execution(
    source: NativeSourceContext,
    reader: SnapshotReader,
    origin: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any] | None:
    """Inspect the already authenticated actual stage's closed Source roster.

    Its closure binding is supplied only by authenticate_analysis_stage_child
    in the enclosing direct graph. No decoded closure can create a stage role.
    """
    remaining(deadline)
    binding = origin["native_stage_original"]["source_closure"]
    snapshot = reader.read(binding["path"], max_bytes=64 * 1024 * 1024)
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("selected stability actual stage Source closure changed")
    closure = snapshot.json_object()
    nominated = str(Path(closure["source_roots"][0]) / SDK_MODULE)
    expected = source.reference.read("infrastructure/" + SDK_MODULE)
    for row in closure["executions"]:
        remaining(deadline)
        if row["source_path"] != nominated:
            continue
        held = reader.read(
            (snapshot.path.parent / row["source"]["path"]).relative_to(reader.root).as_posix(), max_bytes=1024 * 1024
        )
        if (
            not row["runs"]
            or held.sha256 != row["source"]["sha256"]
            or len(held.content) != row["source"]["bytes"]
            or held.content != expected
        ):
            raise ValueError("selected stability executed SDK body differs from the admitted Source")
        return {"closure": binding, "execution": row, "held_source": {"path": held.relative, "sha256": held.sha256}}
    return None


def selected_sdk_stability_domains(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    normalized: ScalarQuadraticConfig,
    config: ArtifactSnapshot,
    variables: ArtifactSnapshot,
    decoded: dict[str, Any],
    selected_keys: frozenset[str],
    *,
    deadline: float,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None, list[str]]:
    """Join real report writes/reads once; the fixed caller retains ownership."""
    report = reader.read(PROJECT + "/" + REPORT, max_bytes=1024 * 1024)
    expected = validate_sdk_stability_report(
        normalized, report.json_object(), decoded, selected_keys, deadline=deadline
    )
    origin, missing = _registered_report_origin(analysis, config, report, variables, deadline=deadline)
    if origin is not None:
        execution = _sdk_execution(source, reader, origin, deadline=deadline)
        origin["sdk_execution"] = execution
        if execution is None:
            missing = "missing-actual-selected-sdk-execution"
    residuals = ["consumed-value-stability-" + missing + ":" + key for key in sorted(selected_keys)] if missing else []
    domains = {}
    for key, payload in expected.items():
        remaining(deadline)
        domains[key] = {
            "key": key,
            "json_pointer": "/" + key,
            "payload": payload,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "config_pointers": [
                "/experiment/quadratic_A",
                "/experiment/quadratic_b",
                "/experiment/stability_starting_points",
            ],
            "csv_cells": [],
            "report": {"path": report.relative, "sha256": report.sha256, "bytes": len(report.content)},
            "report_pointer": "/stability_score" if key == "STABILITY_SCORE" else "/function_name",
            "configured_inputs": list(normalized.stability_starting_points[:4]),
            "fixed_source_transform": "Source-SDK-finite-scalar-objective-stability-first-four:" + key,
            "claim_boundary": "configured objective report meaning; not gradient-descent heatmap or native location",
        }
    remaining(deadline)
    return domains, origin, residuals
