"""Native artifact observation phase for one admitted public project.

Every contracted deliverable is read back, its independent source observer is
recorded, and the selected whole-PDF, Pitch pair and primary-format evidence is
aggregated into the caller's raw execution record. This module owns only that
observation phase; execution and closing custody stay with the worker.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract
from infrastructure.reporting.native_format_observer_dispatch import observe_native_artifact
from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
from infrastructure.reporting.native_office_diagram_source import prepare_office_diagram_source
from infrastructure.reporting.native_oracle_axis_facts import native_observer_components
from infrastructure.reporting.native_print_artifact_observer import selected_print_artifact

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
    from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
    from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidRuntimeAdmission
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

__all__ = ["observe_native_deliverables"]


def observe_native_deliverables(
    root: Path,
    directory: Path,
    scope: str,
    contract: tuple[NativeArtifact, ...],
    formats: tuple[str, ...],
    native_reader: SnapshotReader,
    source_context: NativeSourceContext,
    raw: dict[str, Any],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    mermaid_runtime: NativeMermaidRuntimeAdmission,
    office_font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    pdfium_runtime: PDFiumRuntimeAdmission,
    specification: dict[str, Any],
    pipeline_run_id: str,
    plan_digest: str,
) -> tuple[list[dict[str, Any]], tuple[dict[str, Any], dict[str, Any]] | None]:
    """Record every contracted deliverable and return its checked observations.

    The caller's raw record receives artifact rows, PDF-source and native-source
    blockers, the Pitch pair aggregate and the selected primary formats at the
    same points, and in the same order, as the worker loop this replaces.
    """
    checked_observers: list[dict[str, Any]] = []
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None = None
    for index, artifact in enumerate(contract):
        snapshot = native_reader.read(artifact.path)
        observation = parse_native_bytes(artifact.format, snapshot.content)
        row = {
            **asdict(artifact),
            "sha256": snapshot.sha256,
            "observation": observation,
        }
        if artifact.format == "pdf":
            row["raster"] = audit_pdf_raster(
                root,
                directory,
                snapshot,
                observation,
                env=env,
                deadline=deadline,
                run_id=run_id,
                ordinal=index,
            )
            from infrastructure.reporting.native_projection_source_dispatch import selected_source_projection

            if not selected_print_artifact(scope, artifact) and not selected_source_projection(artifact):
                content = compile_pdf_content_contract(root, scope, artifact, native_reader, deadline=deadline)
                row["content_contract"] = content.to_dict()
                row["pdf_content"] = inspect_pdf_content(
                    snapshot.content,
                    tuple(native_reader.read(item["path"]).content for item in row["raster"]["rasters"]),
                    content,
                    deadline=deadline,
                )
                if row["pdf_content"]["findings"]:
                    raise ValueError(f"actual PDF content/layout/visibility failed: {row['pdf_content']['findings']}")
                raw["blockers"].extend(
                    {"tool": f"PDF source oracle {artifact.id}", "reason": reason}
                    for reason in row["pdf_content"]["blockers"]
                )
        office_admission = None
        if artifact.format in {"docx", "epub"}:
            office_admission = prepare_office_diagram_source(
                root,
                directory / f"office-source-admission-{index:04d}",
                scope,
                artifact,
                source_context,
                package_root=mermaid_runtime.selection.package_root,
                runtime_admission=mermaid_runtime,
                node_executable=mermaid_runtime.selection.node_executable,
                chrome_executable=mermaid_runtime.selection.chrome_executable,
                font_files=office_font_files,
                decoded_pixel_budget=decoded_pixel_budget,
                pdfium_runtime=pdfium_runtime,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
        selected_tools = specification.get("observer_tools", {})
        observer = observe_native_artifact(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            native_reader,
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=index,
            source_reference=source_context.reference,
            verify_source_correspondence=source_context.verify_correspondence,
            office_mermaid_admission=office_admission,
            epubcheck_jar=Path(selected_tools["epubcheck_jar"]) if selected_tools.get("epubcheck_jar") else None,
            java_executable=Path(selected_tools["java_executable"]) if selected_tools.get("java_executable") else None,
            frozen_epub_engine=root / selected_tools["frozen_epub_engine"]
            if selected_tools.get("frozen_epub_engine")
            else None,
        )
        row["native_observer"] = observer
        result = native_observer_outcome(observer)
        if result.get("status") == "fail" or result.get("findings"):
            raise ValueError(f"actual native observer failed for {artifact.id}: {result.get('findings')}")
        raw["blockers"].extend(
            {"tool": f"native source oracle {artifact.id}", "reason": reason} for reason in result.get("blockers", [])
        )
        checked_observers.append(
            {
                "artifact_id": artifact.id,
                "findings": result["findings"],
                "residuals": result["blockers"],
                "source_observer": observer,
                "observations": native_observer_components(observer),
            }
        )
        raw["artifacts"].append(row)
    if any(artifact.format == "pdf" for artifact in contract):
        from infrastructure.reporting.native_pdf_whole_worker import observe_whole_pdf_worker

        whole_pdf = observe_whole_pdf_worker(
            root,
            directory,
            scope,
            formats,
            native_reader,
            pipeline_run_id=pipeline_run_id,
            plan_digest=plan_digest,
            run_id=run_id,
            deadline=deadline,
            env=env,
            raw=raw,
        )
    if scope == "templates/template_pitch_deck":
        from infrastructure.reporting.native_projection_source_dispatch import inspect_admitted_pitch_pairs

        pairs = inspect_admitted_pitch_pairs(
            root,
            scope,
            contract,
            raw["artifacts"],
            native_reader,
            source_reference=source_context.reference,
            verify_source_correspondence=source_context.verify_correspondence,
            deadline=deadline,
        )
        raw["pitch_native_pairs"] = pairs
        if pairs["findings"] or pairs["status"] == "fail":
            raise ValueError(f"actual complete Pitch native pair parity failed: {pairs['findings']}")
        raw["blockers"].extend({"tool": "Pitch all native pairs", "reason": reason} for reason in pairs["blockers"])
    for kind in formats:
        id_ = f"manuscript:{kind}"
        primary: dict[str, Any] | None = next((item for item in raw["artifacts"] if item["id"] == id_), None)
        if kind == "slides":
            primary = next(
                (item for item in raw["artifacts"] if item["id"].endswith(":slides")),
                None,
            )
        if primary is None:
            raise ValueError("required native format has no actual artifact")
        raw["formats"][kind] = {
            "path": primary["path"],
            "sha256": primary["sha256"],
            "validated": True,
        }

    return checked_observers, whole_pdf
