"""Genuine original Source custody of a live Linux filter's held pidfd status."""

from __future__ import annotations

import fcntl
import math
import os
import select
import socket
import sys
import time
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_linux_abi import (
    CREDS,
    EXIT,
    FORMAT,
    GET_INFO,
    GID_FIELDS,
    INFO_SCHEMA,
    MACHINES,
    PID,
    REQUEST_MASK,
    SIZE,
    UID_FIELDS,
    decode_exit_status,
    decode_info,
    request_bytes,
    require_kernel_release,
    validate_info_record,
    validate_live_info,
)
from infrastructure.reporting.native_crossref_protocol import peer_pid, process_birth
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess
from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-source-owned-linux-filter-pidfd-exit-v1"
MAX_EXIT_QUERIES = 32768
_KEY = object()


def require_linux_filter_exit_capability() -> None:
    if (
        not sys.platform.startswith("linux")
        or not callable(getattr(os, "pidfd_open", None))
        or not hasattr(select, "select")
        or sys.byteorder != "little"
        or os.uname().machine not in MACHINES
    ):
        raise ValueError("filter original Linux pidfd observer lacks its exact Source-selected supported ABI")
    require_kernel_release(os.uname().release)


def _handle(fd: int) -> dict[str, Any]:
    value = os.fstat(fd)
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    if not flags & fcntl.FD_CLOEXEC or value.st_ino <= 0:
        raise ValueError("filter actual held pidfd lacks its original stable close-on-exec identity")
    return {
        "descriptor": fd,
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "close_on_exec": True,
    }


def _query(fd: int, *, deadline: float) -> dict[str, Any]:
    remaining(deadline)
    raw = bytearray(request_bytes())
    begin = time.monotonic()
    result = fcntl.ioctl(fd, GET_INFO, raw, True)
    returned = time.monotonic()
    remaining(deadline)
    if type(result) is not int or result != 0:
        raise ValueError("filter actual pidfd ioctl did not return its successful original kernel result")
    return {
        "schema_version": INFO_SCHEMA,
        "ioctl": GET_INFO,
        "request_mask": REQUEST_MASK,
        "request_hex": request_bytes().hex(),
        "return_value": result,
        "raw_hex": raw.hex(),
        "decoded": decode_info(bytes(raw)),
        "begin": begin,
        "returned": returned,
    }


class SourceLinuxFilterExitObserver:
    """Only the genuine Source factory can bind the actual Popen's kernel peer."""

    def __init__(
        self,
        source: NativeSourceContext,
        reader: SnapshotReader,
        live: NativeLiveToolProcess,
        owner: NativeProducerOperation,
        descriptor: int,
        facts: dict[str, Any],
        *,
        deadline: float,
        key: object,
    ) -> None:
        if key is not _KEY:
            raise ValueError("filter Linux pidfd custody requires its actual original Source factory")
        self.source, self.reader, self.live, self.owner = source, reader, live, owner
        self.descriptor, self.facts, self.deadline = descriptor, facts, deadline
        self.closed = False
        self.observation: dict[str, Any] | None = None

    def _verify_owner(self) -> None:
        remaining(self.deadline)
        if current_native_producer_operation() is not self.owner or self.owner.source is not self.source:
            raise ValueError("filter original Linux pidfd lost its genuine enclosing Source owner")
        self.owner.verify(self.reader, run_id=self.owner.run_id, deadline=self.owner.deadline)

    def _verify_handle(self) -> None:
        remaining(self.deadline)
        if self.closed or _handle(self.descriptor) != self.facts["handle"]:
            raise ValueError("filter actual original pidfd closed or its held kernel handle changed")

    def _verify_live(self) -> dict[str, Any]:
        self._verify_owner()
        self.live.verify_live()
        self._verify_handle()
        if (
            process_birth(self.live.pid, deadline=self.deadline) != self.facts["parent"]
            or process_birth(self.facts["child"]["pid"], deadline=self.deadline) != self.facts["child"]
        ):
            raise ValueError("filter original Linux parent/peer birth changed before release")
        info = _query(self.descriptor, deadline=self.deadline)
        self._verify_handle()
        validate_live_info(info["decoded"], self.facts["child"])
        for name in GID_FIELDS:
            if info["decoded"][name] != self.facts["before_info"]["decoded"][name]:
                raise ValueError("filter original Linux peer credentials changed before release")
        return info

    def mark_admitted(self) -> None:
        if "admitted_at_monotonic" in self.facts:
            raise ValueError("filter original Linux peer cannot be admitted twice")
        self.facts["admission_info"] = self._verify_live()
        self.facts["admitted_at_monotonic"] = time.monotonic()
        remaining(self.deadline)

    def mark_released(self) -> None:
        if "admitted_at_monotonic" not in self.facts or "released_at_monotonic" in self.facts:
            raise ValueError("filter original Linux peer requires exactly one original admission and release")
        self.facts["release_info"] = self._verify_live()
        self.facts["released_at_monotonic"] = time.monotonic()
        remaining(self.deadline)

    def observe_exit(self) -> dict[str, Any]:
        """Readiness triggers a query; only the real returned EXIT mask is status."""
        self._verify_owner()
        self._verify_handle()
        if "released_at_monotonic" not in self.facts:
            raise ValueError("filter actual Linux status requires its original Source release")
        try:
            while True:
                try:
                    readable, _, _ = select.select([self.descriptor], [], [], remaining(self.deadline))
                    break
                except InterruptedError:
                    remaining(self.deadline)
            readiness = time.monotonic()
            remaining(self.deadline)
            if readable != [self.descriptor]:
                raise ValueError("filter held pidfd did not become ready within its original finite clock")
            for count in range(1, MAX_EXIT_QUERIES + 1):
                self._verify_handle()
                info = _query(self.descriptor, deadline=self.deadline)
                self._verify_handle()
                self.observation = {
                    **self.facts,
                    "readiness_at_monotonic": readiness,
                    "exit_info": info,
                    "query_count": count,
                    "decoded": None,
                    "observed_at_monotonic": info["returned"],
                }
                if info["decoded"]["mask"] & EXIT:
                    decoded = decode_exit_status(info["decoded"])
                    self.observation["decoded"] = decoded
                    if info["decoded"]["exit_code"] != 0 or decoded["kind"] != "exited" or decoded["exit_code"] != 0:
                        raise ValueError(
                            "filter actual Linux kernel EXIT status differs from required original success"
                        )
                    self._verify_owner()
                    return self.observation
                # Linux 6.15 stores exit_info at release_task, possibly after poll readiness.
                # Waiting on this bounded timer grants no exit proof and no fresh clock.
                select.select([], [], [], min(0.01, remaining(self.deadline)))
            raise ValueError(
                "filter held pidfd never returned its actual Linux EXIT status within the original query bound"
            )
        finally:
            self.close()

    def close(self) -> None:
        if not self.closed:
            os.close(self.descriptor)
            self.closed = True


def register_linux_filter_exit(
    source: NativeSourceContext,
    reader: SnapshotReader,
    live: NativeLiveToolProcess,
    connection: socket.socket,
    *,
    deadline: float,
) -> SourceLinuxFilterExitObserver:
    require_linux_filter_exit_capability()
    remaining(deadline)
    owner = current_native_producer_operation()
    if (
        type(source) is not NativeSourceContext
        or owner is None
        or owner.source is not source
        or type(live) is not NativeLiveToolProcess
        or not deadline <= live.deadline <= owner.deadline
    ):
        raise ValueError("filter Linux status requires its genuine original Source, actual Popen and one clock")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    live.verify_live()
    parent = process_birth(live.pid, deadline=deadline)
    child = process_birth(peer_pid(connection, deadline=deadline), deadline=deadline)
    if child["ppid"] != live.pid or parent["ppid"] != os.getpid() or child["platform"] != "Linux":
        raise ValueError("filter Linux status kernel peer belongs to a different actual Source/Pandoc owner")
    requested = time.monotonic()
    selected_pidfd_open = getattr(os, "pidfd_open", None)
    if not callable(selected_pidfd_open):
        raise ValueError("filter actual Linux pidfd opener is unavailable")
    descriptor = selected_pidfd_open(child["pid"], 0)
    if not isinstance(descriptor, int) or isinstance(descriptor, bool) or descriptor < 0:
        raise ValueError("filter actual Linux pidfd opener did not return a kernel descriptor")
    try:
        handle = _handle(descriptor)
        before = _query(descriptor, deadline=deadline)
        validate_live_info(before["decoded"], child)
        registered = time.monotonic()
        observer = SourceLinuxFilterExitObserver(
            source,
            reader,
            live,
            owner,
            descriptor,
            {
                "schema_version": SCHEMA,
                "run_id": owner.run_id,
                "observer_pid": os.getpid(),
                "parent": parent,
                "child": child,
                "handle": handle,
                "before_info": before,
                "abi": {
                    "platform": "Linux",
                    "machine": os.uname().machine,
                    "byteorder": sys.byteorder,
                    "format": FORMAT,
                    "size": SIZE,
                    "ioctl": GET_INFO,
                },
                "kernel_release": os.uname().release,
                "pidfd_open_flags": 0,
                "requested_at_monotonic": requested,
                "registered_at_monotonic": registered,
                "original_deadline_monotonic": deadline,
                "caller_deadline_monotonic": owner.deadline,
            },
            deadline=deadline,
            key=_KEY,
        )
        observer._verify_live()
        return observer
    except BaseException:
        os.close(descriptor)
        raise


def validate_linux_filter_kernel_exit(
    raw: Any,
    *,
    parent: dict[str, Any],
    child: dict[str, Any],
    observer_pid: int,
    run_id: str,
    original_deadline: float,
    caller_deadline: float,
    original_completion: float,
) -> None:
    """Validate externally authenticated original Linux facts through the fixed Source role."""
    fields = {
        "schema_version",
        "run_id",
        "observer_pid",
        "parent",
        "child",
        "handle",
        "before_info",
        "abi",
        "kernel_release",
        "pidfd_open_flags",
        "requested_at_monotonic",
        "registered_at_monotonic",
        "original_deadline_monotonic",
        "caller_deadline_monotonic",
        "admission_info",
        "release_info",
        "admitted_at_monotonic",
        "released_at_monotonic",
        "readiness_at_monotonic",
        "exit_info",
        "query_count",
        "decoded",
        "observed_at_monotonic",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
        or type(raw["observer_pid"]) is not int
        or raw["observer_pid"] != observer_pid
        or raw["parent"] != parent
        or raw["child"] != child
        or parent["platform"] != "Linux"
        or child["platform"] != "Linux"
        or type(raw["pidfd_open_flags"]) is not int
        or raw["pidfd_open_flags"] != 0
        or type(raw["query_count"]) is not int
        or not 0 < raw["query_count"] <= MAX_EXIT_QUERIES
    ):
        raise ValueError("filter original Linux status fieldset, owner, handle operation or Source role differs")
    require_kernel_release(raw["kernel_release"])
    abi = raw["abi"]
    if (
        not isinstance(abi, dict)
        or set(abi) != {"platform", "machine", "byteorder", "format", "size", "ioctl"}
        or abi["platform"] != "Linux"
        or abi["machine"] not in MACHINES
        or abi["byteorder"] != "little"
        or abi["format"] != FORMAT
        or type(abi["size"]) is not int
        or abi["size"] != SIZE
        or type(abi["ioctl"]) is not int
        or abi["ioctl"] != GET_INFO
    ):
        raise ValueError("filter original Linux status supplied a different Source-declared platform ABI")
    handle = raw["handle"]
    if (
        not isinstance(handle, dict)
        or set(handle) != {"descriptor", "device", "inode", "mode", "close_on_exec"}
        or any(type(handle[name]) is not int or handle[name] < 0 for name in ("descriptor", "device", "inode", "mode"))
        or handle["inode"] <= 0
        or handle["close_on_exec"] is not True
    ):
        raise ValueError("filter original Linux pidfd handle identity differs")
    clocks = (
        "requested_at_monotonic",
        "registered_at_monotonic",
        "admitted_at_monotonic",
        "released_at_monotonic",
        "readiness_at_monotonic",
        "observed_at_monotonic",
        "original_deadline_monotonic",
        "caller_deadline_monotonic",
    )
    if any(type(raw[name]) not in (int, float) or not math.isfinite(raw[name]) for name in clocks):
        raise ValueError("filter original Linux status has an invalid finite original clock")
    requested, registered, admitted, released, ready, observed, deadline, caller = (raw[name] for name in clocks)
    if (
        deadline != original_deadline
        or caller != caller_deadline
        or not 0 < requested <= registered <= admitted <= released <= ready <= observed < deadline <= caller
        or not observed <= original_completion < caller
    ):
        raise ValueError("filter original Linux handle/admission/release/status clocks differ")
    infos = {}
    for name, lower, upper in (
        ("before_info", requested, registered),
        ("admission_info", registered, admitted),
        ("release_info", admitted, released),
        ("exit_info", ready, observed),
    ):
        record = raw[name]
        infos[name] = validate_info_record(record)
        if (
            any(
                type(record[key]) not in (int, float) or not math.isfinite(record[key]) for key in ("begin", "returned")
            )
            or not lower <= record["begin"] <= record["returned"] <= upper
        ):
            raise ValueError("filter original Linux status query falls outside its original custody phase")
        if name != "exit_info":
            validate_live_info(infos[name], child)
    before = infos["before_info"]
    for name in ("admission_info", "release_info"):
        if any(infos[name][key] != before[key] for key in GID_FIELDS):
            raise ValueError("filter original Linux identity changed before its original release")
    after = infos["exit_info"]
    if after["mask"] & (PID | CREDS):
        if (
            after["pid"] != child["pid"]
            or after["tgid"] != child["pid"]
            or any(after[key] != before[key] for key in (*UID_FIELDS, *GID_FIELDS))
        ):
            raise ValueError("filter held original Linux pidfd returned another process's status credentials")
    decoded = decode_exit_status(after)
    if (
        after["exit_code"] != 0
        or decoded["kind"] != "exited"
        or decoded["exit_code"] != 0
        or not isinstance(raw["decoded"], dict)
        or set(raw["decoded"]) != {"kind", "exit_code", "signal", "core_dumped"}
        or type(raw["decoded"]["exit_code"]) is not int
        or raw["decoded"]["core_dumped"] is not False
        or raw["decoded"] != decoded
    ):
        raise ValueError("filter actual original Linux kernel EXIT status differs from required success")
