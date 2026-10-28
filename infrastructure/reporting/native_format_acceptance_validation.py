"""Independent native conformance reconstruction and full-acceptance refusal."""

from __future__ import annotations

import math
import re
from io import BytesIO
from collections.abc import Mapping
from pathlib import Path
from uuid import uuid4
from typing import TYPE_CHECKING, Any

from infrastructure.reporting.native_format_portable_source import native_source_content_identity
from infrastructure.reporting.native_format_joint_source import (
    require_native_operation,
    validate_original_joint_launch,
    validate_retained_sdk_closure,
)
from infrastructure.project.native_format_library_custody import validate_native_library_custody
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.plan_serialization import plan_from_payload
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.reporting.native_format_portable_custody import (
    producer_path,
    validate_producer_custody,
    validate_executable_observation,
)
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import (
    NATIVE_SCHEMA,
    PROCESS_SCHEMA,
    TOOL_SCHEMA,
    TOOL_FIELDS,
    CITATION_TOOL_FIELDS,
    HTML_TOOL_FIELDS,
    contract_digest,
    native_artifact_contract,
    public_source_digest,
    validate_native_specification,
)
from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract
from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
from infrastructure.reporting.native_format_pdf_control_replay import replay_pdf_controls as _pdf_controls  # noqa: F401 - compatibility for existing Source tests
from infrastructure.reporting.native_oracle_phase import NativeOraclePhase, finish_reader_native_oracle_phase
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)
from infrastructure.reporting.native_print_artifact_observer import selected_print_artifact
from infrastructure.rendering.config import RenderingConfig
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance


__all__ = [
    "_pdf_controls",
    "native_environment_for_replay",
    "validate_native_acceptance",
    "validate_native_conformance",
]

if TYPE_CHECKING:
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext
    from infrastructure.reporting.release_readiness_profile import Requirement
    from infrastructure.reporting.native_office_scope_cohorts import CurrentOfficeCohorts
    from infrastructure.reporting.native_renderer_section_roster import RendererScopeReplay
    from infrastructure.reporting.native_office_full_worker_context import OfficeCurrentReaderContext


def _file(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("native evidence requires an exact artifact binding")
    snapshot = reader.read(binding["path"])
    if binding["sha256"] != snapshot.sha256 or not snapshot.content:
        raise ValueError("native evidence bytes differ from their binding")
    return snapshot


def _process(raw: dict[str, Any], nonce: str, command: list[str], code: int) -> None:
    if (
        raw.get("schema_version") != PROCESS_SCHEMA
        or raw.get("run_id") != nonce
        or raw.get("command") != command
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != code
        or type(raw.get("original_exit_code")) is not int
        or raw["original_exit_code"] != code
        or raw.get("timed_out") is not False
        or raw.get("custody_refused") is not False
    ):
        raise ValueError("native process did not produce its bound original outcome")


def _tool(
    binding: object,
    reader: SnapshotReader,
    nonce: str,
    name: str,
    purpose: str,
    arguments: list[str],
    code: int = 0,
) -> dict[str, Any]:
    raw = _file(binding, reader).json_object()
    executable = raw.get("executable")
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError("native tool identity is not an actual absolute executable")
    if (
        frozenset(raw) not in {TOOL_FIELDS, CITATION_TOOL_FIELDS, HTML_TOOL_FIELDS}
        or raw.get("schema_version") != TOOL_SCHEMA
        or raw.get("run_id") != nonce
        or raw.get("tool") != name
        or raw.get("purpose") != purpose
        or not isinstance(raw.get("command"), list)
        or len(raw["command"]) != len(arguments) + 1
        or raw["command"][1:] != arguments
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != code
        or type(raw.get("original_exit_code")) is not int
        or raw["original_exit_code"] != code
        or raw.get("timed_out") is not False
        or raw.get("custody_refused") is not False
    ):
        raise ValueError("actual native tool command/run/outcome differs from its required observation")
    if frozenset(raw) == HTML_TOOL_FIELDS and (
        not isinstance(raw["html_python_source_closure"], dict) or raw["html_python_source_closure_error"] is not None
    ):
        raise ValueError("actual HTML Python launch requires its closed Source observation")
    # The original nomination, including an admitted venv launcher, is closed
    # against actual Popen argv and physical body in validate_native_tool_data.
    # An absolute requested nomination must additionally remain argv[0].
    process = _file(raw.get("native_process_artifact"), reader).json_object()
    nomination = process.get("nomination")
    if (
        not isinstance(nomination, dict)
        or nomination.get("tool") != name
        or nomination.get("resolved_path") != executable
        or (Path(name).is_absolute() and nomination.get("path") != name)
        or raw["command"][0] != (nomination.get("path") if process.get("launcher_preserved") else executable)
    ):
        raise ValueError("actual Source-nominated launcher differs from original Popen custody")
    for key in ("executable_observation_before", "executable_observation_after"):
        validate_executable_observation(raw.get(key), executable, raw.get("executable_sha256"))
    from infrastructure.reporting.native_tool_replay import (
        validate_original_native_tool,
    )

    if reader.native_producer_operation is not None:
        from infrastructure.reporting.native_tool_producer import (
            validate_live_native_tool,
        )

        validate_live_native_tool(binding, raw, reader, run_id=nonce)
    else:
        validate_original_native_tool(binding, raw, reader, run_id=nonce)
    return raw


def _pipeline(raw: dict[str, Any], scope: str, reader: SnapshotReader, custody: dict[str, Any]) -> RunResult:
    from infrastructure.reporting.native_format_acceptance_worker import (
        require_canonical_native_stages,
    )

    if raw.get("mode") != "core" or raw.get("selection") != {
        "skip_clean": True,
        "skip_infra": True,
    }:
        raise ValueError("native conformance requires explicit whole-core selection")
    plan = plan_from_payload(raw.get("plan"), expected_digest=raw.get("plan_digest"))
    if plan.project != scope or not isinstance(raw.get("run_id"), str) or not raw["run_id"]:
        raise ValueError("native pipeline has a different project/run identity")
    reader.read(plan.provenance)
    config = PipelineConfig(
        scope,
        reader.root,
        clean=False,
        skip_infra=True,
        mode="core",
        run_timeout_seconds=plan.run_timeout_seconds,
    )
    expected = compile_execution_plan(config)
    require_canonical_native_stages(expected)
    # Runtime/environment identities belong to the admitted worker, not the
    # environment of a later reader. Compare the entire logical source plan;
    # source bytes, actual interpreter and tools have their separate bindings.
    recorded_shape, expected_shape = plan.to_dict(), expected.to_dict()
    for key in ("source_identity", "environment_identity"):
        recorded_shape.pop(key)
        expected_shape.pop(key)
    if recorded_shape != expected_shape:
        raise ValueError("native execution differs from the complete current source-owned plan")
    content = native_source_content_identity(
        reader.root,
        config.project_dir,
        custody,
        definition_path=reader.root / plan.provenance,
    )
    if raw.get("source_content_identity") != content or raw.get("expected_stage_keys") != list(
        plan.expected_stage_keys
    ):
        raise ValueError("native execution source or expected stages changed")
    rows = raw.get("outcomes")
    if not isinstance(rows, list):
        raise ValueError("native stage outcomes are absent")
    outcomes = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "succeeded":
            raise ValueError("native acceptance needs every fresh succeeded stage")
        codes = row.get("attempt_exit_codes")
        attempts = row.get("attempt_count")
        if (
            not isinstance(codes, list)
            or type(attempts) is not int
            or len(codes) != attempts
            or not codes
            or codes[-1] != 0
        ):
            raise ValueError("native actual child attempt history is incomplete")
        outcome = StageOutcome(
            row.get("stage_key", ""),
            StageStatus.SUCCEEDED,
            row.get("child_exit_code"),
            attempt_count=attempts,
            attempt_exit_codes=tuple(codes),
        )
        if outcome.child_exit_code != 0:
            raise ValueError("native stage did not execute an actual successful child")
        outcomes.append(outcome)
    result = RunResult(plan.expected_stage_keys, tuple(outcomes))
    if not result.complete or result.exit_code:
        raise ValueError("native execution omitted or duplicated required stages")
    return result


def _raster(
    row: dict[str, Any],
    snapshot: ArtifactSnapshot,
    ordinal: int,
    directory: Path,
    reader: SnapshotReader,
    nonce: str,
    versions: dict[str, dict[str, Any]],
    custody: dict[str, str],
) -> None:
    from PIL import Image, ImageStat

    raw = row.get("raster")
    if not isinstance(raw, dict) or raw.get("dpi") != 150:
        raise ValueError("native PDF must have an actual complete 150-dpi raster observation")
    consumed = _file(raw.get("input_artifact"), reader)
    if consumed.path != directory / f"input-{ordinal:04d}.pdf" or consumed.content != snapshot.content:
        raise ValueError("native tools consumed different input bytes from the admitted PDF")
    tools = raw.get("tool_artifacts")
    if not isinstance(tools, list) or len(tools) != 2:
        raise ValueError("native raster/font tools were not both executed")
    prefix = directory / f"raster-{ordinal:04d}"
    for index, (name, arguments, purpose) in enumerate(
        (
            (
                "pdftoppm",
                [
                    "-r",
                    "150",
                    "-png",
                    str(producer_path(custody, reader.root, consumed.path)),
                    str(producer_path(custody, reader.root, prefix)),
                ],
                f"raster-{ordinal:04d}",
            ),
            (
                "pdffonts",
                [str(producer_path(custody, reader.root, consumed.path))],
                f"fonts-{ordinal:04d}",
            ),
        )
    ):
        tool = _tool(tools[index], reader, nonce, name, purpose, arguments)
        if any(tool[key] != versions[name][key] for key in ("executable", "executable_sha256")):
            raise ValueError("native raster used a different tool from its actual version probe")
    rows = raw.get("rasters")
    # Replay every observer schema against geometry parsed from admitted PDF bytes.
    boxes = parse_native_bytes("pdf", snapshot.content)["page_boxes_pt"]
    if not isinstance(rows, list) or len(rows) != len(boxes):
        raise ValueError("native raster omitted actual PDF pages")
    for page, (raster, box) in enumerate(zip(rows, boxes, strict=True), 1):
        if not isinstance(raster, dict):
            raise ValueError("native raster observation is malformed")
        image_file = _file({"path": raster.get("path"), "sha256": raster.get("sha256")}, reader)
        if (
            image_file.path.parent != directory
            or re.fullmatch(
                re.escape(prefix.name) + r"-0*" + str(page) + r"\.png",
                image_file.path.name,
            )
            is None
        ):
            raise ValueError("native raster has the wrong run/page identity")
        with Image.open(BytesIO(image_file.content)) as image:
            image.load()
            variance = sum(ImageStat.Stat(image.convert("RGB")).var)
            if image.format != "PNG" or not math.isfinite(variance) or variance <= 0:
                raise ValueError("native raster is empty/uniform or invalid")
            if (
                raster.get("width_px"),
                raster.get("height_px"),
                raster.get("variance"),
            ) != (
                image.width,
                image.height,
                variance,
            ):
                raise ValueError("native raster observation differs from its actual pixel bytes")
            expected = ((box[2] - box[0]) * 150 / 72, (box[3] - box[1]) * 150 / 72)
            if abs(image.width - expected[0]) > 2 or abs(image.height - expected[1]) > 2:
                raise ValueError("native raster geometry differs from the actual PDF page")


def validate_native_conformance(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
    *,
    current_source: NativeSourceContext | None = None,
    current_directory: Path | None = None,
    provider_wheels: Mapping[str, Path] | None = None,
    pdfium_provider: NativePDFiumProvider | None = None,
    pdfium_runtime: PDFiumRuntimeAdmission | None = None,
    office_font_files: tuple[Path, ...] | None = None,
    current_observer_tools: Mapping[str, Path | None] | None = None,
) -> None:
    """Own genuine fresh current-provider scopes throughout one full readback."""
    from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
        SourceImageDecodeBudget,
        MAX_SOURCE_IMAGE_OCCURRENCES,
    )
    from infrastructure.reporting.native_office_full_worker_context import (
        NativeOfficeReaderSelection,
        office_current_reader_context,
    )

    operation = require_native_operation(reader)
    selection = getattr(operation, "office_reader_selection", None)
    if selection is not None and not isinstance(selection, NativeOfficeReaderSelection):
        raise ValueError("native Office reader selection must be independently supplied and exactly typed")
    from infrastructure.reporting.native_format_scope_replay import replay_native_scope_evidence

    from infrastructure.reporting.native_oracle_phase_reader import current_native_observer_nominees

    observer_nominees = current_native_observer_nominees(current_observer_tools)
    # This is one current replay phase, with one budget held across all source,
    # retained validation, native crop and reproduction allocations.
    budget = getattr(operation, "office_decoded_pixel_budget", None)
    if budget is None:
        budget = SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES)
    if not isinstance(budget, SourceImageDecodeBudget):
        raise ValueError("native Office current reader requires its actual shared decode budget")
    current_artifacts: list[dict[str, Any]] = []
    current_comparisons: list[dict[str, Any]] = []
    oracle_phases: list[NativeOraclePhase] = []
    office_current: list[CurrentOfficeCohorts] = []
    renderer_current: list[RendererScopeReplay] = []
    details["current_scope_replay"] = replay_native_scope_evidence(
        requirement,
        details,
        reader,
        current_source=current_source,
        current_directory=current_directory,
        provider_wheels=provider_wheels,
        pdfium_provider=pdfium_provider,
        pdfium_runtime=pdfium_runtime,
        office_font_files=office_font_files,
        office_current=office_current,
        renderer_current=renderer_current,
        decoded_pixel_budget=budget,
        current_observer_tools=observer_nominees,
        current_artifacts=current_artifacts,
        current_comparisons=current_comparisons,
    )
    if (
        len(office_current) != 1
        or len(renderer_current) != 1
        or len(current_artifacts) != 1
        or len(current_comparisons) != 1
        or current_source is None
    ):
        raise ValueError("native Current Office tuple did not close once under its genuine Source scope")
    directory = reader.root / ".pipeline" / f"native-office-reader-{uuid4().hex}"
    with office_current_reader_context(
        operation,
        selection,
        directory,
        scope=requirement.scope,
        decoded_pixel_budget=budget,
        env=native_environment_for_replay(reader.root),
    ) as office_context:
        _validate_native_conformance(
            requirement,
            details,
            reader,
            office_context=office_context,
            office_current=office_current[0],
            renderer_current=renderer_current[0],
            current_comparison=current_comparisons[0],
            oracle_phases=oracle_phases,
        )
    operation.verify(reader)
    if len(oracle_phases) != 1:
        raise ValueError("native reader requires its one completed checked oracle phase")
    raw = _file(details["native_execution_artifact"], reader).json_object()
    residual_graphs = finish_reader_native_oracle_phase(oracle_phases[0], raw, reader, current_artifacts[0])
    details["native_oracle_phase_residuals"] = residual_graphs.data()
    details["native_oracle_residuals"] = residual_graphs.combined()


def _validate_native_conformance(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
    *,
    office_context: OfficeCurrentReaderContext,
    office_current: CurrentOfficeCohorts,
    renderer_current: RendererScopeReplay,
    current_comparison: dict[str, Any],
    oracle_phases: list[NativeOraclePhase],
) -> None:
    """Validate narrower actual conformance; this never authorizes a full gate."""
    operation = require_native_operation(reader)
    deadline = operation.deadline
    raw_file = _file(details.get("native_execution_artifact"), reader)
    raw = raw_file.json_object()
    if details["current_scope_replay"]["current_renderer"] != renderer_current[0]:
        raise ValueError("Current renderer DATA differs from its genuine retained in-memory roster")
    nonce = raw.get("run_id")
    if (
        raw.get("schema_version") != NATIVE_SCHEMA
        or not isinstance(nonce, str)
        or re.fullmatch(r"[0-9a-f]{32}", nonce) is None
        or raw.get("scope") != requirement.scope
        or details.get("schema_version") != NATIVE_SCHEMA
        or details.get("run_id") != nonce
        or not isinstance(raw.get("native_oracle_requirements"), dict)
        or not isinstance(raw.get("office_mermaid_census"), dict)
        or not isinstance(raw.get("office_diagram_cohorts"), dict)
        or not isinstance(raw.get("office_capability_cells"), list)
        or not isinstance(raw.get("stage_children"), list)
        or not isinstance(raw.get("native_project_domain"), dict)
        or not isinstance(raw.get("loader_persistent_rx_control"), dict)
    ):
        raise ValueError("versioned actual native execution evidence is required")
    specification_file = _file(details.get("specification_artifact"), reader)
    specification = specification_file.json_object()
    validate_native_specification(specification)
    directory = reader.root / specification["directory"]
    if _file(details.get("native_execution_artifact"), reader).path != directory / "native-execution.json":
        raise ValueError("native raw execution belongs to a different evidence attempt")
    if (
        specification["scope"] != requirement.scope
        or specification["run_id"] != nonce
        or specification["formats"] != list(requirement.formats)
        or raw.get("source_digest_before") != public_source_digest(reader.root)
        or raw.get("source_digest_after") != raw["source_digest_before"]
        or specification["source_digest"] != raw["source_digest_before"]
    ):
        raise ValueError("native execution has stale or different source/configuration custody")
    runtime = raw.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("missing") != []:
        raise ValueError("native runtime differs from the actual prepared installed interpreter")
    if runtime.get("python_version") not in {"3.14", "3.15"}:
        raise ValueError("native runtime is unsupported")
    if not isinstance(raw.get("library_custody_before"), dict) or not isinstance(
        raw.get("library_custody_after"), dict
    ):
        raise ValueError("native v4 evidence requires original decoder before/after custody")
    validate_native_library_custody(
        raw["library_custody_before"],
        raw["library_custody_after"],
        formats=requirement.formats,
        reader=reader,
        runtime=runtime,
    )
    probe = _file(raw.get("runtime_artifact"), reader).json_object()
    if probe != {**runtime, "execution_exit_code": 0}:
        raise ValueError("native runtime probe does not bind the recorded actual interpreter")
    custody = validate_producer_custody(raw.get("producer_custody"), runtime, raw["source_digest_before"])
    for key in ("interpreter_observation_before", "interpreter_observation_after"):
        validate_executable_observation(raw.get(key), runtime["executable"], runtime["interpreter_sha256"])
    process_file = _file(details.get("process_artifact"), reader)
    closure_file = _file(details.get("sdk_closure_artifact"), reader)
    command, source_observation = validate_original_joint_launch(
        specification, specification_file, process_file, closure_file, reader, operation
    )
    if (
        custody["root"] != source_observation["current_mirror"]["root"]
        or custody["implementation_root"] != source_observation["selected_sdk"]["package_root"]
        or process_file.json_object().get("selected_interpreter") != runtime["executable"]
    ):
        raise ValueError("native actual worker Root/SDK/interpreter differs from its original launch binding")
    original = operation.originals[requirement.scope]
    if (
        raw_file.sha256 != original.native_execution_sha256
        or raw.get("source_inputs") != specification["source_inputs"]
    ):
        raise ValueError("native raw execution differs from external original custody or source launch inputs")
    process_record = process_file.json_object()
    expected_environment = dict(
        zip(
            (
                "TEMPLATE_PUBLIC_REFERENCE_ROOT",
                "TEMPLATE_PUBLIC_REFERENCE_COMMIT",
                "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT",
            ),
            original.source_binding,
            strict=True,
        )
    )
    if (
        process_record.get("source_environment") != expected_environment
        or process_record.get("sdk_closure_artifact") != details["sdk_closure_artifact"]
    ):
        raise ValueError("native guardian source environment/retained closure binding differs")
    expected_closure = reader.root / specification["source_inputs"]["closure"]["directory"] / "receipt.json"
    if closure_file.path != expected_closure:
        raise ValueError("native retained closure belongs to a different original attempt")
    validate_retained_sdk_closure(closure_file, specification, source_observation, reader, operation)
    _validate_native_providers(raw, specification, reader, deadline)

    # Blocked visual obligations can retain actual complete conformance, but
    # their outer process must preserve 75. Full acceptance below requires 0.
    code = raw.get("execution_exit_code")
    if type(code) is not int or code not in {0, 75}:
        raise ValueError("native conformance has a failed actual execution")
    from infrastructure.reporting.native_format_process_custody import (
        validate_native_worker_process,
    )

    process_record = _file(details.get("process_artifact"), reader).json_object()
    _process(process_record, nonce, command, code)
    validate_native_worker_process(specification, process_record, raw, hosted_origin=reader.hosted_origin)
    from infrastructure.reporting.native_full_worker_pdfium_replay import (
        validate_full_worker_pdfium_event,
    )

    validate_full_worker_pdfium_event(
        raw.get("pdfium_runtime"),
        reader,
        run_id=nonce,
        runtime=office_context.pdfium_runtime,
    )
    pipeline = raw.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ValueError("native whole-core execution evidence is missing")
    checked_pipeline = _pipeline(pipeline, requirement.scope, reader, custody)
    from infrastructure.reporting.native_analysis_boundary_replay import replay_native_analysis_boundary_graph
    from infrastructure.reporting.native_hydration_reconstruction import replay_native_hydration_reconstruction

    checked_analysis = replay_native_analysis_boundary_graph(requirement.scope, raw_file, reader)
    checked_hydration = replay_native_hydration_reconstruction(requirement.scope, raw_file, reader)
    if raw.get("deliverables_identity_after") != requirement.deliverables_identity:
        raise ValueError("native stable deliverables changed after the actual audit")
    import yaml

    rendering = RenderingConfig.from_project_config(
        yaml.safe_load(reader.read(f"projects/{requirement.scope}/manuscript/config.yaml").content),
        env={},
    )
    version_requests = (
        (rendering.pandoc_path, ["--version"]),
        (rendering.latex_compiler, ["--version"]),
        ("pdftoppm", ["-v"]),
        ("pdffonts", ["-v"]),
    )
    tool_bindings = raw.get("tool_artifacts")
    if not isinstance(tool_bindings, list) or len(tool_bindings) != len(version_requests):
        raise ValueError("native execution omitted required actual version probes")
    versions = {
        name: _tool(
            tool_bindings[index],
            reader,
            nonce,
            name,
            f"tool-version-{index}",
            arguments,
        )
        for index, (name, arguments) in enumerate(version_requests)
    }
    from infrastructure.reporting.native_office_scope_cohorts import replay_office_scope_cohorts

    details["office_diagram_cohorts"] = replay_office_scope_cohorts(
        reader,
        office_current.source,
        office_current,
        raw,
        office_context,
        custody,
        versions,
        native_environment_for_replay(reader.root),
        requirement.formats,
        requirement.scope,
    )
    contract = native_artifact_contract(reader.root, requirement.scope, requirement.formats, reader)
    rows = raw.get("artifacts")
    if (
        not isinstance(rows, list)
        or len(rows) != len(contract)
        or raw.get("contract_digest") != contract_digest(contract)
    ):
        raise ValueError("native execution omitted source-owned formats/variants")
    if not {"whole_pdf_cohort", "whole_pdf_source_controls"} <= set(raw):
        raise ValueError("native v9 omitted its coupled whole PDF observation fields")
    expected_blockers: list[dict[str, str]] = []
    whole_pdf_blockers: list[dict[str, str]] = []
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None = None
    if any(artifact.format == "pdf" for artifact in contract):
        from infrastructure.reporting.native_pdf_whole_cohort import replay_whole_pdf_cohort
        from infrastructure.reporting.native_pdf_whole_control_replay import replay_whole_pdf_source_controls
        from infrastructure.reporting.native_pdf_whole_diagnostics import whole_pdf_diagnostics

        cohort_file = _file(raw["whole_pdf_cohort"], reader)
        controls_file = _file(raw["whole_pdf_source_controls"], reader)
        if (
            cohort_file.path != directory / "whole-pdf-cohort/cohort.json"
            or controls_file.path != directory / "whole-pdf-source-controls/control-suite.json"
        ):
            raise ValueError("whole PDF original observations belong to a different evidence attempt")
        replay_env = native_environment_for_replay(reader.root)
        cohort = replay_whole_pdf_cohort(
            reader.root,
            requirement.scope,
            requirement.formats,
            {"path": cohort_file.relative, "sha256": cohort_file.sha256},
            reader,
            env=replay_env,
            deadline=deadline,
        )
        cohort_blockers, cohort_findings = whole_pdf_diagnostics(cohort, control_suite=False)
        whole_pdf_blockers.extend(cohort_blockers)
        if cohort_findings:
            raise ValueError(f"independent current whole PDF cohort failed: {cohort_findings}")
        controls = replay_whole_pdf_source_controls(
            reader.root,
            requirement.scope,
            requirement.formats,
            {"path": controls_file.relative, "sha256": controls_file.sha256},
            reader,
            env=replay_env,
            deadline=deadline,
        )
        control_blockers, control_findings = whole_pdf_diagnostics(controls, control_suite=True)
        whole_pdf_blockers.extend(control_blockers)
        if control_findings:
            raise ValueError(f"independent current whole PDF controls failed: {control_findings}")
        whole_pdf = (cohort, controls)
    elif raw["whole_pdf_cohort"] is not None or raw["whole_pdf_source_controls"] is not None:
        raise ValueError("non-PDF native contract contains unadmitted whole PDF observations")
    checked_observers: list[dict[str, Any]] = []
    for ordinal, (row, obligation) in enumerate(zip(rows, contract, strict=True)):
        if not isinstance(row, dict) or any(
            row.get(key) != getattr(obligation, key) for key in ("id", "format", "path")
        ):
            raise ValueError("native artifact variant differs from its source contract")
        snapshot = _file({"path": row.get("path"), "sha256": row.get("sha256")}, reader)
        if row.get("observation") != parse_native_bytes(obligation.format, snapshot.content):
            raise ValueError("native observation differs from the actual artifact bytes")
        if obligation.format == "pdf":
            _raster(row, snapshot, ordinal, directory, reader, nonce, versions, custody)
            from infrastructure.reporting.native_projection_source_dispatch import selected_source_projection

            if selected_print_artifact(requirement.scope, obligation) or selected_source_projection(obligation):
                if "content_contract" in row or "pdf_content" in row:
                    raise ValueError("specialized native artifact contains an unadmitted generic text fallback")
            else:
                content = compile_pdf_content_contract(
                    reader.root, requirement.scope, obligation, reader, deadline=deadline
                )
                if row.get("content_contract") != content.to_dict():
                    raise ValueError("native PDF obligations differ from the current consumed source bytes")
                observed = inspect_pdf_content(
                    snapshot.content,
                    tuple(reader.read(item["path"]).content for item in row["raster"]["rasters"]),
                    content,
                    deadline=deadline,
                )
                if row.get("pdf_content") != observed or observed["findings"]:
                    raise ValueError("native PDF source/glyph/localized-pixel observation differs or failed")
                expected_blockers.extend(
                    {"tool": f"PDF source oracle {obligation.id}", "reason": reason} for reason in observed["blockers"]
                )
        from infrastructure.reporting.native_format_observer_validation import (
            replay_native_observer,
        )

        observer = row.get("native_observer")
        if not isinstance(observer, dict):
            raise ValueError("native execution lacks independently replayable source/native observation")
        result = replay_native_observer(
            reader.root,
            directory / f"observer-{ordinal:04d}",
            requirement.scope,
            obligation,
            snapshot,
            observer,
            reader,
            run_id=nonce,
            custody=custody,
            runtime=runtime,
            versions=versions,
            deadline=deadline,
            env=native_environment_for_replay(reader.root),
            source_reference=operation.source.reference,
            verify_source_correspondence=operation.source.verify_correspondence,
            office_mermaid_runtime=office_context.runtime_for(observer, reader, ordinal=ordinal, run_id=nonce),
            original_worker_pid=raw["pid"],
            original_worker_platform=raw["host_before"]["system"],
        )
        if result["findings"]:
            raise ValueError("native artifact independent source/readback observations failed")
        checked_observers.append(result)
        expected_blockers.extend(
            {"tool": f"native source oracle {obligation.id}", "reason": reason} for reason in result["residuals"]
        )
    expected_blockers.extend(whole_pdf_blockers)
    if requirement.scope == "templates/template_pitch_deck":
        from infrastructure.reporting.native_projection_source_dispatch import inspect_admitted_pitch_pairs

        pairs = inspect_admitted_pitch_pairs(
            reader.root,
            requirement.scope,
            contract,
            rows,
            reader,
            source_reference=operation.source.reference,
            verify_source_correspondence=operation.source.verify_correspondence,
            deadline=deadline,
        )
        if raw.get("pitch_native_pairs") != pairs or pairs["findings"] or pairs["status"] == "fail":
            raise ValueError("complete independently reconstructed Pitch native pair parity differs or failed")
        expected_blockers.extend({"tool": "Pitch all native pairs", "reason": reason} for reason in pairs["blockers"])
    elif raw.get("pitch_native_pairs") is not None:
        raise ValueError("non-Pitch native scope contains an unadmitted pair aggregate")
    formats = raw.get("formats")
    if not isinstance(formats, dict) or set(formats) != set(requirement.formats) or details.get("formats") != formats:
        raise ValueError("native primary formats omit the declared selection")
    for kind in requirement.formats:
        primary = next(
            (
                row
                for row in rows
                if row["id"] == f"manuscript:{kind}" or kind == "slides" and row["id"].endswith(":slides")
            ),
            None,
        )
        if primary is None or formats[kind] != {
            "path": primary["path"],
            "sha256": primary["sha256"],
            "validated": True,
        }:
            raise ValueError("native primary format differs from the required artifact role")
    from infrastructure.reporting.native_format_acceptance_control_validation import validate_native_controls

    checked_controls = validate_native_controls(
        requirement,
        raw,
        reader,
        directory,
        nonce,
        runtime,
        specification,
        versions,
        contract,
        custody,
        deadline=deadline,
        operation=operation,
    )
    for kind, checked in details["office_diagram_cohorts"]["cohorts"].items():
        if checked["targets"]:
            checked_controls["suites"][kind + "_diagrams"] = checked
    current_scope = details["current_scope_replay"]
    if requirement.scope == "templates/template_pitch_deck":
        checked_controls["suites"]["configured_pitch"] = current_scope["current_pitch_controls"]
    from infrastructure.validation.publication.audit import (
        build_current_publication_audit,
        build_native_published_audit,
        validate_publication_audit,
    )

    published = build_native_published_audit(operation.source, requirement.scope, reader, deadline=deadline)
    if _file(raw.get("published_source_audit_artifact"), reader).json_object() != published.to_dict():
        raise ValueError("Original pre-Core published audit differs from independent pristine Source evidence")
    current_audit = build_current_publication_audit(operation.source, requirement.scope, reader, deadline=deadline)
    audit = _file(raw.get("publication_audit_artifact"), reader).json_object()
    if (
        audit != current_audit.to_dict()
        or validate_publication_audit(current_audit, strict=True) != 0
        or audit.get("status") != "pass"
        or audit.get("projects") != [requirement.scope]
        or audit.get("summary", {}).get("blocking_count") != 0
        or audit.get("summary", {}).get("review_required_count") != 0
        or not validate_current_rendered_provenance(reader.root, requirement.scope).valid
        or not reader.unchanged()
    ):
        raise ValueError("native strict rendered audit/current provenance or custody failed")
    operation.verify(reader)
    from infrastructure.reporting.native_oracle_phase_reader import collect_reader_native_oracle_phase

    oracle_phases.append(
        collect_reader_native_oracle_phase(
            office_current.source,
            office_current,
            raw,
            reader,
            checked_pipeline,
            current_comparison,
            checked_analysis,
            checked_hydration,
            checked_observers,
            checked_controls,
            renderer_current[0],
            expected_blockers,
            requirement.formats,
            whole_pdf=whole_pdf,
            selected_lineage=current_scope["selected_lineage"],
        )
    )


def native_environment_for_replay(root: Path) -> dict[str, str]:
    """Use a credential-free reader environment without producer path overrides."""
    from infrastructure.core.execution_boundary import build_bounded_env
    from infrastructure.reporting.native_format_acceptance_contracts import (
        SOURCE_RENDER_ENV_NAMES,
    )

    env = build_bounded_env()
    for key in tuple(env):
        if key in SOURCE_RENDER_ENV_NAMES or key.startswith("SLIDES_"):
            env.pop(key)
    return env


def validate_native_acceptance(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
    *,
    current_source: NativeSourceContext | None = None,
    current_directory: Path | None = None,
    provider_wheels: Mapping[str, Path] | None = None,
    pdfium_provider: NativePDFiumProvider | None = None,
    pdfium_runtime: PDFiumRuntimeAdmission | None = None,
    office_font_files: tuple[Path, ...] | None = None,
    current_observer_tools: Mapping[str, Path | None] | None = None,
) -> None:
    """Full format acceptance additionally requires every implemented visual oracle."""
    validate_native_conformance(
        requirement,
        details,
        reader,
        current_source=current_source,
        current_directory=current_directory,
        provider_wheels=provider_wheels,
        pdfium_provider=pdfium_provider,
        pdfium_runtime=pdfium_runtime,
        office_font_files=office_font_files,
        current_observer_tools=current_observer_tools,
    )
    raw = _file(details.get("native_execution_artifact"), reader).json_object()
    if (
        raw.get("status") != "pass"
        or raw.get("execution_exit_code") != 0
        or raw.get("blockers") != []
        or details.get("native_oracle_residuals") != []
    ):
        raise ValueError("native conformance cannot grant missing full content/layout/visual acceptance")


def _validate_native_providers(
    raw: dict[str, Any],
    specification: dict[str, Any],
    reader: SnapshotReader,
    deadline: float,
) -> None:
    """Recompute source-owned wheel selection and retained actual RECORD custody."""
    from infrastructure.project.public_acceptance_dependencies import (
        admit_runtime_providers,
    )
    from infrastructure.reporting.readiness_receipts import source_fingerprint
    from infrastructure.reporting.release_readiness_profile import required_profile
    from infrastructure.reporting.release_readiness_dependencies import _custody, _wheel

    operation = require_native_operation(reader)
    if operation.deadline != deadline:
        raise ValueError("native provider replay changed its original reader deadline")
    inputs = specification["source_inputs"]
    providers = inputs["providers"]
    wheels = {scope: reader.public_path(provider["wheel_artifact"]["path"]) for scope, provider in providers.items()}
    requirements, faults = required_profile(reader.root, reader, source_fingerprint(reader.root))
    if faults:
        raise ValueError("native provider replay requires the complete source-owned profile")
    admitted = admit_runtime_providers(
        reader.root,
        specification["scope"],
        wheels,
        {row.id: row for row in requirements},
        reader,
    )
    if admitted != providers:
        raise ValueError("native provider inventory differs from current source-owned declarations")
    custody = raw.get("runtime_providers")
    metadata = raw.get("provider_metadata_artifacts")
    if not isinstance(custody, dict) or set(custody) != {"before", "after"} or not isinstance(metadata, dict):
        raise ValueError("native actual provider before/after and metadata custody is absent")
    if any(
        not isinstance(custody[key], dict) or set(custody[key]) != set(providers) for key in ("before", "after")
    ) or set(metadata) != set(providers):
        raise ValueError("native actual installed provider custody selection differs")
    for scope, provider in providers.items():
        members = _wheel(
            scope,
            provider["package"],
            provider["version"],
            provider["wheel_artifact"],
            reader,
        )
        _custody(
            provider["package"],
            provider["version"],
            members,
            {"before": custody["before"][scope], "after": custody["after"][scope]},
            metadata[scope],
            reader,
        )
    operation.verify(reader)
