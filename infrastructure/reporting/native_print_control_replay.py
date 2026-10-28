"""Independent configured-print mutant reconstruction with original process exits."""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_newspaper_source import NewspaperReference
from infrastructure.reporting.native_print_artifact_controls import (
    SCHEMA,
    mutate_print,
    print_control_names,
    selected_control_artifacts,
)
from infrastructure.reporting.native_print_artifact_observer import (
    PRINT_SCOPES,
    PRINT_PLATFORMS,
    FINDING,
    configured_print_target,
    inspect_configured_print,
)
from infrastructure.reporting.native_print_artifact_replay import _admit_raster, admit_print_reference
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_print_child_custody import PrintControlReaderOperation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def validate_print_controls(
    records: object,
    root: Path,
    directory: Path,
    scope: str,
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    expected_pid: int,
    expected_platform: str,
    original_deadline: float,
    deadline: float,
    source: NativeSourceContext,
) -> dict[str, Any]:
    """Admit every source-defined real baseline/mutant and its original exit."""
    if (
        type(expected_pid) is not int
        or expected_pid <= 0
        or type(expected_platform) is not str
        or expected_platform not in PRINT_PLATFORMS
    ):
        raise ValueError("configured print controls require the admitted actual original worker PID/platform")
    names = print_control_names(scope)
    if not isinstance(records, list) or [row.get("name") for row in records if isinstance(row, dict)] != list(names):
        raise ValueError("configured print controls are missing, duplicated or reordered")
    context = PrintControlReaderOperation(source, reader, records, scope=scope, run_id=run_id, deadline=deadline)
    reader = SnapshotReader(root, native_control_operation=context)
    outcomes: list[dict[str, Any]] = []
    for ordinal, (item, name) in enumerate(zip(records, names, strict=True)):
        if time.monotonic() >= deadline:
            raise TimeoutError("configured print portable control deadline")
        if set(item) != {
            "name",
            "artifact",
            "process_artifact",
            "specification_artifact",
            "closure_artifact",
            "original_exit_code",
        }:
            raise ValueError("configured print control has unsupported fields")
        leaf = directory / f"print-control-{ordinal:04d}"
        expected = 0 if name == "baseline" else 1
        child = context.child(item, reader)
        specification = child["specification"]
        child_pid = child["process"]["pid"]
        if (
            specification["directory"] != leaf.relative_to(root).as_posix()
            or specification["expected_exit"] != expected
            or specification["parent_pid"] != expected_pid
            or specification["parent_platform"] != expected_platform
            or specification["caller_deadline_monotonic"] != original_deadline
            or type(item["original_exit_code"]) is not int
            or item["original_exit_code"] != expected
        ):
            raise ValueError("configured print control differs from its admitted actual parent/role/original clock")
        result = _file(item["artifact"], reader)
        raw = result.json_object()
        if (
            result.path != leaf / "control-observation.json"
            or set(raw)
            != {
                "schema_version",
                "scope",
                "name",
                "run_id",
                "worker_pid",
                "worker_platform",
                "print_reference",
                "rows",
                "oracle_exit_code",
            }
            or raw["schema_version"] != SCHEMA
            or raw["scope"] != scope
            or raw["name"] != name
            or raw["run_id"] != run_id
            or type(raw["worker_pid"]) is not int
            or raw["worker_pid"] != child_pid
            or raw["worker_platform"] != expected_platform
            or type(raw["oracle_exit_code"]) is not int
            or raw["oracle_exit_code"] != expected
        ):
            raise ValueError("configured print original control identity/outcome differs")
        reference, reference_source = admit_print_reference(
            root,
            leaf / "reference-owner",
            scope,
            raw["print_reference"],
            reader,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            expected_pid=child_pid,
            expected_platform=expected_platform,
            deadline=deadline,
        )
        artifacts = selected_control_artifacts(root, scope, name)
        rows = raw["rows"]
        if not isinstance(rows, list) or len(rows) != len(artifacts) or not rows:
            raise ValueError("configured print control omitted source-owned actual artifacts")
        checked_rows: list[dict[str, Any]] = []
        for index, (row, artifact) in enumerate(zip(rows, artifacts, strict=True)):
            fields = {"artifact", "input", "candidate", "observation"} | (
                {"raster"} if isinstance(reference, NewspaperReference) else set()
            )
            if not isinstance(row, dict) or set(row) != fields or row["artifact"] != asdict(artifact):
                raise ValueError("configured print control substituted its native obligation")
            original = reader.read(artifact.path)
            if row["input"] != {"path": original.relative, "sha256": original.sha256}:
                raise ValueError("configured print control input differs from actual pipeline output")
            candidate = _file(row["candidate"], reader)
            if candidate.path != leaf / f"candidate-{index:04d}.{artifact.format}" or candidate.content != mutate_print(
                original.content, name, PRINT_SCOPES[scope]
            ):
                raise ValueError("configured print actual mutant differs from source-defined transformation")
            kind, page = configured_print_target(root, scope, artifact)
            candidate_rasters: tuple[bytes, ...] = ()
            source_rasters: tuple[bytes, ...] = ()
            if isinstance(reference, NewspaperReference):
                candidate_rasters = _admit_raster(
                    row,
                    candidate,
                    leaf / f"native-{index:04d}",
                    reader,
                    run_id=run_id,
                    custody=custody,
                    versions=versions,
                    deadline=deadline,
                )
                source_rasters = tuple(
                    _file({"path": page["path"], "sha256": page["sha256"]}, reader).content
                    for page in reference_source["raster"]["rasters"]
                )
            observed = inspect_configured_print(
                candidate.content,
                reference,
                kind=kind,
                page_number=page,
                candidate_rasters=candidate_rasters,
                source_rasters=source_rasters,
                deadline=deadline,
            )
            if row["observation"] != observed or observed["blockers"]:
                raise ValueError("configured print portable control observation differs or is unsupported")
            if expected == 0:
                if observed["status"] != "pass" or observed["findings"]:
                    raise ValueError("configured print actual complete positive baseline did not pass")
            elif observed["status"] != "fail" or {finding["code"] for finding in observed["findings"]} != {FINDING}:
                raise ValueError("configured print actual native mutant omitted its intended diagnostic")
            checked_rows.append({"artifact": asdict(artifact), "observation": observed})
        outcomes.append(
            {
                "name": name,
                "original_exit_code": item["original_exit_code"],
                "reconstructed_exit_code": expected,
                "intended_diagnostic": None if name == "baseline" else FINDING,
                "targets": [asdict(a) for a in artifacts],
                "rows": checked_rows,
                "artifact": item["artifact"],
            }
        )
    if not reader.unchanged():
        raise ValueError("configured print source/native/control bytes changed during independent admission")
    return {"suite_id": "configured_print", "scope": scope, "original_run_id": run_id, "outcomes": outcomes}
