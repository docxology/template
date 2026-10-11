"""Use the single fixed audited child for an already-owned native stage."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes


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
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    if owner is None:
        return None
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.reporting.native_stage_child import prepare_native_stage_child
    from infrastructure.reporting.native_stage_child_contracts import PURPOSE

    if repo != owner.source.bindings.current_root:
        raise ValueError("native stage actual repository differs from its live Source owner")
    scope = project.relative_to(repo / "projects").as_posix()
    identity = SnapshotReader._identity(request)
    held = read_bytes_confined(request.parent, request, max_bytes=16 * 1024 * 1024)
    if identity != SnapshotReader._identity(request):
        raise ValueError("native stage controller request changed during its actual confined read")
    payload = json_object_from_bytes(held)
    owner.verify(SnapshotReader(repo), run_id=owner.run_id, deadline=deadline)
    scope_directory = owner.stage_scope_directory(scope)
    from infrastructure.reporting.native_stage_child_contracts import STAGE_SCRIPTS

    protocol = payload.get("schema")
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
        if selected in {
            "scripts/pipeline/stage_00_setup.py",
            "scripts/pipeline/stage_01_test.py",
            "scripts/pipeline/stage_05_copy.py",
        }:
            # Only these exact Source core scripts keep the ordinary supervisor.
            # They receive no fixed child capability. Unknown stage selection
            # and every eligible/analysis factory refusal remain fail-closed.
            return None
        if selected not in STAGE_SCRIPTS:
            raise ValueError("native stage selector refuses an unknown Source core script")
    elif protocol != "template-python-analysis/4":
        raise ValueError("native stage selector cannot downgrade an unknown protocol")
    directory = (
        scope_directory
        / "native-stage"
        / hashlib.sha256(owner.run_id.encode()).hexdigest()
        / hashlib.sha256(str(payload.get("stage_key")).encode()).hexdigest()
        / secrets.token_hex(16)
    )
    owner.verify(SnapshotReader(repo), run_id=owner.run_id, deadline=deadline)
    create_private_native_directory(repo, directory)
    copied = directory / "parent-request.json"
    atomic_write_bytes_confined(repo, copied, held, mode=0o600)
    reader = SnapshotReader(repo, native_producer_operation=owner)
    copied_request = reader.read(copied.relative_to(repo).as_posix())
    if copied_request.content != held or identity != SnapshotReader._identity(request):
        raise ValueError("native stage controller request changed during parent custody transfer")
    prepared = prepare_native_stage_child(
        owner.source, scope, copied_request, directory, deadline=deadline, environment=env
    )
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
