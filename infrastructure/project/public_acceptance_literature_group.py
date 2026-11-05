"""One invocation's original ARL producer and independently admitted capability readers.

Retained DATA nominates an original; its real audited process, source and bytes
still decide admission. Group state never survives run_auxiliary_acceptance().
"""

from __future__ import annotations

import hashlib
import math
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.testing._ci_execution_files import MAX_BYTES
from infrastructure.project.public_acceptance_evidence import MissingAuxiliaryProvider, write_json
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCOPE = "templates/template_advanced_literature_review"
CELL = "template_advanced_literature_review"
CAPABILITIES = ("retrieval", "screening", "local-classification", "licensed-fulltext")
GATES = tuple(f"{SCOPE}:live:{name}" for name in CAPABILITIES)
GROUP_SCHEMA = "template-literature-capability-group-v1"
ORIGIN_SCHEMA = "template-literature-capability-origin-v1"
PROJECTION_SCHEMA = "template-literature-capability-projection-v1"
# Match the original bounded unprivileged export; candidate transport keeps its own ceilings.
MAX_RETAINED_BYTES = MAX_BYTES


def _reader_time(reader: SnapshotReader) -> None:
    """Enforce this live reader's clock; original recorded monotonic times stay DATA."""
    if reader.operation_deadline is not None and time.monotonic() >= reader.operation_deadline:
        raise TimeoutError("literature independent reader deadline exhausted")


@dataclass
class LiteratureGroup:
    """Controller-local state; one first attempt, including a refused attempt."""

    binding: dict[str, str]
    origin: dict[str, str] | None = None


def create_group(
    root: Path,
    directory: Path,
    matrix_selection: dict[str, Any] | None,
    python: Path,
    fingerprint: str,
    producer_inputs: dict[str, dict[str, Any]] | None,
    deadline: float,
) -> LiteratureGroup | None:
    """Opt in only the exact complete, serial Source-owned ARL matrix cell."""
    model = (producer_inputs or {}).get(SCOPE, {}).get("model")
    if matrix_selection is None or matrix_selection.get("cell") != CELL or not python.is_file():
        return None
    if not isinstance(model, str) or not model.strip():
        return None  # Existing typed missing-model observations still own this refusal.
    selected = [gate for gate in matrix_selection["gates"] if ":live:" in gate]
    if selected != list(GATES) or matrix_selection["timeout_seconds"] != 1800 or matrix_selection["workers"] != 1:
        raise ValueError("literature grouping requires its exact complete serial ARL selection")
    plan = {
        "schema_version": GROUP_SCHEMA,
        "nonce": uuid.uuid4().hex,
        "scope": SCOPE,
        "gates": list(GATES),
        "selection": matrix_selection,
        "directory": directory.relative_to(root).as_posix(),
        "source_fingerprint": fingerprint,
        "interpreter": {"path": str(python), "sha256": hashlib.sha256(python.read_bytes()).hexdigest()},
        "model": model,
        "operation_deadline": deadline,
    }
    return LiteratureGroup(write_json(root, directory / "literature-group.json", plan))


def bound(reader: SnapshotReader, binding: Any, directory: str | None = None) -> ArtifactSnapshot:
    """Read an exact confined binding, preserving SnapshotReader's stable-byte checks."""
    _reader_time(reader)
    if (
        not isinstance(binding, dict)
        or set(binding) != {"path", "sha256"}
        or not isinstance(binding.get("path"), str)
        or not isinstance(binding.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", binding["sha256"]) is None
    ):
        raise ValueError("literature group requires an exact artifact binding")
    path = Path(binding["path"])
    if path.is_absolute() or ".." in path.parts or directory is not None and not path.is_relative_to(directory):
        raise ValueError("literature group evidence escaped its original invocation")
    held = reader.read(path.as_posix())
    _reader_time(reader)
    if held.sha256 != binding["sha256"]:
        raise ValueError("literature group evidence changed")
    return held


def read_group(reader: SnapshotReader, binding: Any, gate: str, fingerprint: str) -> dict[str, Any]:
    """Re-derive the complete cell from Source; persisted group DATA cannot widen it."""
    from infrastructure.project.auxiliary_matrix_plan import selection
    from infrastructure.reporting.release_readiness_profile import required_profile

    plan = bound(reader, binding).json_object()
    expected_keys = {
        "schema_version",
        "nonce",
        "scope",
        "gates",
        "selection",
        "directory",
        "source_fingerprint",
        "interpreter",
        "model",
        "operation_deadline",
    }
    if (
        set(plan) != expected_keys
        or plan["schema_version"] != GROUP_SCHEMA
        or plan["scope"] != SCOPE
        or plan["gates"] != list(GATES)
        or gate not in GATES
        or not isinstance(plan["nonce"], str)
        or re.fullmatch(r"[0-9a-f]{32}", plan["nonce"]) is None
        or plan["source_fingerprint"] != fingerprint
        or not isinstance(plan["model"], str)
        or not plan["model"].strip()
        or type(plan["operation_deadline"]) not in (int, float)
        or not math.isfinite(plan["operation_deadline"])
        or plan["operation_deadline"] <= 0
        or not isinstance(plan["directory"], str)
        or binding["path"] != str(Path(plan["directory"]) / "literature-group.json")
    ):
        raise ValueError("literature group identity is invalid or foreign")
    interpreter = plan["interpreter"]
    if (
        not isinstance(interpreter, dict)
        or set(interpreter) != {"path", "sha256"}
        or not isinstance(interpreter["path"], str)
        or not Path(interpreter["path"]).is_absolute()
        or not isinstance(interpreter["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", interpreter["sha256"]) is None
    ):
        raise ValueError("literature group omitted its original interpreter identity")
    requirements, faults = required_profile(reader.root, reader, fingerprint)
    _reader_time(reader)
    if faults or plan["selection"] != selection(requirements, CELL):
        raise ValueError("literature group differs from the complete current Source cell")
    return plan


def retain_origin(root: Path, directory: Path, group: LiteratureGroup, gate: str, gate_binding: dict[str, str]) -> None:
    """Retain the first gate's real terminal verdict once, including failed originals."""
    if gate == GATES[0]:
        if group.origin is not None:
            raise ValueError("literature original cannot be attempted more than once")
        group.origin = write_json(
            root,
            directory / "literature-origin.json",
            {"schema_version": ORIGIN_SCHEMA, "group": group.binding, "gate_artifact": gate_binding},
        )


def validate_originals(
    reader: SnapshotReader, plan: dict[str, Any], native_binding: Any, originals_binding: Any
) -> dict[str, Any]:
    """Read every retained original and verify consumed/model commitments independently."""
    directory = plan["directory"]
    native = bound(reader, native_binding, directory).json_object()
    manifest = bound(reader, originals_binding, directory).json_object()
    results = native.get("producer_results")
    if not isinstance(results, dict) or any(not isinstance(results.get(name), dict) for name in CAPABILITIES):
        raise ValueError("literature original capability results are malformed")
    if (
        native.get("schema_version") != "template/literature-unpaid-acceptance/1"
        or native.get("project") != CELL
        or native.get("execution_mode") != "live-unpaid"
        or native.get("status") != "passed"
        or native.get("paid_integrations") is not False
        or native.get("source_unchanged") is not True
        or native.get("consumed_unchanged") is not True
        or native.get("loaded_implementation_verified") is not True
        or native.get("capabilities") != list(CAPABILITIES)
        or any(results[name].get("status") != "passed" for name in CAPABILITIES)
        or manifest.get("acceptance_granted") is not False
        or manifest.get("receipt") != native_binding
    ):
        raise ValueError("literature original lacks complete actual capability/source custody")
    files, artifacts, consumed = manifest.get("files"), native.get("artifacts"), native.get("consumed_artifacts")
    if (
        not isinstance(files, dict)
        or not isinstance(artifacts, dict)
        or not isinstance(consumed, dict)
        or not consumed
        or len(files) > 10000
        or type(manifest.get("bytes")) is not int
        or not 0 <= manifest["bytes"] <= MAX_RETAINED_BYTES
        or set(files) != {"receipt.json", *artifacts}
        or set(consumed) - set(artifacts)
    ):
        raise ValueError("literature original file/consumption census is incomplete")
    retained = {}
    total = 0
    original_receipt = bound(reader, manifest.get("original_receipt"), directory)
    prefix = Path(original_receipt.relative).parent
    declared_total = 0
    for record in files.values():
        _reader_time(reader)
        if (
            not isinstance(record, dict)
            or type(record.get("bytes")) is not int
            or not 0 <= record["bytes"] <= MAX_RETAINED_BYTES
        ):
            raise ValueError("literature original file byte bound is invalid")
        declared_total += record["bytes"]
        if declared_total > MAX_RETAINED_BYTES:
            raise ValueError("literature original exceeds its retained transport byte ceiling")
    if declared_total != manifest["bytes"]:
        raise ValueError("literature original declared byte census is incomplete")
    for name, record in files.items():
        _reader_time(reader)
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "bytes"}:
            raise ValueError("literature original file binding is malformed")
        if record["path"] != str(prefix / name) or type(record["bytes"]) is not int:
            raise ValueError("literature original file escaped its retained snapshot")
        held = bound(reader, {key: record[key] for key in ("path", "sha256")}, directory)
        if len(held.content) != record["bytes"]:
            raise ValueError("literature original file size changed")
        if name != "receipt.json" and artifacts[name] != held.sha256:
            raise ValueError("literature original artifact changed")
        if name in consumed and consumed[name] != held.sha256:
            raise ValueError("literature consumed bytes changed")
        retained[name] = held
        total += len(held.content)
    if (
        retained["receipt.json"] != original_receipt
        or original_receipt.json_object() != native
        or manifest.get("bytes") != total
    ):
        raise ValueError("literature receipt differs from its complete retained original")
    calls = native.get("local_generation_calls")
    model_digest = native["producer_results"]["local-classification"].get("model_sha256")
    if (
        not isinstance(calls, list)
        or not 1 <= len(calls) <= 7
        or any(not isinstance(row, dict) for row in calls)
        or not isinstance(model_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", model_digest) is None
        or [row.get("directory") for row in calls] != [f"model_{index}" for index in range(1, len(calls) + 1)]
    ):
        raise ValueError("literature original omitted its bounded model-call identities")
    for call in calls:
        _reader_time(reader)
        prefix_name = call["directory"]
        names = [f"{prefix_name}/{name}.json" for name in ("request", "response", "model")]
        if (
            call.get("status") != "passed"
            or call.get("model_sha256") != model_digest
            or any(name not in consumed for name in names)
        ):
            raise ValueError("literature original omitted exact consumed model bytes")
        request, _, model = [retained[name].json_object() for name in names]
        if request.get("model") != plan["model"] or model != {"model": plan["model"], "model_sha256": model_digest}:
            raise ValueError("literature original belongs to a different selected model")
    for key in ("source_manifest", "runtime_environment", "implementation_custody", "declared_dependencies"):
        if not isinstance(native.get(key), dict) or not native[key]:
            raise ValueError("literature original omitted implementation/dependency/runtime custody")
    _reader_time(reader)
    return native


def read_origin(
    reader: SnapshotReader, group_binding: Any, origin_binding: Any, plan: dict[str, Any], *, admit: bool = True
) -> dict[str, Any]:
    """Follow one edge to the original-only gate; no retry or recursive projection."""
    if not isinstance(origin_binding, dict) or origin_binding.get("path") != str(
        Path(plan["directory"]) / "literature-origin.json"
    ):
        raise ValueError("literature origin belongs to another invocation directory")
    origin = bound(reader, origin_binding, plan["directory"]).json_object()
    if (
        set(origin) != {"schema_version", "group", "gate_artifact"}
        or origin["schema_version"] != ORIGIN_SCHEMA
        or origin["group"] != group_binding
    ):
        raise ValueError("literature original group identity changed")
    payload = bound(reader, origin["gate_artifact"], plan["directory"]).json_object()
    if payload.get("gate") != GATES[0] or payload.get("source_fingerprint") != plan["source_fingerprint"]:
        raise ValueError("literature origin is not the first Source-selected capability")
    details = payload.get("details", {})
    if not isinstance(details, dict):
        raise ValueError("literature original details are malformed")
    if "literature_origin" in details or details.get("literature_role") == "projection":
        raise ValueError("literature projection cannot serve as another projection's original")
    if payload.get("status") != "pass":
        reason = f"original literature producer did not pass: status={payload.get('status')}"
        if payload.get("status") == "blocked":
            raise MissingAuxiliaryProvider(reason)
        raise ValueError(reason)
    if details.get("literature_role") != "original" or details.get("literature_group") != group_binding:
        raise ValueError("literature origin did not execute the original-only worker path")
    if admit:
        from infrastructure.reporting.release_readiness_profile import required_profile
        from infrastructure.reporting.release_readiness_validators import validate_acceptance

        requirements, faults = required_profile(reader.root, reader, plan["source_fingerprint"])
        if faults:
            raise ValueError("literature original Source requirement is unavailable")
        requirement = next(item for item in requirements if item.id == GATES[0])
        _reader_time(reader)
        validate_acceptance(requirement, payload, reader)
    _reader_time(reader)
    return payload


def project_origin(
    root: Path,
    gate: str,
    directory: Path,
    inputs: dict[str, Any],
    group_binding: Any,
    origin_binding: Any,
    deadline: float,
) -> dict[str, Any]:
    """Execute a supervised capability reader without retrieval or generation."""
    from infrastructure.reporting.readiness_receipts import source_fingerprint
    from infrastructure.core.implementation_custody import runtime_identity

    reader = SnapshotReader(root, operation_deadline=deadline)
    _reader_time(reader)
    runtime_before = runtime_identity()
    _reader_time(reader)
    plan = read_group(reader, group_binding, gate, source_fingerprint(root))
    if inputs.get("model") != plan["model"] or deadline != plan["operation_deadline"]:
        raise ValueError("literature projection changed the selected model or original deadline")
    payload = read_origin(reader, group_binding, origin_binding, plan)
    original = payload["details"]
    native = validate_originals(reader, plan, original["native_artifact"], original["literature_originals"])
    capability = gate.split(":live:", 1)[1]
    if runtime_before != native["runtime_environment"] or runtime_identity() != runtime_before:
        raise ValueError("literature projection runtime differs from the actual original producer")
    if native["producer_results"][capability].get("status") != "passed" or not reader.unchanged():
        raise ValueError("literature original changed during capability projection")
    _reader_time(reader)
    execution = {
        "schema_version": PROJECTION_SCHEMA,
        "execution_kind": "projection",
        "status": "passed",
        "capability": capability,
        "group": group_binding,
        "origin": origin_binding,
        "native_artifact": original["native_artifact"],
        "originals_artifact": original["literature_originals"],
        "runtime_environment": runtime_before,
    }
    return {
        "capability": capability,
        "paid": False,
        "execution_kind": "projection",
        "execution_artifact": write_json(root, directory / "literature-execution.json", execution),
        "assertions": {"actual_provider_and_consumed_custody": True},
        "native_artifact": original["native_artifact"],
        "literature_originals": original["literature_originals"],
        "literature_role": "projection",
        "literature_group": group_binding,
        "literature_origin": origin_binding,
        "literature_runtime": runtime_before,
    }


def validate_projection_execution(gate: str, details: dict[str, Any], reader: SnapshotReader) -> None:
    """Narrow generic live admission to one explicit ARL capability projection."""
    if gate not in GATES or details.get("literature_role") != "projection":
        raise ValueError("only the complete ARL group may project actual literature evidence")
    raw = bound(reader, details.get("execution_artifact")).json_object()
    expected = {
        "schema_version": PROJECTION_SCHEMA,
        "execution_kind": "projection",
        "status": "passed",
        "capability": gate.split(":live:", 1)[1],
        "group": details.get("literature_group"),
        "origin": details.get("literature_origin"),
        "native_artifact": details.get("native_artifact"),
        "originals_artifact": details.get("literature_originals"),
        "runtime_environment": details.get("literature_runtime"),
    }
    if raw != expected:
        raise ValueError("literature projection summary differs from its exact reader artifact")


def validate_group_process(
    gate: str,
    fingerprint: str,
    details: dict[str, Any],
    reader: SnapshotReader,
    process: dict[str, Any],
    spec: dict[str, Any],
) -> None:
    """Link this original or projection and its own control to the same live group."""
    binding = details.get("literature_group")
    plan = read_group(reader, binding, gate, fingerprint)
    directory = Path(plan["directory"])
    spec_path = process["spec_artifact"]["path"]
    if (
        spec.get("literature_group") != binding
        or Path(spec_path).parent.parent != directory
        or spec.get("producer_inputs", {}).get("model") != plan["model"]
        or process.get("selected_interpreter") != plan["interpreter"]["path"]
        or process.get("executable_sha256") != plan["interpreter"]["sha256"]
        or process.get("original_deadline_monotonic") != plan["operation_deadline"]
        or spec.get("operation_deadline") != plan["operation_deadline"]
    ):
        raise ValueError("literature process changed its invocation/source/model/runtime/deadline binding")
    controls = details.get("negative_controls")
    if not isinstance(controls, list) or len(controls) != 1:
        raise ValueError("each literature gate requires its own one executed negative control")
    for control in controls:
        negative = bound(reader, control.get("artifact"), plan["directory"]).json_object()
        negative_spec = bound(reader, negative.get("spec_artifact"), plan["directory"]).json_object()
        if (
            negative.get("original_deadline_monotonic") != plan["operation_deadline"]
            or negative_spec.get("literature_group") != binding
            or negative_spec.get("operation_deadline") != plan["operation_deadline"]
        ):
            raise ValueError("literature control changed the group's original operation clock")
    role = details.get("literature_role")
    if role == "original":
        if gate != GATES[0] or "literature_origin" in spec or "literature_origin" in details:
            raise ValueError("literature original acquired a reuse edge or changed its Source gate")
    elif role == "projection":
        if spec.get("literature_origin") != details.get("literature_origin"):
            raise ValueError("literature projection changed its original binding")
        origin = read_origin(reader, binding, details["literature_origin"], plan)
        if any(details.get(key) != origin["details"].get(key) for key in ("native_artifact", "literature_originals")):
            raise ValueError("literature projection replaced its admitted original bytes")
        validate_projection_execution(gate, details, reader)
    else:
        raise ValueError("literature group omitted its explicit original/projection role")
    native = validate_originals(reader, plan, details.get("native_artifact"), details.get("literature_originals"))
    if native["runtime_environment"].get("python_sha256") != plan["interpreter"]["sha256"]:
        raise ValueError("literature original runtime differs from the selected interpreter bytes")
    if role == "projection" and details.get("literature_runtime") != native["runtime_environment"]:
        raise ValueError("literature projection did not retain its matching independently observed runtime")


def validate_group_report(report: dict[str, Any], reader: SnapshotReader, cell: str) -> None:
    """Consume the enclosing invocation binding; a written group field is not proof."""
    _reader_time(reader)
    binding = report.get("literature_group")
    if binding is None:
        if report.get("literature_origin") is not None:
            raise ValueError("literature original omitted its enclosing group binding")
        if cell == CELL:
            for gate in GATES:
                entry = report.get("gates", {}).get(gate, {})
                packet = bound(
                    reader, {"path": entry.get("artifact"), "sha256": entry.get("artifact_sha256")}
                ).json_object()
                details = packet.get("details", {})
                if any(name in details for name in ("literature_group", "literature_origin", "literature_role")):
                    raise ValueError("grouped literature gate omitted its enclosing invocation binding")
        return  # Historical original-only cells keep their existing contract.
    if cell != CELL:
        raise ValueError("only the complete ARL original cell may nominate a literature group")
    plan = read_group(reader, binding, GATES[0], report["source_fingerprint"])
    if report.get("auxiliary_selection") != plan["selection"]:
        raise ValueError("literature group differs from its enclosing original selection")
    original_entry = report["gates"][GATES[0]]
    origin_binding = report.get("literature_origin")
    origin = bound(reader, origin_binding, plan["directory"]).json_object()
    if origin.get("group") != binding or origin.get("gate_artifact") != {
        "path": original_entry["artifact"],
        "sha256": original_entry["artifact_sha256"],
    }:
        raise ValueError("literature origin is not the enclosing invocation's own first gate")
    for gate in GATES:
        entry = report["gates"][gate]
        payload = bound(
            reader, {"path": entry["artifact"], "sha256": entry["artifact_sha256"]}, plan["directory"]
        ).json_object()
        details = payload.get("details", {})
        process = bound(reader, details.get("process_artifact"), plan["directory"]).json_object()
        spec = bound(reader, process.get("spec_artifact"), plan["directory"]).json_object()
        if spec.get("literature_group") != binding:
            raise ValueError("literature gate belongs to a different enclosing invocation")
        if gate != GATES[0] and spec.get("literature_origin") != origin_binding:
            raise ValueError("literature gate changed the enclosing invocation's exact original")
    _reader_time(reader)


def validate_invocation(root: Path, receipt_path: Path, deadline: float) -> dict[str, Any]:
    """Freshly read the complete selected ARL original; grant no aggregate/release claim."""
    from infrastructure.project.auxiliary_matrix_plan import validate_cell
    from infrastructure.project.public_acceptance_evidence import gate_payload
    from infrastructure.reporting.original_job_outcome import validate_auxiliary_receipt_closure
    from infrastructure.reporting.readiness_receipts import source_fingerprint
    from infrastructure.reporting.release_readiness_profile import required_profile
    from infrastructure.reporting.release_readiness_validators import validate_acceptance

    root = root.resolve(strict=True)
    receipt_path = receipt_path.absolute()
    if not receipt_path.is_relative_to(root):
        raise ValueError("ARL diagnostic receipt must remain in the selected Source root")
    reader = SnapshotReader(root, operation_deadline=deadline)
    _reader_time(reader)
    fingerprint = source_fingerprint(root)
    _reader_time(reader)
    report = reader.read(receipt_path.relative_to(root).as_posix()).json_object()
    requirements, faults = required_profile(root, reader, fingerprint)
    _reader_time(reader)
    if faults or report.get("source_fingerprint") != fingerprint or report.get("exit_code") != 0:
        raise ValueError("ARL diagnostic requires a current successful original cell")
    validate_cell(report, requirements, CELL)
    validate_auxiliary_receipt_closure(report)
    if report.get("literature_group") is None:
        raise ValueError("ARL diagnostic requires its current invocation's original/projection group")
    validate_group_report(report, reader, CELL)
    by_id = {requirement.id: requirement for requirement in requirements}
    roles = {}
    controls = {}
    for gate, entry in report["gates"].items():
        _reader_time(reader)
        if entry.get("status") != "pass":
            raise ValueError("ARL diagnostic omitted a successful selected gate")
        payload = bound(reader, {"path": entry.get("artifact"), "sha256": entry.get("artifact_sha256")}).json_object()
        expected = gate_payload(by_id[gate], fingerprint, "pass", payload.get("details", {}), [])
        if any(payload.get(key) != value for key, value in expected.items() if key != "details"):
            raise ValueError("ARL diagnostic gate disagrees with its current Source requirement")
        validate_acceptance(by_id[gate], payload, reader)
        _reader_time(reader)
        if gate in GATES:
            roles[gate] = payload["details"].get("literature_role")
            controls[gate] = payload["details"]["negative_controls"]
    if roles != {gate: "original" if gate == GATES[0] else "projection" for gate in GATES}:
        raise ValueError("ARL diagnostic did not observe one original and three explicit projections")
    _reader_time(reader)
    current_fingerprint = source_fingerprint(root)
    _reader_time(reader)
    unchanged = reader.unchanged()
    _reader_time(reader)
    if current_fingerprint != fingerprint or not unchanged:
        raise ValueError("ARL diagnostic Source or retained original bytes changed during independent readback")
    return {
        "schema_version": "template-arl-capability-diagnostic-v1",
        "status": "passed",
        "source_fingerprint": fingerprint,
        "auxiliary_selection": report["auxiliary_selection"],
        "literature_group": report["literature_group"],
        "literature_origin": report["literature_origin"],
        "capability_roles": roles,
        "own_negative_controls": controls,
        "original_live_producers": 1,
        "capability_projections": 3,
        "aggregate_acceptance_granted": False,
        "release_authorized": False,
    }
