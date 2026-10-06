"""Independent canonical Root collection evidence reader, separate from producer claims."""

from __future__ import annotations

import math
import sys
from typing import Any

from infrastructure.project.public_acceptance_case_observer import RootCaseObserver
from infrastructure.project.public_acceptance_case_policy import RootCasePolicy, compile_case_plan
from infrastructure.project.public_root_case_contract import (
    COORDINATOR_SCHEMA,
    PROCESS_SCHEMA,
    RECEIPT_SCHEMA,
    _artifact,
    _json,
    _origin,
    _pytest_arguments,
    _spec,
    census_command,
    coordinator_command,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _within_deadline(value: object, timeout: int) -> bool:
    return (
        isinstance(value, (int, float))
        and type(value) in (int, float)
        and math.isfinite(value)
        and 0 <= value < timeout
    )


def _observe_collection(
    reader: SnapshotReader, spec_binding: object, process_binding: object, receipt_binding: object
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One current observation binds specification, native process and metadata."""
    spec_snapshot = _artifact(reader, spec_binding)
    spec = _spec(reader, spec_snapshot, reader_context=True)
    process_snapshot, receipt_snapshot = _artifact(reader, process_binding), _artifact(reader, receipt_binding)
    process, receipt = _json(process_snapshot), _json(receipt_snapshot)
    root, directory = reader.root, reader.root / spec["directory"]
    original_binding = {"path": spec_snapshot.relative, "sha256": spec_snapshot.sha256}
    duration = process.get("duration_seconds")
    if (
        set(process)
        != {
            "schema_version",
            "run_id",
            "nonce",
            "spec_artifact",
            "receipt_artifact",
            "command",
            "returncode",
            "original_returncode",
            "timed_out",
            "custody_refused",
            "command_error",
            "duration_seconds",
        }
        or set(receipt)
        != {
            "schema_version",
            "role",
            "run_id",
            "nonce",
            "spec_artifact",
            "original_pytest_exit_code",
            "exit_code",
            "arguments",
            "source_identity",
            "runtime",
            "runtime_locations",
            "census",
            "cases",
            "nodeids",
            "collection_errors",
            "collection_skips",
            "deselected",
            "executed_reports",
            "interrupted",
            "bytecode_verified",
            "diagnostic",
        }
        or process_snapshot.path != directory / "census-process.json"
        or receipt_snapshot.path != directory / "census.json"
        or process.get("schema_version") != PROCESS_SCHEMA
        or process.get("run_id") != spec["run_id"]
        or process.get("nonce") != spec["nonce"]
        or process.get("spec_artifact") != spec_binding
        or process.get("receipt_artifact") != receipt_binding
        or process.get("command") != list(census_command(root, directory, original_binding))
        or type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or type(process.get("original_returncode")) is not int
        or process["original_returncode"] != 0
        or process.get("timed_out") is not False
        or process.get("custody_refused") is not False
        or process.get("command_error") != ""
        or not _within_deadline(duration, spec["timeout_seconds"])
        or receipt.get("schema_version") != RECEIPT_SCHEMA
        or receipt.get("role") != "canonical-collection-only"
        or receipt.get("run_id") != spec["run_id"]
        or receipt.get("nonce") != spec["nonce"]
        or receipt.get("spec_artifact") != spec_binding
        or receipt.get("source_identity") != spec["source_identity"]
        or receipt.get("runtime") != spec["runtime"]
        or receipt.get("runtime_locations") != spec["runtime_locations"]
        or receipt.get("arguments") != _pytest_arguments(root, directory, spec["test_files"])
        or type(receipt.get("original_pytest_exit_code")) is not int
        or receipt["original_pytest_exit_code"] != 0
        or type(receipt.get("exit_code")) is not int
        or receipt["exit_code"] != 0
        or type(receipt.get("executed_reports")) is not int
        or receipt["executed_reports"] != 0
        or any(receipt.get(key) != [] for key in ("collection_errors", "collection_skips", "deselected"))
        or receipt.get("interrupted") is not False
        or receipt.get("bytecode_verified") is not True
        or receipt.get("diagnostic") != ""
        or not isinstance(receipt.get("cases"), list)
        or not isinstance(receipt.get("nodeids"), list)
    ):
        raise ValueError("original canonical collection/process evidence is incomplete or inconsistent")
    for case in receipt["cases"]:
        if not isinstance(case, dict) or set(case) != {
            "family",
            "nodeid",
            "parameter_id",
            "parameter_names",
            "function_origin",
            "module_origin",
            "class_origin",
            "markers",
            "fixtures",
        }:
            raise ValueError("canonical collection requires exact case metadata fields")
        for key in ("function_origin", "module_origin", "class_origin"):
            if case[key] is not None or key != "class_origin":
                _origin(case[key], spec["source_hashes"], spec["runtime_locations"])
        if not isinstance(case["markers"], list) or not isinstance(case["fixtures"], dict):
            raise ValueError("case marker and fixture declarations are incomplete")
        for marker in case["markers"]:
            if not isinstance(marker, dict) or set(marker) != {"name", "args", "kwargs", "inherited_from", "origin"}:
                raise ValueError("case marker inheritance is incomplete")
            _origin(marker["origin"], spec["source_hashes"], spec["runtime_locations"])
        for definitions in case["fixtures"].values():
            if not isinstance(definitions, list):
                raise ValueError("case fixture definition list is incomplete")
            for definition in definitions:
                if not isinstance(definition, dict) or set(definition) != {"scope", "baseid", "dependencies", "origin"}:
                    raise ValueError("case fixture closure is incomplete")
                _origin(definition["origin"], spec["source_hashes"], spec["runtime_locations"])
    # Reuse normalization only; these assignments do not purport to execute pytest.
    normalized = RootCaseObserver(reader, spec["source_hashes"])
    normalized.nodeids, normalized.cases = receipt["nodeids"], receipt["cases"]
    census = normalized.census(
        source_identity=spec["source_identity"], runtime=spec["runtime"]["python_version"], platform=sys.platform
    )
    if receipt.get("census") != census or not reader.unchanged():
        raise ValueError("canonical collection metadata or source changed after original observation")
    return spec, census


def _read_collection(
    reader: SnapshotReader, spec_binding: object, process_binding: object, receipt_binding: object
) -> dict[str, Any]:
    """Return a candidate after a single full independent current observation."""
    return _observe_collection(reader, spec_binding, process_binding, receipt_binding)[1]


def read_root_census(reader: SnapshotReader, bundle: object, policy: RootCasePolicy) -> dict[str, Any]:
    """Authenticate processes and compare all metadata to the reviewed full policy.

    The policy admission layer must load this baseline from confined source-owned
    declarations. Initial collection candidates cannot grant classified acceptance.
    """
    if not isinstance(policy, RootCasePolicy):
        raise ValueError("classified census readback requires its parsed reviewed full source policy")
    if (
        not isinstance(bundle, dict)
        or set(bundle)
        != {"role", "exit_code", "spec_artifact", "process_artifact", "receipt_artifact", "coordinator_artifact"}
        or bundle["role"] != "canonical-collection-only"
        or type(bundle["exit_code"]) is not int
        or bundle["exit_code"] != 0
    ):
        raise ValueError("canonical census requires its exact successful process bundle")
    outer_snapshot = _artifact(reader, bundle["coordinator_artifact"])
    outer = _json(outer_snapshot)
    original_snapshot = _artifact(reader, outer.get("bundle_artifact"))
    original_bundle = _json(original_snapshot)
    spec, census = _observe_collection(
        reader, bundle["spec_artifact"], bundle["process_artifact"], bundle["receipt_artifact"]
    )
    directory = reader.root / spec["directory"]
    duration = outer.get("duration_seconds")
    admission = outer.get("admission_duration_seconds")
    if not _within_deadline(admission, spec["timeout_seconds"]):
        raise ValueError("canonical coordinator admission exceeded its finite budget")
    if not isinstance(admission, (int, float)):
        raise ValueError("canonical coordinator admission duration must be numeric")
    if not isinstance(duration, (int, float)) or duration < admission:
        raise ValueError("canonical coordinator recorded an impossible admission timeline")
    inner_duration = _json(_artifact(reader, bundle["process_artifact"])).get("duration_seconds")
    if (
        not isinstance(inner_duration, (int, float))
        or type(inner_duration) not in (int, float)
        or not 0 <= inner_duration <= duration - admission
    ):
        raise ValueError("inner collection duration exceeds the original outer process boundary")
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
        or outer_snapshot.path != directory / "coordinator-process.json"
        or original_snapshot.path != directory / "coordinator-bundle.json"
        or original_bundle != {key: value for key, value in bundle.items() if key != "coordinator_artifact"}
        or outer["schema_version"] != COORDINATOR_SCHEMA
        or outer["run_id"] != spec["run_id"]
        or outer["nonce"] != spec["nonce"]
        or outer["command"]
        != list(coordinator_command(reader.root, directory, spec["timeout_seconds"], spec["run_id"], spec["nonce"]))
        or type(outer["returncode"]) is not int
        or outer["returncode"] != 0
        or type(outer["original_returncode"]) is not int
        or outer["original_returncode"] != 0
        or outer["timed_out"] is not False
        or outer["custody_refused"] is not False
        or outer["command_error"] != ""
        or type(outer["launch_budget_seconds"]) is not int
        or outer["launch_budget_seconds"] < 1
        or outer["launch_budget_seconds"] != math.floor(spec["timeout_seconds"] - admission)
        or not _within_deadline(duration, spec["timeout_seconds"])
    ):
        raise ValueError("whole canonical census coordinator evidence is inconsistent or incomplete")
    compile_case_plan(policy, census, source_identity=spec["source_identity"])
    return census
