"""Office child DATA admitted only through the externally held full Original.

Transport never creates a parent-held NativeOfficeControlOriginal. The distinct
reader role authenticates each nested actual ToolAPI and retained Code closure
against the independently admitted full native launch before using its DATA.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_office_control_custody import (
    SCHEMA,
    WORKER,
    NativeOfficeControlOriginal,
    validate_office_control_code,
    office_control_graph_contains,
)
from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PACKET_SCHEMA = "template-native-office-nested-original-packet-v1"


def retain_office_child(original: NativeOfficeControlOriginal, reader: SnapshotReader) -> dict[str, str]:
    """Export only retained DATA from an actual completed parent-held child."""
    producer = reader.native_producer_operation
    if producer is None:
        raise ValueError("Office packet retention requires its genuine live parent Source owner")
    producer.verify(reader, run_id=original.run_id, deadline=producer.deadline)
    original._read(original.observation_relative, reader)
    original.closure(reader, deadline=producer.deadline)
    body = {
        "schema_version": PACKET_SCHEMA,
        "specification": {
            "path": original.specification_relative,
            "sha256": hashlib.sha256(original.specification_bytes).hexdigest(),
        },
        "process": {"path": original.process_relative, "sha256": hashlib.sha256(original.process_bytes).hexdigest()},
        "observation": {
            "path": original.observation_relative,
            "sha256": original.artifact_hashes[original.observation_relative],
        },
        "closure": {"path": original.closure_relative, "sha256": original.artifact_hashes[original.closure_relative]},
        "artifact_hashes": dict(original.artifact_hashes),
    }
    return write_json(
        reader.root, reader.root / Path(original.specification_relative).parent / "parent-child-packet.json", body
    )


@dataclass(frozen=True)
class RetainedOfficeControl:
    """Authenticated observations under a reader role; no live-original key."""

    run_id: str
    scope: str
    kind: str
    control: str
    expected_exit: int
    original_deadline: float
    observed_completion: float
    specification_relative: str
    specification_bytes: bytes
    process_relative: str
    process_bytes: bytes
    closure_relative: str
    observation_relative: str
    command: tuple[str, ...]
    source_commit: str
    source_identity: str
    sdk_root: Path
    expected_code: MappingProxyType[str, str]
    artifact_hashes: MappingProxyType[str, str]
    packet_binding: dict[str, str]
    custodian: OfficeNestedReaderOperation

    def _read(self, relative: str, reader: SnapshotReader) -> ArtifactSnapshot:
        self.custodian.verify(reader)
        value = reader.read(relative)
        if self.artifact_hashes.get(relative) != value.sha256:
            raise ValueError("nested Office bytes changed from the externally authenticated parent graph")
        return value

    def graph_contains(self, selected: ArtifactSnapshot, reader: SnapshotReader, *, deadline: float) -> None:
        office_control_graph_contains(self, selected, reader, deadline=deadline)

    def closure(self, reader: SnapshotReader, *, deadline: float) -> dict[str, Any]:
        return validate_office_control_code(self, reader, deadline=deadline)


class OfficeNestedReaderOperation:
    """Exact Office reader anchored in the genuine external full-worker launch."""

    def __init__(self, reader: SnapshotReader, bindings: list[dict[str, str]], *, scope: str, deadline: float):
        if type(self) is not OfficeNestedReaderOperation or reader.native_control_operation is not None:
            raise ValueError("nested Office needs the genuine top-level external Original reader")
        operation = require_native_operation(reader)
        if (
            deadline != operation.deadline
            or scope not in operation.originals
            or not isinstance(bindings, list)
            or not 1 <= len(bindings) <= 1500
        ):
            raise ValueError("nested Office scope/clock/full retained roster differs")
        self.parent_reader, self.source, self.scope, self.deadline = reader, operation.source, scope, deadline
        self.bindings = tuple(dict(item) for item in bindings)
        self.originals: tuple[RetainedOfficeControl, ...] = ()
        self.verify(reader)
        self.originals = tuple(self._child(item) for item in self.bindings)
        if len({item.specification_relative for item in self.originals}) != len(self.originals):
            raise ValueError("nested Office roster repeats an actual child attempt")

    def verify(self, reader: SnapshotReader) -> None:
        remaining(self.deadline)
        operation = require_native_operation(self.parent_reader)
        if (
            operation.source is not self.source
            or operation.deadline != self.deadline
            or reader.root != self.source.bindings.current_root
        ):
            raise ValueError("nested Office lost its independently held Source/Original/clock")
        original = operation.originals.get(self.scope)
        if original is None:
            raise ValueError("nested Office lacks its exact full Original launch")
        native = self.parent_reader.read(original.native_execution_relative)
        raw = native.json_object()
        if native.sha256 != original.native_execution_sha256:
            raise ValueError("nested Office full execution differs from externally held Original")
        cohorts, capabilities = raw.get("office_diagram_cohorts"), raw.get("office_capability_cells")
        if not isinstance(cohorts, dict) or not isinstance(capabilities, list):
            raise ValueError("nested Office full Original lacks coupled mandatory rosters")
        allowed = [item for roster in cohorts.values() for item in roster] + capabilities
        if any(item not in allowed for item in self.bindings):
            raise ValueError("nested Office packet was not retained by the exact completed full Original")
        operation.verify(self.parent_reader)

    def _child(self, binding: dict[str, str]) -> RetainedOfficeControl:
        from infrastructure.reporting.native_format_acceptance_validation import _file
        from infrastructure.reporting.native_tool_replay import (
            authenticate_original_native_artifact,
            validate_native_tool_data,
            _stamp,
        )
        from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider

        self.verify(self.parent_reader)
        packet_file = _file(binding, self.parent_reader)
        authority = authenticate_original_native_artifact(
            binding,
            self.parent_reader,
            run_id=require_native_operation(self.parent_reader).originals[self.scope].run_id,
            required_sdk_modules=(
                "reporting/native_office_control_supervisor.py",
                "reporting/native_office_nested_custody.py",
            ),
        )
        packet = packet_file.json_object()
        if (
            set(packet) != {"schema_version", "specification", "process", "observation", "closure", "artifact_hashes"}
            or packet["schema_version"] != PACKET_SCHEMA
        ):
            raise ValueError("nested Office packet differs from its fixed Source fields")
        spec_file = _file(packet["specification"], self.parent_reader)
        process_file = _file(packet["process"], self.parent_reader)
        observation = _file(packet["observation"], self.parent_reader)
        closure = _file(packet["closure"], self.parent_reader)
        spec, process = spec_file.json_object(), process_file.json_object()
        parent_source = authority["source"]
        expected_source = {**parent_source, "scope": spec["scope"]}
        mirror, sdk = Path(parent_source["current_mirror"]["root"]), Path(parent_source["selected_sdk"]["package_root"])
        leaf = self.parent_reader.root / spec["directory"]
        code = spec["expected_exit"]
        if (
            spec["schema_version"] != SCHEMA
            or spec["source"] != expected_source
            or type(code) is not int
            or code not in (0, 1)
            or spec["run_id"] != parent_source["run_id"]
            or spec["caller_deadline_monotonic"] != authority["original"].original_deadline
            or not spec["original_deadline_monotonic"] <= spec["caller_deadline_monotonic"]
            or process.get("owner_pid") != authority["process"]["pid"]
            or process.get("purpose") != "office-original-child"
            or process.get("run_id") != spec["run_id"]
            or process.get("original_exit_code") != code
            or process.get("exit_code") != code
            or process.get("original_deadline_monotonic") != spec["original_deadline_monotonic"]
            or spec_file.path != leaf / "specification.json"
            or process_file.path != leaf / "office-original-child.json"
            or observation.path != leaf / "observation.json"
            or closure.path != leaf / "closure/receipt.json"
            or packet_file.path != leaf / "parent-child-packet.json"
        ):
            raise ValueError("nested Office Source/actual parent PID/prelaunch/OS/original clock differs")
        process_authority = authenticate_original_native_artifact(
            packet["process"],
            self.parent_reader,
            run_id=spec["run_id"],
            required_sdk_modules=("reporting/native_office_control_supervisor.py",),
        )
        if (
            process_authority["event"].content != process_file.content
            or process_authority["original"] is not authority["original"]
        ):
            raise ValueError("nested Office actual child ToolAPI belongs to another external full Original")
        native = _file(process["native_process_artifact"], self.parent_reader).json_object()
        implementation = _file(spec["implementation"], self.parent_reader)
        expected, current = implementation.json_object(), json.loads(self.source.bindings.expected_implementation_bytes)
        if (
            expected["files"] != current["files"]
            or native.get("launcher_preserved") is not True
            or native["nomination"]["resolved_path"] != expected["runtime_environment"]["python_executable"]
        ):
            raise ValueError("nested Office selected SDK/interpreter differs from actual admitted Source")
        provider = require_native_operation(self.parent_reader).pdfium_providers.get(self.scope)
        if type(provider) is not NativePDFiumProvider:
            raise ValueError("nested Office requires independent physical current provider nomination")
        provider.verify_current(deadline=self.deadline)
        if spec["pdfium_wheel_sha256"] != provider.wheel["sha256"]:
            raise ValueError("nested Office Original/current independently admitted provider wheel differs")
        provider_site = Path(spec["dependencies"]["pdfium_site"])
        hook = self.source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            tuple(provider_site / name for name in ("pypdfium2", "pypdfium2_raw")),
            mirror / spec["implementation"]["path"],
            implementation.sha256,
            mirror / spec["directory"] / "closure",
            tuple(spec["closure_identity"]),
            spec["original_deadline_monotonic"],
            required_worker_module=WORKER,
        )
        command = [
            native["nomination"]["path"],
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(mirror),
            "--specification",
            spec_file.relative,
            "--specification-sha256",
            spec_file.sha256,
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(spec["original_deadline_monotonic"]),
            "--run-id",
            spec["run_id"],
        ]
        dependencies = spec["dependencies"]
        if dependencies["mermaid_dependency_root"] is not None:
            for flag, field in (
                ("--mermaid-package-root", "package_root"),
                ("--mermaid-dependency-root", "mermaid_dependency_root"),
                ("--mermaid-node", "node_executable"),
                ("--mermaid-chrome", "chrome_executable"),
            ):
                command += [flag, dependencies[field]]
        if (
            process["command"] != command
            or native.get("command") != command
            or native.get("original_exit_code") != code
        ):
            raise ValueError("nested Office actual fixed bootstrap/argv/signed OS result differs")
        completion = _stamp(native["operation_end"])
        validate_native_tool_data(
            process,
            self.parent_reader,
            original_deadline=spec["original_deadline_monotonic"],
            original_completion=completion,
        )
        stdout = _file(
            {"path": process["raw_stdout"]["path"], "sha256": process["raw_stdout"]["sha256"]}, self.parent_reader
        ).content.decode("utf-8", errors="strict")
        seals = [
            line for line in stdout.splitlines() if line.startswith(("OFFICE_OBSERVATION_V1 ", "OFFICE_CLOSURE_V1 "))
        ]
        if seals != [
            f"OFFICE_OBSERVATION_V1 {spec_file.sha256} {observation.sha256} {spec['run_id']} {code}",
            f"OFFICE_CLOSURE_V1 {closure.sha256}",
        ]:
            raise ValueError("nested Office observation and Code lack actual parent-bound raw stdout seals")
        hashes = packet["artifact_hashes"]
        if not isinstance(hashes, dict) or len(hashes) > 20000:
            raise ValueError("nested Office retained child graph exceeds existing bound")
        total = 0
        for path, digest in hashes.items():
            selected = _file({"path": path, "sha256": digest}, self.parent_reader)
            if not selected.path.is_relative_to(leaf):
                raise ValueError("nested Office graph escaped its actual child attempt")
            total += len(selected.content)
            if total > 1024 * 1024 * 1024:
                raise ValueError("nested Office retained graph exceeds existing byte ceiling")
        expected_code = {
            str(sdk / name.removeprefix("infrastructure/")): digest
            for name, digest in current["files"].items()
            if name.startswith("infrastructure/") and name.endswith(".py")
        }
        expected_code.update(
            {
                str(provider_site / name): hashlib.sha256(content).hexdigest()
                for name, content in provider.members.items()
                if name.endswith(".py")
            }
        )
        record = RetainedOfficeControl(
            spec["run_id"],
            spec["scope"],
            spec["kind"],
            spec["control"],
            code,
            spec["original_deadline_monotonic"],
            completion,
            spec_file.relative,
            spec_file.content,
            process_file.relative,
            process_file.content,
            closure.relative,
            observation.relative,
            tuple(command),
            self.source.reference.commit,
            self.source.reference.source_identity,
            sdk,
            MappingProxyType(expected_code),
            MappingProxyType(dict(hashes)),
            dict(binding),
            self,
        )
        record.closure(self.parent_reader, deadline=self.deadline)
        return record

    def authenticate_artifact(
        self, binding: dict[str, Any], reader: SnapshotReader, *, run_id: str, required_sdk_modules: tuple[str, ...]
    ) -> dict[str, Any]:
        self.verify(reader)
        selected = reader.read(binding["path"])
        if selected.sha256 != binding["sha256"]:
            raise ValueError("nested Office selected artifact changed")
        matches = []
        for original in self.originals:
            if original.run_id == run_id and original.artifact_hashes.get(selected.relative) == selected.sha256:
                original.graph_contains(selected, reader, deadline=self.deadline)
                matches.append(original)
        if len(matches) != 1:
            raise ValueError("nested Office artifact needs one exact external parent/child graph")
        original = matches[0]
        closure = original.closure(reader, deadline=self.deadline)
        executed = {row["source_path"] for row in closure["executions"] if row["runs"]}
        if not {str(original.sdk_root / name) for name in required_sdk_modules} <= executed:
            raise ValueError("nested Office lacks actual admitted SDK child helper executions")
        process = original._read(original.process_relative, reader).json_object()
        native = reader.read(process["native_process_artifact"]["path"]).json_object()
        return {
            "operation": self,
            "original": original,
            "process": native,
            "closure": closure,
            "source": {"selected_sdk": {"package_root": str(original.sdk_root)}},
            "event": selected,
        }

    def admit_original_child(
        self,
        raw: dict[str, Any],
        control: str,
        original_pdf_sha256: str,
        code: int,
        *,
        reader: SnapshotReader,
        scope: str,
        kind: str,
        target: dict[str, Any],
    ) -> None:
        matches = [
            item
            for item in self.originals
            if item.control == control
            and item.scope == scope
            and item.kind == kind
            and item.expected_exit == code
            and json.loads(item.process_bytes) == raw
            and json.loads(item.specification_bytes)["target"] == target
        ]
        if len(matches) != 1:
            raise ValueError("nested Office case differs from actual external parent/child target")
        original = matches[0]
        authority = self.authenticate_artifact(
            {"path": original.observation_relative, "sha256": original.artifact_hashes[original.observation_relative]},
            reader,
            run_id=original.run_id,
            required_sdk_modules=(
                "reporting/native_office_diagram_controls.py",
                "reporting/native_office_diagram_positive.py",
                "reporting/native_office_diagram_census.py",
            ),
        )
        observation = authority["event"].json_object()
        if (
            observation["original_pdf_sha256"] != original_pdf_sha256
            or observation["oracle_exit_code"] != code
            or observation["target"] != target
        ):
            raise ValueError("nested Office Source/PDF/target/oracle completion differs")
