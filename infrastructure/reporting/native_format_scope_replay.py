"""Bind one complete configured suite and one fresh Current scope per original.

The existing Source controllers own every execution and its original clock.
Bindings retained here are DATA; the independent native operation supplies
Original authority and the paired Current producer supplies live tool custody.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_loader_negative_control import (
    observe_loader_persistent_rx_control,
    reproduce_loader_persistent_rx_control,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_project_domain import (
    NativeProjectDomainFailure,
    observe_native_project_domain,
    _validate as validate_live_native_project_domain,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
    from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidSelection
    from infrastructure.reporting.release_readiness_profile import Requirement
    from infrastructure.reporting.native_office_scope_cohorts import CurrentOfficeCohorts
    from infrastructure.reporting.native_renderer_section_roster import RendererScopeReplay


def observe_native_scope_evidence(
    source: NativeSourceContext,
    raw: dict[str, Any],
    specification: dict[str, Any],
    reader: SnapshotReader,
    env: dict[str, str],
) -> dict[str, Any]:
    """Run the full Source-selected suite and real loader control under the owner."""
    scope = specification["scope"]
    directory = reader.root / specification["directory"]
    deadline = specification["deadline_monotonic"]
    provider_wheels = {
        name: reader.public_path(provider["wheel_artifact"]["path"])
        for name, provider in specification["source_inputs"]["providers"].items()
    }
    remaining(deadline)
    try:
        raw["native_project_domain"] = observe_native_project_domain(
            source,
            scope,
            directory / "native-project-domain",
            reader,
            deadline=deadline,
            provider_wheels=provider_wheels,
        )
    except NativeProjectDomainFailure as error:
        raw["native_project_domain_attempt"] = error.native_project_domain_attempt
        raw["native_project_domain"] = error.native_project_domain_attempt["artifact"]
        raw["status"] = "fail"
        raw["execution_exit_code"] = error.code if error.code in (124, 130) else 1
        raise
    suite = reader.read(raw["native_project_domain"]["path"])
    if suite.sha256 != raw["native_project_domain"]["sha256"]:
        raise ValueError("native original configured suite bytes changed before live validation")
    checked_domain = validate_live_native_project_domain(
        suite.json_object(), reader, source, original=False, deadline=deadline
    )
    raw["loader_persistent_rx_control"] = observe_loader_persistent_rx_control(
        CitationRuntime(
            root=reader.root,
            directory=directory / "loader-persistent-rx-control",
            env=env,
            deadline=deadline,
            run_id=raw["run_id"],
        ),
        scope,
    )
    remaining(deadline)
    return checked_domain


def replay_native_scope_evidence(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
    *,
    current_source: NativeSourceContext | None,
    current_directory: Path | None,
    provider_wheels: Mapping[str, Path] | None,
    office_current: list[CurrentOfficeCohorts],
    renderer_current: list[RendererScopeReplay],
    pdfium_provider: NativePDFiumProvider | None,
    pdfium_runtime: PDFiumRuntimeAdmission | None,
    office_font_files: tuple[Path, ...] | None,
    decoded_pixel_budget: SourceImageDecodeBudget,
    current_observer_tools: Mapping[str, Path | None],
    current_artifacts: list[dict[str, Any]],
    current_comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute once before the separate Office reader opens its Source owner."""
    from infrastructure.core.pipeline.native_analysis_current import replay_current_native_analysis
    from infrastructure.reporting.native_format_current_orchestration import current_native_analysis_scope
    from infrastructure.reporting.native_format_acceptance_contracts import NATIVE_SCHEMA
    from infrastructure.reporting.native_format_acceptance_validation import native_environment_for_replay
    from infrastructure.reporting.native_format_acceptance_evidence import _file
    from infrastructure.reporting.native_format_acceptance_contracts import validate_native_specification
    from infrastructure.reporting.native_office_full_worker_context import NativeOfficeReaderSelection
    from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidSelection
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
    from infrastructure.reporting.native_office_full_worker_context import verify_office_font_nominations
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    if renderer_current:
        raise ValueError("Current renderer retention requires one fresh caller-held roster")
    operation = require_native_operation(reader)
    selection = operation.office_reader_selection
    if (
        not isinstance(current_source, NativeSourceContext)
        or not isinstance(current_directory, Path)
        or not isinstance(provider_wheels, Mapping)
        or not isinstance(selection, NativeOfficeReaderSelection)
        or not isinstance(selection.mermaid, NativeMermaidSelection)
        or not isinstance(pdfium_provider, NativePDFiumProvider)
        or not isinstance(pdfium_runtime, PDFiumRuntimeAdmission)
        or not isinstance(office_font_files, tuple)
    ):
        raise ValueError("native Current replay requires independently nominated Source, scope, providers and runtime")
    binding = details.get("native_execution_artifact")
    original = operation.originals.get(requirement.scope)
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or original is None:
        raise ValueError("native Current replay requires the complete externally held Original")
    execution = reader.read(binding["path"])
    raw = execution.json_object()
    if (
        execution.sha256 != binding["sha256"]
        or execution.relative != original.native_execution_relative
        or execution.sha256 != original.native_execution_sha256
        or raw.get("schema_version") != NATIVE_SCHEMA
        or raw.get("scope") != requirement.scope
        or raw.get("run_id") != original.run_id
        or not isinstance(raw.get("native_oracle_requirements"), dict)
        or not isinstance(raw.get("native_project_domain"), dict)
        or not isinstance(raw.get("loader_persistent_rx_control"), dict)
    ):
        raise ValueError("native Current replay lacks its mandatory coupled Original suite and loader observations")
    specification_binding = details.get("specification_artifact")
    if not isinstance(specification_binding, dict) or set(specification_binding) != {"path", "sha256"}:
        raise ValueError("native Current replay requires its complete bound Original specification")
    specification_file = reader.read(specification_binding["path"])
    specification = specification_file.json_object()
    validate_native_specification(specification)
    if (
        specification_file.relative != original.specification_relative
        or specification_file.sha256 != original.specification_sha256
        or specification_file.sha256 != specification_binding["sha256"]
        or specification["scope"] != requirement.scope
        or specification["run_id"] != original.run_id
        or specification["formats"] != list(requirement.formats)
        or execution.path != reader.root / specification["directory"] / "native-execution.json"
        or raw.get("source_digest_before") != specification["source_digest"]
        or raw.get("source_digest_after") != specification["source_digest"]
    ):
        raise ValueError("native Current replay differs from the externally held Original Source specification")
    original_provider = operation.pdfium_providers.get(requirement.scope)
    if (
        not isinstance(original_provider, NativePDFiumProvider)
        or pdfium_provider is original_provider
        or pdfium_provider.source is not current_source
        or pdfium_provider.scope != requirement.scope
        or pdfium_provider.deadline != operation.deadline
        or pdfium_provider.selection != original_provider.selection
        or pdfium_runtime.source is not current_source
        or pdfium_runtime.scope != requirement.scope
        or pdfium_runtime.site != pdfium_provider.selection.site
        or pdfium_runtime.wheel != pdfium_provider.selection.wheel
        or pdfium_runtime.deadline != operation.deadline
        or office_font_files != selection.font_files
    ):
        raise ValueError("Current native artifacts require fresh same-selection per-scope Source/PDFium nominations")
    pdfium_provider.verify_current(deadline=operation.deadline)
    pdfium_runtime.verify()
    verify_office_font_nominations(
        specification["source_inputs"]["office_fonts"], office_font_files, deadline=operation.deadline
    )
    remaining(operation.deadline)
    attempt: dict[str, Any] | None = None
    try:
        with current_native_analysis_scope(
            current_source,
            requirement.scope,
            current_directory,
            selection.mermaid,
            deadline=operation.deadline,
        ):
            analysis = replay_current_native_analysis(
                requirement.scope,
                execution,
                reader,
                current_source,
                directory=current_directory,
                original_domain=raw["native_project_domain"],
                provider_wheels=provider_wheels,
            )
            attempt = {
                "observation": {"phase": "post-current-analysis-closing"},
                "artifact": None,
                "current_analysis": analysis,
                "pipeline_observation_available": False,
            }
            # Retain the genuine comparison prefix immediately. These confined
            # reads capture actual pipeline DATA while the Current owner is live;
            # no serialized outcome authorizes a subsequent execution or pass.
            retained = SnapshotReader(current_source.bindings.current_root)
            comparison = _file(analysis, retained)
            if comparison.path != current_directory / "current-analysis/current-analysis-comparison.json":
                raise ValueError("Current comparison escaped its exact nominated scope")
            current_comparisons.append(comparison.json_object())
            pipeline_binding = current_comparisons[0]["current_pipeline"]
            pipeline = _file(pipeline_binding, retained)
            if pipeline.path != current_directory / "current-analysis/pipeline.json" or not retained.unchanged():
                raise ValueError("Current closing pipeline DATA differs from the genuine comparison")
            attempt.update(
                observation=pipeline.json_object(),
                artifact=pipeline_binding,
                pipeline_observation_available=True,
            )
            owner = current_native_producer_operation()
            if owner is None or owner.source is not current_source:
                raise ValueError("native Current scope lost its actual Source owner")
            from infrastructure.reporting.native_renderer_stage_replay import replay_native_renderer_stages
            from infrastructure.reporting.native_renderer_section_roster import validate_renderer_section_rosters

            renderer = replay_native_renderer_stages(
                requirement.scope,
                execution,
                reader,
                pipeline,
                SnapshotReader(current_source.bindings.current_root, native_producer_operation=owner),
            )
            renderer_current.append(renderer)
            attempt["current_renderer"] = renderer[0]
            section_rosters = validate_renderer_section_rosters(
                requirement.scope,
                renderer,
                SnapshotReader(reader.root, native_operation=operation, native_control_operation=renderer[1]),
                SnapshotReader(
                    current_source.bindings.current_root,
                    native_producer_operation=owner,
                    native_control_operation=renderer[2],
                ),
            )
            attempt["current_tex_sections"] = section_rosters
            from infrastructure.reporting.native_current_artifact_join import observe_current_native_artifact_join

            current_stage_reader = SnapshotReader(
                current_source.bindings.current_root,
                native_producer_operation=owner,
                native_control_operation=renderer[2],
            )
            try:
                current_native_artifacts = observe_current_native_artifact_join(
                    requirement.scope,
                    execution,
                    reader,
                    pipeline,
                    current_stage_reader,
                    current_source=current_source,
                    current_stage=renderer[2],
                    directory=current_directory / "current-native-artifacts",
                    pdfium_provider=pdfium_provider,
                    pdfium_runtime=pdfium_runtime,
                    office_font_files=office_font_files,
                    decoded_pixel_budget=decoded_pixel_budget,
                    observer_tools=current_observer_tools,
                )
            except BaseException as error:
                partial = getattr(error, "native_current_artifact_attempt", None)
                if isinstance(partial, dict):
                    attempt["native_current_artifact_attempt"] = partial
                raise
            current_artifacts.append(_file(current_native_artifacts, current_stage_reader).json_object())
            attempt["current_native_artifacts"] = current_native_artifacts
            current_pitch = None
            if requirement.scope == "templates/template_pitch_deck":
                from infrastructure.reporting.native_pitch_control_replay import replay_pitch_controls

                current_pitch = replay_pitch_controls(
                    raw["observer_controls"]["configured_pitch"],
                    reader,
                    current_source=current_source,
                    directory=current_directory / "configured-pitch-controls",
                    formats=requirement.formats,
                    interpreter=Path(sys.executable),
                    env=native_environment_for_replay(current_source.bindings.current_root),
                    deadline=operation.deadline,
                )
                attempt["current_pitch_controls"] = current_pitch
            from infrastructure.reporting.native_office_scope_cohorts import execute_current_office_scope

            office_current.append(
                execute_current_office_scope(
                    current_source,
                    current_directory,
                    reader,
                    requirement.scope,
                    requirement.formats,
                    native_environment_for_replay(current_source.bindings.current_root),
                    pdfium_provider=pdfium_provider,
                    office_font_files=office_font_files,
                )
            )
            current_control = reproduce_loader_persistent_rx_control(
                raw["loader_persistent_rx_control"],
                execution,
                reader,
                CitationRuntime(
                    current_source.bindings.current_root,
                    current_directory / "loader-persistent-rx-control",
                    env=native_environment_for_replay(current_source.bindings.current_root),
                    deadline=operation.deadline,
                    run_id=owner.run_id,
                ),
                current_source=current_source,
                scope=requirement.scope,
                original_run_id=original.run_id,
            )
            from infrastructure.reporting.native_oracle_selected_lineage import (
                classify_selected_native_lineage,
                collect_code_figure_domains,
            )

            comparison_body = current_comparisons[0]
            code = comparison_body["code_consumed_value_join"]
            if requirement.scope == "templates/template_code_project" and (
                not isinstance(code, dict) or set(code) != {"original", "current"}
            ):
                raise ValueError("selected Code lineage omitted complete genuine Original/Current domain joins")
            if requirement.scope != "templates/template_code_project" and code is not None:
                raise ValueError("non-Code scope contains a foreign selected Code domain join")
            current_graph = _file(comparison_body["current_graph"], current_stage_reader).json_object()
            current_hydration = _file(comparison_body["current_hydration"], current_stage_reader).json_object()
            current_join = current_artifacts[0]
            if any(
                graph.get("scope") != requirement.scope
                or graph.get("source_binding")
                != [current_source.reference.commit, current_source.reference.source_identity]
                or graph.get("pipeline_run_id") != current_join["current_pipeline_run_id"]
                or graph.get("plan_digest") != current_join["current_plan_digest"]
                for graph in (current_graph, current_hydration)
            ):
                raise ValueError("Current selected lineage differs from the actual Source/Core artifact join")
            original_pdf = {}
            if requirement.scope == "templates/template_code_project":
                from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact

                authority = authenticate_original_native_artifact(
                    raw["whole_pdf_cohort"],
                    reader,
                    run_id=original.run_id,
                    required_sdk_modules=("reporting/native_pdf_whole_cohort.py",),
                )
                cohort = authority["event"].json_object()
                if (
                    cohort["scope"] != requirement.scope
                    or cohort["run_id"] != original.run_id
                    or cohort["hydration_reconstruction"] != raw["hydration_reconstruction"]
                ):
                    raise ValueError("Original selected figures changed their genuinely held PDF Source roster")
                original_pdf = {row["id"]: row for row in cohort["artifacts"]}
                if len(original_pdf) != len(cohort["artifacts"]):
                    raise ValueError("Original selected native PDF roster repeated an actual artifact identity")
            original_figures = collect_code_figure_domains(
                operation.source,
                reader,
                raw["analysis_data_graph"],
                tuple((row["id"], row["native_observer"], original_pdf.get(row["id"])) for row in raw["artifacts"]),
                deadline=operation.deadline,
            )
            current_figures = collect_code_figure_domains(
                current_source,
                current_stage_reader,
                current_graph,
                tuple((row["id"], row["native_observer"], None) for row in current_join["artifacts"]),
                deadline=operation.deadline,
            )
            from infrastructure.reporting.native_code_native_locations import (
                observe_code_native_locations,
                replay_code_native_locations,
            )
            from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact

            original_locations = replay_code_native_locations(
                raw.get("code_native_locations"),
                execution,
                reader,
                raw["analysis_data_graph"],
                raw["hydration_reconstruction"],
                tuple(
                    (
                        NativeArtifact(row["id"], row["format"], row["path"]),
                        row["native_observer"],
                        original_pdf.get(row["id"]),
                    )
                    for row in raw["artifacts"]
                ),
                custody=raw["producer_custody"],
            )
            current_locations = observe_code_native_locations(
                current_source,
                current_stage_reader,
                current_graph,
                current_hydration,
                tuple(
                    (NativeArtifact(row["id"], row["format"], row["path"]), row["native_observer"], None)
                    for row in current_join["artifacts"]
                ),
                env=native_environment_for_replay(current_source.bindings.current_root),
                deadline=operation.deadline,
            )
            selected_lineage = (
                classify_selected_native_lineage(
                    raw["analysis_data_graph"],
                    raw["hydration_reconstruction"],
                    code_values=None if code is None else code["original"],
                    figure_domains=original_figures,
                    native_locations=original_locations,
                ),
                classify_selected_native_lineage(
                    current_graph,
                    current_hydration,
                    code_values=None if code is None else code["current"],
                    figure_domains=current_figures,
                    native_locations=current_locations,
                    graph_artifacts={
                        "analysis": comparison_body["current_graph"],
                        "hydration": comparison_body["current_hydration"],
                    },
                ),
            )
            if not current_stage_reader.unchanged():
                raise ValueError("Current selected lineage or artifact bodies changed under the live owner")
            current_source.verify_correspondence(
                current_source.reference, current_stage_reader.root, current_stage_reader, operation.deadline
            )
            owner.verify(
                SnapshotReader(current_source.bindings.current_root, native_producer_operation=owner),
                run_id=owner.run_id,
                deadline=operation.deadline,
            )
            closing = {
                "scope": requirement.scope,
                "current_run_id": owner.run_id,
                "source_commit": current_source.reference.commit,
                "source_identity": current_source.reference.source_identity,
                "current_root_identity": list(current_source.bindings.current_root_identity),
                "deadline_monotonic": operation.deadline,
                "stage_children": list(owner.stage_children),
                "tool_artifacts": list(owner.retained_tool_bindings),
            }
        operation.verify(reader)
        return {
            "current_analysis": analysis,
            "current_renderer": renderer[0],
            "current_tex_sections": section_rosters,
            "current_native_artifacts": current_native_artifacts,
            "current_pitch_controls": current_pitch,
            "current_loader_persistent_rx_control": current_control,
            "closing_custody": closing,
            "selected_lineage": selected_lineage,
        }

    except BaseException as error:
        # A later control or Source/runtime close refusal must not erase an
        # actual completed Core/comparison prefix. Preserve existing failed
        # Core/Common carriers and each signed process result separately.
        if attempt is not None and not isinstance(getattr(error, "native_current_pipeline", None), dict):
            setattr(error, "native_current_pipeline", attempt)
        raise


def run_native_scope_worker(
    root: Path,
    specification: dict[str, Any],
    *,
    source_context: NativeSourceContext,
    mermaid_selection: NativeMermaidSelection,
    pdfium_provider: NativePDFiumProvider,
    office_font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget | None = None,
) -> dict[str, Any]:
    """Own live ToolAPI custody throughout this actual Source-admitted producer."""
    from infrastructure.reporting.native_tool_producer import native_producer_operation
    from infrastructure.reporting.native_format_acceptance_worker import _run_native_worker
    from infrastructure.reporting.native_format_acceptance_contracts import (
        create_private_native_directory,
        native_environment,
        validate_native_specification,
    )
    from infrastructure.reporting.native_full_worker_pdfium import full_worker_pdfium_execution
    from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
        SourceImageDecodeBudget,
        MAX_SOURCE_IMAGE_OCCURRENCES,
    )
    from infrastructure.reporting.native_office_full_worker_context import verify_office_font_nominations

    validate_native_specification(specification)
    deadline = specification["deadline_monotonic"]
    verify_office_font_nominations(
        specification["source_inputs"]["office_fonts"],
        office_font_files,
        deadline=deadline,
    )
    # Allocate once at this genuine outer worker when no already-held caller
    # budget is supplied. Every artifact/copy uses this exact same object.
    if decoded_pixel_budget is None:
        decoded_pixel_budget = SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES)
    if not isinstance(decoded_pixel_budget, SourceImageDecodeBudget):
        raise ValueError("native Office source needs the actual shared decoder budget")
    from infrastructure.reporting.native_oracle_phase import NativeOraclePhase, finish_original_native_oracle_phase

    oracle_phases: list[NativeOraclePhase] = []
    raw: dict[str, Any] | None = None
    try:
        with native_producer_operation(
            source_context,
            run_id=specification["run_id"],
            deadline=specification["deadline_monotonic"],
            scope=specification["scope"],
            directory=root / specification["directory"],
        ) as producer:
            from infrastructure.reporting.native_mermaid_runtime_selection import (
                readmit_source_mermaid_selection,
                source_mermaid_runtime_operation,
            )

            runtime_directory = root / specification["directory"] / "mermaid-worker-runtime"
            create_private_native_directory(root, runtime_directory)
            runtime = readmit_source_mermaid_selection(
                specification["source_inputs"]["mermaid_runtime"],
                mermaid_selection,
                source_context,
                deadline=specification["deadline_monotonic"],
                directory=runtime_directory,
                env=native_environment(root, Path(sys.executable), runtime_directory),
            )
            with (
                source_mermaid_runtime_operation(
                    runtime,
                    source=source_context,
                    deadline=specification["deadline_monotonic"],
                ),
                full_worker_pdfium_execution(
                    pdfium_provider,
                    directory=root / specification["directory"] / "pdfium-worker-runtime",
                    deadline=specification["deadline_monotonic"],
                ) as pdfium_execution,
            ):
                raw = _run_native_worker(
                    root,
                    specification,
                    source_context=source_context,
                    mermaid_runtime=runtime,
                    pdfium_runtime=pdfium_execution.runtime,
                    office_font_files=office_font_files,
                    decoded_pixel_budget=decoded_pixel_budget,
                    oracle_phases=oracle_phases,
                )
            if pdfium_execution.completed_binding is None:
                raise ValueError("full native PDFium actual namespace/Code/image closure did not complete")
            raw["pdfium_runtime"] = pdfium_execution.completed_binding
            verify_office_font_nominations(
                specification["source_inputs"]["office_fonts"],
                office_font_files,
                deadline=deadline,
            )
            raw["office_decode_budget"] = {
                "declared_occurrences": decoded_pixel_budget.expected_occurrences,
                "admitted_occurrences": decoded_pixel_budget.admitted_occurrences,
                "decoded_pixels": decoded_pixel_budget.decoded_pixels,
            }
            try:
                if raw["stage_children"] != list(producer.stage_children):
                    completed = len(raw["stage_children"])
                    expected = len(producer.stage_children)
                    detail = str(raw.get("diagnostic") or "").strip()
                    raise ValueError(
                        "native completed stage bindings changed after graph reconstruction "
                        f"(completed={completed}, expected={expected}"
                        + (f", worker diagnostic: {detail}" if detail else "")
                        + ")"
                    )
                producer.verify(
                    SnapshotReader(root, native_producer_operation=producer),
                    run_id=specification["run_id"],
                    deadline=specification["deadline_monotonic"],
                )
            except (OSError, ValueError, RuntimeError) as error:
                raw["status"] = "blocked"
                if raw["execution_exit_code"] == 0:
                    raw["execution_exit_code"] = 75
                raw["diagnostic"] = (
                    str(raw.get("diagnostic", ""))
                    + f"; actual native producer final Source/SDK custody refused: {error}"
                )
            if raw["status"] == "pass" and raw["execution_exit_code"] == 0:
                if len(oracle_phases) != 1:
                    raise ValueError("Original native dispatch requires its one actual completed phase")
                finish_original_native_oracle_phase(
                    oracle_phases[0],
                    raw,
                    source_context,
                    SnapshotReader(root, native_producer_operation=producer),
                )
            return raw

    except (Exception, KeyboardInterrupt) as error:
        # Only a directly returned worker observation can survive later owner
        # closure. No missing successful custody is manufactured or accepted.
        if raw is None:
            raise
        code = raw.get("execution_exit_code")
        raw["status"] = "fail"
        raw["execution_exit_code"] = (
            130
            if isinstance(error, KeyboardInterrupt) or code == 130
            else 124
            if isinstance(error, TimeoutError) or code == 124
            else 1
        )
        raw["closing_custody_refused"] = str(error)
        raw["diagnostic"] = str(raw.get("diagnostic", "")) + f"; native post-return closing custody refused: {error}"
        return raw
