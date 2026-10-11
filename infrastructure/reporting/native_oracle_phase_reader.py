"""Purpose collection of actual independent reader/Current native results."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.reporting.native_oracle_phase import NativeOraclePhase
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidCensus
from infrastructure.reporting.native_oracle_dispatch_requirements import compile_native_oracle_dispatch_requirements
from infrastructure.reporting.native_office_scope_cohorts import CurrentOfficeCohorts
from infrastructure.reporting.native_office_control_custody import OfficeControlReaderOperation
from infrastructure.reporting.native_source_control_targets import OfficeRequirementCohort
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def current_native_observer_nominees(value: Mapping[str, Path | None] | None) -> Mapping[str, Path | None]:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"epubcheck_jar", "java_executable", "frozen_epub_engine"}
        or any(path is not None and not isinstance(path, Path) for path in value.values())
    ):
        raise ValueError("native Current requires the complete caller-held observer path nominees")
    return value


def collect_reader_native_oracle_phase(
    source: NativeSourceContext,
    current: CurrentOfficeCohorts,
    raw: dict[str, Any],
    reader: SnapshotReader,
    pipeline: RunResult,
    comparison: dict[str, Any],
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    observers: list[dict[str, Any]],
    controls: dict[str, Any],
    renderer: dict[str, Any],
    diagnostics: list[dict[str, str]],
    formats: tuple[str, ...],
    *,
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None,
    selected_lineage: tuple[dict[str, Any], ...],
) -> NativeOraclePhase:
    operation = require_native_operation(reader)
    cohorts: dict[str, OfficeRequirementCohort] = {}
    for kind, held in current.children.items():
        role = OfficeControlReaderOperation(source, held, deadline=operation.deadline)
        cohorts[kind] = (held, role, SnapshotReader(source.bindings.current_root, native_control_operation=role))
    current_source_reader = SnapshotReader(source.bindings.current_root)
    source_census: list[SourceMermaidCensus] = []
    requirements, target_plans = compile_native_oracle_dispatch_requirements(
        current_source_reader.root,
        raw["scope"],
        formats,
        current_source_reader,
        source=source,
        deadline=operation.deadline,
        office_cohorts=cohorts,
        source_census=source_census,
    )
    if raw.get("native_oracle_requirements") != requirements.data():
        raise ValueError("native v13 Original/Current exact independently compiled requirement graphs differ")
    if (
        not isinstance(selected_lineage, tuple)
        or len(selected_lineage) != 2
        or any(not isinstance(value, dict) for value in selected_lineage)
        or selected_lineage[0].get("graph_artifacts") is not None
        or selected_lineage[1].get("graph_artifacts")
        != {
            "analysis": comparison["current_graph"],
            "hydration": comparison["current_hydration"],
        }
    ):
        raise ValueError("reader lineage omitted actual Original and held fresh Current graph bindings")
    renderer_edges = list(renderer["unresolved_edges"])
    if renderer["section_packets"]["original"]:
        renderer_edges.append("complete-source-tex-section-semantics-and-native-consuming-role")
    return NativeOraclePhase(
        requirements,
        target_plans,
        pipeline,
        comparison["complete_configured_cases"],
        analysis,
        hydration,
        tuple(observers),
        controls,
        {**renderer, "unresolved_edges": renderer_edges},
        tuple(diagnostics),
        source_census[0],
        whole_pdf,
        raw["pitch_native_pairs"],
        selected_lineage,
    )
