"""Portable native tool readback authenticated by live original launch custody.

Producer paths are labels. Retained DATA cannot mint NativeOriginalLaunch or
NativeReaderOperation; the caller supplies the independently held capability.
"""

from __future__ import annotations

import math
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_EXECUTIONS
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_joint_source import (
    NativeOriginalLaunch,
    require_native_operation,
    validate_original_joint_launch,
    validate_retained_sdk_closure,
)
from infrastructure.reporting.native_tool_process import MAX_STREAM_BYTES, SCHEMA
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)


def _binding(value: object, reader: SnapshotReader, *, allow_empty: bool = False) -> ArtifactSnapshot:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("native original tool requires an exact closed retained artifact binding")
    observed = reader.read(value["path"])
    if observed.sha256 != value["sha256"] or (not allow_empty and not observed.content):
        raise ValueError("native original tool retained artifact bytes differ")
    return observed


def _original_graph_contains(
    selected: ArtifactSnapshot,
    original: NativeOriginalLaunch,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> None:
    """Authenticate exact tool membership through the externally pinned execution.

    The only authority is the live external original capability. Traversing its
    exact retained hash closure produces DATA membership, never a capability.
    No original filesystem/cache/native executable path is opened.
    """
    root = reader.read(original.native_execution_relative)
    if root.sha256 != original.native_execution_sha256:
        raise ValueError("native tool enclosing execution differs from external original custody")
    seen: set[str] = set()
    pending: list[object] = [root.json_object()]
    count = 0
    while pending:
        remaining(deadline)
        count += 1
        if count > MAX_EXECUTIONS:
            raise ValueError("native original tool retained membership exceeds its finite source bound")
        value = pending.pop()
        if isinstance(value, dict):
            relative, digest = value.get("path"), value.get("sha256")
            if (
                isinstance(relative, str)
                and isinstance(digest, str)
                and not Path(relative).is_absolute()
                and ".." not in Path(relative).parts
                and "\\" not in relative
                and "\0" not in relative
            ):
                observed = reader.read(relative)
                if observed.sha256 != digest:
                    raise ValueError("native original execution artifact closure changed")
                if observed.relative == selected.relative:
                    if observed.sha256 != selected.sha256:
                        raise ValueError("native original tool differs from its authenticated closure")
                    return
                if relative.endswith(".json") and relative not in seen:
                    seen.add(relative)
                    pending.append(observed.json_object())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    raise ValueError("native tool is absent from externally authenticated original execution membership")


def _finite(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("native original tool clock value is not finite")
    return float(value)


def _stamp(value: object) -> float:
    if not isinstance(value, dict) or set(value) != {"utc", "monotonic"}:
        raise ValueError("native original tool lacks an ordered clock observation")
    number, utc = value["monotonic"], value["utc"]
    if type(number) not in (int, float) or not math.isfinite(number) or not isinstance(utc, str):
        raise ValueError("native original tool clock observation is invalid")
    moment = datetime.fromisoformat(utc)
    if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
        raise ValueError("native original tool lacks a genuine UTC timestamp label")
    return float(number)


def authenticate_original_native_artifact(
    binding: object,
    reader: SnapshotReader,
    *,
    run_id: str,
    required_sdk_modules: tuple[str, ...],
) -> dict[str, Any]:
    """Bind native event DATA to live external source/process/Code authority.

    This also serves tool-free inline native observers. None of the returned
    live objects is constructed from producer JSON; they came from the reader's
    independently admitted original custodian. Returned dictionaries remain DATA.
    """
    control = reader.native_control_operation
    if control is not None:
        from infrastructure.reporting.native_office_control_custody import (
            OfficeControlReaderOperation,
        )

        if not isinstance(control, OfficeControlReaderOperation):
            raise ValueError("native control artifact requires its genuine typed original Office custodian")
        if not isinstance(binding, dict):
            raise ValueError("native original control artifact binding must be an exact mapping")
        return control.authenticate_artifact(binding, reader, run_id=run_id, required_sdk_modules=required_sdk_modules)
    operation = require_native_operation(reader)
    selected = _binding(binding, reader)
    originals = [
        item
        for item in operation.originals.values()
        if item.run_id == run_id and Path(selected.relative).is_relative_to(Path(item.specification_relative).parent)
    ]
    if len(originals) != 1 or not isinstance(originals[0], NativeOriginalLaunch):
        raise ValueError("native tool needs exactly one externally held original launch capability")
    original = originals[0]
    specification = reader.read(original.specification_relative)
    process = reader.read(original.process_relative)
    closure = reader.read(original.closure_relative)
    command, source = validate_original_joint_launch(
        specification.json_object(), specification, process, closure, reader, operation
    )
    if tuple(command) != original.command:
        raise ValueError("native tool original selected SDK command differs")
    validate_retained_sdk_closure(closure, specification.json_object(), source, reader, operation)
    selected_sdk = Path(source["selected_sdk"]["package_root"])
    if any(
        not isinstance(name, str)
        or Path(name).is_absolute()
        or ".." in Path(name).parts
        or not name.endswith(".py")
        or "\\" in name
        or "\0" in name
        for name in required_sdk_modules
    ):
        raise ValueError("original native SDK event requires canonical relative Source module names")
    expected_helpers = {str(selected_sdk / name) for name in required_sdk_modules}
    executed = {row["source_path"] for row in closure.json_object()["executions"] if row["runs"]}
    if not expected_helpers <= executed:
        raise ValueError("native tool lacks actual original admitted process-helper code execution")
    _original_graph_contains(selected, original, reader, deadline=operation.deadline)

    native = reader.read(original.native_execution_relative).json_object()
    original_process = process.json_object()
    from infrastructure.reporting.native_format_process_custody import (
        validate_native_worker_process,
    )

    validate_native_worker_process(
        specification.json_object(),
        original_process,
        native,
        hosted_origin=reader.hosted_origin,
    )
    if (
        type(original_process.get("original_exit_code")) is not int
        or original_process["original_exit_code"] not in {0, 75}
        or original_process.get("exit_code") != original_process["original_exit_code"]
        or native.get("execution_exit_code") != original_process["original_exit_code"]
        or original_process.get("timed_out") is not False
        or original_process.get("custody_refused") is not False
    ):
        raise ValueError("native original event lacks its actual enclosing supervisor OS custody")
    remaining(operation.deadline)
    return {
        "operation": operation,
        "original": original,
        "process": original_process,
        "closure": closure.json_object(),
        "source": source,
        "event": selected,
    }


def validate_original_native_tool(
    binding: object,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    required_sdk_modules: tuple[str, ...] = (
        "reporting/native_tool_process.py",
        "reporting/native_format_acceptance_checks.py",
    ),
) -> None:
    """Verify actual original PID, signed OS exit, raw streams and one-clock custody."""
    authority = authenticate_original_native_artifact(
        binding,
        reader,
        run_id=run_id,
        required_sdk_modules=required_sdk_modules,
    )
    original = authority["original"]
    if authority["event"].json_object() != raw:
        raise ValueError("native tool bytes differ from the admitted original DATA observation")
    if raw.get("owner_pid") != authority["process"].get("pid"):
        raise ValueError("native tool owner differs from its actual enclosing original child PID")
    validate_native_tool_data(
        raw,
        reader,
        original_deadline=original.original_deadline,
        original_completion=original.observed_completion,
    )
    remaining(authority["operation"].deadline)


def validate_native_tool_data(
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    original_deadline: float,
    original_completion: float,
) -> None:
    """A DATA predicate only; callers separately require live original authority.

    The outer authenticated function obtains both observations from its actual
    external custodian, never the DATA being checked. This leaf cannot approve
    a native/source/portable gate.
    """
    native_file = _binding(raw.get("native_process_artifact"), reader)
    native = native_file.json_object()
    # The tool wrapper binds its exact original process and raw binary streams.
    if (
        native.get("schema_version") != SCHEMA
        or native.get("pid") != raw.get("pid")
        or type(native.get("pid")) is not int
        or native["pid"] <= 0
        or native.get("owner_pid") != raw.get("owner_pid")
        or type(native.get("owner_pid")) is not int
        or native["owner_pid"] <= 0
        or native["owner_pid"] == native["pid"]
        or native.get("command") != raw.get("command")
        or type(native.get("original_exit_code")) is not int
        or native["original_exit_code"] != raw.get("original_exit_code")
        or native.get("accepted") is not True
        or native.get("timed_out") is not False
        or native.get("diagnostics") != []
        or native.get("executable_observation_before") != raw.get("executable_observation_before")
        or native.get("executable_observation_after") != raw.get("executable_observation_after")
    ):
        raise ValueError("native tool lacks its actual original PID/OS/executable observations")
    deadline = _finite(raw.get("original_deadline_monotonic"))
    caller = _finite(raw.get("caller_deadline_monotonic"))
    if native.get("original_deadline_monotonic") != deadline or not deadline <= caller <= original_deadline:
        raise ValueError("native tool deadline differs from its original externally held operation")
    cleanup = native.get("cleanup")
    if (
        not isinstance(cleanup, dict)
        or type(cleanup.get("guardian_pid")) is not int
        or cleanup["guardian_pid"] <= 0
        or cleanup["guardian_pid"] in {native["pid"], native["owner_pid"]}
        or cleanup.get("guardian_original_exit_code") != 0
        or type(cleanup.get("guardian_original_exit_code")) is not int
        or cleanup.get("guardian_armed") is not True
        or cleanup.get("guardian_finished") is not True
        or cleanup.get("root_reaped") is not True
        or cleanup.get("final_token_sweep_matched_pids") != []
    ):
        raise ValueError("native original tool guardian/cleanup custody is incomplete")
    stamps = [
        _stamp(native.get("operation_begin")),
        _stamp(native.get("launch_begin")),
        _stamp(native.get("launch_returned")),
        _stamp(native.get("root_reaped")),
        _stamp(cleanup.get("begin")),
        _stamp(cleanup.get("end")),
        _stamp(native.get("operation_end")),
    ]
    if stamps != sorted(stamps) or not stamps[-1] < deadline or stamps[-1] > original_completion:
        raise ValueError("native original tool ordered observations exceeded original supervisor custody")
    if "live_interaction" in native:
        interaction = native["live_interaction"]
        if (
            not isinstance(interaction, dict)
            or set(interaction) != {"begin", "end", "completed"}
            or interaction["completed"] is not True
            or not stamps[2] <= _stamp(interaction["begin"]) <= _stamp(interaction["end"]) <= stamps[3]
        ):
            raise ValueError("native interaction did not finish inside its actual original process clock")
    identity = raw.get("executable_identity_before")
    if (
        not isinstance(identity, dict)
        or set(identity) != {"device", "inode", "mode", "size", "mtime_ns", "ctime_ns", "links"}
        or any(type(value) is not int or value < 0 for value in identity.values())
        or not stat.S_ISREG(identity["mode"])
        or identity != raw.get("executable_identity_after")
        or identity != native.get("executable_identity_before")
        or identity != native.get("executable_identity_after")
    ):
        raise ValueError("native original executable physical identity changed")
    nomination = native.get("nomination")
    before_nomination = native.get("nominated_identity_before")
    if (
        not isinstance(nomination, dict)
        or not isinstance(before_nomination, dict)
        or set(before_nomination)
        != {
            "device",
            "inode",
            "mode",
            "size",
            "mtime_ns",
            "ctime_ns",
            "links",
            "symlink_target",
        }
        or any(
            type(before_nomination[key]) is not int or before_nomination[key] < 0
            for key in before_nomination
            if key != "symlink_target"
        )
        or before_nomination != native.get("nominated_identity_after")
        or nomination.get("resolved_path") != raw["executable"]
        or native.get("nominated_command") != [nomination.get("path"), *raw["command"][1:]]
        or type(native.get("launcher_preserved")) is not bool
        or raw["command"][0] != (nomination.get("path") if native["launcher_preserved"] else raw["executable"])
        or (stat.S_ISLNK(before_nomination["mode"]) != isinstance(before_nomination["symlink_target"], str))
    ):
        raise ValueError("native original nomination or selected Python launcher custody differs")
    total = 0
    for channel in ("stdout", "stderr"):
        retained = raw.get(f"raw_{channel}")
        original_stream = native.get(f"raw_{channel}")
        if not isinstance(retained, dict) or set(retained) != {
            "path",
            "sha256",
            "bytes",
        }:
            raise ValueError("native original tool raw binary stream binding is incomplete")
        observed = reader.read(retained["path"])
        if (
            not isinstance(original_stream, dict)
            or set(original_stream) != {"path", "sha256", "bytes"}
            or type(retained["bytes"]) is not int
            or retained["bytes"] < 0
            or observed.sha256 != retained["sha256"]
            or len(observed.content) != retained["bytes"]
            or original_stream["sha256"] != observed.sha256
            or original_stream["bytes"] != len(observed.content)
            or observed.path.parent != native_file.path.parent
            or Path(original_stream["path"]).name != observed.path.name
            or native.get(f"{channel}_preview_truncated") is not False
            or raw.get(channel) != observed.content.decode("utf-8", errors="replace")
            or native.get(channel) != raw[channel]
        ):
            raise ValueError("native original tool raw bytes/text differ from retained custody")
        total += len(observed.content)
    if total > MAX_STREAM_BYTES or not reader.unchanged():
        raise ValueError("native original tool stream byte bound or current retained custody differs")
