"""Process-local Source-admitted producer custody, separate from portable readback.

The actual ToolAPI registers direct supervised observations while this owner is
live. Retained JSON never constructs an operation or an original tool token.
A completed external original is required later for portable validation.
"""

from __future__ import annotations

import math
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class _OriginalTool:
    artifact_relative: str
    artifact_sha256: str
    process_relative: str
    process_sha256: str
    pid: int
    owner_pid: int
    guardian_pid: int
    original_exit_code: int
    command: tuple[str, ...]
    completion: float


class NativeProducerOperation:
    """One genuine live Source owner; tools come directly from actual ToolAPI."""

    def __init__(self, source: NativeSourceContext, run_id: str, deadline: float) -> None:
        if not isinstance(source, NativeSourceContext) or not isinstance(run_id, str) or not run_id:
            raise ValueError("native producer requires genuine admitted Source and run identity")
        if type(deadline) not in (float, int) or not math.isfinite(deadline):
            raise ValueError("native producer requires the existing finite original clock")
        self.source = source
        self.run_id = run_id
        self.deadline = float(deadline)
        self.owner_pid = os.getpid()
        self._tools: dict[str, _OriginalTool] = {}
        self._closed = False

    def verify(self, reader: SnapshotReader, *, run_id: str, deadline: float) -> None:
        if self._closed or _CURRENT.get() is not self or os.getpid() != self.owner_pid:
            raise ValueError("native producer custody is not this actual live process owner")
        if run_id != self.run_id or run_id != self.source.bindings.run_id or not deadline <= self.deadline:
            raise ValueError("native producer run or original clock differs")
        remaining(self.deadline)
        self.source.verify_correspondence(self.source.reference, reader.root, reader, self.deadline)
        remaining(self.deadline)

    def _retain_actual_tool(
        self,
        root: Path,
        binding: dict[str, str],
        process_binding: dict[str, str],
        result: dict[str, Any],
        *,
        run_id: str,
        deadline: float,
    ) -> None:
        """Called only by ToolAPI immediately after actual Popen/retention, not a parser."""
        reader = SnapshotReader(root)
        self.verify(reader, run_id=run_id, deadline=deadline)
        selected = reader.read(binding["path"])
        process = reader.read(process_binding["path"])
        complete = time.monotonic()
        if (
            selected.sha256 != binding["sha256"]
            or process.sha256 != process_binding["sha256"]
            or result.get("accepted") is not True
            or result.get("timed_out") is not False
            or type(result.get("pid")) is not int
            or result["pid"] <= 0
            or result.get("owner_pid") != self.owner_pid
            or type(result.get("original_exit_code")) is not int
            or type(result.get("cleanup", {}).get("guardian_pid")) is not int
            or not complete < deadline <= self.deadline
            or selected.relative in self._tools
        ):
            raise ValueError("native ToolAPI cannot retain incomplete or duplicate actual original custody")
        self._tools[selected.relative] = _OriginalTool(
            selected.relative,
            selected.sha256,
            process.relative,
            process.sha256,
            result["pid"],
            self.owner_pid,
            result["cleanup"]["guardian_pid"],
            result["original_exit_code"],
            tuple(result["command"]),
            complete,
        )
        if not reader.unchanged():
            raise ValueError("native actual ToolAPI artifact changed during live custody retention")
        remaining(self.deadline)

    def validate_tool(self, binding: object, raw: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
        self.verify(reader, run_id=run_id, deadline=self.deadline)
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("live native tool requires an exact retained binding")
        original = self._tools.get(binding["path"])
        selected = reader.read(binding["path"])
        if (
            original is None
            or binding["sha256"] != original.artifact_sha256
            or selected.sha256 != original.artifact_sha256
            or selected.json_object() != raw
            or raw.get("native_process_artifact")
            != {"path": original.process_relative, "sha256": original.process_sha256}
            or raw.get("pid") != original.pid
            or raw.get("owner_pid") != original.owner_pid
            or raw.get("original_exit_code") != original.original_exit_code
            or tuple(raw.get("command", ())) != original.command
        ):
            raise ValueError("native tool is absent from the actual live ToolAPI custodian")
        from infrastructure.reporting.native_tool_replay import validate_native_tool_data

        validate_native_tool_data(raw, reader, original_deadline=self.deadline, original_completion=original.completion)
        self.verify(reader, run_id=run_id, deadline=self.deadline)


_CURRENT: ContextVar[NativeProducerOperation | None] = ContextVar("template_native_producer", default=None)


def current_native_producer_operation() -> NativeProducerOperation | None:
    """Return the actual process-local owner; a child must admit its own Source."""
    operation = _CURRENT.get()
    return operation if operation is not None and operation.owner_pid == os.getpid() and not operation._closed else None


@contextmanager
def native_producer_operation(
    source: NativeSourceContext, *, run_id: str, deadline: float
) -> Iterator[NativeProducerOperation]:
    """Begin only from genuine admitted Source, and never start another clock."""
    from infrastructure.reporting.native_format_joint_source import _require_installed_sdk

    _require_installed_sdk(source.bindings.expected_implementation_bytes)
    if _CURRENT.get() is not None:
        raise ValueError("native producer cannot replace another live original owner")
    operation = NativeProducerOperation(source, run_id, deadline)
    token = _CURRENT.set(operation)
    try:
        operation.verify(SnapshotReader(source.bindings.current_root), run_id=run_id, deadline=deadline)
        yield operation
    finally:
        operation._closed = True
        _CURRENT.reset(token)


def validate_live_native_tool(binding: object, raw: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
    operation = reader.native_producer_operation
    if not isinstance(operation, NativeProducerOperation):
        raise ValueError("native producer validation requires its actual live Source owner")
    operation.validate_tool(binding, raw, reader, run_id=run_id)
