"""Observe an authenticated live Darwin filter's kernel exit status before replay."""

from __future__ import annotations

import math
import os
import select
import socket
import sys
import time
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_protocol import peer_pid, process_birth
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess
from infrastructure.reporting.native_tool_producer import (
    NativeProducerOperation,
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-source-owned-darwin-filter-kernel-exit-v1"
# Public Darwin sys/event.h ABI. Python's select module does not expose these two.
NOTE_EXITSTATUS = 0x04000000
EV_RECEIPT = 0x0040
FILTER_PROC = -5
NOTE_EXIT = 0x80000000
EV_ADD, EV_ENABLE, EV_ONESHOT, EV_CLEAR = 0x0001, 0x0004, 0x0010, 0x0020
EV_ERROR, EV_EOF = 0x4000, 0x8000
REQUEST_FLAGS = EV_ADD | EV_ENABLE | EV_ONESHOT | EV_CLEAR | EV_RECEIPT
REQUEST_FFLAGS = NOTE_EXIT | NOTE_EXITSTATUS
_KEY = object()
_EVENT_FIELDS = {"ident", "filter", "flags", "fflags", "data", "udata"}


def require_filter_exit_capability() -> None:
    """Refuse unsupported original topology before launching Pandoc or its child."""
    if sys.platform != "darwin" or not all(hasattr(select, name) for name in ("kqueue", "kevent")):
        raise ValueError("filter kernel exit-status custody requires the original Darwin kqueue observer")
    for name, value in (
        ("KQ_FILTER_PROC", FILTER_PROC),
        ("KQ_NOTE_EXIT", NOTE_EXIT),
        ("KQ_EV_ADD", EV_ADD),
        ("KQ_EV_ENABLE", EV_ENABLE),
        ("KQ_EV_ONESHOT", EV_ONESHOT),
        ("KQ_EV_CLEAR", EV_CLEAR),
        ("KQ_EV_ERROR", EV_ERROR),
        ("KQ_EV_EOF", EV_EOF),
    ):
        if getattr(select, name, None) != value:
            raise ValueError("filter original kqueue API differs from the declared Darwin ABI")


def _event(value: select.kevent) -> dict[str, int]:
    return {name: int(getattr(value, name)) for name in _EVENT_FIELDS}


def _event_fields(value: Any, *, pid: int, cookie: int) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != _EVENT_FIELDS
        or any(type(number) is not int for number in value.values())
        or value["ident"] != pid
        or value["filter"] != FILTER_PROC
        or value["udata"] != cookie
    ):
        raise ValueError("filter retained kernel event is absent or belongs to another registration")


def _receipt(value: Any, *, pid: int, cookie: int) -> None:
    _event_fields(value, pid=pid, cookie=cookie)
    if value["data"] != 0 or value["fflags"] != REQUEST_FFLAGS or value["flags"] != (REQUEST_FLAGS | EV_ERROR):
        raise ValueError("filter kernel registration did not return its exact successful receipt")


def _exit_event(value: Any, *, pid: int, cookie: int) -> dict[str, Any]:
    _event_fields(value, pid=pid, cookie=cookie)
    if (
        value["fflags"] != REQUEST_FFLAGS
        or value["flags"] & (EV_EOF | EV_ONESHOT) != (EV_EOF | EV_ONESHOT)
        or value["flags"] & ~(REQUEST_FLAGS | EV_EOF)
        or not 0 <= value["data"] <= 0xFFFF
    ):
        raise ValueError("filter actual kernel event lacks an independently observed Darwin exit status")
    status = value["data"]
    signal = status & 0x7F
    # Darwin wait.h: NOTE_EXIT data is the low 16 bits of the real p_xstat.
    if signal == 0:
        decoded = {"kind": "exited", "exit_code": (status >> 8) & 0xFF, "signal": None, "core_dumped": False}
    elif signal != 0x7F:
        decoded = {"kind": "signaled", "exit_code": None, "signal": signal, "core_dumped": bool(status & 0x80)}
    else:
        raise ValueError("filter kernel event carries a stopped or continued status instead of terminal exit")
    return decoded


class SourceFilterExitObserver:
    """One live kernel registration held by the genuine Source/Pandoc owner."""

    def __init__(
        self,
        source: NativeSourceContext,
        reader: SnapshotReader,
        live: NativeLiveToolProcess,
        owner: NativeProducerOperation,
        queue: select.kqueue,
        facts: dict[str, Any],
        *,
        deadline: float,
        key: object,
    ) -> None:
        if key is not _KEY:
            raise ValueError("filter kernel observer requires the original live Source registration factory")
        self.source, self.reader, self.live, self.owner = source, reader, live, owner
        self.queue, self.facts, self.deadline = queue, facts, deadline
        self.closed = False
        self.observation: dict[str, Any] | None = None

    def _verify_owner(self) -> None:
        remaining(self.deadline)
        if current_native_producer_operation() is not self.owner or self.owner.source is not self.source:
            raise ValueError("filter kernel observer lost its genuine original Source owner")
        self.owner.verify(self.reader, run_id=self.owner.run_id, deadline=self.owner.deadline)

    def _verify_live(self) -> None:
        self._verify_owner()
        self.live.verify_live()
        if self.closed or self.queue.control([], 1, 0):
            raise ValueError("filter exited or its original kernel observer closed before Source output release")
        if (
            process_birth(self.live.pid, deadline=self.deadline) != self.facts["parent"]
            or process_birth(self.facts["child"]["pid"], deadline=self.deadline) != self.facts["child"]
        ):
            raise ValueError("filter original kernel identities changed after successful registration")

    def mark_admitted(self) -> None:
        self._verify_live()
        if "admitted_at_monotonic" in self.facts:
            raise ValueError("filter kernel observer cannot admit the original worker twice")
        self.facts["admitted_at_monotonic"] = time.monotonic()
        remaining(self.deadline)

    def mark_released(self) -> None:
        self._verify_live()
        if "admitted_at_monotonic" not in self.facts or "released_at_monotonic" in self.facts:
            raise ValueError("filter kernel observer requires exactly one original admission and release")
        self.facts["released_at_monotonic"] = time.monotonic()
        remaining(self.deadline)

    def observe_exit(self) -> dict[str, Any]:
        """Wait only within the original phase clock; never reap or signal a peer."""
        self._verify_owner()
        if self.closed or "released_at_monotonic" not in self.facts:
            raise ValueError("filter actual kernel exit requires its original open observer and release")
        try:
            while True:
                try:
                    events = self.queue.control([], 1, remaining(self.deadline))
                    break
                except InterruptedError:
                    remaining(self.deadline)
            observed = time.monotonic()
            remaining(self.deadline)
            if len(events) != 1:
                raise ValueError("filter original kernel exit was not observed inside its original finite clock")
            raw = _event(events[0])
            self.observation = {
                **self.facts,
                "event": raw,
                "decoded": None,
                "observed_at_monotonic": observed,
            }
            decoded = _exit_event(raw, pid=self.facts["child"]["pid"], cookie=self.facts["cookie"])
            self.observation["decoded"] = decoded
            if raw["data"] != 0 or decoded["kind"] != "exited" or decoded["exit_code"] != 0:
                raise ValueError("filter actual kernel exit status differs from required original success")
            self._verify_owner()
            return self.observation
        finally:
            self.close()

    def close(self) -> None:
        if not self.closed:
            self.queue.close()
            self.closed = True


def register_filter_exit(
    source: NativeSourceContext,
    reader: SnapshotReader,
    live: NativeLiveToolProcess,
    connection: socket.socket,
    *,
    deadline: float,
) -> SourceFilterExitObserver:
    """Attach to the actual kernel peer while Source keeps it blocked on ready."""
    remaining(deadline)
    require_filter_exit_capability()
    owner = current_native_producer_operation()
    if (
        type(source) is not NativeSourceContext
        or owner is None
        or owner.source is not source
        or type(live) is not NativeLiveToolProcess
        or not deadline <= live.deadline <= owner.deadline
    ):
        raise ValueError("filter kernel registration requires the genuine original Source/live Pandoc and clock")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    live.verify_live()
    parent = process_birth(live.pid, deadline=deadline)
    child = process_birth(peer_pid(connection, deadline=deadline), deadline=deadline)
    if child["ppid"] != live.pid or parent["ppid"] != os.getpid():
        raise ValueError("filter kernel registration belongs to a different actual Source/Pandoc child")
    # A per-registration kernel udata correlation label; it grants no custody.
    cookie = int.from_bytes(os.urandom(8), "little") & 0x7FFFFFFF or 1
    requested = time.monotonic()
    queue = select.kqueue()
    try:
        change = select.kevent(
            child["pid"], filter=FILTER_PROC, flags=REQUEST_FLAGS, fflags=REQUEST_FFLAGS, udata=cookie
        )
        receipts = queue.control([change], 1, 0)
        registered = time.monotonic()
        remaining(deadline)
        if len(receipts) != 1:
            raise ValueError("filter kernel registration omitted its independent original receipt")
        receipt = _event(receipts[0])
        _receipt(receipt, pid=child["pid"], cookie=cookie)
        observer = SourceFilterExitObserver(
            source,
            reader,
            live,
            owner,
            queue,
            {
                "schema_version": SCHEMA,
                "run_id": owner.run_id,
                "observer_pid": os.getpid(),
                "parent": parent,
                "child": child,
                "cookie": cookie,
                "request_flags": REQUEST_FLAGS,
                "request_fflags": REQUEST_FFLAGS,
                "registration_receipt": receipt,
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
        queue.close()
        raise


def validate_filter_kernel_exit(
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
    """Validate externally authenticated original DATA without consulting a new kernel."""
    fields = {
        "schema_version",
        "run_id",
        "observer_pid",
        "parent",
        "child",
        "cookie",
        "request_flags",
        "request_fflags",
        "registration_receipt",
        "requested_at_monotonic",
        "registered_at_monotonic",
        "original_deadline_monotonic",
        "caller_deadline_monotonic",
        "admitted_at_monotonic",
        "released_at_monotonic",
        "observed_at_monotonic",
        "event",
        "decoded",
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
        or parent["platform"] != "Darwin"
        or child["platform"] != "Darwin"
        or type(raw["cookie"]) is not int
        or not 0 < raw["cookie"] <= 0x7FFFFFFF
        or type(raw["request_flags"]) is not int
        or raw["request_flags"] != REQUEST_FLAGS
        or type(raw["request_fflags"]) is not int
        or raw["request_fflags"] != REQUEST_FFLAGS
    ):
        raise ValueError("filter original kernel exit custody fieldset, owner or actual registration differs")
    clock_fields = (
        "requested_at_monotonic",
        "registered_at_monotonic",
        "admitted_at_monotonic",
        "released_at_monotonic",
        "observed_at_monotonic",
        "original_deadline_monotonic",
        "caller_deadline_monotonic",
    )
    if any(type(raw[name]) not in (int, float) or not math.isfinite(raw[name]) for name in clock_fields):
        raise ValueError("filter original kernel exit contains an invalid original finite clock")
    requested, registered, admitted, released, observed, deadline, caller = (raw[name] for name in clock_fields)
    if (
        deadline != original_deadline
        or caller != caller_deadline
        or not 0 < requested <= registered <= admitted <= released <= observed < deadline <= caller
        or not observed <= original_completion < caller
    ):
        raise ValueError("filter original kernel registration, admission, release and exit clocks differ")
    _receipt(raw["registration_receipt"], pid=child["pid"], cookie=raw["cookie"])
    decoded = _exit_event(raw["event"], pid=child["pid"], cookie=raw["cookie"])
    if (
        raw["event"]["data"] != 0
        or decoded["kind"] != "exited"
        or decoded["exit_code"] != 0
        or not isinstance(raw["decoded"], dict)
        or set(raw["decoded"]) != {"kind", "exit_code", "signal", "core_dumped"}
        or type(raw["decoded"]["exit_code"]) is not int
        or raw["decoded"]["core_dumped"] is not False
        or raw["decoded"] != decoded
    ):
        raise ValueError("filter retained kernel wait-status decode differs from its original Darwin event")
