"""Actual Source-owned slide children and independently authenticated readback."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def supervise_slide_source_controls(
    root: Path,
    directory: Path,
    *,
    scope: str,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> list[dict[str, Any]]:
    """Admit and supervise each real child through the genuine parent ToolAPI."""
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.reporting.native_print_child_custody import SLIDE_CHILD_SCHEMA, SlideControlReaderOperation
    from infrastructure.reporting.native_slide_controls import SLIDE_CONTROL_CODES
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source.bindings.current_root != root
        or owner.run_id != run_id
        or owner.deadline != deadline
    ):
        raise ValueError("slide controls require this actual live Source/tool owner and unchanged clock")
    source = owner.source
    selected_runtime = json.loads(source.bindings.expected_implementation_bytes)["runtime_environment"]
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != selected_runtime["python_executable"]:
        raise ValueError("slide controls differ from the actual admitted selected interpreter")
    parent_reader = SnapshotReader(root, native_producer_operation=owner)
    records: list[dict[str, Any]] = []
    for ordinal, (name, code) in enumerate(SLIDE_CONTROL_CODES.items()):
        remaining(deadline)
        child_deadline = min(deadline, time.monotonic() + 120.0)
        leaf = directory / f"slide-source-control-{ordinal}"
        create_private_native_directory(root, leaf)
        create_private_native_directory(root, leaf / "closure")
        source.verify_correspondence(source.reference, root, parent_reader, child_deadline)
        implementation_path = leaf / "implementation.json"
        atomic_write_bytes_confined(
            root, implementation_path, source.bindings.expected_implementation_bytes, mode=0o600
        )
        implementation = parent_reader.read(implementation_path.relative_to(root).as_posix())
        identity = (leaf / "closure").stat()
        specification = {
            "schema_version": SLIDE_CHILD_SCHEMA,
            "scope": scope,
            "name": name,
            "run_id": run_id,
            "directory": leaf.relative_to(root).as_posix(),
            "source": json.loads(source.descriptor(scope, deadline=child_deadline)),
            "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
            "expected_exit": 0 if code is None else 1,
            "parent_pid": os.getpid(),
            "parent_platform": platform.system(),
            "deadline_monotonic": child_deadline,
            "caller_deadline_monotonic": deadline,
            "closure_identity": [identity.st_dev, identity.st_ino],
        }
        spec = write_json(root, leaf / "specification.json", specification)
        sdk = source.bindings.selected_sdk_package_root
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        expected = json.loads(source.bindings.expected_implementation_bytes)["files"]
        if expected["infrastructure/core/bytecode_audit.py"] != hashlib.sha256(hook).hexdigest():
            raise ValueError("slide child raw hook differs from the admitted installed SDK")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            (),
            implementation_path,
            implementation.sha256,
            leaf / "closure",
            (identity.st_dev, identity.st_ino),
            child_deadline,
            required_worker_module="infrastructure.reporting.native_slide_controls",
        )
        command = [
            str(interpreter),
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
        ]
        process = native_tool_record(
            root,
            leaf,
            str(interpreter),
            command[1:],
            env=env,
            deadline=child_deadline,
            run_id=run_id,
            purpose="slide-child",
            preserve_nominated_launcher=True,
        )
        expected_exit = specification["expected_exit"]
        if process["exit_code"] != expected_exit or process["original_exit_code"] != expected_exit:
            raise ValueError("actual slide child failed its required original native oracle")
        observation = parent_reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
        closure = parent_reader.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
        item = {
            "name": name,
            "artifact": {"path": observation.relative, "sha256": observation.sha256},
            "process_artifact": process["artifact"],
            "specification_artifact": spec,
            "closure_artifact": {"path": closure.relative, "sha256": closure.sha256},
            "original_exit_code": expected_exit,
        }
        context = SlideControlReaderOperation(
            source, parent_reader, [item], scope=scope, run_id=run_id, deadline=deadline
        )
        context.child(item, SnapshotReader(root, native_control_operation=context))
        actual = observation.json_object()
        if (
            actual.get("name") != name
            or actual.get("expected_code") != code
            or actual.get("oracle_exit_code") != expected_exit
        ):
            raise ValueError("slide original child result differs from its Source-owned native oracle")
        records.append(item)
        source.verify_correspondence(source.reference, root, parent_reader, deadline)
    return records


def replay_slide_source_controls(
    records: object,
    reader: SnapshotReader,
    directory: Path,
    *,
    scope: str,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    original_deadline: float,
    deadline: float,
    env: dict[str, str],
) -> dict[str, Any]:
    """Authenticate each original child before fresh source/native readback."""
    from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _raster, _tool
    from infrastructure.reporting.native_format_control_replay import _closure, _keys, _outcome
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_format_portable_custody import producer_path
    from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
    from infrastructure.reporting.native_print_child_custody import SlideControlReaderOperation
    from infrastructure.reporting.native_slide_checks import inspect_slide_source_paint
    from infrastructure.reporting.native_slide_controls import (
        CONTROL_SOURCE,
        SLIDE_CONTROL_CODES,
        slide_source_control_fixture,
    )
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
        native_producer_operation,
    )

    if (
        not math.isfinite(original_deadline)
        or original_deadline <= 0
        or not math.isfinite(deadline)
        or deadline <= time.monotonic()
    ):
        raise ValueError("slide-source replay lacks its admitted original finite deadline")
    if not isinstance(records, list) or [row.get("name") for row in records if isinstance(row, dict)] != list(
        SLIDE_CONTROL_CODES
    ):
        raise ValueError("slide-source control suite is missing, reordered or duplicated")
    operation = require_native_operation(reader)
    if deadline != operation.deadline:
        raise ValueError("slide-source replay requires the unchanged admitted current reader deadline")
    source = operation.source
    context = SlideControlReaderOperation(source, reader, records, scope=scope, run_id=run_id, deadline=deadline)
    controls = SnapshotReader(reader.root, native_control_operation=context)
    current_run_id = source.bindings.run_id
    outcomes: list[dict[str, Any]] = []
    with ExitStack() as current_scope:
        owner = current_native_producer_operation()
        if owner is None:
            current_scope.enter_context(native_producer_operation(source, run_id=current_run_id, deadline=deadline))
        elif owner.source is not source or owner.run_id != current_run_id or owner.deadline != deadline:
            raise ValueError("slide current source parser differs from its genuine enclosing Source/clock")
        # Current ToolAPI executions stay inside the admitted current mirror.
        with tempfile.TemporaryDirectory(prefix="slide-control-source-replay-", dir=directory.parent) as private:
            current = CitationRuntime(
                reader.root, Path(private) / "parser", env=env, deadline=deadline, run_id=current_run_id
            )
            source_path = current.freeze("invented.md", CONTROL_SOURCE)
            parsed = current.tool(
                "pandoc", [str(source_path), "--to=json"], "control-source-ast", input_paths=(source_path,)
            )
            ast = parsed["stdout"].encode()
        for ordinal, (item, (name, code)) in enumerate(zip(records, SLIDE_CONTROL_CODES.items(), strict=True)):
            _keys(
                item,
                {
                    "name",
                    "original_exit_code",
                    "process_artifact",
                    "artifact",
                    "specification_artifact",
                    "closure_artifact",
                },
            )
            leaf = directory / f"slide-source-control-{ordinal}"
            result = _file(item["artifact"], controls)
            if result.path != leaf / "control-observation.json":
                raise ValueError("slide-source control belongs to another original attempt")
            authority = context.child(item, controls)
            expected = 0 if code is None else 1
            if (
                authority["specification"]["caller_deadline_monotonic"] != original_deadline
                or item["original_exit_code"] != expected
            ):
                raise ValueError("slide child differs from its enclosing admitted original clock/oracle")
            raw = result.json_object()
            _keys(
                raw,
                {
                    "schema_version",
                    "name",
                    "expected_code",
                    "input",
                    "parser",
                    "raster",
                    "source_tools",
                    "observation",
                    "oracle_exit_code",
                },
            )
            if (
                raw["schema_version"] != "template-native-slide-source-valid-control-v1"
                or raw["name"] != name
                or raw["expected_code"] != code
            ):
                raise ValueError("slide-source control original identity differs")
            _closure(raw, controls, directory, run_id)
            if not isinstance(raw["source_tools"], list) or len(raw["source_tools"]) != 1:
                raise ValueError("slide-source control omitted its original source parser")
            original_source = leaf / "fixture/parser/invented.md"
            if controls.read(original_source.relative_to(reader.root).as_posix()).content != CONTROL_SOURCE:
                raise ValueError("slide-source original parser consumed different source DATA")
            source_tool = _tool(
                raw["source_tools"][0],
                controls,
                run_id,
                "pandoc",
                "control-source-ast",
                [str(producer_path(custody, reader.root, original_source)), "--to=json"],
            )
            if json.loads(source_tool["stdout"]) != json.loads(ast):
                raise ValueError("slide-source current parser differs from the actual original source parse")
            pdf, contract, bindings = slide_source_control_fixture(name, ast)
            native = _file(raw["input"], controls)
            if (
                native.path != leaf / "fixture/control.pdf"
                or native.content != pdf
                or raw["parser"] != parse_native_bytes("pdf", pdf)
            ):
                raise ValueError("slide-source valid mutant differs from independent current source fixture")
            _raster(raw, native, 0, leaf / "fixture", controls, run_id, versions, custody)
            pixels = tuple(
                _file({"path": row["path"], "sha256": row["sha256"]}, controls).content
                for row in raw["raster"]["rasters"]
            )
            observed = inspect_slide_source_paint(pdf, pixels, contract, bindings, deadline=deadline, source_images={})
            if raw["observation"] != observed:
                raise ValueError("slide-source independent paint/geometry/typography observations differ")
            _outcome(raw, [observed], code)
            outcomes.append(
                {
                    "name": name,
                    "original_exit_code": item["original_exit_code"],
                    "reconstructed_exit_code": expected,
                    "intended_diagnostic": code,
                    "targets": [{"fixture": "two-page-source-pdf", "name": name}],
                    "observation": observed,
                    "artifact": item["artifact"],
                }
            )
    if not controls.unchanged() or not reader.unchanged():
        raise ValueError("slide-source control custody changed during independent readback")
    remaining(deadline)
    return {"suite_id": "manuscript_slides", "scope": scope, "original_run_id": run_id, "outcomes": outcomes}
