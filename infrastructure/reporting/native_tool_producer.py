"""Process-local Source-admitted producer custody, separate from portable readback.

The actual ToolAPI registers direct supervised observations while this owner is
live. Retained JSON never constructs an operation or an original tool token.
A completed external original is required later for portable validation.
"""

from __future__ import annotations

from infrastructure.reporting.native_worker_startup_diagnostics import (
    _worker_execution_phase,
)

import hashlib
import math
import os
import secrets
import time
import copy
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

if TYPE_CHECKING:
    from infrastructure.rendering.native_render_custody import (
        NativeTexSectionPass,
        SourceNativeMermaid,
        SourceNativePandoc,
    )
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext


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


def _stage_scope_nomination(
    root: Path,
    scope: str | None,
    directory: Path | None,
) -> tuple[str, Path, tuple[int, int]] | None:
    """Observe optional paired DATA; this helper never constructs ownership."""
    from infrastructure.project.public_acceptance_evidence import evidence_directory

    if scope is None and directory is None:
        return None
    if not isinstance(scope, str) or scope not in PUBLIC_PROJECT_NAMES or not isinstance(directory, Path):
        raise ValueError("native stage scope requires a paired exact public scope and directory nomination")
    from infrastructure.reporting.native_source_external_admission import _physical_directory

    selected = evidence_directory(root, directory)
    return scope, selected, _physical_directory(selected)


class NativeProducerOperation:
    """One genuine live Source owner; tools come directly from actual ToolAPI."""

    def __init__(
        self,
        source: NativeSourceContext,
        run_id: str,
        deadline: float,
        *,
        scope: str | None = None,
        directory: Path | None = None,
    ) -> None:
        from infrastructure.reporting.native_source_external_admission import NativeSourceContext

        if not isinstance(source, NativeSourceContext) or not isinstance(run_id, str) or not run_id:
            raise ValueError("native producer requires genuine admitted Source and run identity")
        if type(deadline) not in (float, int) or not math.isfinite(deadline):
            raise ValueError("native producer requires the existing finite original clock")
        self.source = source
        self.run_id = run_id
        self.deadline = float(deadline)
        self.owner_pid = os.getpid()
        self._stage_scope = _stage_scope_nomination(source.bindings.current_root, scope, directory)
        self._tools: dict[str, _OriginalTool] = {}
        self._stage_children: dict[str, dict[str, Any]] = {}
        self._closed = False

    def verify(self, reader: SnapshotReader, *, run_id: str, deadline: float) -> None:
        with self._verification_guard(reader, run_id=run_id, deadline=deadline):
            pass

    @contextmanager
    def _verification_guard(self, reader: SnapshotReader, *, run_id: str, deadline: float) -> Iterator[None]:
        """Enclose fixed synchronous DATA comparisons in one fresh Source boundary."""
        from infrastructure.reporting.native_source_external_admission import _physical_directory

        source, owner_run, original_deadline = self.source, self.run_id, self.deadline
        owner_pid, scope, root = self.owner_pid, self._stage_scope, reader.root

        def check_owner() -> None:
            if (
                self._closed
                or _CURRENT.get() is not self
                or self.source is not source
                or self.owner_pid != owner_pid
                or os.getpid() != owner_pid
                or self.run_id != owner_run
                or self.deadline != original_deadline
                or self._stage_scope is not scope
                or reader.root != root
            ):
                raise ValueError("native producer custody is not this actual unchanged live process owner")
            if (
                run_id != owner_run
                or run_id != source.bindings.run_id
                or type(deadline) not in (int, float)
                or not math.isfinite(deadline)
                or not deadline <= original_deadline
            ):
                raise ValueError("native producer run or original clock differs")
            remaining(original_deadline)
            remaining(deadline)
            if scope is not None and _physical_directory(scope[1]) != scope[2]:
                raise ValueError("native producer nominated stage scope directory changed physical identity")

        check_owner()
        with source._correspondence_guard(source.reference, root, reader, original_deadline):
            check_owner()
            try:
                yield None
            finally:
                check_owner()
        check_owner()
        remaining(deadline)

    def stage_scope_directory(self, scope: str) -> Path:
        """Return the held directory only in the exact actual live public owner."""
        self.verify(SnapshotReader(self.source.bindings.current_root), run_id=self.run_id, deadline=self.deadline)
        return self._stage_scope_directory_data(scope)

    def _stage_scope_directory_data(self, scope: str) -> Path:
        """Read held scope DATA only; this does not verify or construct an owner."""
        if self._stage_scope is None or scope != self._stage_scope[0]:
            raise ValueError("native stage requires this actual owner's exact nominated public scope directory")
        return self._stage_scope[1]

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
        with _worker_execution_phase("retain-tool-verify"):
            self.verify(reader, run_id=run_id, deadline=deadline)
        with _worker_execution_phase("retain-tool-data"):
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
        with _worker_execution_phase("retain-tool-unchanged"):
            if not reader.unchanged():
                raise ValueError("native actual ToolAPI artifact changed during live custody retention")
            remaining(self.deadline)

    def validate_tool(self, binding: object, raw: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
        with self._verification_guard(reader, run_id=run_id, deadline=self.deadline):
            self._validate_tool_data(binding, raw, reader, run_id=run_id)

    def _validate_tool_data(self, binding: object, raw: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
        """Compare actual retained ToolAPI DATA within a caller's fresh Source guard."""
        if run_id != self.run_id:
            raise ValueError("native tool DATA belongs to another actual run")
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

    @property
    def retained_tool_bindings(self) -> tuple[dict[str, str], ...]:
        """Read copied DATA for actual ToolAPI events while this owner is live."""
        self.verify(SnapshotReader(self.source.bindings.current_root), run_id=self.run_id, deadline=self.deadline)
        return tuple({"path": tool.artifact_relative, "sha256": tool.artifact_sha256} for tool in self._tools.values())

    @property
    def stage_children(self) -> tuple[dict[str, str], ...]:
        """Expose exact closed stage packets; these bindings create no authority."""
        reader = SnapshotReader(self.source.bindings.current_root)
        self.verify(reader, run_id=self.run_id, deadline=self.deadline)
        bindings = []
        for relative, item in self._stage_children.items():
            held = reader.read(relative)
            if held.sha256 != item["sha256"]:
                raise ValueError("live native stage child packet changed after actual retention")
            bindings.append({"path": relative, "sha256": held.sha256})
        if not reader.unchanged():
            raise ValueError("live native stage child packet changed during accessor readback")
        return tuple(bindings)

    def _retain_actual_stage_child(
        self,
        preparation: Any,
        process_binding: dict[str, str],
        packet_binding: dict[str, str],
    ) -> None:
        """Only the fixed factory closes real ToolAPI/Source/Code before retention."""
        from infrastructure.reporting.native_stage_child import NativeStageChildPreparation

        if type(preparation) is not NativeStageChildPreparation or preparation.owner is not self:
            raise ValueError("native stage child retention requires the actual live fixed parent preparation")
        reader = SnapshotReader(self.source.bindings.current_root, native_producer_operation=self)
        preparation.verify_owner(reader)
        process = reader.read(process_binding["path"])
        self.validate_tool(process_binding, process.json_object(), reader, run_id=self.run_id)
        packet = reader.read(packet_binding["path"])
        if (
            packet.sha256 != packet_binding["sha256"]
            or packet.relative in self._stage_children
            or packet.path != preparation.directory / "stage-child.json"
        ):
            raise ValueError("native stage packet is replaced, duplicated or belongs to another actual attempt")
        value = packet.json_object()
        preparation.verify_closed_packet(value, process_binding, reader)
        self._stage_children[packet.relative] = {
            "sha256": packet.sha256,
            "value": copy.deepcopy(value),
            "process_binding": dict(process_binding),
        }
        if not reader.unchanged():
            raise ValueError("native stage packet changed during actual ToolAPI retention")
        preparation.verify_owner(reader)


_CURRENT: ContextVar[NativeProducerOperation | None] = ContextVar("template_native_producer", default=None)


class _NativeRenderLaunchers:
    """Reporting's native rendering launchers, resolved only when rendering asks.

    Rendering may not import reporting, so a live owner installs these through
    the rendering seam. Each method returns the real custody function so
    rendering calls it from its own frame; each function still checks its own
    live owner, admitted Source and stage, so installation grants no authority.
    """

    def pandoc_launcher(self) -> SourceNativePandoc:
        from infrastructure.reporting.native_renderer_source_call import run_source_native_pandoc

        return run_source_native_pandoc

    def mermaid_launcher(self) -> SourceNativeMermaid:
        from infrastructure.reporting.native_mermaid_production_tool import run_source_native_mermaid

        return run_source_native_mermaid

    def tex_section_launcher(self) -> NativeTexSectionPass:
        from infrastructure.reporting.native_tex_section_render import run_native_tex_section_pass

        return run_native_tex_section_pass


def current_native_producer_operation() -> NativeProducerOperation | None:
    """Return the actual process-local owner; a child must admit its own Source."""
    operation = _CURRENT.get()
    return operation if operation is not None and operation.owner_pid == os.getpid() and not operation._closed else None


@dataclass(frozen=True)
class NativeStageLaunch:
    """Direct launch result DATA; successful custody remains in the live owner."""

    result: BoundedSubprocessResult
    scratch: Path
    child_artifact: dict[str, str] | None


def launch_owned_native_stage(
    repo: Path,
    project: Path,
    request: Path,
    env: dict[str, str],
    *,
    deadline: float,
    analysis_receipt: dict[str, object] | None = None,
) -> NativeStageLaunch | None:
    """Ordinary stages keep their supervisor; active native owners use one role.

    The existing controller wrote this actual request. The fixed factory
    independently verifies Source selection, physical scope and current owner
    before the real NativeToolAPI launches it. Neither request JSON nor an
    environment path constructs ownership or chooses a generic child role.
    """
    owner = current_native_producer_operation()
    if owner is None:
        return None
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
    from infrastructure.reporting import native_stage_child as factory
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.reporting.native_stage_child_contracts import PURPOSE, STAGE_SCRIPTS

    source = owner.source
    if repo != source.bindings.current_root:
        raise ValueError("native stage actual repository differs from its live Source owner")
    scope = project.relative_to(repo / "projects").as_posix()
    registry, original_registry = factory._PREPARED, dict(factory._PREPARED)
    reader = SnapshotReader(repo, native_producer_operation=owner)
    prepared = None
    execution = None
    original_environment = dict(env)
    with owner._verification_guard(reader, run_id=owner.run_id, deadline=deadline):
        identity = SnapshotReader._identity(request)
        held = read_bytes_confined(request.parent, request, max_bytes=16 * 1024 * 1024)
        if identity != SnapshotReader._identity(request):
            raise ValueError("native stage controller request changed during its actual confined read")
        payload = json_object_from_bytes(held)
        scope_directory = owner._stage_scope_directory_data(scope)
        protocol = payload.get("schema")
        ordinary_stage = False
        if protocol == "template-python-stage/3":
            argv = payload.get("argv")
            if (
                not isinstance(argv, list)
                or not argv
                or not isinstance(argv[0], str)
                or not Path(argv[0]).is_absolute()
                or ".." in Path(argv[0]).parts
            ):
                raise ValueError("native stage selector lacks its actual absolute Source script")
            selected = Path(argv[0]).relative_to(repo).as_posix()
            ordinary_stage = selected in {
                "scripts/pipeline/stage_00_setup.py",
                "scripts/pipeline/stage_01_test.py",
                "scripts/pipeline/stage_05_copy.py",
            }
            if not ordinary_stage and selected not in STAGE_SCRIPTS:
                raise ValueError("native stage selector refuses an unknown Source core script")
        elif protocol != "template-python-analysis/4":
            raise ValueError("native stage selector cannot downgrade an unknown protocol")
        if not ordinary_stage:
            directory = (
                scope_directory
                / "native-stage"
                / hashlib.sha256(owner.run_id.encode()).hexdigest()
                / hashlib.sha256(str(payload.get("stage_key")).encode()).hexdigest()
                / secrets.token_hex(16)
            )
            create_private_native_directory(repo, directory)
            copied = directory / "parent-request.json"
            atomic_write_bytes_confined(repo, copied, held, mode=0o600)
            copied_request = reader.read(copied.relative_to(repo).as_posix())
            if copied_request.content != held or identity != SnapshotReader._identity(request):
                raise ValueError("native stage controller request changed during parent custody transfer")
            prepared = factory._prepare_native_stage_child_data(
                source,
                scope,
                copied_request,
                directory,
                deadline=deadline,
                environment=original_environment,
                owner=owner,
                reader=reader,
            )
            execution = (
                prepared.command,
                tuple(prepared.command),
                prepared.environment,
                dict(prepared.environment),
                prepared.cwd,
                str(prepared.cwd),
            )
            prepared._verify_owner_data(reader)
        if not reader.unchanged():
            raise ValueError("native dispatcher inputs changed before complete Source closure")
    if (
        current_native_producer_operation() is not owner
        or owner.source is not source
        or factory._PREPARED is not registry
        or len(registry) != len(original_registry)
        or any(registry.get(key) is not value for key, value in original_registry.items())
        or dict(env) != original_environment
        or identity != SnapshotReader._identity(request)
        or read_bytes_confined(request.parent, request, max_bytes=16 * 1024 * 1024) != held
    ):
        raise ValueError("native dispatcher owner/request/registry changed during Source closure")
    if prepared is not None:
        if (
            prepared._key is not factory._FACTORY_KEY
            or prepared.owner is not owner
            or prepared.source is not source
            or prepared.scope != scope
            or prepared.deadline != deadline
            or id(prepared) in registry
            or execution is None
            or prepared.command is not execution[0]
            or tuple(prepared.command) != execution[1]
            or prepared.environment is not execution[2]
            or dict(prepared.environment) != execution[3]
            or prepared.cwd is not execution[4]
            or str(prepared.cwd) != execution[5]
        ):
            raise ValueError("native dispatcher did not retain its one unpublished actual factory")
        prepared._verify_owner_data(reader)
    if not reader.unchanged():
        raise ValueError("native dispatcher physical inputs changed during final Source closure")
    remaining(deadline)
    if prepared is None:
        # Only the three exact Source core scripts retain their ordinary
        # supervisor, after this fresh boundary has completely closed.
        return None
    registry[id(prepared)] = prepared
    observed_tools: list[dict[str, Any]] = []
    child_binding = None
    failure: Exception | None = None
    try:
        tool = native_tool_record(
            repo,
            prepared.directory,
            prepared.command[0],
            list(prepared.command[1:]),
            env=dict(prepared.environment),
            deadline=deadline,
            phase_deadline=deadline,
            run_id=owner.run_id,
            purpose=PURPOSE,
            prepared_stage=prepared,
            observed_tools=observed_tools,
        )
        child_binding = prepared.observe(tool)
    except Exception as error:
        failure = error
        if not observed_tools:
            raise
    finally:
        if analysis_receipt is not None and observed_tools:
            # This direct observation also survives a parent interruption or
            # later persistence refusal. It cannot authenticate an original.
            actual = observed_tools[-1]
            analysis_receipt["native_stage_process"] = {
                "artifact": actual["artifact"],
                "completion_authorized": actual["completion_authorized"],
                "observation": actual["observation"],
            }
    if len(observed_tools) != 1:
        raise ValueError("native stage requires one exact independently supervised tool observation")
    packet = observed_tools[0]
    actual = packet["observation"]
    original = actual["original_exit_code"]
    refused = failure is not None or packet["completion_authorized"] is not True or child_binding is None
    code = (
        130
        if original in (130, -2)
        else 124
        if actual["timed_out"] or isinstance(failure, TimeoutError)
        else 75
        if refused and original in (None, 0, 75)
        else original
        if type(original) is int
        else 75
    )
    result = BoundedSubprocessResult(
        argv=tuple(actual["command"] or prepared.command),
        returncode=code,
        timed_out=actual["timed_out"] or isinstance(failure, TimeoutError),
        stdout=actual["stdout"],
        stderr=actual["stderr"],
        command_error=str(failure) if failure is not None else actual["diagnostic"],
        custody_refused=refused or actual["custody_refused"],
        original_returncode=original,
        pid=actual["pid"],
    )
    if analysis_receipt is not None and child_binding is not None:
        analysis_receipt["native_stage_child"] = child_binding
    return NativeStageLaunch(result, prepared.directory, child_binding)


@contextmanager
def native_producer_operation(
    source: NativeSourceContext,
    *,
    run_id: str,
    deadline: float,
    scope: str | None = None,
    directory: Path | None = None,
) -> Iterator[NativeProducerOperation]:
    """Begin only from genuine admitted Source, and never start another clock."""
    from infrastructure.reporting.native_format_joint_source import _require_installed_sdk
    from infrastructure.rendering.native_render_custody import installed_native_render_custody

    _require_installed_sdk(source.bindings.expected_implementation_bytes)
    if _CURRENT.get() is not None:
        raise ValueError("native producer cannot replace another live original owner")
    operation = NativeProducerOperation(source, run_id, deadline, scope=scope, directory=directory)
    token = _CURRENT.set(operation)
    try:
        with installed_native_render_custody(_NativeRenderLaunchers()):
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
