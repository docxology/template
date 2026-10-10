"""Fixed complete Pitch axis children, using the existing genuine Source route."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_pitch_control_plan import SCOPE, compile_pitch_control_plan
from infrastructure.reporting.native_pitch_control_worker import CHILD_SCHEMA, WORKER
from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def supervise_pitch_controls(
    root: Path,
    directory: Path,
    *,
    formats: tuple[str, ...],
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> list[dict[str, Any]]:
    from infrastructure.reporting.native_pitch_control_custody import PitchControlReaderOperation

    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source.bindings.current_root != root
        or owner.run_id != run_id
        or owner.deadline != deadline
        or not directory.is_relative_to(owner.stage_scope_directory(SCOPE))
    ):
        raise ValueError("Pitch controls require the genuine paired parent Source/root/run/clock")
    source = owner.source
    runtime = json.loads(source.bindings.expected_implementation_bytes)["runtime_environment"]
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != runtime["python_executable"]:
        raise ValueError("Pitch child launcher differs from actual admitted selected interpreter")
    reader = SnapshotReader(root, native_producer_operation=owner)
    plan, _ = compile_pitch_control_plan(root, reader, formats=formats, deadline=deadline)
    create_private_native_directory(root, directory)
    records = []
    for ordinal, name in enumerate(plan["active_controls"]):
        remaining(deadline)
        leaf = directory / f"pitch-control-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        create_private_native_directory(root, leaf / "closure")
        source.verify_correspondence(source.reference, root, reader, deadline)
        path = leaf / "implementation.json"
        atomic_write_bytes_confined(root, path, source.bindings.expected_implementation_bytes, mode=0o600)
        implementation = reader.read(path.relative_to(root).as_posix())
        identity = (leaf / "closure").stat()
        expected = 0 if name == "baseline" else 1
        specification = {
            "schema_version": CHILD_SCHEMA,
            "scope": SCOPE,
            "name": name,
            "run_id": run_id,
            "directory": leaf.relative_to(root).as_posix(),
            "source": json.loads(source.descriptor(SCOPE, deadline=deadline)),
            "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
            "expected_exit": expected,
            "parent_pid": os.getpid(),
            "parent_platform": platform.system(),
            "deadline_monotonic": deadline,
            "caller_deadline_monotonic": deadline,
            "closure_identity": [identity.st_dev, identity.st_ino],
            "formats": list(formats),
            "plan_digest": plan["digest"],
        }
        spec = write_json(root, leaf / "specification.json", specification)
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        if (
            json.loads(implementation.content)["files"]["infrastructure/core/bytecode_audit.py"]
            != hashlib.sha256(hook).hexdigest()
        ):
            raise ValueError("Pitch child bootstrap hook differs from actual selected SDK body")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            source.bindings.selected_sdk_package_root,
            (),
            path,
            implementation.sha256,
            leaf / "closure",
            (identity.st_dev, identity.st_ino),
            deadline,
            required_worker_module=WORKER,
        )
        args = [
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(root),
            "--specification",
            spec["path"],
            "--specification-sha256",
            spec["sha256"],
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(deadline),
            "--run-id",
            run_id,
        ]
        # The whole existing scope clock bounds this complete axis; each nested
        # tool still has its own real API cap. There is no fresh suite budget.
        process = native_tool_record(
            root,
            leaf,
            str(interpreter),
            args,
            env=env,
            deadline=deadline,
            phase_deadline=deadline,
            run_id=run_id,
            purpose="pitch-child",
            preserve_nominated_launcher=True,
        )
        if process["exit_code"] != expected or process["original_exit_code"] != expected:
            raise ValueError("actual configured Pitch child lost required signed original oracle outcome")
        observation = reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
        closure = reader.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
        item = {
            "name": name,
            "artifact": {"path": observation.relative, "sha256": observation.sha256},
            "process_artifact": process["artifact"],
            "specification_artifact": spec,
            "closure_artifact": {"path": closure.relative, "sha256": closure.sha256},
            "original_exit_code": expected,
        }
        context = PitchControlReaderOperation(source, reader, [item], scope=SCOPE, run_id=run_id, deadline=deadline)
        context.child(item, SnapshotReader(root, native_control_operation=context))
        actual = observation.json_object()
        if actual["plan"] != plan or actual["name"] != name or actual["oracle_exit_code"] != expected:
            raise ValueError("Pitch original child altered its whole Source selector or outcome")
        records.append(item)
        owner.verify(reader, run_id=run_id, deadline=deadline)
    return records
