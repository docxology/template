"""Actual subprocess controls over configured print outputs and source witnesses."""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any


from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.project.public_acceptance_evidence import runtime_identity, write_json
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_print_artifact_observer import (
    PRINT_SCOPES,
    PRINT_PLATFORMS,
    FINDING,
    configured_print_target,
    inspect_configured_print,
)
from infrastructure.reporting.native_print_artifact_replay import admit_print_reference
from infrastructure.reporting.native_print_mutations import mutate_print as mutate_print
from infrastructure.reporting.native_storybook_source import source_package
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-configured-print-controls-v2"
PROCESS_SCHEMA = "template-configured-print-control-process-v1"
MODULE = "infrastructure.reporting.native_print_artifact_controls"
STORYBOOK_CONTROLS = (
    "baseline",
    "caption-pixels",
    "background-pixels",
    "png-transparency",
    "contact-order",
    "contact-caption",
    "page-order",
    "omitted-page",
    "pdf-clipping",
    "pdf-geometry",
    "pdf-hidden",
    "pdf-image",
    "pdf-font",
)
NEWSPAPER_CONTROLS = (
    "baseline",
    "page-order",
    "omitted-page",
    "pdf-clipping",
    "pdf-geometry",
    "pdf-hidden",
    "pdf-image",
    "pdf-font",
    "pdf-text",
)


def print_control_names(scope: str) -> tuple[str, ...]:
    if scope not in PRINT_SCOPES:
        raise ValueError("unknown configured print control scope")
    return STORYBOOK_CONTROLS if PRINT_SCOPES[scope] == "storybook" else NEWSPAPER_CONTROLS


def print_control_artifacts(root: Path, scope: str) -> tuple[NativeArtifact, ...]:
    """Derive only the specialized artifacts from current source configuration."""
    project = root / "projects" / scope
    base = f"projects/{scope}"
    if PRINT_SCOPES[scope] == "newspaper":
        from infrastructure.reporting.native_storybook_source import read_source_yaml

        manifest = read_source_yaml(project / "content/edition.yaml")
        name = manifest.get("render", {}).get("output_basename", "the-triplicate")
        rows = [NativeArtifact("newspaper:edition:pdf", "pdf", f"{base}/output/pdf/{name}.pdf")]
    else:
        provider = source_package(project, "storybook")
        spec = provider.load_storybook(project)
        rows = [NativeArtifact("storybook:print:pdf", "pdf", f"{base}/{spec.output_pdf.as_posix()}")]
        rows.extend(
            NativeArtifact(f"storybook:page:{index}", "png", f"{base}/output/figures/storybook_pages/{page.filename}")
            for index, page in enumerate(spec.pages)
        )
        rows.append(
            NativeArtifact("storybook:contact-sheet", "png", f"{base}/output/figures/storybook_contact_sheet.png")
        )
    for row in rows:
        configured_print_target(root, scope, row)
    return tuple(rows)


def selected_control_artifacts(root: Path, scope: str, name: str) -> tuple[NativeArtifact, ...]:
    rows = print_control_artifacts(root, scope)
    if name not in print_control_names(scope):
        raise ValueError("unknown configured print negative control")
    if name == "baseline":
        return rows
    if name in {"caption-pixels", "background-pixels", "png-transparency"}:
        return tuple(row for row in rows if row.id == "storybook:page:0")
    if name in {"contact-order", "contact-caption"}:
        return tuple(row for row in rows if row.id == "storybook:contact-sheet")
    return tuple(row for row in rows if row.format == "pdf")


def run_print_control(
    root: Path,
    directory: Path,
    scope: str,
    name: str,
    *,
    run_id: str,
    worker_pid: int,
    worker_platform: str,
    deadline: float,
    env: dict[str, str],
    reader: SnapshotReader,
) -> int:
    """Write and inspect actual native bytes; caller preserves the original exit."""
    if worker_platform not in PRINT_PLATFORMS or platform.system() != worker_platform:
        raise ValueError("configured print control does not execute on the admitted original worker platform")
    kind = PRINT_SCOPES[scope]
    from infrastructure.reporting.native_print_artifact_observer import _source_reference

    # Every child starts with genuine fresh Source/Code custody and makes its
    # own original witness. Parent font/tool transcripts are never authority.
    reference_directory = directory / "reference-owner"
    binding = _source_reference(root, reference_directory, scope, reader, env=env, deadline=deadline, run_id=run_id)
    reference, source = admit_print_reference(
        root,
        reference_directory,
        scope,
        binding,
        reader,
        run_id=run_id,
        custody={"root": str(root.resolve())},
        runtime=runtime_identity(),
        expected_pid=worker_pid,
        expected_platform=worker_platform,
        deadline=deadline,
    )
    from infrastructure.reporting.native_newspaper_source import NewspaperReference

    rows = []
    for ordinal, artifact in enumerate(selected_control_artifacts(root, scope, name)):
        snapshot = reader.read(artifact.path)
        target, page = configured_print_target(root, scope, artifact)
        candidate = mutate_print(snapshot.content, name, kind)
        output = write_binary(root, directory / f"candidate-{ordinal:04d}.{artifact.format}", candidate)
        row: dict[str, Any] = {
            "artifact": asdict(artifact),
            "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "candidate": output,
        }
        candidate_rasters: tuple[bytes, ...] = ()
        source_rasters: tuple[bytes, ...] = ()
        if isinstance(reference, NewspaperReference):
            native = directory / f"native-{ordinal:04d}"
            create_private_native_directory(root, native)
            row["raster"] = audit_pdf_raster(
                root,
                native,
                reader.read(output["path"]),
                parse_native_bytes("pdf", candidate),
                env=env,
                deadline=deadline,
                run_id=run_id,
                ordinal=0,
            )
            candidate_rasters = tuple(reader.read(item["path"]).content for item in row["raster"]["rasters"])
            source_rasters = tuple(reader.read(item["path"]).content for item in source["raster"]["rasters"])
        row["observation"] = inspect_configured_print(
            candidate,
            reference,
            kind=target,
            page_number=page,
            candidate_rasters=candidate_rasters,
            source_rasters=source_rasters,
            deadline=deadline,
        )
        rows.append(row)
    code = 0 if name == "baseline" else 1
    if not rows or any(row["observation"]["blockers"] for row in rows):
        raise ValueError("unsupported print control cannot provide a native negative result")
    if name == "baseline":
        if any(row["observation"]["status"] != "pass" for row in rows):
            raise ValueError("actual configured print positive baseline failed")
    elif not all(
        row["observation"]["status"] == "fail"
        and {item["code"] for item in row["observation"]["findings"]} == {FINDING}
        for row in rows
    ):
        raise ValueError("actual configured print mutant lacked its intended source diagnostic")
    if not reader.unchanged():
        raise ValueError("actual print control source/artifacts changed during inspection")
    write_json(
        root,
        directory / "control-observation.json",
        {
            "schema_version": SCHEMA,
            "scope": scope,
            "name": name,
            "run_id": run_id,
            "worker_pid": worker_pid,
            "worker_platform": worker_platform,
            "print_reference": binding,
            "rows": rows,
            "oracle_exit_code": code,
        },
    )
    return code


def supervise_print_controls(
    root: Path,
    directory: Path,
    scope: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    interpreter: Path,
) -> list[dict[str, Any]]:
    """Launch fresh admitted SDK/Source children; retain genuine original 0/1 exits."""
    import hashlib
    import json
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.reporting.native_print_child_custody import CHILD_SCHEMA, WORKER, PrintControlReaderOperation
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.project.public_reference_git import remaining

    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline:
        raise ValueError("configured print controls require this actual live Source/ToolAPI owner and original clock")
    source = owner.source
    selected_runtime = json.loads(source.bindings.expected_implementation_bytes)["runtime_environment"]
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != selected_runtime["python_executable"]:
        raise ValueError("configured print controls differ from the actual admitted selected interpreter")
    parent_reader = SnapshotReader(root, native_producer_operation=owner)
    records: list[dict[str, Any]] = []
    for ordinal, name in enumerate(print_control_names(scope)):
        remaining(deadline)
        # Admission, fresh code prefix, child, cleanup and sealing share this
        # genuine existing ToolAPI cap; the enclosing clock never extends.
        child_deadline = min(deadline, time.monotonic() + 120.0)
        leaf = directory / f"print-control-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        create_private_native_directory(root, leaf / "closure")
        source.verify_correspondence(source.reference, root, parent_reader, child_deadline)
        implementation_path = leaf / "implementation.json"
        atomic_write_bytes_confined(
            root, implementation_path, source.bindings.expected_implementation_bytes, mode=0o600
        )
        implementation = parent_reader.read(implementation_path.relative_to(root).as_posix())
        closure_identity = (leaf / "closure").stat()
        specification = {
            "schema_version": CHILD_SCHEMA,
            "scope": scope,
            "name": name,
            "run_id": run_id,
            "directory": leaf.relative_to(root).as_posix(),
            "source": json.loads(source.descriptor(scope, deadline=child_deadline)),
            "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
            "expected_exit": 0 if name == "baseline" else 1,
            "parent_pid": os.getpid(),
            "parent_platform": platform.system(),
            "deadline_monotonic": child_deadline,
            "caller_deadline_monotonic": deadline,
            "closure_identity": [closure_identity.st_dev, closure_identity.st_ino],
        }
        spec = write_json(root, leaf / "specification.json", specification)
        sdk = source.bindings.selected_sdk_package_root
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        if (
            json.loads(source.bindings.expected_implementation_bytes)["files"]["infrastructure/core/bytecode_audit.py"]
            != hashlib.sha256(hook).hexdigest()
        ):
            raise ValueError("configured print child raw hook differs from the admitted installed SDK")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            (root / "projects" / scope / "src",),
            implementation_path,
            implementation.sha256,
            leaf / "closure",
            (closure_identity.st_dev, closure_identity.st_ino),
            child_deadline,
            required_worker_module=WORKER,
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
            purpose="print-child",
            preserve_nominated_launcher=True,
        )
        expected = specification["expected_exit"]
        if process["exit_code"] != expected or process["original_exit_code"] != expected:
            raise ValueError("actual configured print child failed its required original native oracle")
        result = parent_reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
        closure = parent_reader.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
        item = {
            "name": name,
            "artifact": {"path": result.relative, "sha256": result.sha256},
            "process_artifact": process["artifact"],
            "specification_artifact": spec,
            "closure_artifact": {"path": closure.relative, "sha256": closure.sha256},
            "original_exit_code": expected,
        }
        # This constructor requires the actual live parent, not its JSON. The
        # final installed reader independently supplies its own genuine owner.
        context = PrintControlReaderOperation(
            source, parent_reader, [item], scope=scope, run_id=run_id, deadline=deadline
        )
        context.child(item, SnapshotReader(root, native_control_operation=context))
        records.append(item)
        source.verify_correspondence(source.reference, root, parent_reader, deadline)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
    from infrastructure.reporting.native_print_child_custody import CHILD_SCHEMA
    from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
    from infrastructure.reporting.native_tool_producer import native_producer_operation
    import infrastructure
    import json

    with native_deadline_guard(args.deadline):
        root = args.root.absolute()
        reader = SnapshotReader(root)
        specification = reader.read(args.specification)
        spec = specification.json_object()
        if (
            specification.sha256 != args.specification_sha256
            or spec.get("schema_version") != CHILD_SCHEMA
            or spec.get("deadline_monotonic") != args.deadline
            or spec.get("run_id") != args.run_id
        ):
            raise ValueError("configured print child differs from actual parent prelaunch role/clock/Source bytes")
        scope, name = spec["scope"], spec["name"]
        if (
            scope not in PRINT_SCOPES
            or name not in print_control_names(scope)
            or spec["expected_exit"] != (0 if name == "baseline" else 1)
        ):
            raise ValueError("configured print child is outside the complete Source-owned control roster")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("configured print child selected implementation differs from its actual parent nomination")
        if infrastructure.__file__ is None:
            raise ValueError("configured print child actual installed SDK origin is unavailable")
        metadata = root.stat()
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(metadata.st_dev, metadata.st_ino),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(scope, deadline=args.deadline)) != spec["source"]:
            raise ValueError("configured print child lacks fresh genuine original/current Source correspondence")
        directory = root / spec["directory"]
        if (
            specification.path != directory / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
        ):
            raise ValueError("configured print child differs from actual original parent/root/platform")
        with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            code = run_print_control(
                root,
                directory,
                scope,
                name,
                run_id=args.run_id,
                worker_pid=os.getpid(),
                worker_platform=platform.system(),
                deadline=args.deadline,
                env=native_environment(root, Path(sys.executable), directory),
                reader=reader,
            )
            source.verify_correspondence(source.reference, root, reader, args.deadline)
            observation = reader.read((directory / "control-observation.json").relative_to(root).as_posix())
            sys.stdout.write(f"PRINT_OBSERVATION_V2 {specification.sha256} {observation.sha256} {args.run_id} {code}\n")
            sys.stdout.flush()
            return code


if __name__ == "__main__":
    raise SystemExit(main())
