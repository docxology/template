"""Fixed Darwin print ownership from actual worker/tools and original supervision.

Live ToolAPI ownership is distinct from completed original replay. JSON never
enters the worker role or constructs an original supervisor capability.
"""

from __future__ import annotations

import os
import math
import json
import hashlib
import platform
import subprocess
import sys
import time
import types
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Iterator

from infrastructure.project.auxiliary_print_code import require_entry, validate_code
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_CURRENT: ContextVar[AuxiliaryPrintProducerOperation | None] = ContextVar("auxiliary_print_producer", default=None)
_ORIGINAL = object()


@dataclass(frozen=True)
class _ToolEvent:
    artifact: str
    sha256: str
    process: str
    process_sha256: str
    original_deadline: float
    observed_completion: float


def _tools(raw: dict[str, Any]) -> tuple[dict[str, str], ...]:
    tools = list(raw["versions"].values())
    for row in raw["prints"]:
        tools.extend(row["raster"]["tool_artifacts"])
        if row["kind"] == "newspaper":
            tools.extend(row["source"]["raster"]["tool_artifacts"])
    if len(tools) != 8 or len({item["path"] for item in tools}) != 8:
        raise ValueError("auxiliary print needs its exact eight original native events")
    return tuple(tools)


class AuxiliaryPrintProducerOperation:
    """Only the live fixed audited worker can hold and register actual events."""

    def __init__(self, root: Path, directory: Path) -> None:
        self.held = require_entry(root)
        self.root, self.directory = root, directory
        self.run_id, self.deadline = self.held["run_id"], self.held["deadline"]
        self.pid = os.getpid()
        self._events: dict[str, _ToolEvent] = {}
        self.witness: dict[str, str] | None = None
        from infrastructure.reporting.native_print_witness import source_inventory

        from infrastructure.core.files.secure_write import read_bytes_confined
        from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

        spec = json_object_from_bytes(read_bytes_confined(root, Path(self.held["spec_path"])))
        expected = (root / spec["raw_path"]).parent / "print-witness"
        from infrastructure.project.public_acceptance_evidence import evidence_directory

        evidence_directory(root, directory, fresh=True)
        if platform.system() != "Darwin" or directory.exists() or directory != expected:
            raise ValueError("auxiliary print owner requires its fresh actual Darwin evidence directory")
        self.source = source_inventory(root, original=True)

    def verify(self) -> None:
        if _CURRENT.get() is not self or self.pid != os.getpid() or require_entry(self.root) != self.held:
            raise ValueError("auxiliary print owner is not the current actual fixed worker")
        remaining(self.deadline)
        from infrastructure.reporting.native_print_witness import source_inventory

        if source_inventory(self.root, original=True) != self.source:
            raise ValueError("auxiliary print Source changed during its actual operation")

    def retain_actual_tool(
        self,
        root: Path,
        binding: dict[str, str],
        process: dict[str, str],
        result: dict[str, Any],
        *,
        run_id: str,
        deadline: float,
    ) -> None:
        from infrastructure.reporting.native_format_acceptance_checks import native_tool_record

        if sys._getframe(1).f_code is not native_tool_record.__code__:
            raise ValueError("auxiliary print events can only come from the actual Source ToolAPI")
        self.verify()
        reader = SnapshotReader(root)
        selected, observed = reader.read(binding["path"]), reader.read(process["path"])
        now = time.monotonic()
        if (
            root != self.root
            or run_id != self.run_id
            or deadline != self.deadline
            or not selected.path.is_relative_to(self.directory)
            or selected.sha256 != binding["sha256"]
            or observed.sha256 != process["sha256"]
            or result.get("owner_pid") != self.pid
            or result.get("accepted") is not True
            or result.get("timed_out") is not False
            or result.get("original_exit_code") != 0
            or selected.relative in self._events
            or now >= deadline
        ):
            raise ValueError("auxiliary print cannot adopt incomplete or unrelated actual ToolAPI events")
        self._events[selected.relative] = _ToolEvent(
            selected.relative, selected.sha256, observed.relative, observed.sha256, self.deadline, now
        )
        if not reader.unchanged():
            raise ValueError("auxiliary print actual tool changed during retention")

    def authenticate_artifact(
        self, binding: dict[str, str], reader: SnapshotReader, *, run_id: str, required_sdk_modules: tuple[str, ...]
    ) -> dict[str, Any]:
        _role_modules(required_sdk_modules)
        self.verify()
        if run_id != self.run_id or reader.root != self.root:
            raise ValueError("auxiliary print live tool belongs to another root/run")
        return _authenticate(binding, reader, self._events, self.pid, self)

    def validate_witness(self, binding: object, reader: SnapshotReader) -> None:
        self.verify()
        if (
            binding != self.witness
            or not isinstance(binding, dict)
            or reader.read(binding["path"]).sha256 != binding["sha256"]
        ):
            raise ValueError("auxiliary print witness differs from its actual live publication")


@contextmanager
def original_print_producer(root: Path, directory: Path) -> Iterator[AuxiliaryPrintProducerOperation]:
    if _CURRENT.get() is not None:
        raise ValueError("auxiliary print producer cannot nest")
    owner = AuxiliaryPrintProducerOperation(root, directory)
    token = _CURRENT.set(owner)
    try:
        owner.verify()
        yield owner
        owner.verify()
    finally:
        _CURRENT.reset(token)


def current_auxiliary_print_producer() -> AuxiliaryPrintProducerOperation | None:
    return _CURRENT.get()


@dataclass(frozen=True, init=False)
class AuxiliaryPrintOriginal:
    """Completed original held only by the real supervisor or hosted collector."""

    _held: tuple[tuple[str, Any], ...]
    pid: int
    _binding: tuple[tuple[str, str], ...]
    _code: tuple[tuple[str, str], ...]
    root: Path
    completion: float
    origin: str
    source_digest: str
    _events: Any

    @property
    def held(self) -> dict[str, Any]:
        return dict(self._held)

    @property
    def binding(self) -> dict[str, str]:
        return dict(self._binding)

    @property
    def code(self) -> dict[str, str]:
        return dict(self._code)

    def __init__(
        self,
        key: object,
        root: Path,
        held: dict[str, Any],
        pid: int,
        binding: dict[str, str],
        code: dict[str, str],
        completion: float,
    ) -> None:
        if key is not _ORIGINAL:
            raise ValueError("auxiliary print original requires its genuine supervisor/collector")
        from infrastructure.project.auxiliary_print_hosted import collect_auxiliary_print_original

        if sys._getframe(1).f_code not in (
            capture_supervised_print.__code__,
            collect_auxiliary_print_original.__code__,
        ):
            raise ValueError("auxiliary print original must come from its actual supervisor/collector call")
        object.__setattr__(
            self, "origin", "supervised" if sys._getframe(1).f_code is capture_supervised_print.__code__ else "hosted"
        )
        for name, attribute_value in (
            ("_held", tuple(held.items())),
            ("pid", pid),
            ("_binding", tuple(binding.items())),
            ("_code", tuple(code.items())),
            ("root", root),
            ("completion", completion),
        ):
            object.__setattr__(self, name, attribute_value)
        from infrastructure.reporting.native_print_witness import source_inventory

        object.__setattr__(self, "source_digest", _source_digest(source_inventory(root)))
        events: dict[str, _ToolEvent] = {}
        reader = SnapshotReader(root)
        selected = reader.read(binding["path"])
        if selected.sha256 != binding["sha256"]:
            raise ValueError("auxiliary print original witness differs from its held hash")
        raw = selected.json_object()
        if raw["pid"] != pid or raw["run_id"] != held["run_id"]:
            raise ValueError("auxiliary print witness belongs to another original worker/run")
        for value in _tools(raw):
            tool = reader.read(value["path"])
            if tool.sha256 != value["sha256"]:
                raise ValueError("auxiliary print original tool closure changed")
            process = tool.json_object()["native_process_artifact"]
            events[tool.relative] = _ToolEvent(
                tool.relative, tool.sha256, process["path"], process["sha256"], held["deadline"], completion
            )
        if not reader.unchanged():
            raise ValueError("auxiliary print original changed during held adoption")
        object.__setattr__(self, "_events", types.MappingProxyType(events))


def capture_supervised_print(
    root: Path,
    held: dict[str, Any],
    child: subprocess.Popen[bytes],
    guardian: object,
    directory: Path,
    deadline: float,
    completion: float,
) -> AuxiliaryPrintOriginal:
    """Called inside the real supervisor while its direct child/guardian remain held."""
    from infrastructure.core._bounded_run_guardian import BoundedRunGuardian
    from infrastructure.project.public_acceptance_auxiliary_supervision import supervise

    if (
        sys._getframe(1).f_code is not supervise.__code__
        or type(child) is not subprocess.Popen
        or not isinstance(guardian, BoundedRunGuardian)
        or not guardian.armed
        or not guardian.finished
        or guardian.process.returncode != 0
        or child.poll() != 0
        or child.pid <= 0
        or deadline != held["deadline"]
    ):
        raise ValueError("auxiliary print original needs actual completed OS0/guardian ownership")
    reader = SnapshotReader(root)
    spec = reader.read(Path(held["spec_path"]).relative_to(root).as_posix())
    if spec.sha256 != held["spec_sha256"]:
        raise ValueError("auxiliary print parent-held spec changed before original return")
    raw = reader.read(spec.json_object()["raw_path"]).json_object()
    code_path = (directory / "print-code/receipt.json").relative_to(root).as_posix()
    code = reader.read(code_path)
    binding = raw.get("details", {}).get("print_witness_artifact")
    if raw.get("exit_code") != 0 or raw.get("pid") != child.pid or not isinstance(binding, dict):
        raise ValueError("auxiliary print worker omitted its original successful witness")
    validate_code(reader, {"path": code.relative, "sha256": code.sha256}, held, child.pid, deadline)
    remaining(deadline)
    if not reader.unchanged():
        raise ValueError("auxiliary print original facts changed before supervisor completion")
    return AuxiliaryPrintOriginal(
        _ORIGINAL, root, held, child.pid, binding, {"path": code.relative, "sha256": code.sha256}, completion
    )


class AuxiliaryPrintReaderOperation:
    def __init__(self, original: AuxiliaryPrintOriginal, root: Path, deadline: float) -> None:
        if type(original) is not AuxiliaryPrintOriginal:
            raise ValueError("auxiliary print replay needs its externally held original")
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError("auxiliary print replay requires its existing finite current clock")
        self.original, self.root, self.deadline = original, root, deadline
        self.verify()

    def verify(self) -> None:
        remaining(self.deadline)
        from infrastructure.reporting.native_print_witness import source_inventory

        if _source_digest(source_inventory(self.root)) != self.original.source_digest:
            raise ValueError("auxiliary print current Source differs from its held original")

    def validate_witness(self, binding: object, reader: SnapshotReader) -> None:
        self.verify()
        if (
            binding != self.original.binding
            or reader.root != self.root
            or reader.read(self.original.binding["path"]).sha256 != self.original.binding["sha256"]
        ):
            raise ValueError("auxiliary print witness differs from its held actual original")

    def authenticate_artifact(
        self, binding: dict[str, str], reader: SnapshotReader, *, run_id: str, required_sdk_modules: tuple[str, ...]
    ) -> dict[str, Any]:
        _role_modules(required_sdk_modules)
        self.verify()
        if reader.root != self.root or run_id != self.original.held["run_id"]:
            raise ValueError("auxiliary print replay belongs to another current root/original run")
        validate_code(reader, self.original.code, self.original.held, self.original.pid, self.deadline)
        return _authenticate(binding, reader, self.original._events, self.original.pid, self)


def _authenticate(
    binding: dict[str, str], reader: SnapshotReader, events: dict[str, _ToolEvent], pid: int, operation: Any
) -> dict[str, Any]:
    if set(binding) != {"path", "sha256"}:
        raise ValueError("auxiliary print tool needs an exact held binding")
    event = events.get(binding["path"])
    selected = reader.read(binding["path"])
    if event is None or event.sha256 != binding["sha256"] or selected.sha256 != event.sha256:
        raise ValueError("auxiliary print tool is absent from genuine original custody")
    raw = selected.json_object()
    process = reader.read(event.process)
    if (
        process.sha256 != event.process_sha256
        or raw.get("native_process_artifact") != {"path": event.process, "sha256": event.process_sha256}
        or raw.get("owner_pid") != pid
        or raw.get("tool") not in {"pdftoppm", "pdffonts"}
    ):
        raise ValueError("auxiliary print original process membership changed")
    return {"original": event, "event": selected, "process": {"pid": pid}, "operation": operation}


def _role_modules(required: tuple[str, ...]) -> None:
    if not set(required) <= {
        "reporting/native_tool_process.py",
        "reporting/native_format_acceptance_checks.py",
        "reporting/native_print_witness.py",
        "project/public_acceptance_auxiliary_worker.py",
    }:
        raise ValueError("auxiliary print cannot authorize another native SDK role")


def _source_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
