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


from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.project.public_acceptance_evidence import bootstrap_command, runtime_identity, write_json
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

SCHEMA = "template-configured-print-controls-v1"
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
) -> int:
    """Write and inspect actual native bytes; caller preserves the original exit."""
    if worker_platform not in PRINT_PLATFORMS or platform.system() != worker_platform:
        raise ValueError("configured print control does not execute on the admitted original worker platform")
    reader = SnapshotReader(root)
    kind = PRINT_SCOPES[scope]
    reference_file = reader.read(
        (directory.parent / f"print-reference-{kind}/source-reference.json").relative_to(root).as_posix()
    )
    binding = {"path": reference_file.relative, "sha256": reference_file.sha256}
    reference, source = admit_print_reference(
        root,
        directory,
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
    """Retain original baseline 0 and meaningful native-mutant 1 subprocess exits."""
    records = []
    for ordinal, name in enumerate(print_control_names(scope)):
        leaf = directory / f"print-control-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        command = bootstrap_command(
            interpreter,
            root,
            MODULE,
            "--scope",
            scope,
            "--control",
            name,
            "--root",
            str(root),
            "--directory",
            str(leaf),
            "--deadline",
            str(deadline),
            "--run-id",
            run_id,
            "--worker-pid",
            str(os.getpid()),
            "--worker-platform",
            platform.system(),
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("configured print controls exhausted original deadline")
        process = run_bounded_subprocess(command, cwd=root, env=env, timeout=remaining)
        expected = 0 if name == "baseline" else 1
        if (
            process.timed_out
            or process.custody_refused
            or process.returncode != expected
            or process.original_returncode != expected
        ):
            raise ValueError("actual print control failed to preserve its required original process outcome")
        reader = SnapshotReader(root)
        result = reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
        if result.json_object().get("oracle_exit_code") != expected:
            raise ValueError("actual print control omitted its observed oracle outcome")
        binding = write_json(
            root,
            leaf / "control-process.json",
            {
                "schema_version": PROCESS_SCHEMA,
                "run_id": run_id,
                "command": list(command),
                "exit_code": process.returncode,
                "original_exit_code": process.original_returncode,
                "timed_out": process.timed_out,
                "custody_refused": process.custody_refused,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "diagnostic": process.command_error,
            },
        )
        records.append(
            {
                "name": name,
                "artifact": {"path": result.relative, "sha256": result.sha256},
                "process_artifact": binding,
                "original_exit_code": process.original_returncode,
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=tuple(PRINT_SCOPES), required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--worker-pid", type=int, required=True)
    parser.add_argument("--worker-platform", choices=tuple(sorted(PRINT_PLATFORMS)), required=True)
    args = parser.parse_args()
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment

    with native_deadline_guard(args.deadline):
        return run_print_control(
            args.root,
            args.directory,
            args.scope,
            args.control,
            run_id=args.run_id,
            worker_pid=args.worker_pid,
            worker_platform=args.worker_platform,
            deadline=args.deadline,
            env=native_environment(args.root, Path(sys.executable), args.directory),
        )


if __name__ == "__main__":
    raise SystemExit(main())
