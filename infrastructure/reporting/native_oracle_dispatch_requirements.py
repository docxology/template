"""Compile one held Source requirement graph and its literal target plans.

Target plans are DATA. Their declarations never replace any actual native
adapter, genuine Original child, fresh Current check or closing custody.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_oracle_obligation_compiler import compile_native_oracle_obligations
from infrastructure.reporting.native_oracle_obligation_spec import NativeOracleSpecification
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidCensus
from infrastructure.reporting.native_source_control_targets import (
    OfficeRequirementCohort,
    bind_office_control_target_requirements,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def compile_native_oracle_dispatch_requirements(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    deadline: float,
    office_cohorts: dict[str, OfficeRequirementCohort] | None = None,
    source_census: list[SourceMermaidCensus] | None = None,
) -> tuple[NativeOracleSpecification, dict[str, Any]]:
    """Compile once in each actual phase, using its genuine Source and clock.

    Literal fixtures stay literal. Configured print targets are independently
    selected from the Source model. Office targets use the phase's genuine
    held complete census. Pitch uses the same complete held-Source selector as
    its actual writer. Missing Office nominations remain explicit residuals.
    """
    specification = compile_native_oracle_obligations(
        root, scope, formats, reader, source=source, deadline=deadline, source_census=source_census
    )
    specification = bind_office_control_target_requirements(
        specification, office_cohorts, source=source, deadline=deadline
    )
    targets: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for suite in specification.suites:
        remaining(deadline)
        selected: dict[str, list[dict[str, Any]]] = {}
        if suite.id in {"configured_pitch", "docx_diagrams", "epub_diagrams"}:
            if all(control.target_requirements for control in suite.controls):
                selected = {
                    control.name: [target.target for target in control.target_requirements]
                    for control in suite.controls
                }
        elif suite.id == "configured_print":
            from infrastructure.reporting.native_print_artifact_controls import selected_control_artifacts

            for control in suite.controls:
                artifacts = selected_control_artifacts(root, scope, control.name)
                if not artifacts or any(item.id not in suite.related_artifact_ids for item in artifacts):
                    raise ValueError("configured print selector escaped its complete held Source artifact contract")
                selected[control.name] = [asdict(item) for item in artifacts]
        elif suite.id in {"pdf", "html", "html_semantic", "docx", "epub", "projection", "pptx"}:
            fixture = {
                "pdf": "invented-control:pdf",
                "html": "browser-control",
                "html_semantic": "browser-semantic",
            }.get(suite.id, suite.id)
            selected = {control.name: [{"fixture": fixture, "name": control.name}] for control in suite.controls}
        elif suite.id in {"docx_scientific", "epub_scientific"}:
            kind = suite.id.removesuffix("_scientific")
            selected = {
                control.name: [
                    {"fixture": "scientific-" + kind, "control": name}
                    for name in (("baseline",) if control.name == "baseline" else ("baseline", control.name))
                ]
                for control in suite.controls
            }
        elif suite.id == "manuscript_slides":
            selected = {
                control.name: [{"fixture": "two-page-source-pdf", "name": control.name}] for control in suite.controls
            }
        elif suite.id not in {"docx_diagrams", "epub_diagrams"}:
            raise ValueError("native Source requirements selected an unsupported target-plan interface")
        if selected:
            targets[suite.id] = selected
    source.reference.verify_unchanged(deadline=deadline)
    source.verify_correspondence(source.reference, root, reader, deadline)
    if not reader.unchanged():
        raise ValueError("native Source requirements/target plan changed during complete compilation")
    remaining(deadline)
    return specification, {
        "scope": scope,
        "source_binding": list(specification.source_binding),
        "artifact_contract_digest": specification.artifact_contract_digest,
        "suites": targets,
    }
