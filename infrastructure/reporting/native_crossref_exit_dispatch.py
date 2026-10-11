"""Fixed Source-owned original-host roles for Linux and Darwin exit status."""

from __future__ import annotations

import socket
import sys
from typing import Any

from infrastructure.reporting.native_crossref_exit import (
    SourceFilterExitObserver as DarwinFilterExitObserver,
    register_filter_exit as register_darwin_filter_exit,
    require_filter_exit_capability as require_darwin_filter_exit_capability,
    validate_filter_kernel_exit as validate_darwin_filter_kernel_exit,
)
from infrastructure.reporting.native_crossref_linux_exit import (
    SourceLinuxFilterExitObserver,
    register_linux_filter_exit,
    require_linux_filter_exit_capability,
    validate_linux_filter_kernel_exit,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SourceFilterExitObserver = DarwinFilterExitObserver | SourceLinuxFilterExitObserver
ORIGINAL_HOST_ROSTER = ("Linux", "Darwin")


def require_filter_exit_capability() -> None:
    if sys.platform == "darwin":
        require_darwin_filter_exit_capability()
    elif sys.platform.startswith("linux"):
        require_linux_filter_exit_capability()
    else:
        raise ValueError("filter original Source host is outside the fixed Linux/Darwin roster")


def register_filter_exit(
    source: NativeSourceContext,
    reader: SnapshotReader,
    live: NativeLiveToolProcess,
    connection: socket.socket,
    *,
    deadline: float,
) -> SourceFilterExitObserver:
    require_filter_exit_capability()
    if sys.platform == "darwin":
        return register_darwin_filter_exit(source, reader, live, connection, deadline=deadline)
    return register_linux_filter_exit(source, reader, live, connection, deadline=deadline)


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
    """Enclosing genuine original custody authenticates identities before this DATA call."""
    if parent["platform"] != child["platform"] or parent["platform"] not in ORIGINAL_HOST_ROSTER:
        raise ValueError("filter original kernel status is outside its Source-owned host-role roster")
    validator = (
        validate_darwin_filter_kernel_exit if parent["platform"] == "Darwin" else validate_linux_filter_kernel_exit
    )
    validator(
        raw,
        parent=parent,
        child=child,
        observer_pid=observer_pid,
        run_id=run_id,
        original_deadline=original_deadline,
        caller_deadline=caller_deadline,
        original_completion=original_completion,
    )
