"""Read completed Original stage/control facts under its genuine existing owner."""

from __future__ import annotations

from typing import Any

from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.reporting.native_oracle_dispatch_requirements import compile_native_oracle_dispatch_requirements
from infrastructure.reporting.native_oracle_original_control_facts import collect_original_native_controls
from infrastructure.reporting.native_oracle_phase import NativeOraclePhase
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidCensus
from infrastructure.reporting.native_office_control_custody import (
    NativeOfficeControlOriginal,
    OfficeControlReaderOperation,
)
from infrastructure.reporting.native_renderer_stage_replay import _scope_renderers
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_oracle_selected_lineage import (
    collect_code_figure_domains,
    observe_selected_native_lineage,
)
from infrastructure.reporting.native_oracle_axis_facts import _pdf_row


def collect_original_native_oracle_phase(
    source: NativeSourceContext,
    raw: dict[str, Any],
    reader: SnapshotReader,
    pipeline: RunResult,
    domain: dict[str, Any],
    observers: list[dict[str, Any]],
    children: dict[str, tuple[NativeOfficeControlOriginal, ...]],
    pdf_body: bytes | None,
    formats: tuple[str, ...],
    *,
    deadline: float,
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None,
    env: dict[str, str],
) -> NativeOraclePhase:
    owner = reader.native_producer_operation
    if owner is None or owner.source is not source or owner.deadline != deadline or owner.run_id != raw["run_id"]:
        raise ValueError("Original native collector needs its actual Source owner/run/clock")
    from infrastructure.reporting.native_source_control_targets import OfficeRequirementCohort

    cohorts: dict[str, OfficeRequirementCohort] = {}
    for kind, held in children.items():
        operation = OfficeControlReaderOperation(source, held, deadline=deadline)
        cohorts[kind] = (held, operation, SnapshotReader(reader.root, native_control_operation=operation))
    source_census: list[SourceMermaidCensus] = []
    requirements, targets = compile_native_oracle_dispatch_requirements(
        reader.root,
        raw["scope"],
        formats,
        reader,
        source=source,
        deadline=deadline,
        office_cohorts=cohorts,
        source_census=source_census,
    )
    stage = NativeStageChildReaderOperation(
        source,
        reader,
        list(owner.stage_children),
        scope=raw["scope"],
        run_id=owner.run_id,
        deadline=deadline,
    )
    stage_reader = SnapshotReader(reader.root, native_producer_operation=owner, native_control_operation=stage)
    renderer_rows, section_rows, mermaid_rows = _scope_renderers(
        stage_reader, stage, raw["hydration_reconstruction"], pdf_body
    )
    unresolved_edges: list[str] = list(
        dict.fromkeys(edge for row in (*renderer_rows, *mermaid_rows) for edge in row["unresolved_edges"])
    )
    renderer = {
        "unresolved_edges": unresolved_edges,
        "renderers": renderer_rows,
        "section_packets": {"original": section_rows},
        "mermaid_commands": {"original": mermaid_rows},
    }
    if section_rows:
        unresolved_edges.append("complete-source-tex-section-semantics-and-native-consuming-role")
    controls = collect_original_native_controls(requirements, raw, reader, cohorts, deadline=deadline)
    figure_domains = collect_code_figure_domains(
        source,
        reader,
        raw["analysis_data_graph"],
        tuple(
            (
                artifact.id,
                report["source_observer"],
                _pdf_row(None if whole_pdf is None else whole_pdf[0], artifact) if artifact.format == "pdf" else None,
            )
            for artifact, report in zip(requirements.artifacts, observers, strict=True)
        ),
        deadline=deadline,
    )
    from infrastructure.reporting.native_code_native_locations import observe_code_native_locations

    locations = observe_code_native_locations(
        source,
        reader,
        raw["analysis_data_graph"],
        raw["hydration_reconstruction"],
        tuple(
            (
                artifact,
                report["source_observer"],
                _pdf_row(None if whole_pdf is None else whole_pdf[0], artifact) if artifact.format == "pdf" else None,
            )
            for artifact, report in zip(requirements.artifacts, observers, strict=True)
        ),
        env=env,
        deadline=deadline,
    )
    raw["code_native_locations"] = locations
    selected_lineage = observe_selected_native_lineage(
        source,
        reader,
        raw["analysis_data_graph"],
        raw["hydration_reconstruction"],
        deadline=deadline,
        figure_domains=figure_domains,
        native_locations=locations,
    )
    stage.verify(stage_reader)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    return NativeOraclePhase(
        requirements,
        targets,
        pipeline,
        domain,
        raw["analysis_data_graph"],
        raw["hydration_reconstruction"],
        tuple(observers),
        controls,
        renderer,
        tuple(raw["blockers"]),
        source_census[0],
        whole_pdf,
        raw["pitch_native_pairs"],
        (selected_lineage,),
    )
