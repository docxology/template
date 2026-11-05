"""Actual consuming-process loader callbacks under the genuine Source ToolAPI.

Explicit qualification only. This route never creates an owner from an env flag,
receipt, callback supplied by a caller, or a worker-self library enumeration.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import socket
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, TYPE_CHECKING

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_protocol import peer_pid, process_birth
from infrastructure.reporting.native_loader_build import CompiledNativeLoader
from infrastructure.reporting.native_loader_protocol import (
    CHUNK,
    MAX_EVENTS,
    MAX_OBJECTS,
    MAX_SEGMENTS,
    MAX_TOTAL,
    SEGMENT,
    body,
    frame,
    identity,
    mapped_segment,
    maps,
    read,
    retain,
)

if TYPE_CHECKING:
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

SCHEMA = "template-consuming-native-loader-lifecycle-v3"
ENV_KEYS = {
    "LD_AUDIT",
    "LD_PRELOAD",
    "TEMPLATE_LOADER_TOKEN",
    "TEMPLATE_LOADER_SOCKET",
    "TEMPLATE_LOADER_DEADLINE_NS",
    "TEMPLATE_LOADER_OWNER_PID",
}


class NativeLoaderObservation:
    """One actual Popen operation, compiler capability, Source and original clock."""

    compiled: CompiledNativeLoader
    root: Path
    directory: Path
    purpose: str
    deadline: float
    owner_pid: int
    token: bytes
    socket_directory: tempfile.TemporaryDirectory[str]
    address: str
    server: socket.socket
    prepared: bool
    eof: bool
    total_body: int
    total_memory: int
    preinit: bool
    done: bool

    def __init__(self, compiled: CompiledNativeLoader, directory: Path, *, purpose: str, deadline: float) -> None:
        if type(compiled) is not CompiledNativeLoader or not sys.platform.startswith("linux"):
            raise ValueError("loader qualification needs actual fixed Linux compiler/Source custody")
        compiled.verify(deadline=deadline)
        self.compiled, self.root, self.directory = (
            compiled,
            compiled.owner.source.bindings.current_root,
            directory.absolute(),
        )
        self.purpose, self.deadline = purpose, deadline
        if self.directory != self.directory.resolve(strict=True) or not self.directory.is_relative_to(
            compiled.directory
        ):
            raise ValueError("loader callback directory must be an extant owned compiler-child directory")
        self.owner_pid = os.getpid()
        self.token = secrets.token_hex(32).encode("ascii")
        self.socket_directory = tempfile.TemporaryDirectory(prefix="template-loader-")
        self.address = str(Path(self.socket_directory.name) / "peer.sock")
        if len(os.fsencode(self.address)) >= 108 or Path(self.address).exists():
            raise ValueError("loader callback socket must be fresh and fit the actual Linux ABI")
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.address)
        os.chmod(self.address, 0o600)
        self.server.listen(1)
        self.prepared = False
        self.eof = False
        self.events: list[dict[str, Any]] = []
        self.peer: dict[str, Any] | None = None
        self.command: tuple[str, ...] | None = None
        self.active: dict[int, tuple[dict[str, Any], int | None]] = {}
        self.seen: dict[int, dict[str, Any]] = {}
        self.closed: list[int] = []
        self.descriptors: dict[int, int] = {}
        self.total_body = 0
        self.total_memory = 0
        self.preinit = False
        self.done = False
        self.binding: dict[str, str] | None = None
        self.environment_injections: dict[str, str] | None = None
        self.resident_terminal: dict[str, Any] | None = None
        self.connection: socket.socket | None = None

    def prepare_env(self, env: dict[str, str], *, deadline: float, purpose: str) -> dict[str, str]:
        """Called inside the actual supervisor after sanitation, before Popen."""
        self.compiled.verify(deadline=deadline)
        if self.prepared or purpose != self.purpose or deadline != self.deadline or os.getpid() != self.owner_pid:
            raise ValueError("loader observation differs from its one actual consuming ToolAPI launch")
        if ENV_KEYS & set(env) or any(name.startswith("DYLD_") for name in env):
            raise ValueError("fixed loader qualification refuses preexisting ambient loader instrumentation")
        self.prepared = True
        from infrastructure.reporting.native_environment_custody import loader_environment_injections, value_commitment

        injections = loader_environment_injections(self)
        self.environment_injections = {key: value_commitment(value) for key, value in injections.items()}
        return {**env, **injections}

    def _verify_peer(self, live: NativeLiveToolProcess, connection: socket.socket) -> None:
        live.verify_live()
        pid = peer_pid(connection, deadline=self.deadline)
        actual = process_birth(pid, deadline=self.deadline)
        if (
            pid != live.pid
            or actual["ppid"] != self.owner_pid
            or actual["uid"] != os.getuid()
            or (self.peer is not None and actual != self.peer)
        ):
            raise ValueError("loader callback is not this genuine live Popen's kernel PID/birth/parent")
        if live.deadline != self.deadline or os.getpid() != self.owner_pid:
            raise ValueError("loader callback changed its actual owner or original clock")
        self.peer = actual

    def _map_event(self, live: NativeLiveToolProcess, sequence: int) -> list[dict[str, Any]]:
        raw, rows = maps(live.pid, self.deadline)
        self.events[-1]["kernel_maps"] = retain(self.root, self.directory, f"event-{sequence:05d}-maps.bin", raw)
        return rows

    def _open(
        self, value: dict[str, Any], descriptor: int | None, connection: socket.socket, live: NativeLiveToolProcess
    ) -> None:
        object_id, count = value["id"], value.pop("segments")
        size = value.pop("path_bytes")
        if (
            not 0 < object_id <= MAX_OBJECTS
            or object_id in self.seen
            or value["namespace"] != 0
            or not 0 < count <= MAX_SEGMENTS
            or not 0 < size < 4096
        ):
            raise ValueError("loader open callback exceeds its exact identity/namespace/roster bounds")
        value["path_label"] = read(connection, size, self.deadline).decode("utf-8", "strict")
        value["body"] = (
            body(self.root, self.directory, descriptor, object_id, self.deadline) if descriptor is not None else None
        )
        if value["body"] is not None:
            self.total_body += value["body"]["bytes"]
        if self.total_body > MAX_TOTAL:
            raise ValueError("loader original complete backing bodies exceed the finite aggregate ceiling")
        segments = []
        # Read the actual descriptor's ELF header table separately; the callback
        # cannot nominate a different executable-segment list from JSON.
        expected = None
        if descriptor is not None:
            header = os.pread(descriptor, min(identity(descriptor)["size"], 4 * 1024 * 1024 + 128 * 56), 0)
            # The full file-size bound is checked separately for large bodies.
            expected = _header_segments(header, value["body"]["bytes"])
        rows = self._map_event(live, value["sequence"])
        for index in range(count):
            remaining(self.deadline)
            address, memory_size, offset, file_size, flags, retained_size = SEGMENT.unpack(
                read(connection, SEGMENT.size, self.deadline)
            )
            if (
                memory_size > 512 * 1024 * 1024
                or file_size > memory_size
                or retained_size != (file_size if flags & 1 else 0)
                or flags & ~7
                or (flags & 1 and (flags & 2 or file_size != memory_size))
            ):
                raise ValueError("loader callback executable memory descriptor exceeds its exact ABI/bounds")
            if expected is not None and (
                index >= len(expected)
                or (address - value["base"], memory_size, offset, file_size, flags) != expected[index]
            ):
                raise ValueError("loader callback segment does not match its actual consumed ELF backing descriptor")
            selected: dict[str, Any] = {
                "address": address,
                "memory_bytes": memory_size,
                "file_offset": offset,
                "file_bytes": file_size,
                "flags": flags,
            }
            chunks: list[dict[str, Any]] = []
            observed, code_digest = 0, hashlib.sha256()
            while observed < retained_size:
                piece = read(connection, min(CHUNK, retained_size - observed), self.deadline)
                if descriptor is not None and piece != os.pread(descriptor, len(piece), offset + observed):
                    raise ValueError("actual loader mapped executable bytes differ from their consumed backing body")
                # File-backed mapped bytes were compared to the actual held FD
                # above. Retain a span into the same complete body, avoiding a
                # second copy of every executable segment. Kernel-only images
                # retain their actual callback bytes directly.
                if descriptor is None:
                    chunks.append(
                        retain(
                            self.root,
                            self.directory,
                            f"object-{object_id:04d}-segment-{index:03d}-{len(chunks):03d}.bin",
                            piece,
                        )
                    )
                code_digest.update(piece)
                observed += len(piece)
            selected["mapped_code"] = {
                "sha256": code_digest.hexdigest(),
                "bytes": observed,
                "chunks": chunks,
                "body_slice": {"offset": offset, "bytes": observed} if descriptor is not None else None,
            }
            self.total_memory += observed
            if self.total_memory > 512 * 1024 * 1024:
                raise ValueError("loader actual executable-memory aggregate exceeds its finite ceiling")
            if flags & 1:
                mapped_segment(selected, rows, value["body"])
            segments.append(selected)
        if expected is not None and len(expected) != count:
            raise ValueError("loader callback omitted a complete actual ELF PT_LOAD row")
        if not any(segment["mapped_code"]["bytes"] for segment in segments):
            raise ValueError("loader actual opened image lacks observed mapped executable bytes")
        value["segments"] = segments
        if descriptor is None and value["path_label"] not in {"linux-vdso.so.1", "linux-vdso.so.2"}:
            raise ValueError("bodyless loader image is not the fixed Linux kernel vDSO")
        self.active[object_id], self.seen[object_id] = (value, descriptor), value
        if descriptor is not None:
            self.descriptors[object_id] = descriptor

    def _close(self, value: dict[str, Any], live: NativeLiveToolProcess) -> None:
        if value["id"] not in self.active:
            raise ValueError("loader close lacks exactly one prior original open callback")
        opened, descriptor = self.active[value["id"]]
        rows = self._map_event(live, value["sequence"])
        for segment in opened["segments"]:
            if segment["flags"] & 1:
                mapped_segment(segment, rows, opened["body"])
        from infrastructure.reporting.native_loader_helper_memory import observe_consumer_memory

        value["consumer_mapped_code"] = observe_consumer_memory(
            live, {value["id"]: opened}, self.descriptors, rows, deadline=self.deadline
        )
        if descriptor is not None:
            _unchanged_body(opened["body"], descriptor, self.deadline)
        # Keep the actual descriptor through OS termination: glibc's fini
        # objclose notification can precede unmapping resident executable code.
        value["original_open_sequence"] = opened["sequence"]
        del self.active[value["id"]]
        self.closed.append(value["id"])

    def _census(self, rows: list[dict[str, Any]], live: NativeLiveToolProcess) -> dict[str, Any]:
        from infrastructure.reporting.native_loader_maps import census_images, executable_census

        from infrastructure.reporting.native_loader_helper_memory import observe_helper_memory

        self.events[-1]["source_auditor_mapped_code"] = observe_helper_memory(
            live, self.compiled, rows, page=os.sysconf("SC_PAGE_SIZE"), deadline=self.deadline
        )
        helper = self.compiled.library.stat()
        images = census_images(
            rows,
            self.seen,
            {key: value[0] for key, value in self.active.items()},
            self.closed,
            deadline=self.deadline,
        )
        from infrastructure.reporting.native_loader_helper_memory import observe_consumer_memory

        self.events[-1]["consumer_mapped_code"] = observe_consumer_memory(
            live, images, self.descriptors, rows, deadline=self.deadline
        )
        return executable_census(
            rows,
            images,
            helper_identity={"device": helper.st_dev, "inode": helper.st_ino},
            compiler=self.compiled.binding,
            page=os.sysconf("SC_PAGE_SIZE"),
            deadline=self.deadline,
        )

    def collect(self, live: NativeLiveToolProcess) -> None:
        """Only the genuine supervisor supplies this short-lived Popen capability."""
        from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

        if type(live) is not NativeLiveToolProcess or not self.prepared or self.events:
            raise ValueError("loader collection requires its one actual live consuming Popen")
        self.compiled.verify(deadline=self.deadline)
        self.command = live.command
        self.server.settimeout(remaining(self.deadline))
        connection, _ = self.server.accept()
        self.connection = connection
        try:
            with connection:
                self._verify_peer(live, connection)
                previous = 0
                while True:
                    value, descriptor = frame(connection, self.deadline)
                    if value is None:
                        self.eof = True
                        break
                    try:
                        self._verify_peer(live, connection)
                        peer = self.peer
                        if peer is None:
                            raise ValueError("loader frame lost its verified kernel peer")
                        if (
                            value.pop("token") != self.token
                            or value["pid"] != peer["pid"]
                            or value["sequence"] != len(self.events) + 1
                            or value["sequence"] > MAX_EVENTS
                        ):
                            raise ValueError("loader frame differs from its actual Source launch token/PID/sequence")
                        stamp = value["monotonic_ns"]
                        if not previous <= stamp <= time.monotonic_ns() < int(self.deadline * 1_000_000_000):
                            raise ValueError("loader callback timestamp exceeds the one original clock")
                        previous = stamp
                        self.events.append(value)
                        if len(self.events) == 1 and value["kind"] != "hello":
                            raise ValueError("loader must initialize before any consuming image callback")
                        if value["kind"] == "open":
                            if self.done:
                                raise ValueError("loader reopened an image after its terminal closed roster")
                            self._open(value, descriptor, connection, live)
                            descriptor = None  # retained until the actual matching close
                        else:
                            if descriptor is not None or value.pop("path_bytes") != 0 or value.pop("segments") != 0:
                                raise ValueError(
                                    "loader non-open callback cannot carry a backing body/segment selection"
                                )
                            if value["kind"] == "close":
                                self._close(value, live)
                            elif value["kind"] == "preinit":
                                if self.preinit or not self.active or self.done:
                                    raise ValueError(
                                        "loader preinit does not follow its one actual initial load roster"
                                    )
                                self.preinit = True
                                rows = self._map_event(live, value["sequence"])
                                value["complete_executable_map_census"] = self._census(rows, live)
                            elif value["kind"] == "done":
                                if self.done or self.active or not self.preinit or set(self.closed) != set(self.seen):
                                    raise ValueError("loader terminal callback omits an actual opened/closed image")
                                self.done = True
                            elif value["kind"] == "hello" and len(self.events) != 1:
                                raise ValueError("loader repeated its Source launch initialization")
                            elif value["kind"] == "activity":
                                if value["base"] not in {0, 1, 2}:
                                    raise ValueError("loader activity differs from the fixed glibc auditing ABI")
                                if self.preinit and value["base"] == 0:
                                    rows = self._map_event(live, value["sequence"])
                                    value["complete_executable_map_census"] = self._census(rows, live)
                        self._verify_peer(live, connection)
                        connection.settimeout(remaining(self.deadline))
                        connection.sendall(b"\xa5")
                    finally:
                        if descriptor is not None:
                            os.close(descriptor)
                if not self.preinit:
                    raise ValueError("loader channel ended without its actual initial complete load census")
                outcome = live.observe_original_os_exit()
                if outcome != 0:
                    raise ValueError(
                        "loader channel closure lacks actual signed normal consuming-process OS termination"
                    )
                residents = list(self.active)
                for object_id, descriptor in self.descriptors.items():
                    _unchanged_body(self.seen[object_id]["body"], descriptor, self.deadline)
                self.resident_terminal = {
                    "kind": "actual-parent-Popen-signed-OS-reaping",
                    "original_exit_code": outcome,
                    "resident_object_ids": residents,
                    "observed_monotonic": time.monotonic(),
                }
                self.done = True
        finally:
            self.server.close()
            for descriptor in self.descriptors.values():
                os.close(descriptor)
            self.descriptors.clear()
            self.active.clear()
            Path(self.address).unlink(missing_ok=True)
            self.socket_directory.cleanup()

    def abort(self) -> None:
        """Close owned IPC only; ordinary ToolAPI/guardian owns process cleanup."""
        if self.connection is not None:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        try:
            self.server.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.server.close()

    def finish(self, result: dict[str, Any]) -> dict[str, str]:
        """Called after actual OS reaping; enclosing ToolAPI must still close guardian."""
        self.compiled.verify(deadline=self.deadline)
        if (
            not self.eof
            or not self.done
            or self.peer is None
            or self.command is None
            or tuple(result["command"]) != self.command
            or result["pid"] != self.peer["pid"]
            or result["owner_pid"] != self.owner_pid
            or result["original_exit_code"] != 0
        ):
            raise ValueError("loader callbacks lack the same actual consuming tool's signed normal OS exit")
        raw: dict[str, Any] = {
            "schema_version": SCHEMA,
            "run_id": self.compiled.owner.run_id,
            "source_binding": [
                self.compiled.owner.source.reference.commit,
                self.compiled.owner.source.reference.source_identity,
            ],
            "compiler": self.compiled.binding,
            "purpose": self.purpose,
            "owner_pid": self.owner_pid,
            "consuming_process": self.peer,
            "command": list(self.command),
            "original_deadline_monotonic": self.deadline,
            "token_sha256": hashlib.sha256(self.token).hexdigest(),
            "environment_injections": self.environment_injections,
            "events": self.events,
            "opened": list(self.seen),
            "closed": self.closed,
            "complete_callbacks": True,
            "channel_eof": True,
            "original_exit_code": result["original_exit_code"],
            "resident_terminal": self.resident_terminal,
            "scope_limit": "this-actual-consuming-process-callback-and-kernel-map-cohort",
        }
        self.binding = write_json(self.root, self.directory / "loader-lifecycle.json", raw)
        remaining(self.deadline)
        return self.binding


def _header_segments(content: bytes, physical_bytes: int) -> list[tuple[int, int, int, int, int]]:
    """Read actual ELF headers without copying a large backing image into memory."""
    import struct

    if len(content) < 64:
        raise ValueError("loader actual ELF header is truncated")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", content)
    rows = []
    if (
        content[:7] != b"\x7fELF\x02\x01\x01"
        or header[9] != 56
        or not 0 < header[10] <= MAX_SEGMENTS
        or header[5] + header[9] * header[10] > len(content)
    ):
        raise ValueError("loader actual ELF program table exceeds its fixed ABI/bound")
    for index in range(header[10]):
        kind, flags, offset, address, _, size, memory, _ = struct.unpack_from("<II6Q", content, header[5] + index * 56)
        if kind == 1:
            if size > memory or offset + size > physical_bytes:
                raise ValueError("loader actual ELF segment exceeds its physical body")
            rows.append((address, memory, offset, size, flags))
    return rows


def _unchanged_body(observed: dict[str, Any], descriptor: int, deadline: float) -> None:
    before = identity(descriptor)
    digest, offset = hashlib.sha256(), 0
    while offset < before["size"]:
        remaining(deadline)
        piece = os.pread(descriptor, min(CHUNK, before["size"] - offset), offset)
        if not piece:
            raise ValueError("loader original resident backing body truncated before actual OS termination")
        digest.update(piece)
        offset += len(piece)
    if before != identity(descriptor) or before != observed["identity"] or digest.hexdigest() != observed["sha256"]:
        raise ValueError("loader resident backing body changed during its complete actual process lifetime")
