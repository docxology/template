"""Actual Source-pinned official Crossref archive/executable correspondence.

Archive and member records are DATA. Original custody requires the real current
Source owner; replay requires externally held original Source/Code/tool custody.
This adapter does not authenticate actual loaded native libraries.
"""

from __future__ import annotations

import hashlib
import lzma
import os
import platform
import re
import stat
import tarfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-source-official-crossref-archive-v2"
PIN_SOURCE = ".github/actions/setup-acceptance-documents/action.yml"
_MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
_MAX_EXECUTABLE_BYTES = 512 * 1024 * 1024
_MAX_PAYLOAD_BYTES = 1024 * 1024 * 1024
_MAX_MEMBERS = 1000
_XZ_MEMORY_BYTES = 128 * 1024 * 1024
_MAX_METADATA_READ_BYTES = 8 * 1024 * 1024
_CHUNK_BYTES = 65536


def _uncompressed(archive: bytes, *, deadline: float) -> bytes:
    """Bound all decompressed bytes before tarfile consumes internal metadata."""
    remaining(deadline)
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=_XZ_MEMORY_BYTES)
    chunks: list[bytes] = []
    cursor = size = 0
    while not decoder.eof:
        remaining(deadline)
        if decoder.needs_input:
            if cursor == len(archive):
                raise ValueError("official Crossref XZ stream is truncated")
            content = archive[cursor : cursor + _CHUNK_BYTES]
            cursor += len(content)
        else:
            content = b""
        chunk = decoder.decompress(content, max_length=_CHUNK_BYTES)
        remaining(deadline)
        size += len(chunk)
        if size > _MAX_PAYLOAD_BYTES:
            raise ValueError("official Crossref complete uncompressed stream exceeds its finite bound")
        chunks.append(chunk)
    if decoder.unused_data or cursor != len(archive):
        raise ValueError("official Crossref archive has unsupported concatenated or trailing XZ streams")
    if not size:
        raise ValueError("official Crossref archive has an empty uncompressed stream")
    result = b"".join(chunks)
    remaining(deadline)
    return result


class _BoundedTarBytes(BytesIO):
    """Keep tarfile's internal longname/PAX/sparse reads on the original clock."""

    def __init__(self, content: bytes, deadline: float) -> None:
        self.deadline = deadline
        super().__init__(content)

    def read(self, size: int | None = -1) -> bytes:
        remaining(self.deadline)
        if type(size) is not int or not 0 <= size <= _MAX_METADATA_READ_BYTES:
            raise ValueError("official Crossref tar parser requested unsupported or excessive metadata bytes")
        result = super().read(size)
        remaining(self.deadline)
        return result

    def seek(self, offset: int, whence: int = 0) -> int:
        remaining(self.deadline)
        result = super().seek(offset, whence)
        remaining(self.deadline)
        return result


def _pin(content: bytes, host: dict[str, str]) -> dict[str, Any]:
    """Interpret the actual Source-owned action, without executing shell DATA.

    The action currently owns exact platform/version/hash/size nominations. A
    changed selector syntax refuses until its Source adapter is jointly updated.
    No hard-coded duplicate digest supplies an archive pin.
    """
    if type(host) is not dict or set(host) != {"system", "machine"}:
        raise ValueError("official Crossref archive requires actual complete original host facts")
    document = yaml.safe_load(content)
    if not isinstance(document, dict) or document.get("runs", {}).get("using") != "composite":
        raise ValueError("official Crossref pin source is not the actual Source composite action")
    steps = [
        row
        for row in document["runs"]["steps"]
        if isinstance(row, dict) and row.get("name") == "Prepare exact compatible Pandoc and cross-reference binaries"
    ]
    if len(steps) != 1 or steps[0].get("shell") != "bash" or not isinstance(steps[0].get("run"), str):
        raise ValueError("official Crossref source requires its exact Source-owned preparation role")
    run = steps[0]["run"]
    branches = re.findall(
        r'if \[ "\$RUNNER_OS" = Linux \]; then\n(.*?)elif \[ "\$RUNNER_ARCH" = ARM64 \]; then\n(.*?)else\n(.*?)fi\n',
        run,
        re.DOTALL,
    )
    if len(branches) != 1:
        raise ValueError("official Crossref Source platform selector changed or is ambiguous")
    system, machine = host["system"], host["machine"]
    if system == "Linux" and machine in {"x86_64", "amd64"}:
        selected = branches[0][0]
    elif system == "Darwin" and machine == "arm64":
        selected = branches[0][1]
    elif system == "Darwin" and machine == "x86_64":
        selected = branches[0][2]
    else:
        raise ValueError("official Crossref Source has no admitted archive for this actual host")
    fields = {}
    for name, pattern in (
        ("asset", r"pandoc-crossref-[A-Za-z0-9_-]+\.tar\.xz"),
        ("sha256", r"[0-9a-f]{64}"),
        ("bytes", r"[1-9][0-9]*"),
    ):
        variable = {"asset": "asset", "sha256": "sha", "bytes": "size"}[name]
        matches = re.findall(r"(?m)^\s*crossref_" + variable + "=(" + pattern + r")\s*$", selected)
        if len(matches) != 1:
            raise ValueError("official Crossref Source pin is missing or ambiguous")
        fields[name] = int(matches[0]) if name == "bytes" else matches[0]
    urls = re.findall(
        r"https://github\.com/lierdakil/pandoc-crossref/releases/download/([^/\s\"]+)/\$crossref_asset", run
    )
    if len(urls) != 1 or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+[a-z]?", urls[0]):
        raise ValueError("official Crossref Source release URL is missing, nonofficial or ambiguous")
    if run.count('"$destination/pandoc-crossref" --version') != 1 or not 0 < fields["bytes"] <= _MAX_ARCHIVE_BYTES:
        raise ValueError("official Crossref Source executable member or archive bound differs")
    return {
        **fields,
        "version": urls[0],
        "member": "pandoc-crossref",
        "url": "https://github.com/lierdakil/pandoc-crossref/releases/download/" + urls[0] + "/" + fields["asset"],
    }


def _member(archive_bytes: bytes, pin: dict[str, Any], *, deadline: float) -> tuple[dict[str, Any], bytes]:
    if len(archive_bytes) != pin["bytes"] or hashlib.sha256(archive_bytes).hexdigest() != pin["sha256"]:
        raise ValueError("official Crossref archive bytes differ from the actual current Source pin")
    selected = None
    selected_data = None
    names = set()
    payload_bytes = count = 0
    complete = _uncompressed(archive_bytes, deadline=deadline)
    with _BoundedTarBytes(complete, deadline) as stream, tarfile.open(fileobj=stream, mode="r:") as archive:
        for member in archive:
            remaining(deadline)
            count += 1
            name = PurePosixPath(member.name)
            if count > _MAX_MEMBERS or name.is_absolute() or ".." in name.parts or not name.parts:
                raise ValueError("official Crossref archive has an unsafe or excessive complete member roster")
            label = name.as_posix()
            if label in names or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError("official Crossref archive has duplicate, linked or unsupported member types")
            names.add(label)
            if member.isfile():
                payload_bytes += member.size
                if not 0 <= member.size <= _MAX_EXECUTABLE_BYTES or payload_bytes > _MAX_PAYLOAD_BYTES:
                    raise ValueError("official Crossref archive exceeds its finite uncompressed payload bound")
            if label == pin["member"]:
                if selected is not None or not member.isfile() or member.mode & 0o111 == 0:
                    raise ValueError("official Crossref Source member is not one real executable file")
                member_stream = archive.extractfile(member)
                if member_stream is None:
                    raise ValueError("official Crossref archive cannot read its selected Source member")
                chunks, size = [], 0
                with member_stream:
                    while chunk := member_stream.read(65536):
                        remaining(deadline)
                        size += len(chunk)
                        if size > _MAX_EXECUTABLE_BYTES:
                            raise ValueError("official Crossref extracted executable exceeds its native byte bound")
                        chunks.append(chunk)
                selected_data = b"".join(chunks)
                if size != member.size or not selected_data:
                    raise ValueError("official Crossref extracted Source member is truncated or empty")
                selected = {
                    "name": member.name,
                    "canonical_name": label,
                    "mode": member.mode,
                    "bytes": size,
                    "sha256": hashlib.sha256(selected_data).hexdigest(),
                }
    if selected is None or selected_data is None:
        raise ValueError("official Crossref archive omitted its exact Source-selected executable")
    remaining(deadline)
    return {
        **selected,
        "archive_members": count,
        "uncompressed_payload_bytes": payload_bytes,
        "complete_uncompressed_archive_bytes": len(complete),
    }, selected_data


def _physical(path: Path, *, max_bytes: int, deadline: float) -> tuple[bytes, dict[str, Any]]:
    """Hold one actual regular nonsymlink body and recheck its kernel identity."""
    if not path.is_absolute() or path != path.resolve(strict=True):
        raise ValueError("official Crossref custody requires an explicit actual physical path")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= max_bytes:
            raise ValueError("official Crossref custody requires a bounded nonempty actual regular file")
        chunks, size = [], 0
        while chunk := os.read(descriptor, 65536):
            remaining(deadline)
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("official Crossref actual physical bytes exceed their finite bound")
            chunks.append(chunk)
        fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        identity = {field: getattr(before, field) for field in fields}
        if (
            identity != {field: getattr(os.fstat(descriptor), field) for field in fields}
            or identity != {field: getattr(path.lstat(), field) for field in fields}
            or size != before.st_size
        ):
            raise ValueError("official Crossref actual file body/identity changed during custody")
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
        raise ValueError("official Crossref pin source differs from independently admitted original/current Source")
    return held.content, _pin(held.content, host)


def _observation(raw: Any, *, max_bytes: int) -> dict[str, Any]:
    """Validate original metadata DATA without opening its producer path."""
    if type(raw) is not dict or set(raw) != {"path", "sha256", "bytes", "identity"}:
        raise ValueError("official Crossref physical observation has changed fields")
    path = raw["path"]
    if type(path) is not str or not Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("official Crossref physical path label is unsafe")
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
        raise ValueError("official Crossref physical identity/byte observation is malformed")
    return raw


def observe_crossref_official_archive(
    source: NativeSourceContext,
    directory: Path,
    archive_path: Path,
    executable: Path,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, str]:
    """Retain actual archive/member/body before original native launch.

    The caller supplies only locations. Genuine current Source selects every
    expected platform/version/hash/member; actual physical bytes must match.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or owner.deadline != deadline:
        raise ValueError("official Crossref archive requires its actual live Source/SDK owner and unchanged clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    host = {"system": platform.system(), "machine": platform.machine()}
    action, pin = _source_pin(source, reader, host, deadline=deadline)
    raw_archive, archive_observation = _physical(archive_path, max_bytes=_MAX_ARCHIVE_BYTES, deadline=deadline)
    raw_executable, executable_observation = _physical(executable, max_bytes=_MAX_EXECUTABLE_BYTES, deadline=deadline)
    member, body = _member(raw_archive, pin, deadline=deadline)
    if raw_executable != body or executable_observation["identity"]["st_mode"] & 0o111 == 0:
        raise ValueError("actual installed Crossref executable differs from the Source-pinned official member")
    root = source.bindings.current_root
    create_private_native_directory(root, directory)
    bindings = {}
    # Retain the complete official compressed archive, which contains the actual
    # member. Replay extracts that body itself; a duplicate large executable
    # artifact is unnecessary and exceeds the ordinary 64 MiB snapshot ceiling.
    for label, content in (("pin_source", action), ("archive", raw_archive)):
        target = directory / (label + ".bin")
        atomic_write_bytes_confined(root, target, content, mode=0o600)
        held = reader.read(target.relative_to(root).as_posix())
        bindings[label] = {"path": held.relative, "sha256": held.sha256}
    # Keep the before and closing original physical reads, not only copied bytes.
    if _physical(archive_path, max_bytes=_MAX_ARCHIVE_BYTES, deadline=deadline) != (
        raw_archive,
        archive_observation,
    ) or _physical(executable, max_bytes=_MAX_EXECUTABLE_BYTES, deadline=deadline) != (
        raw_executable,
        executable_observation,
    ):
        raise ValueError("official Crossref archive or installed body changed before original binding")
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


def replay_crossref_official_archive(
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
    """Recheck original official correspondence under actual external custody.

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
        raise ValueError("official Crossref replay requires its actual independent current Source/original owner")
    control.verify()
    authority = authenticate_original_native_artifact(
        binding,
        reader,
        run_id=run_id,
        required_sdk_modules=("reporting/native_crossref_archive.py",),
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
        raise ValueError("official Crossref archive belongs to another externally held original scope/run")
    host = reader.read(original.process_relative).json_object()["host_before"]
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
        or raw["run_id"] != run_id
        or raw["host"] != host
        or raw["pin"] != pin
        or raw["pin_source_path"] != PIN_SOURCE
        or raw["source_binding"] != [source.reference.commit, source.reference.source_identity]
    ):
        raise ValueError("official Crossref original archive changed Source/platform/pin fields")
    if (
        set(raw["bindings"]) != {"pin_source", "archive"}
        or _file(raw["bindings"]["pin_source"], reader).content != action
    ):
        raise ValueError("official Crossref original Source pin body differs from independently current Source")
    archive = _file(raw["bindings"]["archive"], reader)
    member, body = _member(archive.content, pin, deadline=deadline)
    member_sha256 = hashlib.sha256(body).hexdigest()
    tool = tool_authority["event"].json_object()
    if (
        member != raw["member"]
        or tool.get("tool") != "pandoc-crossref"
        or tool.get("run_id") != run_id
        or tool.get("executable_sha256") != member_sha256
    ):
        raise ValueError("official Crossref archive member differs from the genuine original executed native body")
    # The complete Source-owned original tool validator authenticates exact
    # command/OS/consumed stdin separately; this bridge cannot replace it.
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
        raise ValueError("official Crossref genuine original process nomination/body differs from its archive")
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
        raise ValueError("official Crossref original physical identity differs from its real prelaunch archive/body")
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
