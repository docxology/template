"""Selected finite Code scalar meanings from genuine Original/Current graphs.

These joins are DATA. No graph, number, test result or serialized status creates
Source ownership, scientific authority or native occurrence admission. The
existing graph APIs authenticate the real completed stages before this module
binds every supported selected scalar to its actual read/write and token paths.
"""

from __future__ import annotations

import hashlib
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_value_predicate import (
    ScalarQuadraticConfig,
    validate_explicit_scalar_config,
    validate_scalar_values,
)
from infrastructure.reporting.native_code_scalar_domains import SUPPORTED_KEYS, selected_code_domains
from infrastructure.reporting.native_code_stability_domain import STABILITY_KEYS, selected_sdk_stability_domains
from infrastructure.reporting.native_code_metadata_domains import METADATA_KEYS, selected_metadata_domains
from infrastructure.reporting.native_format_html_source_metadata import require_unambiguous_yaml
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCOPE = "templates/template_code_project"
PROJECT = f"projects/{SCOPE}"
SRC = f"{PROJECT}/src/template_code_project"
KEY = "RESULT_MIN_ITERATIONS"
CSV = "output/data/optimization_results.csv"
VARIABLES = "output/data/manuscript_variables.json"
HYDRATION = "hydration:scripts/z_generate_manuscript_variables.py"


def _binding(item: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": item.relative, "sha256": item.sha256, "bytes": len(item.content)}


def _scalar_config(content: bytes) -> ScalarQuadraticConfig:
    """Normalize explicit Source YAML, then reuse its full independent predicate."""
    require_unambiguous_yaml(content)
    settings = yaml.safe_load(content)
    if not isinstance(settings, dict) or not isinstance(settings.get("experiment"), dict):
        raise ValueError("selected Code consumption lacks its explicit authored experiment")
    data = settings["experiment"]
    matrix, linear = data.get("quadratic_A"), data.get("quadratic_b")
    if (
        not isinstance(matrix, list)
        or len(matrix) != 1
        or not isinstance(matrix[0], list)
        or len(matrix[0]) != 1
        or not isinstance(linear, list)
        or len(linear) != 1
        or any(
            not isinstance(data.get(key), list)
            for key in ("step_sizes", "stability_starting_points", "stability_step_sizes", "benchmark_dimensions")
        )
    ):
        raise ValueError("selected Code consumption requires the complete declared scalar configuration")
    config = ScalarQuadraticConfig(
        step_sizes=tuple(data["step_sizes"]),
        coefficient=matrix[0][0],
        linear=linear[0],
        initial_point=data.get("initial_point"),
        max_iterations=data.get("max_iterations"),
        tolerance=data.get("tolerance"),
        convergence_tolerance=data.get("convergence_tolerance"),
        stability_starting_points=tuple(data["stability_starting_points"]),
        stability_step_sizes=tuple(data["stability_step_sizes"]),
        benchmark_dimensions=tuple(data["benchmark_dimensions"]),
    )
    validate_explicit_scalar_config(config, data)
    return config


def _selected_occurrences(
    hydration: dict[str, Any],
    reader: SnapshotReader,
    *,
    deadline: float,
    supported_keys: frozenset[str] = frozenset({KEY}),
) -> tuple[list[dict[str, Any]], list[str]]:
    selected: list[dict[str, Any]] = []
    residuals: list[str] = []
    for row in hydration["ordered_inputs"]:
        remaining(deadline)
        consumed = reader.read(row["consumed"]["path"])
        if _binding(consumed) != row["consumed"]:
            raise ValueError("selected consumed-value manuscript differs from its authenticated hydration body")
        if row["transformation"] == "exact-authored-source-body":
            continue
        if row["transformation"] != "shared-uppercase-token-hydration":
            residuals.append("consumed-value-generated-fragment-adapter:" + consumed.relative)
            continue
        source = reader.read(row["source"]["path"])
        if _binding(source) != row["source"]:
            raise ValueError("selected consumed-value authored manuscript binding changed")
        for occurrence in row["hydration"]["occurrences"]:
            remaining(deadline)
            identity = f"{source.relative}:{occurrence['ordinal']}:{occurrence['key']}"
            if occurrence["key"] not in supported_keys:
                residuals.append("consumed-value-domain-adapter:" + identity)
                continue
            first, last = occurrence["output_start_byte"], occurrence["output_end_byte"]
            if (
                occurrence["resolved"] is not True
                or type(first) is not int
                or type(last) is not int
                or not 0 <= first <= last <= len(consumed.content)
                or source.content[occurrence["source_start_byte"] : occurrence["source_end_byte"]]
                != ("{{" + occurrence["key"] + "}}").encode()
                or hashlib.sha256(consumed.content[first:last]).hexdigest() != occurrence["replacement_sha256"]
            ):
                raise ValueError("selected Code value lost its exact authored ordinal and final payload interval")
            selected.append({"source": _binding(source), "consumed": _binding(consumed), **occurrence})
    return selected, residuals


def _registered_origin(
    analysis: dict[str, Any],
    config: ArtifactSnapshot,
    csv: ArtifactSnapshot,
    variables: ArtifactSnapshot,
    *,
    deadline: float,
    selected_keys: tuple[str, ...] = (KEY,),
) -> tuple[dict[str, Any] | None, list[str]]:
    """Use completed writes and the actual consuming read, never a changed file."""
    csv_write = None
    csv_stage = None
    hydration = None
    for stage in analysis["ordered_stages"]:
        remaining(deadline)
        if stage["stage_key"] == HYDRATION:
            hydration = stage
            break
        for written in stage["registered_returned_reads"]["completed_writes"]["records"]:
            if written["path"] == CSV:
                csv_write, csv_stage = written, stage
    if hydration is None or csv_write is None or csv_stage is None:
        return None, [
            "consumed-value-missing-completed-analysis-write-or-hydration-stage:" + key for key in selected_keys
        ]
    producer_reads = csv_stage["registered_returned_reads"]["records"]
    config_reads = [
        row
        for row in producer_reads
        if row["path"] == "manuscript/config.yaml"
        and row["consumer"]["source"] == SRC + "/core/experiment_config.py"
        and row["consumer"]["function"] == "load_experiment_config"
        and row["ordinal"] <= csv_write["prior_registered_read_count"]
    ]
    reads = hydration["registered_returned_reads"]["records"]
    csv_reads = [
        row
        for row in reads
        if row["path"] == CSV
        and row["consumer"]["source"] == SRC + "/core/manuscript_variables.py"
        and row["consumer"]["function"] == "_load_optimization_results"
    ]
    variable_writes = [
        row for row in hydration["registered_returned_reads"]["completed_writes"]["records"] if row["path"] == VARIABLES
    ]
    if not config_reads or len(csv_reads) != 1 or not variable_writes:
        return None, ["consumed-value-missing-exact-hydration-read-or-variable-write:" + key for key in selected_keys]
    read, written = csv_reads[0], variable_writes[-1]
    required_roles = {(SRC + "/core/experiment_config.py", "load_experiment_config")}
    if set(selected_keys) & {"CONFIG_VERSION", "CONFIG_FIRST_AUTHOR", "CONFIG_KEYWORDS"}:
        required_roles.add((SRC + "/core/manuscript_variables.py", "_load_config"))
    if "CONFIG_HASH" in selected_keys:
        required_roles.add((SRC + "/core/manuscript_variables.py", "_compute_config_hash"))
    hydration_config_reads = [
        row
        for row in reads
        if row["path"] == "manuscript/config.yaml"
        and (row["consumer"]["source"], row["consumer"]["function"]) in required_roles
    ]
    if {(row["consumer"]["source"], row["consumer"]["function"]) for row in hydration_config_reads} != required_roles:
        return None, ["consumed-value-missing-exact-hydration-config-read:" + key for key in selected_keys]
    if (
        csv_write["producer"]["source"] != SRC + "/analysis/experiments.py"
        or csv_write["producer"]["function"] != "save_optimization_results"
        or written["producer"]["source"] != SRC + "/core/manuscript_variables.py"
        or written["producer"]["function"] != "save_variables"
        or any((row["sha256"], row["bytes"]) != (config.sha256, len(config.content)) for row in config_reads)
        or (csv_write["sha256"], csv_write["bytes"]) != (csv.sha256, len(csv.content))
        or (read["sha256"], read["bytes"], read["native_identity"])
        != (csv_write["sha256"], csv_write["bytes"], csv_write["native_identity"])
        or (written["sha256"], written["bytes"]) != (variables.sha256, len(variables.content))
        or written["prior_registered_read_count"] < read["ordinal"]
        or any(
            (row["sha256"], row["bytes"]) != (config.sha256, len(config.content))
            or row["ordinal"] > written["prior_registered_read_count"]
            for row in hydration_config_reads
        )
    ):
        raise ValueError("selected Code cell lost its actual Source write/read/variable temporal chain")
    return {
        "producer_stage": csv_stage["stage_key"],
        "producer_nonce": csv_stage["analysis_nonce"],
        "producer_process": csv_stage["observed_process"],
        "producer_config_reads": config_reads,
        "csv_completed_write": csv_write,
        "hydration_nonce": hydration["analysis_nonce"],
        "hydration_process": hydration["observed_process"],
        "csv_read": read,
        "hydration_config_reads": hydration_config_reads,
        "variables_completed_write": written,
    }, []


def join_code_consumed_value(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Join checked existing graph returns while their genuine owner stays live.

    The fixed Root caller first authenticates Original and independently
    reconstructs both whole graphs under the existing Original/Current APIs.
    Graph arguments are checked DATA returns of that fixed caller, never
    standalone admission. This join grants no fulfilled axis or capability;
    its DATA is independently rebuilt by that same Source route.
    """
    operation = require_native_operation(reader) if reader.native_operation is not None else None
    owner = current_native_producer_operation() if operation is None else None
    if operation is not None:
        if operation.source is not source or SCOPE not in operation.originals or deadline != operation.deadline:
            raise ValueError("Code join lacks its externally held genuine Original Source and clock")
        operation.verify(reader)
    else:
        if (
            owner is None
            or owner.source is not source
            or reader.native_producer_operation is not owner
            or deadline != owner.deadline
        ):
            raise ValueError("Code join lacks its actual live Current Source owner and clock")
        owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    if (
        reader.root != source.bindings.current_root
        or any(graph["scope"] != SCOPE for graph in (analysis, hydration))
        or analysis["pipeline_run_id"] != hydration["pipeline_run_id"]
        or analysis["plan_digest"] != hydration["plan_digest"]
        or any(
            graph["source_binding"] != [source.reference.commit, source.reference.source_identity]
            for graph in (analysis, hydration)
        )
    ):
        raise ValueError("selected Code join changed the actual Source/Core/analysis/hydration selection")
    occurrences, residuals = _selected_occurrences(
        hydration, reader, deadline=deadline, supported_keys=SUPPORTED_KEYS | STABILITY_KEYS | METADATA_KEYS
    )
    value = None
    values = []
    origin = None
    if occurrences:
        config = reader.read(PROJECT + "/manuscript/config.yaml", max_bytes=1024 * 1024)
        if config.content != source.reference.read(config.relative):
            raise ValueError("selected Code domain configuration differs from held Source")
        normalized = _scalar_config(config.content)
        csv = reader.read(PROJECT + "/" + CSV, max_bytes=1024 * 1024)
        variables = reader.read(PROJECT + "/" + VARIABLES, max_bytes=4 * 1024 * 1024)
        if hydration["variables"] != _binding(variables):
            raise ValueError("selected Code variable differs from the actual complete hydration input")
        decoded = variables.json_object()
        rows, checked_values = validate_scalar_values(normalized, csv.content, decoded, deadline=deadline)
        domains = selected_code_domains(
            config.content,
            rows,
            checked_values,
            decoded,
            frozenset(item["key"] for item in occurrences),
            deadline=deadline,
        )
        stability_origin = None
        selected_stability = frozenset(item["key"] for item in occurrences) & STABILITY_KEYS
        if selected_stability:
            stability_domains, stability_origin, stability_residuals = selected_sdk_stability_domains(
                source,
                reader,
                analysis,
                normalized,
                config,
                variables,
                decoded,
                selected_stability,
                deadline=deadline,
            )
            domains.update(stability_domains)
            residuals.extend(stability_residuals)
        selected_metadata = frozenset(item["key"] for item in occurrences) & METADATA_KEYS
        if selected_metadata:
            metadata_domains, metadata_origin, metadata_residuals = selected_metadata_domains(
                source,
                reader,
                analysis,
                variables,
                decoded,
                selected_metadata,
                deadline=deadline,
            )
            domains.update(metadata_domains)
            residuals.extend(metadata_residuals)
        else:
            metadata_origin = None
        origin, missing = _registered_origin(
            analysis,
            config,
            csv,
            variables,
            deadline=deadline,
            selected_keys=tuple(sorted(domains)),
        )
        residuals.extend(missing)
        by_key: dict[str, list[dict[str, Any]]] = {key: [] for key in domains}
        for occurrence in occurrences:
            remaining(deadline)
            by_key[occurrence["key"]].append(occurrence)
        for key, domain in sorted(domains.items()):
            remaining(deadline)
            selected = by_key[key]
            for occurrence in selected:
                remaining(deadline)
                consumed = reader.read(occurrence["consumed"]["path"])
                if (
                    consumed.content[occurrence["output_start_byte"] : occurrence["output_end_byte"]]
                    != domain["payload"].encode()
                ):
                    raise ValueError("selected Code token consumed a different Source-formatted field payload")
                residuals.append(
                    f"consumed-value-native-location-link:{occurrence['source']['path']}:{occurrence['ordinal']}:{key}"
                )
            values.append(
                {
                    **domain,
                    "stability_origin": stability_origin if key in STABILITY_KEYS else None,
                    "metadata_origin": metadata_origin if key in METADATA_KEYS else None,
                    "variables": _binding(variables),
                    "csv": _binding(csv),
                    "config": _binding(config),
                    "selected_occurrences": selected,
                }
            )
            if key == KEY:
                # Preserve the existing reader API until Root couples the full
                # direct values projection below; this field grants no pass.
                value = {
                    "key": KEY,
                    "variables": _binding(variables),
                    "json_pointer": "/" + KEY,
                    "csv": _binding(csv),
                    "csv_cells": domain["csv_cells"],
                    "config": _binding(config),
                    "independent_predicate": (
                        "Source-scalar-quadratic-complete-CSV-recurrence-and-min-iterations-meaning"
                    ),
                    "fixed_source_transform": "str(min(int(row['iterations']) for row in complete_Source_CSV))",
                    "payload_sha256": domain["payload_sha256"],
                    "registered_origin": origin,
                    "selected_occurrences": selected,
                }
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    remaining(deadline)
    if not reader.unchanged():
        raise ValueError("selected Code value inputs changed during complete Source/read/write/domain join")
    body = {
        "scope": SCOPE,
        "pipeline_run_id": analysis["pipeline_run_id"],
        "source_binding": analysis["source_binding"],
        "analysis_digest": analysis["content_digest"],
        "hydration_digest": hydration["content_digest"],
        "value": value,
        "values": values,
        "registered_origin": origin,
        "residuals": residuals,
        "claim_boundary": (
            "selected Source scalar/config metadata origin/domain/hydration DATA; native location remains separate"
        ),
    }
    if operation is not None:
        operation.verify(reader)
    elif owner is not None:
        owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    return {**body, "content_digest": canonical_digest(body)}
