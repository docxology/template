"""Independently validate exact Root v2 lane processes, source policy and case reports."""

from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any


from infrastructure.project.public_acceptance_case_policy import digest
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_contract import _artifact, _json
from infrastructure.project.public_root_case_readback import _within_deadline
from infrastructure.project.public_root_lane_coverage import measurement, merge, report
from infrastructure.project.public_root_lane_diagnostics import read_output, read_reports
from infrastructure.project.public_root_lane_contract import (
    CHUNK_SCHEMA,
    COORDINATOR_SCHEMA,
    COORDINATOR_PROCESS_SCHEMA,
    LANE_SCHEMA,
    PROCESS_SCHEMA,
    admission,
    groups,
    lane_command,
    selection,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _zero(process: dict[str, Any], command: tuple[str, ...]) -> None:
    if (
        type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or type(process.get("original_returncode")) is not int
        or process["original_returncode"] != 0
        or process.get("timed_out") is not False
        or process.get("custody_refused") is not False
        or process.get("command_error") != ""
        or process.get("command") != list(command)
    ):
        raise ValueError("original Root lane process did not complete its exact admitted invocation")


def _read_lane_result(reader: SnapshotReader, bundle: object, *, origin: Any = None) -> dict[str, Any]:
    if not isinstance(bundle, dict) or set(bundle) != {"spec_artifact", "result_artifact", "process_artifact"}:
        raise ValueError("Root lane readback needs its exact original process/spec/result bundle")
    snapshot = _artifact(reader, bundle["spec_artifact"])
    spec, admitted = admission(reader, snapshot, origin=origin)
    process_snapshot = _artifact(reader, bundle["process_artifact"])
    result_snapshot = _artifact(reader, bundle["result_artifact"])
    process, result = _json(process_snapshot), _json(result_snapshot)
    directory = reader.root / spec["directory"]
    _zero(process, lane_command(reader.root, snapshot, origin=origin))
    selected = selection(admitted, spec["lane"])
    if admitted.plan.platform not in selected.platforms or admitted.plan.runtime not in selected.runtimes:
        raise ValueError("Root lane original census runtime/platform is outside its source-owned applicability")
    if (
        set(process)
        != {
            "schema_version",
            "run_id",
            "nonce",
            "spec_artifact",
            "result_artifact",
            "command",
            "returncode",
            "original_returncode",
            "timed_out",
            "custody_refused",
            "command_error",
            "admission_duration_seconds",
            "launch_budget_seconds",
            "duration_seconds",
        }
        or process["schema_version"] != COORDINATOR_PROCESS_SCHEMA
        or process["run_id"] != spec["run_id"]
        or process["nonce"] != spec["nonce"]
        or not _within_deadline(process["admission_duration_seconds"], spec["timeout_seconds"])
        or type(process["launch_budget_seconds"]) is not int
        or process["launch_budget_seconds"] < 1
        or process["launch_budget_seconds"]
        != math.floor(spec["timeout_seconds"] - process["admission_duration_seconds"])
        or process_snapshot.path != directory / "lane-process.json"
        or result_snapshot.path != directory / "lane.json"
        or process.get("spec_artifact") != bundle["spec_artifact"]
        or process.get("result_artifact") != bundle["result_artifact"]
        or not _within_deadline(process.get("duration_seconds"), spec["timeout_seconds"])
        or set(result)
        != {
            "schema_version",
            "role",
            "run_id",
            "nonce",
            "spec_artifact",
            "lane",
            "mode",
            "policy_sha256",
            "prerequisites_artifact",
            "census_sha256",
            "source_identity",
            "deliverables_identity",
            "selected_nodes",
            "records",
            "coverage_artifact",
            "blockers",
            "exit_code",
            "duration_seconds",
            "plan_sha256",
        }
        or result["schema_version"] != LANE_SCHEMA
        or result["role"] != "actual-root-lane"
        or result["run_id"] != spec["run_id"]
        or result["nonce"] != spec["nonce"]
        or result["spec_artifact"] != bundle["spec_artifact"]
        or result["lane"] != selected.id
        or result["mode"] != spec["mode"]
        or result["policy_sha256"] != admitted.policy.sha256
        or result["prerequisites_artifact"] != admitted.prerequisites_artifact
        or result["census_sha256"] != admitted.plan.census_sha256
        or result["plan_sha256"] != digest(asdict(admitted.plan))
        or result["source_identity"] != admitted.plan.source_identity
        or result["deliverables_identity"] != RuntimeScope(reader.root, "root").deliverables_identity()
        or result["selected_nodes"] != list(selected.nodeids)
        or result["blockers"] != []
        or type(result["exit_code"]) is not int
        or result["exit_code"] != 0
        or not _within_deadline(result["duration_seconds"], spec["timeout_seconds"])
        or not isinstance(result["records"], list)
        or len(result["records"]) != len(groups(selected.nodeids))
    ):
        raise ValueError("Root lane completion does not match its current complete policy and original native process")
    original_bundle = _json(_artifact(reader, spec["census_bundle_artifact"]))
    census = _json(_artifact(reader, original_bundle["receipt_artifact"]))
    original_spec = _json(_artifact(reader, original_bundle["spec_artifact"]))
    runtime = original_spec["runtime"]
    measured = measurement(reader.root)
    if (
        process["duration_seconds"] < process["admission_duration_seconds"]
        or result["duration_seconds"] > process["duration_seconds"] - process["admission_duration_seconds"]
    ):
        raise ValueError("Root lane original worker duration exceeds its coordinator boundary")
    seen: set[str] = set()
    chunk_duration = 0.0
    previous_remaining = spec["timeout_seconds"]
    for index, (record, nodes) in enumerate(zip(result["records"], groups(selected.nodeids), strict=True)):
        if (
            not isinstance(record, dict)
            or set(record) != {"index", "nodes", "receipt_artifact", "process_artifact"}
            or type(record["index"]) is not int
            or record["index"] != index
            or record["nodes"] != list(nodes)
        ):
            raise ValueError("Root lane omitted or repeated an exact admitted chunk")
        chunk_directory = directory / f"chunk-{index:04d}"
        child_snapshot, native_snapshot = (
            _artifact(reader, record["receipt_artifact"]),
            _artifact(reader, record["process_artifact"]),
        )
        child, native = _json(child_snapshot), _json(native_snapshot)
        if child_snapshot.relative in seen or native_snapshot.relative in seen:
            raise ValueError("Root lane repeats a retained native child artifact")
        seen.update((child_snapshot.relative, native_snapshot.relative))
        _zero(native, lane_command(reader.root, snapshot, chunk=index, origin=origin))
        expected_metadata = {case["nodeid"]: case for case in census["cases"] if case["nodeid"] in nodes}
        if (
            native_snapshot.path != chunk_directory / "process.json"
            or child_snapshot.path != chunk_directory / "receipt.json"
            or set(native)
            != {
                "schema_version",
                "command",
                "run_id",
                "nonce",
                "spec_artifact",
                "index",
                "receipt_artifact",
                "returncode",
                "original_returncode",
                "timed_out",
                "custody_refused",
                "command_error",
                "remaining_budget_seconds",
                "duration_seconds",
                "output_artifact",
            }
            or native["schema_version"] != PROCESS_SCHEMA
            or native["run_id"] != spec["run_id"]
            or native["nonce"] != spec["nonce"]
            or native["spec_artifact"] != bundle["spec_artifact"]
            or native["receipt_artifact"] != record["receipt_artifact"]
            or type(native["index"]) is not int
            or native["index"] != index
            or type(native["remaining_budget_seconds"]) is not int
            or not 1 <= native["remaining_budget_seconds"] <= previous_remaining
            or not _within_deadline(native["duration_seconds"], native["remaining_budget_seconds"])
            or set(child)
            != {
                "schema_version",
                "role",
                "run_id",
                "nonce",
                "spec_artifact",
                "index",
                "lane",
                "policy_sha256",
                "census_sha256",
                "source_identity",
                "deliverables_identity",
                "runtime",
                "original_pytest_exit_code",
                "exit_code",
                "interrupted",
                "timed_out",
                "coverage_data_artifact",
                "bytecode_verified",
                "nodeids",
                "cases",
                "reports",
                "collection_errors",
                "collection_skips",
                "deselected",
                "diagnostic",
                "diagnostics_artifact",
            }
            or child["schema_version"] != CHUNK_SCHEMA
            or child["role"] != "actual-root-lane-chunk"
            or child["run_id"] != spec["run_id"]
            or child["nonce"] != spec["nonce"]
            or child["spec_artifact"] != bundle["spec_artifact"]
            or type(child["index"]) is not int
            or child["index"] != index
            or child["lane"] != selected.id
            or child["policy_sha256"] != admitted.policy.sha256
            or child["census_sha256"] != admitted.plan.census_sha256
            or child["source_identity"] != admitted.plan.source_identity
            or child["deliverables_identity"] != result["deliverables_identity"]
            or child["runtime"] != runtime
            or type(child["original_pytest_exit_code"]) is not int
            or child["original_pytest_exit_code"] != 0
            or type(child["exit_code"]) is not int
            or child["exit_code"] != 0
            or child["interrupted"] is not False
            or child["timed_out"] is not False
            or child["bytecode_verified"] is not True
            or not isinstance(child["nodeids"], list)
            or len(child["nodeids"]) != len(nodes)
            or set(child["nodeids"]) != set(nodes)
            or not isinstance(child["cases"], list)
            or len(child["cases"]) != len(nodes)
            or any(not isinstance(case, dict) or not isinstance(case.get("nodeid"), str) for case in child["cases"])
            or {case["nodeid"]: case for case in child["cases"]} != expected_metadata
            or child["reports"]
            != {node: [["setup", "passed"], ["call", "passed"], ["teardown", "passed"]] for node in nodes}
            or any(child[key] != [] for key in ("collection_errors", "collection_skips", "deselected"))
            or child["diagnostic"] != ""
        ):
            raise ValueError("Root lane child source, metadata or original setup/call/teardown outcomes are incomplete")
        read_output(reader, chunk_directory, native["output_artifact"])
        diagnostics = read_reports(reader, chunk_directory, child["diagnostics_artifact"])
        if diagnostics["reports"] or diagnostics["exception"] is not None or diagnostics["dropped_reports"]:
            raise ValueError("Root successful chunk retained unsuccessful original pytest diagnostics")
        coverage_data = _artifact(reader, child["coverage_data_artifact"])
        if coverage_data.path != chunk_directory / "coverage-data.json":
            raise ValueError("Root lane coverage input is outside its original chunk")
        merge(measured, _json(coverage_data), original_spec["implementation"])
        chunk_duration += native["duration_seconds"]
        previous_remaining = native["remaining_budget_seconds"]
    if chunk_duration > result["duration_seconds"]:
        raise ValueError("Root lane chunk duration exceeds original worker boundary")
    coverage = _artifact(reader, result["coverage_artifact"])
    expected_coverage = report(measured)
    actual_coverage = _json(coverage)
    if (
        any(actual_coverage.get(key) != expected_coverage.get(key) for key in ("files", "totals"))
        or coverage.path != directory / "coverage.json"
        or not reader.unchanged()
    ):
        raise ValueError("Root lane coverage or source changed after actual execution")
    return result


def read_lane(reader: SnapshotReader, bundle: object, *, origin: Any = None) -> dict[str, Any]:
    """Read original outer, coordinator and case processes against current source."""
    from infrastructure.project.public_root_lane_producer import coordinator_command

    if (
        not isinstance(bundle, dict)
        or set(bundle)
        != {"role", "exit_code", "spec_artifact", "result_artifact", "process_artifact", "coordinator_artifact"}
        or bundle["role"] != "actual-root-lane"
        or type(bundle["exit_code"]) is not int
        or bundle["exit_code"] != 0
    ):
        raise ValueError("Root lane requires its exact successful original outer bundle")
    snapshot = _artifact(reader, bundle["spec_artifact"])
    spec, _ = admission(reader, snapshot, origin=origin)
    directory = reader.root / spec["directory"]
    outer_snapshot = _artifact(reader, bundle["coordinator_artifact"])
    outer = _json(outer_snapshot)
    original = _artifact(reader, outer.get("bundle_artifact"))
    _zero(outer, coordinator_command(reader.root, snapshot, origin=origin))
    if (
        set(outer)
        != {
            "schema_version",
            "run_id",
            "nonce",
            "command",
            "bundle_artifact",
            "returncode",
            "original_returncode",
            "timed_out",
            "custody_refused",
            "command_error",
            "admission_duration_seconds",
            "launch_budget_seconds",
            "duration_seconds",
        }
        or outer["schema_version"] != COORDINATOR_SCHEMA
        or outer["run_id"] != spec["run_id"]
        or outer["nonce"] != spec["nonce"]
        or outer_snapshot.path != directory / "lane-coordinator-process.json"
        or original.path != directory / "lane-coordinator-bundle.json"
        or _json(original) != {key: value for key, value in bundle.items() if key != "coordinator_artifact"}
        or not _within_deadline(outer["admission_duration_seconds"], spec["timeout_seconds"])
        or not _within_deadline(outer["duration_seconds"], spec["timeout_seconds"])
        or outer["duration_seconds"] < outer["admission_duration_seconds"]
        or type(outer["launch_budget_seconds"]) is not int
        or outer["launch_budget_seconds"] < 1
        or outer["launch_budget_seconds"] != math.floor(spec["timeout_seconds"] - outer["admission_duration_seconds"])
    ):
        raise ValueError("Root lane outer admission, exact result or finite timeline changed")
    process = _json(_artifact(reader, bundle["process_artifact"]))
    if (
        not _within_deadline(process.get("duration_seconds"), spec["timeout_seconds"])
        or process["duration_seconds"] > outer["duration_seconds"] - outer["admission_duration_seconds"]
    ):
        raise ValueError("Root lane coordinator exceeded original outer boundary")
    return _read_lane_result(
        reader, {key: bundle[key] for key in ("spec_artifact", "result_artifact", "process_artifact")}, origin=origin
    )
