"""Genuine Source-owned complete PDF contract/control child supervision.

Every supported page/occurrence is executed by a fixed selected-SDK worker.
Unsupported Source writers/positions remain exact unfulfilled roster records.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_artifact_contract,
)
from infrastructure.reporting.native_pdf_whole_control_run import observe_whole_pdf_control_baseline
from infrastructure.reporting.native_print_child_custody import (
    WHOLE_PDF_CHILD_SCHEMA,
    WHOLE_PDF_WORKER,
    WholePDFControlReaderOperation,
)
from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SUITE_SCHEMA = "template-source-owned-whole-pdf-control-suite-v1"
SUITE_REMAINING = (
    "independent Source scientific value/registry/domain truth",
    "whole Source renderer-stage and official native runtime/archive/library admission",
    "every explicitly unsupported PDF writer/Source occurrence control",
)


def _child(
    root: Path,
    leaf: Path,
    scope: str,
    formats: tuple[str, ...],
    artifact_id: str,
    pipeline_run_id: str,
    plan_digest: str,
    requirements: dict[str, Any],
    control: dict[str, Any],
    interpreter: Path,
    reader: SnapshotReader,
    env: dict[str, str],
    *,
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline:
        raise ValueError("whole PDF original child requires actual enclosing Source/ToolAPI owner")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    source = owner.source
    # No per-control phase extends the original caller clock.
    child_deadline = min(deadline, time.monotonic() + 600.0)
    create_private_native_directory(root, leaf)
    create_private_native_directory(root, leaf / "closure")
    implementation_path = leaf / "implementation.json"
    atomic_write_bytes_confined(root, implementation_path, source.bindings.expected_implementation_bytes, mode=0o600)
    implementation = reader.read(implementation_path.relative_to(root).as_posix())
    identity = (leaf / "closure").stat()
    expected = int(control["intended_diagnostic"] is not None)
    specification = {
        "schema_version": WHOLE_PDF_CHILD_SCHEMA,
        "scope": scope,
        "name": control["identity"],
        "run_id": run_id,
        "directory": leaf.relative_to(root).as_posix(),
        "source": json.loads(source.descriptor(scope, deadline=child_deadline)),
        "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
        "expected_exit": expected,
        "parent_pid": os.getpid(),
        "parent_platform": platform.system(),
        "deadline_monotonic": child_deadline,
        "caller_deadline_monotonic": deadline,
        "closure_identity": [identity.st_dev, identity.st_ino],
        "artifact_id": artifact_id,
        "declared_formats": list(formats),
        "pipeline_run_id": pipeline_run_id,
        "plan_digest": plan_digest,
        "requirements_digest": requirements["content_digest"],
    }
    spec = write_json(root, leaf / "specification.json", specification)
    hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
    if (
        json.loads(source.bindings.expected_implementation_bytes)["files"]["infrastructure/core/bytecode_audit.py"]
        != hashlib.sha256(hook).hexdigest()
    ):
        raise ValueError("whole PDF child raw hook differs from independently admitted selected SDK")
    bootstrap = format_selected_sdk_native_bootstrap(
        hook,
        source.bindings.selected_sdk_package_root,
        (),
        implementation_path,
        implementation.sha256,
        leaf / "closure",
        (identity.st_dev, identity.st_ino),
        child_deadline,
        required_worker_module=WHOLE_PDF_WORKER,
    )
    process = native_tool_record(
        root,
        leaf,
        str(interpreter),
        [
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
            repr(child_deadline),
            "--run-id",
            run_id,
        ],
        env=env,
        deadline=child_deadline,
        run_id=run_id,
        purpose="whole-pdf-child",
        preserve_nominated_launcher=True,
    )
    if (
        type(process["original_exit_code"]) is not int
        or process["original_exit_code"] != expected
        or process["exit_code"] != expected
    ):
        raise ValueError("actual whole PDF child failed its required signed original OS outcome")
    observed = reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
    closure = reader.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
    item = {
        "name": control["identity"],
        "artifact": {"path": observed.relative, "sha256": observed.sha256},
        "process_artifact": process["artifact"],
        "specification_artifact": spec,
        "closure_artifact": {"path": closure.relative, "sha256": closure.sha256},
        "original_exit_code": expected,
    }
    context = WholePDFControlReaderOperation(source, reader, [item], scope=scope, run_id=run_id, deadline=deadline)
    context.child(item, reader)
    actual = observed.json_object()
    if actual["selected_control"] != control or actual["oracle_exit_code"] != expected:
        raise ValueError("whole PDF original child changed the exact Source-selected control/outcome")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    return item


def supervise_whole_pdf_source_controls(
    root: Path,
    directory: Path,
    scope: str,
    formats: tuple[str, ...],
    *,
    pipeline_run_id: str,
    plan_digest: str,
    interpreter: Path,
    reader: SnapshotReader,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, str]:
    """Select the complete Source contract and supervise all supported rows.

    No caller subset or decoded receipt supplies the selected controls. Each
    independently rebuilt child must reach its native expected diagnostic.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline or reader.root != root:
        raise ValueError("whole PDF supervisor lacks its actual enclosing Source/run/clock")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    runtime = json.loads(owner.source.bindings.expected_implementation_bytes)["runtime_environment"]
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != runtime["python_executable"]:
        raise ValueError("whole PDF original worker differs from its genuine admitted Python launcher")
    create_private_native_directory(root, directory)
    artifacts = tuple(row for row in native_artifact_contract(root, scope, formats, reader) if row.format == "pdf")
    if not artifacts:
        raise ValueError("whole PDF original controls require the complete nonempty Source PDF contract")
    rows = []
    for ordinal, artifact in enumerate(artifacts):
        remaining(deadline)
        row: dict[str, Any] = {
            "id": artifact.id,
            "format": artifact.format,
            "path": artifact.path,
            "role": "unsupported-writer",
            "requirements": None,
            "children": [],
            "unsupported": [artifact.id + ": complete original/current Source-writer reference is unimplemented"],
        }
        if artifact.id == "manuscript:pdf":
            leaf = directory / f"artifact-{ordinal:04d}"
            create_private_native_directory(root, leaf)
            baseline = observe_whole_pdf_control_baseline(
                root,
                leaf / "baseline",
                scope,
                formats,
                artifact_id=artifact.id,
                pipeline_run_id=pipeline_run_id,
                plan_digest=plan_digest,
                reader=reader,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
            requirements = baseline["source_predicates"]["control_requirements"]
            row.update({"role": "whole-manuscript-source-controls", "requirements": requirements, "unsupported": []})
            for control_ordinal, control in enumerate(requirements["controls"]):
                remaining(deadline)
                if control["unsupported"] is not None:
                    row["unsupported"].append(control)
                    continue
                row["children"].append(
                    _child(
                        root,
                        leaf / f"child-{control_ordinal:06d}",
                        scope,
                        formats,
                        artifact.id,
                        pipeline_run_id,
                        plan_digest,
                        requirements,
                        control,
                        interpreter,
                        reader,
                        env,
                        deadline=deadline,
                        run_id=run_id,
                    )
                )
        rows.append(row)
    suite = {
        "schema_version": SUITE_SCHEMA,
        "scope": scope,
        "run_id": run_id,
        "declared_formats": list(formats),
        "pipeline_run_id": pipeline_run_id,
        "plan_digest": plan_digest,
        "ordered_pdf_contract": [{"id": row.id, "format": row.format, "path": row.path} for row in artifacts],
        "artifacts": rows,
        "remaining": list(SUITE_REMAINING),
    }
    result = write_json(root, directory / "control-suite.json", suite)
    owner.verify(reader, run_id=run_id, deadline=deadline)
    if not reader.unchanged():
        raise ValueError("whole PDF original control Source/input custody changed before suite retention")
    remaining(deadline)
    return result
