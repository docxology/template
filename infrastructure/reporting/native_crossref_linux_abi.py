"""Fixed Linux 6.15 pidfd_info ABI and original-platform DATA decoding."""

from __future__ import annotations

import re
import struct
from typing import Any

INFO_SCHEMA = "template-linux-pidfd-info-v615-v1"
FORMAT = "<QQ11Ii"
SIZE = 64
GET_INFO = 0xC040FF0B
PID, CREDS, CGROUP, EXIT = 1, 2, 4, 8
REQUEST_MASK = EXIT
FIELDS = (
    "mask",
    "cgroupid",
    "pid",
    "tgid",
    "ppid",
    "ruid",
    "rgid",
    "euid",
    "egid",
    "suid",
    "sgid",
    "fsuid",
    "fsgid",
    "exit_code",
)
UID_FIELDS = ("ruid", "euid", "suid", "fsuid")
GID_FIELDS = ("rgid", "egid", "sgid", "fsgid")
MACHINES = ("x86_64", "aarch64")


def require_kernel_release(release: Any) -> None:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$", release) if isinstance(release, str) else None
    if match is None or tuple(map(int, match.groups())) < (6, 15, 0):
        raise ValueError("filter original Linux kernel predates the required pidfd EXIT status extension")


def request_bytes() -> bytes:
    if struct.calcsize(FORMAT) != SIZE:
        raise ValueError("filter Source pidfd ABI has an inconsistent physical struct size")
    return struct.pack(FORMAT, REQUEST_MASK, *([0] * (len(FIELDS) - 1)))


def decode_info(raw: bytes) -> dict[str, int]:
    if len(raw) != SIZE:
        raise ValueError("filter pidfd ioctl returned a different exact original struct size")
    result = dict(zip(FIELDS, struct.unpack(FORMAT, raw), strict=True))
    mask = result["mask"]
    if mask & ~(PID | CREDS | CGROUP | EXIT) or bool(mask & PID) != bool(mask & CREDS):
        raise ValueError("filter pidfd ioctl returned unsupported or incomplete original field masks")
    if not mask & CGROUP and result["cgroupid"] != 0:
        raise ValueError("filter pidfd ioctl supplied an undeclared original cgroup field")
    if not mask & EXIT and result["exit_code"] != 0:
        raise ValueError("filter pidfd status lacks its actual original EXIT return mask")
    if not mask & PID and any(result[name] != 0 for name in FIELDS[2:13]):
        raise ValueError("filter reaped pidfd supplied identity data without its actual return masks")
    return result


def validate_info_record(value: Any) -> dict[str, int]:
    fields = {
        "schema_version",
        "ioctl",
        "request_mask",
        "request_hex",
        "return_value",
        "raw_hex",
        "decoded",
        "begin",
        "returned",
    }
    if (
        not isinstance(value, dict)
        or set(value) != fields
        or value["schema_version"] != INFO_SCHEMA
        or type(value["ioctl"]) is not int
        or value["ioctl"] != GET_INFO
        or type(value["request_mask"]) is not int
        or value["request_mask"] != REQUEST_MASK
        or value["request_hex"] != request_bytes().hex()
        or type(value["return_value"]) is not int
        or value["return_value"] != 0
        or not isinstance(value["raw_hex"], str)
        or re.fullmatch(r"[0-9a-f]{128}", value["raw_hex"]) is None
    ):
        raise ValueError("filter original pidfd query differs from its exact Source-selected ioctl")
    decoded = decode_info(bytes.fromhex(value["raw_hex"]))
    if (
        not isinstance(value["decoded"], dict)
        or set(value["decoded"]) != set(FIELDS)
        or any(type(number) is not int for number in value["decoded"].values())
        or value["decoded"] != decoded
    ):
        raise ValueError("filter retained original pidfd struct decode differs from its kernel bytes")
    return decoded


def validate_live_info(info: dict[str, int], child: dict[str, Any]) -> None:
    if (
        info["mask"] not in {PID | CREDS, PID | CREDS | CGROUP}
        or info["pid"] != child["pid"]
        or info["tgid"] != child["pid"]
        or info["ppid"] != child["ppid"]
        or any(info[name] != child["uid"] for name in UID_FIELDS)
    ):
        raise ValueError("filter held pidfd identity/credentials differ from its original blocked kernel peer")


def decode_exit_status(info: dict[str, int]) -> dict[str, Any]:
    status = info["exit_code"]
    if not info["mask"] & EXIT or not 0 <= status <= 0xFFFF:
        raise ValueError("filter held pidfd lacks its independently observed actual Linux EXIT status")
    signal = status & 0x7F
    if signal == 0:
        return {"kind": "exited", "exit_code": (status >> 8) & 0xFF, "signal": None, "core_dumped": False}
    if signal != 0x7F:
        return {"kind": "signaled", "exit_code": None, "signal": signal, "core_dumped": bool(status & 0x80)}
    raise ValueError("filter pidfd returned a stopped or continued value instead of actual terminal EXIT")
