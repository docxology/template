"""Existing exact parser, PDF and Source-selected native control replay."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.reporting.native_format_acceptance_contracts import CONTROL_SCHEMA, WORKER_MODULE, NativeArtifact
from infrastructure.reporting.native_format_portable_custody import producer_bootstrap, producer_path
from infrastructure.reporting.native_print_artifact_observer import PRINT_SCOPES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_joint_source import NativeReaderOperation
    from infrastructure.reporting.release_readiness_profile import Requirement


def validate_native_controls(
    requirement: Requirement,
    raw: dict[str, Any],
    reader: SnapshotReader,
    directory: Path,
    nonce: str,
    runtime: dict[str, Any],
    specification: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    contract: tuple[NativeArtifact, ...],
    custody: dict[str, str],
    *,
    deadline: float,
    operation: NativeReaderOperation,
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _process,
        _tool,
        native_environment_for_replay,
    )

    checked_refusals: list[dict[str, Any]] = []
    checked_suites: dict[str, Any] = {}
    controls = raw.get("negative_controls")
    kinds = sorted({item.format for item in contract})
    if not isinstance(controls, list) or [item.get("name") for item in controls if isinstance(item, dict)] != [
        *(f"invalid-native-{kind}" for kind in kinds),
        "invalid-pdf-tool",
    ]:
        raise ValueError("native actual negative controls are missing or duplicated")
    for control, kind in zip(controls[:-1], kinds, strict=True):
        observed_file = _file(control.get("artifact"), reader)
        observed = observed_file.json_object()
        expected = {
            "schema_version": CONTROL_SCHEMA,
            "run_id": nonce,
            "name": f"invalid-native-{kind}",
            "format": kind,
            "exit_code": 1,
        }
        if observed != expected or control.get("expected_exit_code") != 1 or control.get("observed_exit_code") != 1:
            raise ValueError("native parser control did not record its actual rejection")
        args = [
            "--root",
            custody["root"],
            "--control",
            kind,
            "--run-id",
            nonce,
            "--control-output",
            str(producer_path(custody, reader.root, observed_file.path)),
        ]
        control_command = producer_bootstrap(custody, reader.root, runtime, WORKER_MODULE, *args)
        _process(
            _file(control.get("process_artifact"), reader).json_object(),
            nonce,
            control_command,
            1,
        )
        checked_refusals.append(
            {
                "name": control["name"],
                "original_exit_code": 1,
                "artifact": control["artifact"],
                "process_artifact": control["process_artifact"],
            }
        )
    invalid = directory / "invented-invalid.pdf"
    if (
        reader.read(invalid.relative_to(reader.root).as_posix()).content
        != b"invented public malformed PDF negative control\n"
    ):
        raise ValueError("native tool negative-control input changed")
    _tool(
        controls[-1].get("artifact"),
        reader,
        nonce,
        "pdftoppm",
        "invalid-pdf-tool",
        [
            str(producer_path(custody, reader.root, invalid)),
            str(producer_path(custody, reader.root, directory / "invalid-raster")),
        ],
        1,
    )
    checked_refusals.append({"name": "invalid-pdf-tool", "original_exit_code": 1, "artifact": controls[-1]["artifact"]})
    from infrastructure.reporting.native_format_pdf_control_replay import replay_pdf_controls

    pdf_results = replay_pdf_controls(
        raw,
        reader,
        directory,
        nonce,
        runtime,
        specification,
        versions,
        any(item.format == "pdf" for item in contract),
        custody,
        deadline=deadline,
    )
    if pdf_results:
        checked_suites["pdf"] = {**pdf_results, "scope": requirement.scope}
    from infrastructure.reporting.native_format_control_replay import (
        validate_format_controls,
    )
    from infrastructure.reporting.native_format_observer_validation import (
        replay_browser_controls,
    )

    controls = raw.get("observer_controls")
    if not isinstance(controls, dict):
        raise ValueError("native format observer control suite is missing")
    if requirement.scope in PRINT_SCOPES:
        from infrastructure.reporting.native_print_control_replay import validate_print_controls

        checked_suites["configured_print"] = validate_print_controls(
            controls.get("print"),
            reader.root,
            directory,
            requirement.scope,
            reader,
            run_id=nonce,
            custody=custody,
            runtime=runtime,
            versions=versions,
            expected_pid=raw["pid"],
            expected_platform=raw["host_before"]["system"],
            original_deadline=specification["deadline_monotonic"],
            deadline=deadline,
            source=operation.source,
        )
    elif "print" in controls:
        raise ValueError("native print control suite is outside the source-owned configured print scope")
    replay_deadline = deadline
    replay_env = native_environment_for_replay(reader.root)
    from infrastructure.reporting.native_office_scientific_suite import replay_selected_office_scientific_controls

    scientific_results = replay_selected_office_scientific_controls(
        controls,
        contract,
        reader,
        directory,
        scope=requirement.scope,
        source=operation.source,
        run_id=nonce,
        custody=custody,
        runtime=runtime,
        versions=versions,
        original_deadline=specification["deadline_monotonic"],
        deadline=replay_deadline,
        env=replay_env,
        observer_tools=specification.get("observer_tools", {}),
    )
    checked_suites.update(scientific_results)
    format_controls = {
        key: value for key, value in controls.items() if key not in {"print", "office_scientific", "configured_pitch"}
    }
    from infrastructure.reporting.native_projection_source_dispatch import projection_control_formats

    format_results = validate_format_controls(
        format_controls,
        projection_control_formats(contract, requirement.formats),
        reader,
        directory,
        scope=requirement.scope,
        run_id=nonce,
        custody=custody,
        runtime=runtime,
        versions=versions,
        deadline=replay_deadline,
        env=replay_env,
        original_deadline=specification["deadline_monotonic"],
    )
    checked_suites.update(format_results)
    if "html" in requirement.formats:
        for semantic, key in ((False, "html"), (True, "html_semantic")):
            checked_suites[key] = replay_browser_controls(
                reader.root,
                directory,
                controls[key],
                reader,
                run_id=nonce,
                custody=custody,
                runtime=runtime,
                semantic=semantic,
                deadline=replay_deadline,
                env=replay_env,
                scope=requirement.scope,
            )
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("complete native control replay changed held Source evidence")
    return {
        "scope": requirement.scope,
        "original_run_id": nonce,
        "source_binding": [operation.source.reference.commit, operation.source.reference.source_identity],
        "suites": checked_suites,
        "original_refusals": checked_refusals,
    }
