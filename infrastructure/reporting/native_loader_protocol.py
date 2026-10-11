"""Fixed Linux callback wire format and actual consuming-process map/body reads.

These DATA primitives cannot create a Source owner, a Popen or native authority.
The live collector authenticates the kernel peer before accepting any frames.
"""

from __future__ import annotations

import array
import hashlib
import os
import socket
import stat
import struct
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

HEADER = struct.Struct("<8s10Q64s")
SEGMENT = struct.Struct("<6Q")
MAX_EVENTS = 32768
MAX_OBJECTS = 4096
MAX_SEGMENTS = 128
MAX_FILE = 512 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
CHUNK = 8 * 1024 * 1024
KINDS = {1: "hello", 2: "open", 3: "close", 4: "activity", 5: "preinit", 6: "done"}


def read(connection: socket.socket, size: int, deadline: float) -> bytes:
    if type(size) is not int or not 0 <= size <= CHUNK:
        raise ValueError("loader callback read exceeds its exact finite ceiling")
    content = bytearray()
    while len(content) < size:
        connection.settimeout(remaining(deadline))
        part = connection.recv(size - len(content))
        if not part:
            raise ValueError("loader callback truncated its original exact record")
        content.extend(part)
    return bytes(content)


def frame(connection: socket.socket, deadline: float) -> tuple[dict[str, Any] | None, int | None]:
    connection.settimeout(remaining(deadline))
    close_on_exec = getattr(socket, "MSG_CMSG_CLOEXEC", None)
    if type(close_on_exec) is not int:
        raise ValueError("loader callback requires the actual Linux close-on-exec descriptor ABI")
    raw, ancillary, flags, _ = connection.recvmsg(HEADER.size, socket.CMSG_SPACE(4), close_on_exec)
    received: list[int] = []
    try:
        for level, kind, data in ancillary:
            if level != socket.SOL_SOCKET or kind != socket.SCM_RIGHTS or len(data) != 4:
                raise ValueError("loader callback supplies unknown or repeated descriptor control data")
            values = array.array("i")
            values.frombytes(data)
            received.extend(values)
        if flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC) or len(received) > 1:
            raise ValueError("loader callback descriptor/frame was truncated or ambiguous")
        if not raw:
            if received:
                raise ValueError("loader EOF cannot carry a descriptor")
            return None, None
        if len(raw) < HEADER.size:
            raw += read(connection, HEADER.size - len(raw), deadline)
        magic, seq, pid, stamp, kind, identity, base, namespace, path_size, segments, has_fd, token = HEADER.unpack(raw)
        if magic != b"TLDOBS1\0" or kind not in KINDS or has_fd not in (0, 1) or len(received) != has_fd:
            raise ValueError("loader callback differs from the fixed Source wire ABI")
        result = {
            "sequence": seq,
            "pid": pid,
            "monotonic_ns": stamp,
            "kind": KINDS[kind],
            "id": identity,
            "base": base,
            "namespace": namespace,
            "path_bytes": path_size,
            "segments": segments,
            "token": token,
        }
        return result, received.pop() if received else None
    finally:
        for descriptor in received:
            os.close(descriptor)


def identity(descriptor: int) -> dict[str, int]:
    observed = os.fstat(descriptor)
    if not stat.S_ISREG(observed.st_mode) or not 0 < observed.st_size <= MAX_FILE or observed.st_nlink < 1:
        raise ValueError("loader backing body is not an extant bounded regular file")
    return {
        "device": observed.st_dev,
        "inode": observed.st_ino,
        "mode": observed.st_mode,
        "size": observed.st_size,
        "mtime_ns": observed.st_mtime_ns,
        "ctime_ns": observed.st_ctime_ns,
        "links": observed.st_nlink,
    }


def retain(root: Path, directory: Path, name: str, content: bytes) -> dict[str, Any]:
    path = directory / name
    if path.exists() or path.is_symlink() or path.parent != directory:
        raise ValueError("loader evidence chunks require fresh owned direct paths")
    atomic_write_bytes_confined(root, path, content, mode=0o600)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def body(root: Path, directory: Path, descriptor: int, object_id: int, deadline: float) -> dict[str, Any]:
    before = identity(descriptor)
    digest = hashlib.sha256()
    chunks: list[dict[str, Any]] = []
    offset = 0
    while offset < before["size"]:
        remaining(deadline)
        piece = os.pread(descriptor, min(CHUNK, before["size"] - offset), offset)
        if not piece:
            raise ValueError("loader original backing descriptor truncated during retention")
        digest.update(piece)
        chunks.append(retain(root, directory, f"object-{object_id:04d}-body-{len(chunks):03d}.bin", piece))
        offset += len(piece)
    if identity(descriptor) != before:
        raise ValueError("actual consumed library backing body changed during the blocked callback")
    return {"identity": before, "sha256": digest.hexdigest(), "bytes": offset, "chunks": chunks}


def maps(pid: int, deadline: float) -> tuple[bytes, list[dict[str, Any]]]:
    remaining(deadline)
    path = Path("/proc") / str(pid) / "maps"
    with path.open("rb") as stream:
        raw = stream.read(CHUNK + 1)
    if not 0 < len(raw) <= CHUNK:
        raise ValueError("actual consuming-process kernel map exceeds its finite ceiling")
    from infrastructure.reporting.native_loader_maps import parse_maps

    return raw, parse_maps(raw, deadline=deadline)


def mapped_segment(segment: dict[str, Any], rows: list[dict[str, Any]], backing: dict[str, Any] | None) -> None:
    """Every actual executable byte is covered by kernel RX mappings and offset."""
    low, size = segment["address"], segment["memory_bytes"]
    high = low + size
    selected = sorted((row for row in rows if row["low"] < high and row["high"] > low), key=lambda row: row["low"])
    cursor = low
    for row in selected:
        if row["low"] > cursor or row["protection"][:3] != "r-x":
            raise ValueError("loader executable segment has missing, writable or non-executable kernel coverage")
        if backing is None:
            if row["label"] != "[vdso]" or row["inode"] != 0:
                raise ValueError("bodyless loader image is not the actual kernel vDSO")
        elif (
            row["device"] != backing["identity"]["device"]
            or row["inode"] != backing["identity"]["inode"]
            or row["offset"] + (cursor - row["low"]) != segment["file_offset"] + (cursor - low)
        ):
            raise ValueError("loader mapped address does not consume the retained physical library body")
        cursor = min(high, row["high"])
        if cursor == high:
            break
    if cursor != high:
        raise ValueError("loader mapped executable segment is not completely covered")


def chunks_content(value: dict[str, Any], reader: SnapshotReader, *, limit: int, deadline: float) -> bytes:
    if (
        set(value) != {"sha256", "bytes", "chunks"}
        or type(value["bytes"]) is not int
        or not 0 <= value["bytes"] <= limit
    ):
        raise ValueError("loader retained body chunk graph has an unknown exact schema/bound")
    pieces = []
    total = 0
    for binding in value["chunks"]:
        remaining(deadline)
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256", "bytes"}:
            raise ValueError("loader retained chunk differs from its exact binding")
        observed = reader.read(binding["path"], max_bytes=CHUNK)
        if observed.sha256 != binding["sha256"] or len(observed.content) != binding["bytes"]:
            raise ValueError("loader retained chunk body differs from its original exact bytes")
        total += len(observed.content)
        if total > limit:
            raise ValueError("loader retained chunk graph exceeds its finite aggregate ceiling")
        pieces.append(observed.content)
    content = b"".join(pieces)
    if len(content) != value["bytes"] or hashlib.sha256(content).hexdigest() != value["sha256"]:
        raise ValueError("loader complete retained body differs from its ordered original chunks")
    return content
