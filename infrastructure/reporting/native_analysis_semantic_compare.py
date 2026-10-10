"""Compare complete authenticated analysis graphs across physical executions.

This is a DATA predicate. Callers separately authenticate Original and Current
Source, stage-child and actual ToolAPI custody. Labels, nonces and OS identities
must differ across fresh roots; whole body, event order and Source frame meaning
remain exact. No semantic selector or expected-result callback is accepted.
"""

from __future__ import annotations

from typing import Any

from infrastructure.core.analysis_data_custody import MAX_FILES
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_analysis_boundary_replay import SCHEMA
from infrastructure.reporting.native_hydration_reconstruction import SCHEMA as HYDRATION_SCHEMA
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _fields(value: object, names: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError("analysis semantic fields differ from their fixed authenticated graph")
    return value


def _body(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in ("path", "sha256", "bytes")}


def _boundary(value: object, raw: dict[str, Any]) -> dict[str, Any]:
    graph = _fields(value, {"content_digest", "records", "total_bytes"})
    rows = graph["records"]
    if not isinstance(rows, list) or len(rows) > MAX_FILES:
        raise ValueError("analysis semantic boundary exceeds its existing complete body ceiling")
    for row in rows:
        _fields(row, {"path", "sha256", "bytes", "retained_path", "native_identity", "retained"})
    return {
        **{key: raw[key] for key in ("root_policy", "file_policy", "present_roots", "output_policy", "claim_boundary")},
        "records": [_body(row) for row in rows],
        "total_bytes": graph["total_bytes"],
    }


def _runtime(value: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    runtime = _fields(
        value,
        {
            "schema",
            "executable",
            "resolved_executable",
            "binary_sha256",
            "prefix",
            "python_minor",
            "configuration_sha256",
            "site_roots",
            "installation_metadata",
            "dependency_scope",
        },
    )
    return {
        **{
            key: runtime[key]
            for key in (
                "schema",
                "binary_sha256",
                "python_minor",
                "configuration_sha256",
                "installation_metadata",
                "dependency_scope",
            )
        },
        "actual_python_version": actual["python_version"],
        "actual_implementation": actual["implementation"],
    }


def _events(value: object, *, deadline: float) -> dict[str, Any]:
    reads = _fields(
        value,
        {
            "content_digest",
            "records",
            "total_returned_bytes",
            "completed_writes",
            "coverage_boundary",
        },
    )
    if not isinstance(reads["records"], list) or len(reads["records"]) > 10000:
        raise ValueError("analysis semantic reads exceed their complete authenticated event ceiling")
    normalized_reads = []
    for row in reads["records"]:
        remaining(deadline)
        _fields(
            row,
            {
                "ordinal",
                "path",
                "sha256",
                "bytes",
                "native_identity",
                "retained_path",
                "origin",
                "consumer",
                "retained",
                "consumer_source",
            },
        )
        normalized_reads.append(
            {
                **_body(row),
                "ordinal": row["ordinal"],
                "origin": row["origin"],
                "consumer": row["consumer"],
                "consumer_source": row["consumer_source"],
            }
        )
    writes = _fields(
        reads["completed_writes"],
        {
            "content_digest",
            "records",
            "total_written_bytes",
            "coverage_boundary",
        },
    )
    if not isinstance(writes["records"], list) or len(writes["records"]) > 10000:
        raise ValueError("analysis semantic writes exceed their complete authenticated event ceiling")
    normalized_writes = []
    for row in writes["records"]:
        remaining(deadline)
        _fields(
            row,
            {
                "ordinal",
                "path",
                "sha256",
                "bytes",
                "native_identity",
                "retained_path",
                "prior_observed",
                "prior_observation_authority",
                "producer",
                "prior_registered_read_count",
                "prior_registered_read_prefix_digest",
                "retained",
                "producer_source",
            },
        )
        count = row["prior_registered_read_count"]
        if type(count) is not int or not 0 <= count <= len(normalized_reads):
            raise ValueError("analysis semantic write lost its full preceding registered read prefix")
        prior = row["prior_observed"]
        if prior is not None:
            _fields(prior, {"sha256", "bytes", "native_identity", "retained_path"})
        normalized_writes.append(
            {
                **_body(row),
                "ordinal": row["ordinal"],
                "prior_observed": None if prior is None else {key: prior[key] for key in ("sha256", "bytes")},
                "prior_observation_authority": row["prior_observation_authority"],
                "producer": row["producer"],
                "producer_source": row["producer_source"],
                # Full read roster/order plus this exact prefix length uniquely
                # bind the temporal edge without rehashing every prefix twice.
                "prior_registered_read_count": count,
            }
        )
    return {
        "records": normalized_reads,
        "total_returned_bytes": reads["total_returned_bytes"],
        "coverage_boundary": reads["coverage_boundary"],
        "completed_writes": {
            "records": normalized_writes,
            "total_written_bytes": writes["total_written_bytes"],
            "coverage_boundary": writes["coverage_boundary"],
        },
    }


def native_analysis_semantics(
    graph: dict[str, Any],
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Project every fixed graph semantic field after genuine reconstruction.

    Each process/inode/nonce was already checked within its own actual role.
    No scientific interpretation is inferred from equality. Unknown graph fields
    fail rather than silently disappear from the paired comparison contract.
    """
    _fields(
        graph,
        {
            "schema_version",
            "scope",
            "pipeline_run_id",
            "plan_digest",
            "source_binding",
            "aggregate",
            "ordered_stages",
            "produced_current_bodies",
            "source_registry_reconstruction",
            "unresolved_edges",
            "content_digest",
        },
    )
    if graph["schema_version"] != SCHEMA or graph["content_digest"] != canonical_digest(
        {key: value for key, value in graph.items() if key != "content_digest"}
    ):
        raise ValueError("analysis semantic graph differs from its authenticated paired schema/digest")
    stages = []
    if not isinstance(graph["ordered_stages"], list) or len(graph["ordered_stages"]) > 10000:
        raise ValueError("analysis semantic stages exceed the complete Source roster ceiling")
    for stage in graph["ordered_stages"]:
        remaining(deadline)
        _fields(
            stage,
            {
                "stage_key",
                "leaf",
                "request_digest",
                "analysis_nonce",
                "observed_process",
                "native_stage_original",
                "incoming",
                "outgoing",
                "registered_returned_reads",
                "script",
            },
        )
        binding = stage["leaf"]
        leaf = reader.read(binding["path"], max_bytes=64 * 1024 * 1024)
        if leaf.sha256 != binding["sha256"] or len(leaf.content) != binding["bytes"]:
            raise ValueError("analysis semantic leaf changed after actual role authentication")
        worker = leaf.json_object()["worker"]
        request, completion = worker["request"], worker["completion"]
        native = stage["native_stage_original"]
        if native["actual_signed_os_exit"] != 0 or native["script_completion_intent"] != 0:
            raise ValueError("analysis semantic comparison cannot admit incomplete original/current execution")
        stages.append(
            {
                "stage_key": stage["stage_key"],
                "script": stage["script"],
                "actual_signed_os_exit": native["actual_signed_os_exit"],
                "script_completion_intent": native["script_completion_intent"],
                "runtime": _runtime(request["runtime_binding"], completion["actual_runtime"]),
                "incoming": _boundary(stage["incoming"], request["data_before"]),
                "outgoing": _boundary(stage["outgoing"], completion["data_after"]),
                "registered_returned_reads": _events(stage["registered_returned_reads"], deadline=deadline),
            }
        )
    body = {
        "schema_version": "template-native-analysis-semantic-comparison-v1",
        "scope": graph["scope"],
        "source_binding": graph["source_binding"],
        "ordered_stages": stages,
        "produced_current_bodies": [
            {"producer_stage": row["producer_stage"], "body": row["body"]} for row in graph["produced_current_bodies"]
        ],
        "source_registry_reconstruction": graph["source_registry_reconstruction"],
        "unresolved_edges": graph["unresolved_edges"],
        "claim_boundary": "complete-authenticated-boundary-and-registered-event-equivalence; not-all-domain-truth",
    }
    if not reader.unchanged():
        raise ValueError("Original/Current retained graph bodies changed during semantic comparison")
    remaining(deadline)
    return {**body, "content_digest": canonical_digest(body)}


def require_native_analysis_equivalence(
    original: dict[str, Any],
    current: dict[str, Any],
) -> None:
    """Require exact complete normalized DATA; no caller-selected exclusions."""
    if original != current:
        raise ValueError("fresh Current analysis/hydration differs from complete authenticated Original semantics")


def native_hydration_semantics(graph: dict[str, Any]) -> dict[str, Any]:
    """Preserve complete Source hydration/composition DATA across run labels.

    Its caller obtains each full graph through the genuine role, independently
    rereading every variable, Source input, consumed occurrence and combined
    body. Physical run/plan labels are separately authenticated. All remaining
    fields, including every explicit unresolved edge, compare exactly.
    """
    _fields(
        graph,
        {
            "schema_version",
            "scope",
            "pipeline_run_id",
            "plan_digest",
            "source_binding",
            "variables",
            "config",
            "ordered_inputs",
            "composition",
            "algorithm",
            "combined",
            "dotted_variables",
            "independent_combined_sha256",
            "pdf_recomposition",
            "unresolved_edges",
            "content_digest",
        },
    )
    if graph["schema_version"] != HYDRATION_SCHEMA or graph["content_digest"] != canonical_digest(
        {key: value for key, value in graph.items() if key != "content_digest"}
    ):
        raise ValueError("hydration semantic graph differs from its exact authenticated paired schema/digest")
    body = {
        key: value for key, value in graph.items() if key not in {"pipeline_run_id", "plan_digest", "content_digest"}
    }
    return {**body, "content_digest": canonical_digest(body)}
