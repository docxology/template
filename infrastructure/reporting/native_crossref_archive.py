"""Actual Source-pinned Crossref provider archive/executable correspondence.

Archive and member records are DATA. Original custody requires the real current
Source owner; replay requires externally held original Source/Code/tool custody.
This adapter does not authenticate actual loaded native libraries.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import stat
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_document_provider_archives import (
    MAX_ARCHIVE_BYTES,
    MAX_EXECUTABLE_BYTES,
    provider_archive_member,
)
from infrastructure.reporting.native_document_provider_contracts import PIN_SOURCE, select_document_tool
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-source-crossref-provider-archive-v3"


def _physical(path: Path, *, max_bytes: int, deadline: float) -> tuple[bytes, dict[str, Any]]:
    """Hold one actual regular nonsymlink body and recheck its kernel identity."""
    if not path.is_absolute() or path != path.resolve(strict=True):
        raise ValueError("Crossref provider custody requires an explicit actual physical path")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= max_bytes:
            raise ValueError("Crossref provider custody requires a bounded nonempty actual regular file")
        chunks, size = [], 0
        while chunk := os.read(descriptor, 65536):
            remaining(deadline)
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("Crossref provider actual physical bytes exceed their finite bound")
            chunks.append(chunk)
        fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        identity = {field: getattr(before, field) for field in fields}
        if (
            identity != {field: getattr(os.fstat(descriptor), field) for field in fields}
            or identity != {field: getattr(path.lstat(), field) for field in fields}
            or size != before.st_size
        ):
            raise ValueError("Crossref provider actual file body/identity changed during custody")
        content = b"".join(chunks)
        return content, {
            "path": str(path),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "identity": identity,
        }
    finally:
        os.close(descriptor)


def _source_pin(
    source: NativeSourceContext, reader: SnapshotReader, host: dict[str, str], *, deadline: float
) -> tuple[bytes, dict[str, Any]]:
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    held = source.current_source_reader.read(PIN_SOURCE)
    if source.reference.read(PIN_SOURCE) != held.content:
        raise ValueError("Crossref provider pin source differs from independently admitted original/current Source")
    return held.content, select_document_tool(held.content, host, "crossref")


def _validate_record(
    raw: Any,
    *,
    run_id: str,
    host: dict[str, str],
    pin: dict[str, Any],
    source_binding: list[str],
) -> None:
    """Check retained DATA against independently selected Source, not grant custody."""
    if (
        type(raw) is not dict
        or set(raw)
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
        or raw["run_id"] != run_id
        or raw["host"] != host
        or raw["pin"] != pin
        or raw["pin_source_path"] != PIN_SOURCE
        or raw["source_binding"] != source_binding
        or type(raw["bindings"]) is not dict
        or set(raw["bindings"]) != {"pin_source", "archive"}
    ):
        raise ValueError("Crossref provider original archive changed Source/platform/pin fields")


def _observation(raw: Any, *, max_bytes: int) -> dict[str, Any]:
    """Validate original metadata DATA without opening its producer path."""
    if type(raw) is not dict or set(raw) != {"path", "sha256", "bytes", "identity"}:
        raise ValueError("Crossref provider physical observation has changed fields")
    path = raw["path"]
    if type(path) is not str or not Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("Crossref provider physical path label is unsafe")
    identity = raw["identity"]
    fields = {"st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink"}
    if (
        type(identity) is not dict
        or set(identity) != fields
        or any(type(value) is not int or value < 0 for value in identity.values())
        or not stat.S_ISREG(identity["st_mode"])
        or identity["st_nlink"] < 1
        or type(raw["bytes"]) is not int
        or not 0 < raw["bytes"] <= max_bytes
        or identity["st_size"] != raw["bytes"]
        or type(raw["sha256"]) is not str
        or re.fullmatch(r"[0-9a-f]{64}", raw["sha256"]) is None
    ):
        raise ValueError("Crossref provider physical identity/byte observation is malformed")
    return raw


def observe_crossref_provider_archive(
    source: NativeSourceContext,
    directory: Path,
    archive_path: Path,
    executable: Path,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, str]:
    """Retain actual archive/member/body before original native launch.

    The caller supplies only locations. Genuine current Source selects the
    platform, provider, build pins and exact body; actual physical bytes must match.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or owner.deadline != deadline:
        raise ValueError("Crossref provider archive requires its actual live Source/SDK owner and unchanged clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    host = {"system": platform.system(), "machine": platform.machine()}
    pin_source, pin = _source_pin(source, reader, host, deadline=deadline)
    raw_archive, archive_observation = _physical(archive_path, max_bytes=MAX_ARCHIVE_BYTES, deadline=deadline)
    raw_executable, executable_observation = _physical(executable, max_bytes=MAX_EXECUTABLE_BYTES, deadline=deadline)
    member, body = provider_archive_member(raw_archive, pin, deadline=deadline)
    if raw_executable != body or executable_observation["identity"]["st_mode"] & 0o111 == 0:
        raise ValueError("actual installed Crossref executable differs from the Source-pinned provider member")
    root = source.bindings.current_root
    create_private_native_directory(root, directory)
    bindings = {}
    # Retain the complete provider compressed archive, which contains the actual
    # member. Replay extracts that body itself; a duplicate large executable
    # artifact is unnecessary and exceeds the ordinary 64 MiB snapshot ceiling.
    for label, content in (("pin_source", pin_source), ("archive", raw_archive)):
        target = directory / (label + ".bin")
        atomic_write_bytes_confined(root, target, content, mode=0o600)
        held = reader.read(target.relative_to(root).as_posix())
        bindings[label] = {"path": held.relative, "sha256": held.sha256}
    # Keep the before and closing original physical reads, not only copied bytes.
    if _physical(archive_path, max_bytes=MAX_ARCHIVE_BYTES, deadline=deadline) != (
        raw_archive,
        archive_observation,
    ) or _physical(executable, max_bytes=MAX_EXECUTABLE_BYTES, deadline=deadline) != (
        raw_executable,
        executable_observation,
    ):
        raise ValueError("Crossref provider archive or installed body changed before original binding")
    record = {
        "schema_version": SCHEMA,
        "run_id": owner.run_id,
        "host": host,
        "pin": pin,
        "pin_source_path": PIN_SOURCE,
        "bindings": bindings,
        "member": member,
        "archive_observation": archive_observation,
        "executable_observation": executable_observation,
        "source_binding": [source.reference.commit, source.reference.source_identity],
    }
    binding = write_json(root, directory / "archive-admission.json", record)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    return binding


def replay_crossref_provider_archive(
    source: NativeSourceContext,
    binding: dict[str, str],
    tool_binding: dict[str, str],
    reader: SnapshotReader,
    *,
    tool_reader: SnapshotReader,
    scope: str,
    run_id: str,
    deadline: float,
) -> dict[str, Any]:
    """Recheck original provider correspondence under actual external custody.

    The archive is authenticated by its genuine original parent operation;
    tool_reader holds the separately authenticated nested Crossref child. Both
    must carry the same actual external current operation. No child context is
    created from these receipt fields. Original paths are labels. Replay extracts
    the retained compressed archive itself and compares its complete member to
    the genuine original executed body. Current execution nominates its archive.
    """
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation

    operation = require_native_operation(reader)
    control = tool_reader.native_control_operation
    if (
        operation.source is not source
        or operation.deadline != deadline
        or require_native_operation(tool_reader) is not operation
        or type(control) is not CrossrefFilterReaderOperation
        or control.parent_reader is not reader
        or control.scope != scope
        or control.run_id != run_id
        or control.deadline != deadline
        or tool_reader.root != reader.root
    ):
        raise ValueError("Crossref provider replay requires its actual independent current Source/original owner")
    control.verify()
    authority = authenticate_original_native_artifact(
        binding,
        reader,
        run_id=run_id,
        required_sdk_modules=(
            "reporting/native_crossref_archive.py",
            "reporting/native_document_provider_archives.py",
            "reporting/native_document_provider_contracts.py",
        ),
    )
    tool_authority = authenticate_original_native_artifact(
        tool_binding,
        tool_reader,
        run_id=run_id,
        required_sdk_modules=("reporting/native_crossref_worker.py",),
    )
    raw = authority["event"].json_object()
    original = operation.originals.get(scope)
    if original is None or original.run_id != run_id:
        raise ValueError("Crossref provider archive belongs to another externally held original scope/run")
    host = reader.read(original.process_relative).json_object()["host_before"]
    pin_source, pin = _source_pin(source, reader, host, deadline=deadline)
    _validate_record(
        raw,
        run_id=run_id,
        host=host,
        pin=pin,
        source_binding=[source.reference.commit, source.reference.source_identity],
    )
    if _file(raw["bindings"]["pin_source"], reader).content != pin_source:
        raise ValueError("Crossref provider original Source pin body differs from independently current Source")
    archive = _file(raw["bindings"]["archive"], reader)
    member, body = provider_archive_member(archive.content, pin, deadline=deadline)
    member_sha256 = hashlib.sha256(body).hexdigest()
    tool = tool_authority["event"].json_object()
    if (
        member != raw["member"]
        or tool.get("tool") != "pandoc-crossref"
        or tool.get("run_id") != run_id
        or tool.get("executable_sha256") != member_sha256
    ):
        raise ValueError("Crossref provider archive member differs from the genuine original executed native body")
    # The complete Source-owned original tool validator authenticates exact
    # command/OS/consumed stdin separately; this bridge cannot replace it.
    native = _file(tool["native_process_artifact"], reader).json_object()
    observed = _observation(raw["executable_observation"], max_bytes=MAX_EXECUTABLE_BYTES)
    archive_observation = _observation(raw["archive_observation"], max_bytes=MAX_ARCHIVE_BYTES)
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
        raise ValueError("Crossref provider genuine original process nomination/body differs from its archive")
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
        raise ValueError("Crossref provider original physical identity differs from its real prelaunch archive/body")
    operation.verify(reader)
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
