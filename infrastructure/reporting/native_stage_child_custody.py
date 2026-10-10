"""Fixed nested stage role authenticated through its genuine parent ToolAPI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_EXECUTIONS
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_stage_child_code_closure import _stage_closure
from infrastructure.reporting.native_stage_child_contracts import (
    PACKET_SCHEMA,
    PURPOSE,
    WORKER,
    audit_roots,
    binding,
    validate_artifact_bindings,
    validate_request,
    validate_specification,
    verify_stage_observation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class _Completion:
    original_deadline: float
    observed_completion: float


def validate_stage_child_packet(
    source: NativeSourceContext,
    packet: dict[str, Any],
    reader: SnapshotReader,
    *,
    process: dict[str, Any],
    source_record: dict[str, Any],
    parent_pid: int,
    parent_directory: str,
    original_deadline: float,
    deadline: float,
) -> dict[str, Any]:
    """DATA reconstruction AFTER the caller authenticates genuine parent Popen."""
    from infrastructure.reporting.native_format_acceptance_validation import _file
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
    from infrastructure.reporting.native_tool_replay import _stamp

    if (
        set(packet)
        != {
            "schema_version",
            "process_artifact",
            "specification_artifact",
            "artifact",
            "closure_artifact",
            "original_exit_code",
        }
        or packet["schema_version"] != PACKET_SCHEMA
    ):
        raise ValueError("native stage child packet fields differ from the fixed Source role")
    process_file = _file(packet["process_artifact"], reader)
    if process_file.json_object() != process:
        raise ValueError("native stage child packet replaced its genuine parent ToolAPI event")
    specification = _file(packet["specification_artifact"], reader)
    spec = specification.json_object()
    validate_specification(spec)
    mirror = Path(source_record["current_mirror"]["root"])
    sdk = Path(source_record["selected_sdk"]["package_root"])
    leaf = reader.root / spec["directory"]
    if (
        spec["source"] != source_record
        or spec["run_id"] != source_record["run_id"]
        or spec["parent_pid"] != parent_pid
        or spec["parent_directory"] != parent_directory
        or not process_file.path.is_relative_to(reader.root / parent_directory)
        or spec["scope"] != source_record["scope"]
        or process.get("owner_pid") != parent_pid
        or spec["parent_deadline_monotonic"] != original_deadline
        or not spec["deadline_monotonic"] <= original_deadline
        or process.get("caller_deadline_monotonic") != spec["deadline_monotonic"]
        or process.get("original_deadline_monotonic") != spec["deadline_monotonic"]
        or type(packet["original_exit_code"]) is not int
        or process.get("original_exit_code") != packet["original_exit_code"]
        or process.get("run_id") != spec["run_id"]
        or process.get("purpose") != PURPOSE
        or specification.path != leaf / "specification.json"
        or process_file.path != leaf / (PURPOSE + ".json")
        or spec["source_audit_roots"] != [str(path) for path in audit_roots(mirror, sdk, spec["scope"])]
    ):
        raise ValueError(
            "native stage child Source/run/parent/original stage clock or actual signed OS custody differs"
        )
    request = _file(spec["request"], reader)
    payload, protocol, script_sha = validate_request(
        source, spec["scope"], request, deadline=deadline, original_root_label=mirror
    )
    if (
        canonical_digest(payload) != spec["request_digest"]
        or protocol != spec["protocol"]
        or script_sha != spec["script"]["sha256"]
        or payload["run_id"] != spec["pipeline_run_id"]
        or payload["stage_key"] != spec["stage_key"]
        or payload["cwd"] != spec["cwd"]
        or Path(payload["argv"][0]).relative_to(mirror).as_posix() != spec["script"]["path"]
    ):
        raise ValueError("native stage child request differs from exact original Source and separate pipeline identity")
    implementation = _file(spec["implementation"], reader)
    expected = json.loads(implementation.content)
    current = json.loads(source.bindings.expected_implementation_bytes)
    if expected["files"] != current["files"]:
        raise ValueError("native stage child selected SDK body differs from current independently admitted Source")
    native = _file(process["native_process_artifact"], reader).json_object()
    nomination = native["nomination"]["path"]
    if native.get("launcher_preserved") is not True or native["nomination"]["resolved_path"] != expected[
        "runtime_environment"
    ].get("python_executable"):
        raise ValueError("native stage child actual selected launcher differs from its independently admitted SDK")
    if protocol == "analysis" and nomination != payload["runtime_binding"]["executable"]:
        raise ValueError("native stage analysis child replaced its actual Source-selected project runtime")
    hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
    bootstrap = format_selected_sdk_native_bootstrap(
        hook,
        sdk,
        audit_roots(mirror, sdk, spec["scope"])[1:],
        mirror / spec["implementation"]["path"],
        implementation.sha256,
        mirror / spec["directory"] / "closure",
        tuple(spec["closure_identity"]),
        spec["deadline_monotonic"],
        required_worker_module=WORKER,
    )
    command = [
        nomination,
        "-I",
        "-c",
        bootstrap,
        "--root",
        str(mirror),
        "--specification",
        specification.relative,
        "--specification-sha256",
        specification.sha256,
        "--implementation-sha256",
        implementation.sha256,
        "--deadline",
        repr(spec["deadline_monotonic"]),
        "--run-id",
        spec["run_id"],
    ]
    if process["command"] != command or native.get("command") != command or native.get("cwd") != spec["cwd"]:
        raise ValueError("native stage child actual command/cwd differs from its fixed Source prelaunch role")
    observation_file = _file(packet["artifact"], reader)
    closure_file = _file(packet["closure_artifact"], reader)
    if observation_file.path != leaf / "observation.json":
        raise ValueError("native stage child retained observation belongs to another actual attempt")
    observation = observation_file.json_object()
    verify_stage_observation(spec, observation, child_pid=process["pid"], request=request)
    code = observation["stage_return_code"]
    worker_code = (
        code if code is not None else (130 if observation["stage_exception"]["class"] == "KeyboardInterrupt" else 1)
    )
    stdout = _file(
        {"path": process["raw_stdout"]["path"], "sha256": process["raw_stdout"]["sha256"]}, reader
    ).content.decode("utf-8", errors="strict")
    seals = [
        line
        for line in stdout.splitlines()
        if line.startswith(("STAGE_CHILD_OBSERVATION_V1 ", "STAGE_CHILD_CLOSURE_V1 "))
    ]
    if seals != [
        f"STAGE_CHILD_OBSERVATION_V1 {specification.sha256} {observation_file.sha256} "
        f"{spec['run_id']} {spec['nonce']} {worker_code}",
        f"STAGE_CHILD_CLOSURE_V1 {closure_file.sha256}",
    ]:
        raise ValueError("native stage child lacks actual raw stdout observation and full Code seals")
    closure = _stage_closure(
        source, spec, packet["closure_artifact"], reader, deadline=deadline, worker_code=worker_code
    )
    for name, filename in (("result", "result.json"), ("original_checkpoint", "original.json")):
        value = observation[name]
        if value is not None:
            observed = _file(value, reader)
            result = observed.json_object()
            if (
                observed.path != leaf / filename
                or result.get("request_digest") != spec["request_digest"]
                or result.get("run_id") != spec["pipeline_run_id"]
                or result.get("stage_key") != spec["stage_key"]
            ):
                raise ValueError("native stage child result/checkpoint differs from its exact actual request")
            original = result.get("original_exit_code")
            if original is not None and (type(original) is not int or not 0 <= original <= 255):
                raise ValueError("native stage child script intent is not a Source worker convention")
            if name == "original_checkpoint" and (
                spec["protocol"] != "analysis"
                or result.get("schema") != "template-analysis-original-checkpoint/1"
                or result.get("pid") != process["pid"]
                or result.get("analysis_nonce") != payload["analysis_nonce"]
                or result.get("completion_authorized") is not False
                or original is None
            ):
                raise ValueError("native stage original-only checkpoint cannot authorize completion")
            if name == "result" and (
                result.get("schema") != payload["schema"]
                or result.get("custody") not in {"verified", "blocked"}
                or code is not None
                and result.get("custody") == "verified"
                and original != code
                or spec["protocol"] == "analysis"
                and result.get("analysis_nonce") != payload["analysis_nonce"]
            ):
                raise ValueError("native stage result differs from the actual existing worker intent/custody")
    if code is not None and observation["result"] is None:
        raise ValueError("native stage child returned intent without its actual existing worker result")
    for value in observation["nested_tool_artifacts"]:
        event = _file(value, reader).json_object()
        if event.get("owner_pid") != process["pid"] or event.get("run_id") != spec["run_id"]:
            raise ValueError("native stage retained nested ToolAPI belongs to another actual child owner")
    for value in observation["stage_children"]:
        child = _file(value, reader).json_object()
        if child.get("schema_version") != PACKET_SCHEMA:
            raise ValueError("native stage retained child graph is not the one fixed Source stage role")
    from infrastructure.reporting.native_stage_child_scope import validate_renderer_stage_artifact

    seen_artifacts: set[str] = set()
    for value in observation["stage_artifacts"]:
        artifact = _file(value, reader)
        if artifact.relative in seen_artifacts or not artifact.path.is_relative_to(leaf):
            raise ValueError("native stage retained renderer packet repeats or escaped actual child scope")
        seen_artifacts.add(artifact.relative)
        renderer = artifact.json_object()
        validate_renderer_stage_artifact(
            source,
            renderer,
            reader,
            scope=spec["scope"],
            run_id=spec["run_id"],
            owner_pid=process["pid"],
            original_root_label=mirror,
        )
        if any(tool not in observation["nested_tool_artifacts"] for tool in renderer["tool_artifacts"]):
            raise ValueError("native stage renderer packet names unretained actual child ToolAPI events")
    return {
        "original": _Completion(spec["deadline_monotonic"], _stamp(native.get("operation_end"))),
        "process": native,
        "closure": closure,
        "source": source_record,
        "event": observation_file,
        "specification": spec,
    }


class NativeStageChildReaderOperation:
    """Typed nested role with genuine parent custody; packets never mint it."""

    def __init__(
        self,
        source: NativeSourceContext,
        parent_reader: SnapshotReader,
        records: list[dict[str, str]],
        *,
        scope: str,
        run_id: str,
        deadline: float,
    ) -> None:
        if type(self) is not NativeStageChildReaderOperation or not isinstance(source, NativeSourceContext):
            raise ValueError("native stage reader requires its exact Source-owned concrete role")
        if not isinstance(records, list) or len(records) > MAX_EXECUTIONS:
            raise ValueError("native stage reader retained graph exceeds its existing bound")
        validate_artifact_bindings(records)
        self.source, self.parent_reader, self.records = source, parent_reader, tuple(dict(item) for item in records)
        self.scope, self.run_id, self.deadline = scope, run_id, deadline
        parent = parent_reader.native_control_operation
        self.depth: int = parent.depth + 1 if type(parent) is NativeStageChildReaderOperation else 0
        if self.depth > 64:
            raise ValueError("native stage Source role exceeds its bounded child graph depth")
        self.verify(parent_reader)

    def verify(self, reader: SnapshotReader) -> None:
        remaining(self.deadline)
        if reader.root != self.source.bindings.current_root:
            raise ValueError("native stage current reader differs from independently admitted Source")
        parent = self.parent_reader.native_control_operation
        if parent is not None:
            if (
                type(parent) is not NativeStageChildReaderOperation
                or parent.source is not self.source
                or parent.run_id != self.run_id
                or not self.deadline <= parent.deadline
            ):
                raise ValueError("native stage nested reader differs from its genuine enclosing stage role")
            parent.verify(self.parent_reader)
        elif self.parent_reader.native_producer_operation is not None and self.parent_reader.native_operation is None:
            producer = self.parent_reader.native_producer_operation
            if producer.source is not self.source:
                raise ValueError("native stage producer differs from actual independently admitted Source")
            producer.verify(self.parent_reader, run_id=self.run_id, deadline=self.deadline)
        else:
            from infrastructure.reporting.native_format_joint_source import require_native_operation

            operation = require_native_operation(self.parent_reader)
            if operation.source is not self.source or not self.deadline <= operation.deadline:
                raise ValueError("native stage lacks genuine externally held original/current Source custody")
            original = operation.originals.get(self.scope)
            if original is None or original.run_id != self.run_id:
                raise ValueError("native stage lacks the exact externally held original scope/run")
            operation.verify(self.parent_reader)
        self.source.verify_correspondence(self.source.reference, reader.root, reader, self.deadline)

    def child(self, packet_binding: dict[str, str], reader: SnapshotReader) -> dict[str, Any]:
        from infrastructure.reporting.native_format_acceptance_validation import _file
        from infrastructure.reporting.native_tool_replay import (
            authenticate_original_native_artifact,
            validate_native_tool_data,
        )

        self.verify(reader)
        if packet_binding not in self.records:
            raise ValueError("native stage packet is absent from the nominated actual enclosing graph")
        packet = _file(packet_binding, reader).json_object()
        process_file = _file(packet["process_artifact"], self.parent_reader)
        process = process_file.json_object()
        producer = self.parent_reader.native_producer_operation
        if (
            self.parent_reader.native_control_operation is None
            and producer is not None
            and self.parent_reader.native_operation is None
        ):
            producer.validate_tool(packet["process_artifact"], process, self.parent_reader, run_id=self.run_id)
            if packet_binding not in producer.stage_children:
                raise ValueError("native stage packet was never closed by its actual live parent factory")
            source_record = json.loads(self.source.descriptor(self.scope, deadline=self.deadline))
            original_deadline, parent_pid = producer.deadline, producer.owner_pid
            parent_directory = producer.stage_scope_directory(self.scope).relative_to(reader.root).as_posix()
        else:
            authority = authenticate_original_native_artifact(
                packet["process_artifact"],
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=(
                    "reporting/native_stage_child.py",
                    "reporting/native_source_provider_bootstrap.py",
                ),
            )
            if authority["event"].json_object() != process:
                raise ValueError("native stage parent event differs from actual original custody")
            completion = authority["original"]
            validate_native_tool_data(
                process,
                self.parent_reader,
                original_deadline=completion.original_deadline,
                original_completion=completion.observed_completion,
            )
            source_record, original_deadline, parent_pid = (
                authority["source"],
                completion.original_deadline,
                authority["process"]["pid"],
            )
            parent_directory = (
                authority["specification"]["directory"]
                if self.parent_reader.native_control_operation is not None
                else Path(authority["original"].specification_relative).parent.as_posix()
            )
        authority = validate_stage_child_packet(
            self.source,
            packet,
            reader,
            process=process,
            source_record=source_record,
            parent_pid=parent_pid,
            parent_directory=parent_directory,
            original_deadline=original_deadline,
            deadline=self.deadline,
        )
        if authority["specification"]["scope"] != self.scope or authority["specification"]["run_id"] != self.run_id:
            raise ValueError("native stage authenticated packet belongs to another scope/globalnative run")
        self.verify(reader)
        return {**authority, "operation": self}

    def _authenticated_descendants(self, reader: SnapshotReader) -> list[tuple[dict[str, str], dict[str, Any]]]:
        """Follow only closed child rosters of genuinely authenticated ancestors."""
        from infrastructure.reporting.native_format_acceptance_validation import _file

        pending = [(self, packet) for packet in self.records]
        seen: set[str] = set()
        results = []
        while pending:
            remaining(self.deadline)
            if len(seen) >= MAX_EXECUTIONS:
                raise ValueError("native stage actual descendant graph exceeds its existing execution bound")
            role, packet_binding = pending.pop(0)
            packet = _file(packet_binding, reader)
            if packet.relative in seen:
                raise ValueError("native stage actual descendant graph repeats a packet or contains a cycle")
            seen.add(packet.relative)
            authority = role.child(packet_binding, reader)
            results.append((packet_binding, authority))
            nested = authority["event"].json_object()["stage_children"]
            if nested:
                parent_reader = SnapshotReader(
                    reader.root,
                    native_operation=self.parent_reader.native_operation,
                    native_producer_operation=self.parent_reader.native_producer_operation,
                    native_control_operation=role,
                )
                child_role = NativeStageChildReaderOperation(
                    self.source,
                    parent_reader,
                    nested,
                    scope=self.scope,
                    run_id=self.run_id,
                    deadline=self.deadline,
                )
                pending.extend((child_role, item) for item in nested)
        if not reader.unchanged():
            raise ValueError("native stage descendant packet bytes changed during authenticated traversal")
        return results

    def descendant(self, packet_binding: dict[str, str], reader: SnapshotReader) -> dict[str, Any]:
        """Return one causally authenticated leaf; JSON alone creates no role."""
        validate_artifact_bindings([packet_binding])
        matches = [authority for item, authority in self._authenticated_descendants(reader) if item == packet_binding]
        if len(matches) != 1:
            raise ValueError("native stage descendant needs one actual retained ancestor chain")
        return matches[0]

    def authenticate_artifact(
        self,
        selected_binding: dict[str, Any],
        reader: SnapshotReader,
        *,
        run_id: str,
        required_sdk_modules: tuple[str, ...],
    ) -> dict[str, Any]:
        from infrastructure.reporting.native_format_acceptance_validation import _file

        if run_id != self.run_id:
            raise ValueError("native stage nested ToolAPI belongs to another global native run")
        selected = _file(selected_binding, reader)
        matches = []
        for packet_binding in self.records:
            authority = self.child(packet_binding, reader)
            observed = authority["event"].json_object()
            if binding(selected) in (*observed["nested_tool_artifacts"], *observed["stage_artifacts"]):
                matches.append(authority)
        if not matches:
            for _, authority in self._authenticated_descendants(reader):
                observed = authority["event"].json_object()
                if binding(selected) in (*observed["nested_tool_artifacts"], *observed["stage_artifacts"]):
                    matches.append(authority)
        if len(matches) != 1:
            raise ValueError("native stage nested tool needs one actually retained genuine child owner")
        authority = matches[0]
        sdk = Path(authority["source"]["selected_sdk"]["package_root"])
        executed = {row["source_path"] for row in authority["closure"]["executions"] if row["runs"]}
        if not {str(sdk / name) for name in required_sdk_modules} <= executed:
            raise ValueError("native stage nested tool lacks actual admitted SDK helper executions")
        event = selected.json_object()
        if event.get("owner_pid") != authority["process"]["pid"]:
            raise ValueError("native stage nested tool owner differs from the actual child PID")
        return {**authority, "event": selected}
