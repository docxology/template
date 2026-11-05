"""Purpose-specific Original/reader native DATA collection after real checks.

Live owners and Source/SDK checks remain in the existing callers. These holders
retain their actual returned facts; no serialized pass or declared axis is an
admission capability. Missing complete predicates remain explicit residuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.reporting.native_oracle_dispatch import project_native_oracle_residuals
from infrastructure.reporting.native_oracle_phase_residuals import (
    NativeOracleResidualGraphs,
    native_residual_rows as _phase_residual_rows,
    reconcile_native_phase_residual_graphs,
)
from infrastructure.reporting.native_oracle_obligation_spec import NativeOracleSpecification
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidCensus
from infrastructure.reporting.native_oracle_axis_facts import collect_artifact_axis_facts
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_oracle_selected_lineage import (
    selected_lineage_residuals,
    selected_asset_lineage_residuals,
    selected_value_lineage_residuals,
)
from infrastructure.reporting.native_oracle_axis_facts import _pdf_row


@dataclass(frozen=True)
class NativeOraclePhase:
    requirements: NativeOracleSpecification
    target_plans: dict[str, Any]
    pipeline: RunResult
    domain: dict[str, Any]
    analysis: dict[str, Any]
    hydration: dict[str, Any]
    observers: tuple[dict[str, Any], ...]
    controls: dict[str, Any]
    renderer: dict[str, Any]
    diagnostics: tuple[dict[str, str], ...]
    source_census: SourceMermaidCensus
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None
    pitch_pairs: dict[str, Any] | None
    selected_lineage: tuple[dict[str, Any], ...]


def _edges(value: dict[str, Any]) -> tuple[str, ...]:
    edges = value.get("unresolved_edges")
    if not isinstance(edges, list) or any(not isinstance(row, str) or not row for row in edges):
        raise ValueError("checked native graph omitted its specific unresolved Source edges")
    return tuple(edges)


def collect_native_axis_results(
    phase: NativeOraclePhase,
    original_run_id: str,
    *,
    current_artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join actual complete Core/Common/graph returns and exact artifact rows.

    Full semantic, occurrence and consuming-role axes are not established by
    an empty adapter aggregate. This collector fills only concrete predicates;
    all other declared axes stay absent for the projector's specific residual.
    """
    specification = phase.requirements
    if type(phase.pipeline) is not RunResult or not phase.pipeline.complete or phase.pipeline.exit_code:
        raise ValueError("native axes require the checked complete actual Core result")
    if any(outcome.child_exit_code != 0 for outcome in phase.pipeline.outcomes):
        raise ValueError("native axes require each observed actual successful Core child")
    counts = phase.domain.get("counts")
    if (
        not isinstance(counts, dict)
        or counts.get("collected") != counts.get("passed")
        or any(counts.get(key) != 0 for key in ("failed", "errors", "skipped", "deselected"))
    ):
        raise ValueError("native axes require the actually checked complete configured Common suite")
    identities = [artifact.id for artifact in specification.artifacts]
    if [row.get("artifact_id") for row in phase.observers] != identities:
        raise ValueError("checked native observer returns omitted/reordered the Source artifact roster")
    if current_artifacts is not None and (
        current_artifacts.get("scope") != specification.scope
        or current_artifacts.get("original_run_id") != original_run_id
        or current_artifacts.get("source_binding") != list(specification.source_binding)
        or current_artifacts.get("artifact_contract_digest") != specification.artifact_contract_digest
        or current_artifacts.get("artifact_ids") != identities
        or [row["id"] for row in current_artifacts["artifacts"]] != identities
        or not isinstance(current_artifacts.get("pdfium_runtime"), dict)
    ):
        raise ValueError("native reader axes omitted their real complete separately executed Current join")
    lineage = selected_lineage_residuals(
        phase.selected_lineage,
        phase.analysis,
        phase.hydration,
        reader_phase=current_artifacts is not None,
        current_artifacts=current_artifacts,
    )
    renderer_edges = _edges(phase.renderer)
    axis_results: dict[str, dict[str, tuple[str, ...]]] = {}
    for ordinal, (artifact, report) in enumerate(zip(specification.artifacts, phase.observers, strict=True)):
        if report.get("findings"):
            raise ValueError("checked native artifact findings remain a failure")
        residuals = report.get("residuals")
        if not isinstance(residuals, list) or any(not isinstance(row, str) or not row for row in residuals):
            raise ValueError("checked native artifact omitted explicit residuals")
        if current_artifacts is not None:
            fresh = current_artifacts["artifacts"][ordinal]
            if fresh["findings"] or tuple(fresh["residuals"]) != tuple(residuals):
                raise ValueError("actual Current observer findings/residuals differ from independent Original readback")
        pdf = (
            _pdf_row(None if phase.whole_pdf is None else phase.whole_pdf[0], artifact)
            if artifact.format == "pdf"
            else None
        )
        current_observer = (
            None if current_artifacts is None else current_artifacts["artifacts"][ordinal]["native_observer"]
        )
        native_axes = collect_artifact_axis_facts(
            artifact,
            specification,
            report,
            phase.source_census,
            phase.whole_pdf,
            phase.pitch_pairs,
            phase.controls,
            phase.renderer,
            current_observer=current_observer,
        )
        native_qualified = bool(native_axes) and all(not reasons for reasons in native_axes.values())
        asset_edges = selected_asset_lineage_residuals(
            phase.selected_lineage[0],
            artifact.id,
            report["source_observer"],
            pdf=pdf,
            native_qualified=native_qualified,
        )
        if current_artifacts is not None:
            asset_edges += selected_asset_lineage_residuals(
                phase.selected_lineage[1],
                artifact.id,
                current_artifacts["artifacts"][ordinal]["native_observer"],
                native_qualified=native_qualified,
            )
        artifact_lineage = selected_value_lineage_residuals(
            phase.selected_lineage,
            artifact.id,
            lineage,
            native_qualified=native_qualified,
        )
        axis_results[artifact.id] = {
            "externally-admitted-original-source-and-installed-sdk": (),
            "complete-original-core-plan-stage-inputs-and-actual-zero-exit-attempts": (),
            "same-native-run-analysis-domain-hydration-registry-asset-lineage": tuple(
                dict.fromkeys((*artifact_lineage, *asset_edges))
            ),
            "unchanged-opening-and-closing-source-policy-provider-custody": renderer_edges,
        }
        axis_results[artifact.id].update(native_axes)
    return {
        "scope": specification.scope,
        "source_binding": list(specification.source_binding),
        "original_run_id": original_run_id,
        "artifact_contract_digest": specification.artifact_contract_digest,
        "artifact_ids": identities,
        "artifact_axis_results": axis_results,
        "advisory_limits": phase.selected_lineage[0]["advisory_limits"],
        "findings": [],
    }


def finish_original_native_oracle_phase(
    phase: NativeOraclePhase,
    raw: dict[str, Any],
    source: NativeSourceContext,
    reader: SnapshotReader,
) -> None:
    """Called after actual PDFium/Mermaid/provider/audit/Source closure checks."""
    owner = reader.native_producer_operation
    if owner is None or owner.source is not source or raw["run_id"] != owner.run_id:
        raise ValueError("Original native dispatch lost its actual existing Source owner")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    source.verify_correspondence(source.reference, reader.root, reader, owner.deadline)
    if not reader.unchanged() or raw["source_digest_before"] != raw["source_digest_after"]:
        raise ValueError("Original native dispatch closing Source custody changed")
    raw["native_oracle_requirements"] = phase.requirements.data()
    raw["blockers"] = project_native_oracle_residuals(
        phase.requirements,
        original_run_id=owner.run_id,
        checked_axes=collect_native_axis_results(phase, owner.run_id),
        checked_controls=phase.controls,
        source_target_plans=phase.target_plans,
        phase="original",
    )
    raw["status"] = "blocked" if raw["blockers"] else "pass"
    raw["execution_exit_code"] = 75 if raw["blockers"] else 0


def finish_reader_native_oracle_phase(
    phase: NativeOraclePhase,
    raw: dict[str, Any],
    reader: SnapshotReader,
    current_artifacts: dict[str, Any],
) -> NativeOracleResidualGraphs:
    """Keep Original and independently checked joint reader obligations distinct."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation

    operation = require_native_operation(reader)
    original = operation.originals.get(phase.requirements.scope)
    if (
        original is None
        or raw["run_id"] != original.run_id
        or raw.get("native_oracle_requirements") != phase.requirements.data()
    ):
        raise ValueError("native v13 omitted/altered its strictly Source-bound Original requirement graph")
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("reader native dispatch closing custody changed")
    residuals = project_native_oracle_residuals(
        phase.requirements,
        original_run_id=original.run_id,
        checked_axes=collect_native_axis_results(phase, original.run_id, current_artifacts=current_artifacts),
        checked_controls=phase.controls,
        source_target_plans=phase.target_plans,
        phase="reader",
    )
    return reconcile_native_phase_residual_graphs(
        raw["blockers"],
        residuals,
        original_status=raw["status"],
        original_exit_code=raw["execution_exit_code"],
        scope=phase.requirements.scope,
        source_binding=phase.requirements.source_binding,
        original_run_id=original.run_id,
        artifact_contract_digest=phase.requirements.artifact_contract_digest,
    )


def native_residual_rows(value: object) -> bool:
    """Preserve the existing public residual-row shape predicate."""
    return _phase_residual_rows(value)
