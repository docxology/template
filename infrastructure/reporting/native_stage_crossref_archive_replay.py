"""Official archive readback through the genuine renderer→Crossref role.

This retains all Source pin/member/physical identity predicates. It admits the
archive only from the actual Source-closed filter specification; it cannot be
selected from a free binding or a direct Stage tool-roster shortcut.
"""

from __future__ import annotations

import hashlib
import platform
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation


def replay_stage_crossref_official_archive(
    control: CrossrefFilterReaderOperation,
    binding: dict[str, str],
    tool_binding: dict[str, str],
    tool_reader: SnapshotReader,
) -> dict[str, Any]:
    from infrastructure.reporting.native_crossref_archive import (
        PIN_SOURCE,
        SCHEMA,
        _MAX_ARCHIVE_BYTES,
        _MAX_EXECUTABLE_BYTES,
        _member,
        _observation,
        _source_pin,
    )
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation
    from infrastructure.reporting.native_format_acceptance_evidence import _file
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
    from infrastructure.reporting.native_stage_loader_replay import require_current_stage_reader
    from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact

    stage = getattr(control, "_renderer_stage_owner", None)
    if (
        type(control) is not CrossrefFilterReaderOperation
        or type(stage) is not NativeStageChildReaderOperation
        or tool_reader.native_control_operation is not control
        or tool_reader.root != control.parent_reader.root
        or control.parent_reader.native_control_operation is not stage
    ):
        raise ValueError("official archive requires the concrete genuine renderer→Crossref Stage role")
    control.verify()
    reader, source, deadline = control.parent_reader, control.source, control.deadline
    renderer = stage.authenticate_artifact(
        control._renderer_binding,
        reader,
        run_id=control.run_id,
        required_sdk_modules=("reporting/native_renderer_source_call.py", "reporting/native_crossref_archive.py"),
    )
    child = control._child()
    if child["specification"]["official_archive"] != binding:
        raise ValueError("official archive is not the genuine Source-selected Crossref specification pointer")
    # The pointer is admitted only after the complete parent/filter Source Code,
    # actual OS/kernel relation and exact writer execution were authenticated.
    raw = _file(binding, reader).json_object()
    tool_authority = authenticate_original_native_artifact(
        tool_binding,
        tool_reader,
        run_id=control.run_id,
        required_sdk_modules=("reporting/native_crossref_worker.py",),
    )
    operation = None
    if reader.native_operation is not None:
        operation = require_native_operation(reader)
        original = operation.originals.get(control.scope)
        if (
            original is None
            or original.run_id != control.run_id
            or operation.source is not source
            or operation.deadline != deadline
        ):
            raise ValueError("official archive differs from the externally held Original Source/run/clock")
        host = reader.read(original.process_relative).json_object()["host_before"]
    else:
        require_current_stage_reader(reader, stage)
        host = {"system": platform.system(), "machine": platform.machine()}
        if renderer["specification"]["parent_platform"] != host["system"]:
            raise ValueError("official archive actual Current host differs from its genuine Stage parent")
    action, pin = _source_pin(source, reader, host, deadline=deadline)
    if (
        set(raw)
        != {
            "schema_version",
            "run_id",
            "host",
            "pin",
            "pin_source_path",
            "bindings",
            "member",
            "archive_observation",
            "executable_observation",
            "source_binding",
        }
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != control.run_id
        or raw["host"] != host
        or raw["pin"] != pin
        or raw["pin_source_path"] != PIN_SOURCE
        or raw["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or set(raw["bindings"]) != {"pin_source", "archive"}
        or _file(raw["bindings"]["pin_source"], reader).content != action
    ):
        raise ValueError("official archive differs from the complete genuine Source/host/pin fields")
    archive = _file(raw["bindings"]["archive"], reader)
    member, body = _member(archive.content, pin, deadline=deadline)
    member_sha256 = hashlib.sha256(body).hexdigest()
    tool = tool_authority["event"].json_object()
    if (
        member != raw["member"]
        or tool.get("tool") != "pandoc-crossref"
        or tool.get("run_id") != control.run_id
        or tool.get("executable_sha256") != member_sha256
    ):
        raise ValueError("official archive member differs from the genuine nested executed Crossref body")
    native = _file(tool["native_process_artifact"], reader).json_object()
    observed = _observation(raw["executable_observation"], max_bytes=_MAX_EXECUTABLE_BYTES)
    archive_observation = _observation(raw["archive_observation"], max_bytes=_MAX_ARCHIVE_BYTES)
    original_body = native["executable_observation_before"]
    identity = observed["identity"]
    if (
        native["executable_observation_after"] != original_body
        or original_body["sha256"] != member_sha256
        or native["executable_identity_before"]["size"] != len(body)
        or observed["path"] != native["nomination"]["resolved_path"]
        or observed["sha256"] != member_sha256
        or observed["bytes"] != len(body)
        or native["executable_identity_before"] != native["executable_identity_after"]
    ):
        raise ValueError("official archive actual process nomination/body differs from its held complete member")
    expected_identity = {
        "device": identity["st_dev"],
        "inode": identity["st_ino"],
        "mode": identity["st_mode"],
        "size": identity["st_size"],
        "mtime_ns": identity["st_mtime_ns"],
        "ctime_ns": identity["st_ctime_ns"],
        "links": identity["st_nlink"],
    }
    if (
        native["executable_identity_before"] != expected_identity
        or archive_observation["sha256"] != archive.sha256
        or archive_observation["bytes"] != len(archive.content)
    ):
        raise ValueError("official archive actual physical identity differs from its real prelaunch member/archive")
    if operation is not None:
        operation.verify(reader)
    else:
        if host != {"system": platform.system(), "machine": platform.machine()}:
            raise ValueError("official archive actual Current host changed during readback")
        require_current_stage_reader(reader, stage)
    control.verify()
    remaining(deadline)
    return {
        "schema_version": SCHEMA,
        "source_pin": pin,
        "original_host": host,
        "archive_sha256": archive.sha256,
        "member_sha256": member_sha256,
        "original_tool": tool_binding,
    }
