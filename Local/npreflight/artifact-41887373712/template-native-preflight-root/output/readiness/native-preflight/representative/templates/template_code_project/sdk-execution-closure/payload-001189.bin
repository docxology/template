"""Actual positive/refusal control under existing genuine Source outer owners.

A failed instrumented process retains direct OS/cleanup DATA. It never receives
an accepted ToolAPI token. Original admission comes from the exact enclosing
Source/Code worker and its externally held complete native-execution binding.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_loader_build import compile_native_loader
from infrastructure.reporting.native_loader_observation import NativeLoaderObservation
from infrastructure.reporting.native_loader_qualification import (
    qualify_native_loader_tool,
    replay_native_loader_qualification,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-source-loader-persistent-rx-control-v1"
SOURCE = "infrastructure/reporting/native_loader_assets/persistent_rx_drift.c"
FLAGS = ("-std=c11", "-O0", "-fno-inline", "-Wall", "-Wextra", "-Werror")
_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "scope",
        "source_binding",
        "owner_pid",
        "source_fixture",
        "compiler_tool",
        "executable",
        "compiled_fixture",
        "positive_qualification",
        "baseline_drift_tool",
        "refused_process",
        "direct_process_outcome",
        "actual_signed_exit",
        "scope_limit",
    }
)
_OUTCOME_FIELDS = ("pid", "owner_pid", "command", "original_exit_code", "timed_out", "diagnostics")
_READY = b"persistent-rx-ready\n"
_DRIFT = _READY + b"persistent-rx-drift\n"
_CLEAN = _READY + b"persistent-rx-clean\n"
_DRIFT_DIAGNOSTICS = (
    ["ValueError: consumer persistent RX byte drift differs from its original backing body"],
    ["ValueError: consumer persistent RX byte drift differs from original mapped-code commitment"],
)


def _bound(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("loader control requires an exact retained artifact binding")
    if not all(isinstance(binding[key], str) for key in binding):
        raise ValueError("loader control artifact path/digest is not text")
    selected = reader.read(binding["path"])
    if selected.sha256 != binding["sha256"]:
        raise ValueError("loader control retained artifact changed")
    return selected


def _streams(raw: dict[str, Any], reader: SnapshotReader, stdout: bytes) -> None:
    for channel, expected in (("stdout", stdout), ("stderr", b"")):
        stream = raw["raw_" + channel]
        path = Path(stream["path"])
        relative = path.relative_to(reader.root).as_posix() if path.is_absolute() else path.as_posix()
        held = _bound({"path": relative, "sha256": stream["sha256"]}, reader)
        if held.content != expected or stream["bytes"] != len(expected):
            raise ValueError("loader control differs from its complete actual trigger/output stream")


def _refusal(raw: dict[str, Any], *, owner_pid: int, command: list[str], caller_deadline: float) -> None:
    cleanup = raw.get("cleanup", {})
    if (
        raw.get("command") != command
        or raw.get("owner_pid") != owner_pid
        or type(raw.get("pid")) is not int
        or raw["pid"] <= 0
        or raw.get("original_exit_code") != 125
        or raw.get("accepted") is not False
        or raw.get("timed_out") is not False
        or raw.get("schema_version") != "template-original-native-loader-tool-process-v3"
        or not raw["operation_begin"]["monotonic"]
        < raw["operation_end"]["monotonic"]
        < raw["original_deadline_monotonic"]
        or not raw["original_deadline_monotonic"] <= caller_deadline
        or raw.get("diagnostics") not in _DRIFT_DIAGNOSTICS
        or cleanup.get("guardian_armed") is not True
        or cleanup.get("guardian_finished") is not True
        or cleanup.get("guardian_original_exit_code") != 0
        or cleanup.get("root_reaped") is not True
        or cleanup.get("final_token_sweep_matched_pids") != []
        or "loader_lifecycle" in raw
    ):
        raise ValueError(
            "actual negative loader control lacks intended byte-drift refusal and signed OS/cleanup custody"
        )


def observe_loader_persistent_rx_control(runtime: CitationRuntime, scope: str) -> dict[str, str]:
    """Called once by the real original/current outer Source worker, never DATA."""
    owner = current_native_producer_operation()
    if (
        not sys.platform.startswith("linux")
        or owner is None
        or owner.run_id != runtime.run_id
        or owner.deadline != runtime.deadline
    ):
        raise ValueError("real loader control needs the genuine Source outer owner and original clock")
    if not runtime.directory.is_relative_to(owner.stage_scope_directory(scope)):
        raise ValueError("real loader control belongs to another owner's nominated scope directory")
    reader = SnapshotReader(runtime.root, native_producer_operation=owner)
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    original = owner.source.current_source_reader.read(SOURCE)
    if original.content != owner.source.reference.read(SOURCE):
        raise ValueError("real loader negative fixture differs from independently held exact Source")
    source = runtime.freeze("persistent-rx-control.c", original.content)
    executable = runtime.directory / "persistent-rx-control"
    runtime.tool(
        "cc", [*FLAGS, str(source), "-o", str(executable), "-ldl"], "loader-control-compilation", input_paths=(source,)
    )
    compiler_binding = runtime.tools[-1]
    before = file_observation(executable)
    held_executable = runtime.freeze("persistent-rx-control-elf.input", runtime.read(executable))
    compiled_fixture = reader.read(held_executable.relative_to(runtime.root).as_posix())
    if compiled_fixture.sha256 != before["sha256"] or len(compiled_fixture.content) != before["bytes"]:
        raise ValueError("actual fixed fixture compiler output changed before Source byte retention")
    compiler = CitationRuntime(
        runtime.root,
        runtime.directory / "auditor-build",
        env=runtime.env,
        deadline=runtime.deadline,
        run_id=runtime.run_id,
    )
    compiled = compile_native_loader(compiler)
    clean, positive, _ = qualify_native_loader_tool(
        runtime, str(executable), ["clean"], "loader-control-clean", input_paths=(source,), compiled=compiled
    )
    baseline = runtime.tool(str(executable), ["drift"], "baseline-loader-control-drift", input_paths=(source,))
    baseline_binding = runtime.tools[-1]
    _streams(clean, reader, _CLEAN)
    _streams(baseline, reader, _DRIFT)
    directory = compiled.directory / "callbacks-persistent-rx"
    create_private_native_directory(runtime.root, directory)
    deadline = min(runtime.deadline, time.monotonic() + 120.0)
    observer = NativeLoaderObservation(compiled, directory, purpose="loader-control-drift", deadline=deadline)
    if before != file_observation(executable):
        raise ValueError("real clean/drift fixture executions changed the actual Source compiler output")
    outcomes: list[dict[str, Any]] = []
    result = run_native_tool_process(
        runtime.directory,
        str(executable),
        ["drift"],
        cwd=runtime.directory,
        env=runtime.env,
        deadline=deadline,
        purpose="loader-control-drift",
        loader=observer,
        observed_processes=outcomes,
    )
    _refusal(result, owner_pid=owner.owner_pid, command=[str(executable), "drift"], caller_deadline=runtime.deadline)
    if outcomes != [{key: result[key] for key in _OUTCOME_FIELDS}]:
        raise ValueError("negative control lost the independently reaped supervisor OS outcome sink")
    if before != file_observation(executable):
        raise ValueError("persistent RX control modified its physical executable instead of private mapped memory")
    process = reader.read(
        (runtime.directory / "loader-control-drift.native-process.json").relative_to(runtime.root).as_posix()
    )
    _streams(result, reader, _READY)
    if process.json_object() != result:
        raise ValueError("real loader drift refusal lacks its exact original process bytes/trigger marker")
    # No _retain_actual_tool call occurs for this failed child. Its finite
    # refusal DATA is admitted only through the complete external outer worker.
    value = {
        "schema_version": SCHEMA,
        "run_id": runtime.run_id,
        "scope": scope,
        "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
        "owner_pid": owner.owner_pid,
        "source_fixture": {"path": SOURCE, "sha256": original.sha256},
        "compiler_tool": compiler_binding,
        "executable": before,
        "compiled_fixture": {"path": compiled_fixture.relative, "sha256": compiled_fixture.sha256},
        "positive_qualification": positive,
        "baseline_drift_tool": baseline_binding,
        "refused_process": {"path": process.relative, "sha256": process.sha256},
        "direct_process_outcome": outcomes[0],
        "actual_signed_exit": result["original_exit_code"],
        "scope_limit": "persistent-private-rx-drift-at-actual-loader-callback-boundary",
    }
    binding = write_json(runtime.root, runtime.directory / "persistent-rx-control.json", value)
    if not reader.unchanged():
        raise ValueError("real loader control Source/actual execution evidence changed")
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    return binding


def replay_loader_persistent_rx_control(
    binding: dict[str, str], native_execution: ArtifactSnapshot, reader: SnapshotReader, *, scope: str, run_id: str
) -> dict[str, Any]:
    """Require exact complete outer Original; failed child DATA grants no token."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool

    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    if original is None or original.run_id != run_id or native_execution.sha256 != original.native_execution_sha256:
        raise ValueError("loader refusal requires the genuine externally held complete original Source worker")
    outer = native_execution.json_object()
    if outer.get("loader_persistent_rx_control") != binding:
        raise ValueError("loader refusal is not this actual Source outer worker's selected original control")
    raw = _bound(binding, reader).json_object()
    source = operation.source.current_source_reader.read(SOURCE)
    if (
        set(raw) != _FIELDS
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
        or raw["scope"] != scope
        or raw["owner_pid"] != outer["pid"]
        or raw["source_binding"] != [operation.source.reference.commit, operation.source.reference.source_identity]
        or raw["source_fixture"] != {"path": SOURCE, "sha256": source.sha256}
        or source.content != operation.source.reference.read(SOURCE)
        or raw["scope_limit"] != "persistent-private-rx-drift-at-actual-loader-callback-boundary"
    ):
        raise ValueError("loader refusal differs from actual outer Source/Code/run/fixture/boundary custody")
    required = (
        "reporting/native_loader_negative_control.py",
        "reporting/native_tool_process.py",
        "reporting/native_loader_helper_memory.py",
    )
    compiler = _bound(raw["compiler_tool"], reader).json_object()
    baseline = _bound(raw["baseline_drift_tool"], reader).json_object()
    for name, tool in (("compiler_tool", compiler), ("baseline_drift_tool", baseline)):
        validate_original_native_tool(raw[name], tool, reader, run_id=run_id, required_sdk_modules=required)
        if tool["owner_pid"] != raw["owner_pid"] or tool["original_exit_code"] != 0:
            raise ValueError("loader control's accepted fixture tools belong to another Source owner or OS result")
    selected = compiler["consumed_input_artifacts"]
    if len(selected) != 1 or _bound(selected[0]["artifact"], reader).content != source.content:
        raise ValueError("negative control actual compiler did not consume the exact Source C fixture")
    if compiler["command"] != [
        compiler["executable"],
        *FLAGS,
        selected[0]["observation"]["path"],
        "-o",
        raw["executable"]["path"],
        "-ldl",
    ]:
        raise ValueError("negative control actual compiler differs from fixed Source argv/output")
    compiled_fixture = _bound(raw["compiled_fixture"], reader)
    if (
        compiled_fixture.sha256 != raw["executable"]["sha256"]
        or len(compiled_fixture.content) != raw["executable"]["bytes"]
    ):
        raise ValueError("negative control actual native executions changed their retained fixed compiler output")
    positive = replay_native_loader_qualification(raw["positive_qualification"], reader, run_id=run_id)
    clean = _bound(positive["observed_tool"], reader).json_object()
    if (
        positive["purpose"] != "loader-control-clean"
        or positive["tool"] != raw["executable"]["path"]
        or clean["command"] != [raw["executable"]["path"], "clean"]
        or clean["owner_pid"] != raw["owner_pid"]
        or clean["executable_sha256"] != raw["executable"]["sha256"]
        or len(positive["selected_inputs"]) != 1
        or _bound(positive["selected_inputs"][0], reader).content != source.content
    ):
        raise ValueError("negative control's genuine clean pair belongs to another original Source executable")
    _streams(clean, reader, _CLEAN)
    _streams(baseline, reader, _DRIFT)
    if (
        baseline["command"] != [raw["executable"]["path"], "drift"]
        or baseline["executable_sha256"] != raw["executable"]["sha256"]
    ):
        raise ValueError("negative control original baseline belongs to another actual executable/argument body")
    if (
        len(baseline["consumed_input_artifacts"]) != 1
        or _bound(baseline["consumed_input_artifacts"][0]["artifact"], reader).content != source.content
    ):
        raise ValueError("negative control original drift baseline omits the exact Source fixture input")
    refused = _bound(raw["refused_process"], reader).json_object()
    _refusal(
        refused, owner_pid=raw["owner_pid"], command=baseline["command"], caller_deadline=original.original_deadline
    )
    _streams(refused, reader, _READY)
    if (
        refused["executable_observation_before"] != baseline["executable_observation_before"]
        or refused["executable_observation_after"] != refused["executable_observation_before"]
        or refused["executable_identity_before"] != refused["executable_identity_after"]
        or raw["actual_signed_exit"] != refused["original_exit_code"]
        or raw["direct_process_outcome"] != {key: refused[key] for key in _OUTCOME_FIELDS}
        or refused["executable_observation_before"]["sha256"] != raw["executable"]["sha256"]
    ):
        raise ValueError("negative mapped-memory drift changed its physical executable or original signed OS result")
    remaining(operation.deadline)
    operation.verify(reader)
    return raw


def reproduce_loader_persistent_rx_control(
    binding: dict[str, str],
    native_execution: ArtifactSnapshot,
    reader: SnapshotReader,
    current: CitationRuntime,
    *,
    scope: str,
    original_run_id: str,
    current_source: NativeSourceContext,
) -> dict[str, str]:
    """Execute the same fixed Source mutation anew under the actual reader owner."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation

    operation = require_native_operation(reader)
    original = replay_loader_persistent_rx_control(
        binding, native_execution, reader, scope=scope, run_id=original_run_id
    )
    owner = current_native_producer_operation()
    if (
        not isinstance(current_source, NativeSourceContext)
        or owner is None
        or owner.source is not current_source
        or current.root != current_source.bindings.current_root
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_commit != operation.source.bindings.expected_commit
        or current_source.bindings.expected_source_identity != operation.source.bindings.expected_source_identity
        or current_source.bindings.selected_sdk_package_root != operation.source.bindings.selected_sdk_package_root
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or current_source.bindings.run_id in (operation.source.bindings.run_id, original_run_id)
        or owner.deadline != operation.deadline
        or current.deadline != operation.deadline
        or current.run_id != owner.run_id
        or current.run_id != current_source.bindings.run_id
    ):
        raise ValueError("fresh negative control needs independently nominated Current Source and its actual owner")
    for protected in (
        operation.source.bindings.current_root,
        operation.source.reference.root,
        operation.source.bindings.selected_sdk_package_root,
    ):
        if current.root.is_relative_to(protected) or protected.is_relative_to(current.root):
            raise ValueError("fresh loader control Current root overlaps held Original, Source or installed SDK")
    if not current.directory.is_relative_to(owner.stage_scope_directory(scope)):
        raise ValueError("fresh loader control is outside its actual paired Current owner scope directory")
    fresh_reader = SnapshotReader(current.root, native_producer_operation=owner)
    owner.verify(fresh_reader, run_id=current.run_id, deadline=operation.deadline)
    fresh = observe_loader_persistent_rx_control(current, scope)
    value = _bound(fresh, fresh_reader).json_object()
    # Compiled native addresses/PIDs/paths can relocate. Both real controls must
    # establish the same exact Source mutation, successful clean/raw baseline,
    # persistent-memory refusal, direct signed OS result and closed guardian.
    for field in ("schema_version", "scope", "source_binding", "source_fixture", "actual_signed_exit", "scope_limit"):
        if value[field] != original[field]:
            raise ValueError("fresh actual negative control changed the original Source mutation or refusal effect")
    owner.verify(fresh_reader, run_id=current.run_id, deadline=operation.deadline)
    operation.verify(reader)
    return fresh
