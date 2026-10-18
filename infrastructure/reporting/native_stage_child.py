"""Prepare one fixed Source stage child only inside its actual native owner."""

from __future__ import annotations

import json
import math
import os
import platform
import secrets
import stat
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_environment,
)
from infrastructure.reporting.native_format_joint_source import source_environment
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
from infrastructure.reporting.native_stage_child_contracts import (
    PACKET_SCHEMA,
    PURPOSE,
    SCHEMA,
    WORKER,
    audit_roots,
    binding,
    validate_request,
    validate_specification,
)
from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_stage_child_scope import (
    current_native_stage_directory as current_native_stage_directory,
    retain_native_stage_artifact as retain_native_stage_artifact,
)

_FACTORY_KEY = object()
_PREPARED: dict[int, NativeStageChildPreparation] = {}


def directory_identity(path: Path) -> tuple[int, int]:
    """Observe a real confined directory, refusing symbolic path components."""
    observed = path.lstat()
    if not stat.S_ISDIR(observed.st_mode) or path.absolute() != path.resolve(strict=True):
        raise ValueError("native stage child lost a parent-held real directory")
    return observed.st_dev, observed.st_ino


@dataclass(frozen=True)
class NativeStageChildPreparation:
    """Live factory token; serialized specification and packets remain DATA."""

    _key: object
    owner: NativeProducerOperation
    source: NativeSourceContext
    scope: str
    directory: Path
    command: tuple[str, ...]
    environment: Mapping[str, str]
    cwd: Path
    request: ArtifactSnapshot
    specification: ArtifactSnapshot
    implementation: ArtifactSnapshot
    closure: Path
    deadline: float
    original_request: ArtifactSnapshot

    def verify_owner(self, reader: SnapshotReader) -> None:
        owner, source, scope, deadline = self.owner, self.source, self.scope, self.deadline

        def check_factory() -> None:
            if (
                self._key is not _FACTORY_KEY
                or _PREPARED.get(id(self)) is not self
                or self.owner is not owner
                or self.source is not source
                or self.scope != scope
                or self.deadline != deadline
                or current_native_producer_operation() is not owner
                or owner.source is not source
                or reader.root != source.bindings.current_root
            ):
                raise ValueError("native stage requires its actual fixed factory and live enclosing Source owner")

        check_factory()
        with owner._verification_guard(reader, run_id=owner.run_id, deadline=deadline):
            check_factory()
            try:
                self._verify_owner_data(reader)
            finally:
                check_factory()
        remaining(deadline)

    def _verify_owner_data(self, reader: SnapshotReader) -> None:
        """Compare held factory DATA only inside the caller's fresh Source guard."""
        spec = self.specification.json_object()
        validate_specification(spec)
        for held in (self.request, self.specification, self.implementation, self.original_request):
            current = reader.read(held.relative)
            if current.sha256 != held.sha256 or current.content != held.content:
                raise ValueError("native stage parent request/specification/implementation changed")
        if (
            directory_identity(self.directory) != tuple(spec["directory_identity"])
            or directory_identity(self.closure) != tuple(spec["closure_identity"])
            or directory_identity(self.directory / "bytecode") != tuple(spec["prefix_identity"])
            or spec["source"] != json.loads(self.source._descriptor_data(self.scope, deadline=self.deadline))
            or spec["parent_pid"] != self.owner.owner_pid
            or spec["parent_directory"]
            != self.owner._stage_scope_directory_data(self.scope).relative_to(reader.root).as_posix()
            or spec["parent_deadline_monotonic"] != self.owner.deadline
            or spec["run_id"] != self.owner.run_id
            or spec["request"] != binding(self.request)
            or self.request.content != self.original_request.content
        ):
            raise ValueError("native stage parent Source/physical-directory/run custody differs")

    def verify_tool_launch(
        self,
        root: Path,
        directory: Path,
        name: str,
        args: list[str] | tuple[str, ...],
        env: Mapping[str, str],
        deadline: float,
        purpose: str,
    ) -> Path:
        """Called before actual ToolAPI Popen; no generic cwd or role override."""
        reader = SnapshotReader(root, native_producer_operation=self.owner)
        self.verify_owner(reader)
        if (
            root != self.source.bindings.current_root
            or directory != self.directory
            or name != self.command[0]
            or purpose != PURPOSE
            or (name, *args) != self.command
            or dict(env) != dict(self.environment)
            or deadline != self.deadline
            or any(self.closure.iterdir())
            or any((self.directory / "bytecode").iterdir())
            or (self.directory / "result.json").exists()
            or (self.directory / "observation.json").exists()
        ):
            raise ValueError("native stage ToolAPI launch differs from its one fresh fixed parent preparation")
        if not reader.unchanged():
            raise ValueError("native stage launch inputs changed before actual ToolAPI Popen")
        return self.cwd

    def verify_closed_packet(
        self,
        packet: dict[str, Any],
        process_binding: dict[str, str],
        reader: SnapshotReader,
    ) -> None:
        """Recheck all packet bytes after genuine parent ToolAPI authentication."""
        from infrastructure.reporting.native_stage_child_custody import validate_stage_child_packet

        self.verify_owner(reader)
        process = reader.read(process_binding["path"])
        self.owner.validate_tool(process_binding, process.json_object(), reader, run_id=self.owner.run_id)
        validate_stage_child_packet(
            self.source,
            packet,
            reader,
            process=process.json_object(),
            source_record=self.specification.json_object()["source"],
            parent_pid=self.owner.owner_pid,
            original_deadline=self.owner.deadline,
            parent_directory=self.owner.stage_scope_directory(self.scope).relative_to(reader.root).as_posix(),
            deadline=self.deadline,
        )
        if (
            packet["process_artifact"] != process_binding
            or packet["specification_artifact"] != binding(self.specification)
            or packet["artifact"]["path"] != (self.directory / "observation.json").relative_to(reader.root).as_posix()
        ):
            raise ValueError("native stage closed packet belongs to another actual factory attempt")

    def observe(self, result: dict[str, Any]) -> dict[str, str]:
        """Close only an actually retained ToolAPI event, never caller status DATA."""
        reader = SnapshotReader(self.source.bindings.current_root, native_producer_operation=self.owner)
        self.verify_owner(reader)
        process_binding = result.get("artifact", result)
        if not isinstance(process_binding, dict) or set(process_binding) != {"path", "sha256"}:
            raise ValueError("native stage observation needs its actual ToolAPI artifact binding")
        process = reader.read(process_binding["path"])
        self.owner.validate_tool(process_binding, process.json_object(), reader, run_id=self.owner.run_id)
        packet = {
            "schema_version": PACKET_SCHEMA,
            "process_artifact": process_binding,
            "specification_artifact": binding(self.specification),
            "artifact": binding(reader.read((self.directory / "observation.json").relative_to(reader.root).as_posix())),
            "closure_artifact": binding(
                reader.read((self.closure / "receipt.json").relative_to(reader.root).as_posix())
            ),
            "original_exit_code": process.json_object()["original_exit_code"],
        }
        self.verify_closed_packet(packet, process_binding, reader)
        if not reader.unchanged():
            raise ValueError("native stage child bytes changed before closing actual parent observation")
        retained = write_json(reader.root, self.directory / "stage-child.json", packet)
        self.owner._retain_actual_stage_child(self, process_binding, retained)
        _PREPARED.pop(id(self))
        return retained


def prepare_native_stage_child(
    source: NativeSourceContext,
    scope: str,
    request_binding: ArtifactSnapshot,
    directory: Path,
    *,
    deadline: float,
    environment: Mapping[str, str] | None = None,
) -> NativeStageChildPreparation:
    """Prepare actual Source inputs before the real parent launches one child."""
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or type(deadline) not in (float, int) or not math.isfinite(deadline):
        raise ValueError("native stage factory requires the actual live Source owner and original finite deadline")
    root = source.bindings.current_root
    reader = SnapshotReader(root, native_producer_operation=owner)
    # All preparation is fixed synchronous DATA work. The actual Source
    # correspondence closes before the factory enters the live registry.
    with owner._verification_guard(reader, run_id=owner.run_id, deadline=deadline):
        prepared = _prepare_native_stage_child_data(
            source,
            scope,
            request_binding,
            directory,
            deadline=deadline,
            environment=environment,
            owner=owner,
            reader=reader,
        )
        prepared._verify_owner_data(reader)
        if not reader.unchanged():
            raise ValueError("native stage fixed prelaunch Source/request changed during preparation")
    remaining(deadline)
    _PREPARED[id(prepared)] = prepared
    return prepared


def _prepare_native_stage_child_data(
    source: NativeSourceContext,
    scope: str,
    request_binding: ArtifactSnapshot,
    directory: Path,
    *,
    deadline: float,
    environment: Mapping[str, str] | None,
    owner: NativeProducerOperation,
    reader: SnapshotReader,
) -> NativeStageChildPreparation:
    """Build unpublished fixed DATA inside the caller's fresh Source guard."""
    root = source.bindings.current_root
    held = reader.read(request_binding.relative)
    if (
        held.path != request_binding.path
        or held.content != request_binding.content
        or held.sha256 != request_binding.sha256
    ):
        raise ValueError("native stage factory request is not the actual parent's held SnapshotReader artifact")
    payload, protocol, script_sha = validate_request(source, scope, held, deadline=deadline)
    directory = directory.absolute()
    parent_directory = owner._stage_scope_directory_data(scope)
    if (
        not directory.is_relative_to(parent_directory / "native-stage")
        or len(directory.relative_to(parent_directory / "native-stage").parts) != 3
    ):
        raise ValueError("native stage factory is confined to its fixed runtime evidence lane")
    directory_identity(directory)
    if not held.path.is_relative_to(directory):
        raise ValueError("native stage factory request belongs to another parent attempt")
    nonce = secrets.token_hex(16)
    leaf = directory / ("child-" + nonce)
    create_private_native_directory(root, leaf)
    for child in (leaf / "closure", leaf / "bytecode"):
        create_private_native_directory(root, child)
    atomic_write_bytes_confined(root, leaf / "request.json", held.content, mode=0o600)
    atomic_write_bytes_confined(
        root, leaf / "implementation.json", source.bindings.expected_implementation_bytes, mode=0o600
    )
    request = reader.read((leaf / "request.json").relative_to(root).as_posix())
    implementation = reader.read((leaf / "implementation.json").relative_to(root).as_posix())
    spec = {
        "schema_version": SCHEMA,
        "scope": scope,
        "run_id": owner.run_id,
        "pipeline_run_id": payload["run_id"],
        "stage_key": payload["stage_key"],
        "nonce": nonce,
        "directory": leaf.relative_to(root).as_posix(),
        "source": json.loads(source._descriptor_data(scope, deadline=deadline)),
        "implementation": binding(implementation),
        "request": binding(request),
        "request_digest": canonical_digest(payload),
        "protocol": protocol,
        "script": {"path": Path(payload["argv"][0]).relative_to(root).as_posix(), "sha256": script_sha},
        "cwd": payload["cwd"],
        "parent_pid": os.getpid(),
        "parent_directory": parent_directory.relative_to(root).as_posix(),
        "parent_platform": platform.system(),
        "deadline_monotonic": float(deadline),
        "parent_deadline_monotonic": owner.deadline,
        "closure_identity": list(directory_identity(leaf / "closure")),
        "prefix_identity": list(directory_identity(leaf / "bytecode")),
        "directory_identity": list(directory_identity(leaf)),
        "source_audit_roots": [
            str(path) for path in audit_roots(root, source.bindings.selected_sdk_package_root, scope)
        ],
    }
    validate_specification(spec)
    write_json(root, leaf / "specification.json", spec)
    specification = reader.read((leaf / "specification.json").relative_to(root).as_posix())
    runtime = json.loads(implementation.content)["runtime_environment"]
    interpreter = (
        Path(payload["runtime_binding"]["executable"]) if protocol == "analysis" else Path(sys.executable).absolute()
    )
    if str(interpreter.resolve(strict=True)) != runtime.get("python_executable"):
        raise ValueError("native stage selected interpreter differs from the independently admitted SDK runtime")
    hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
    bootstrap = format_selected_sdk_native_bootstrap(
        hook,
        source.bindings.selected_sdk_package_root,
        audit_roots(root, source.bindings.selected_sdk_package_root, scope)[1:],
        implementation.path,
        implementation.sha256,
        leaf / "closure",
        tuple(spec["closure_identity"]),
        deadline,
        required_worker_module=WORKER,
    )
    command = (
        str(interpreter),
        "-I",
        "-c",
        bootstrap,
        "--root",
        str(root),
        "--specification",
        specification.relative,
        "--specification-sha256",
        specification.sha256,
        "--implementation-sha256",
        implementation.sha256,
        "--deadline",
        repr(float(deadline)),
        "--run-id",
        owner.run_id,
    )
    selected_env = native_environment(root, interpreter, leaf) if environment is None else dict(environment)
    if any(
        not isinstance(key, str) or not isinstance(value, str) or "\0" in key + value
        for key, value in selected_env.items()
    ):
        raise ValueError("native stage factory accepts only the actual resolved Source environment DATA")
    selected_env.update(source_environment(source))
    selected_env["PYTHONPYCACHEPREFIX"] = str(leaf / "bytecode")
    if payload.get("stage_admission") is not None:
        for key, name in (
            ("run_id", "PIPELINE_RUN_ID"),
            ("stage_key", "PIPELINE_STAGE_KEY"),
            ("plan_digest", "PIPELINE_PLAN_DIGEST"),
        ):
            if selected_env.get(name) != payload[key]:
                raise ValueError("native stage actual Source resolver environment differs from stage admission")
    prepared = NativeStageChildPreparation(
        _FACTORY_KEY,
        owner,
        source,
        scope,
        leaf,
        command,
        MappingProxyType(selected_env),
        Path(payload["cwd"]),
        request,
        specification,
        implementation,
        leaf / "closure",
        float(deadline),
        held,
    )
    return prepared
