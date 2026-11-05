"""Finite kernel-identified filter IPC; messages never nominate a process PID."""

from __future__ import annotations

import ctypes
import json
import os
import socket
import struct
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining

MAX_MESSAGE = 16 * 1024


class _BSDInfo(ctypes.Structure):
    _fields_ = (
        [
            (name, ctypes.c_uint32)
            for name in (
                "flags",
                "status",
                "xstatus",
                "pid",
                "ppid",
                "uid",
                "gid",
                "ruid",
                "rgid",
                "svuid",
                "svgid",
                "reserved",
            )
        ]
        + [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)]
        + [(name, ctypes.c_uint32) for name in ("nfiles", "pgid", "jobc", "tdev", "tpgid")]
        + [
            ("nice", ctypes.c_int32),
            ("birth_seconds", ctypes.c_uint64),
            ("birth_microseconds", ctypes.c_uint64),
        ]
    )


def process_birth(pid: int, *, deadline: float) -> dict[str, Any]:
    """Read actual kernel PID/parent/birth/UID; no receipt supplies these facts."""
    remaining(deadline)
    if type(pid) is not int or pid <= 0:
        raise ValueError("filter process identity requires a positive observed PID")
    row: dict[str, Any]
    if sys.platform == "darwin":
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        query = library.proc_pidinfo
        query.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        query.restype = ctypes.c_int
        value = _BSDInfo()
        if (
            ctypes.sizeof(value) != 136
            or query(pid, 3, 0, ctypes.byref(value), ctypes.sizeof(value)) != ctypes.sizeof(value)
            or value.status == 5  # Darwin sys/proc.h SZOMB: no longer a live peer.
        ):
            raise ValueError("filter process BSD identity is absent or ambiguous")
        row = {
            "pid": value.pid,
            "ppid": value.ppid,
            "uid": value.uid,
            "birth": [value.birth_seconds, value.birth_microseconds],
            "platform": "Darwin",
        }
    elif sys.platform.startswith("linux"):
        directory = Path("/proc") / str(pid)
        before = directory.stat()
        raw = (directory / "stat").read_text()
        fields = raw[raw.rfind(")") + 2 :].split()
        if before.st_ino != directory.stat().st_ino or len(fields) < 20 or fields[0] == "Z":
            raise ValueError("filter process Linux identity is absent or ambiguous")
        row = {
            "pid": pid,
            "ppid": int(fields[1]),
            "uid": before.st_uid,
            "birth": [int(fields[19])],
            "platform": "Linux",
        }
    else:
        raise ValueError("filter process identity requires the declared Linux or Darwin kernel")
    remaining(deadline)
    if row["pid"] != pid or row["uid"] != os.getuid() or not any(row["birth"]):
        raise ValueError("filter peer PID/birth/UID differs from actual current kernel ownership")
    return row


def peer_pid(connection: socket.socket, *, deadline: float) -> int:
    remaining(deadline)
    if sys.platform == "darwin":
        # XNU sys/un.h: SOL_LOCAL=0, LOCAL_PEERPID=0x002.
        pid = struct.unpack("=i", connection.getsockopt(0, 0x002, 4))[0]
    elif sys.platform.startswith("linux"):
        pid, uid, _ = struct.unpack("=iii", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid != os.getuid():
            raise ValueError("filter socket peer has a different actual kernel UID")
    else:
        raise ValueError("filter peer identity is unsupported on this platform")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError("filter kernel socket peer PID is not a positive original integer")
    process_birth(pid, deadline=deadline)
    return pid


def _read(connection: socket.socket, size: int, deadline: float) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        connection.settimeout(remaining(deadline))
        piece = connection.recv(size - len(chunks))
        if not piece:
            raise ValueError("filter side channel closed before its exact complete message")
        chunks.extend(piece)
    return bytes(chunks)


def receive(connection: socket.socket, *, deadline: float) -> dict[str, Any]:
    count = struct.unpack("!I", _read(connection, 4, deadline))[0]
    if not 0 < count <= MAX_MESSAGE:
        raise ValueError("filter side channel exceeds its finite message bound")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("filter side channel repeats a message field")
            result[key] = value
        return result

    value = json.loads(_read(connection, count, deadline), object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError("filter side channel requires an exact Source-owned object")
    return value


def send(connection: socket.socket, value: dict[str, Any], *, deadline: float) -> None:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if not 0 < len(raw) <= MAX_MESSAGE:
        raise ValueError("filter side channel exceeds its finite message bound")
    connection.settimeout(remaining(deadline))
    connection.sendall(struct.pack("!I", len(raw)) + raw)
    remaining(deadline)
