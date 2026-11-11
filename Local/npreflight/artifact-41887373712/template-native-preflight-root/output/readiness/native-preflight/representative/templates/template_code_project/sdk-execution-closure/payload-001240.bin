"""Actual complete Office Mermaid Source under its live original process owner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.reporting.native_mermaid_font_bodies import (
    NativeMermaidFontSelection,
    source_mermaid_font_bodies_operation,
)
from infrastructure.reporting.native_office_mermaid_font_binding import (
    verify_actual_office_mermaid_fonts,
)

from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidRuntimeAdmission,
    current_source_mermaid_runtime_admission,
)

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeArtifact,
    create_private_native_directory,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_mermaid_source_reference import (
    observe_original_mermaid_sources,
)
from infrastructure.reporting.native_mermaid_svg_topology import (
    inspect_original_mermaid_svg,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
    office_original_mermaid_sources,
)
from infrastructure.reporting.native_office_semantic_source import (
    office_semantic_source_plan,
)
from infrastructure.reporting.native_citation_process_custody import (
    CitationOriginalProcessCustodian,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def prepare_office_diagram_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    source: NativeSourceContext,
    *,
    package_root: Path,
    runtime_admission: NativeMermaidRuntimeAdmission | None = None,
    node_executable: Path,
    chrome_executable: Path,
    font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    pdfium_runtime: PDFiumRuntimeAdmission,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> OfficeMermaidAdmission | None:
    """Rebuild actual original Source and retain genuinely owned Node invocations."""
    remaining(deadline)
    if source.bindings.current_root != root or source.bindings.run_id != run_id or pdfium_runtime.source is not source:
        raise ValueError("Office Mermaid source requires the same genuine original Source/provider owner")
    create_private_native_directory(root, directory)
    create_private_native_directory(root, directory / "source-plan")
    reader = SnapshotReader(root)
    source.verify_correspondence(source.reference, root, reader, deadline)
    plan = office_semantic_source_plan(root, directory / "source-plan", scope, artifact, reader, deadline=deadline)
    sources = office_original_mermaid_sources(plan.original_content.decode(), scope)
    if not sources:
        source.verify_correspondence(source.reference, root, reader, deadline)
        remaining(deadline)
        return None
    if runtime_admission is None:
        runtime_admission = current_source_mermaid_runtime_admission()
    if runtime_admission is not None:
        if runtime_admission.source is not source:
            raise ValueError("Office Source11 runtime belongs to another genuine Source operation")
        runtime_admission.observe(deadline=deadline)
    custodian = CitationOriginalProcessCustodian(root, source, run_id=run_id, deadline=deadline)

    def admit_process(record: dict[str, Any]) -> None:
        if record.get("purpose") == "source-mermaid-node-version":
            if runtime_admission is None:
                raise ValueError("Office Source11 version proof lacks its genuinely held original runtime")
            runtime_admission.admit_node_version_process(record)
        else:
            custodian.admit_original_process(record)

    with source_mermaid_font_bodies_operation(
        NativeMermaidFontSelection(font_files), source, deadline=deadline
    ) as font_bodies:
        reference = observe_original_mermaid_sources(
            root,
            directory / "original-mermaid",
            sources,
            package_root=package_root,
            node_executable=node_executable,
            chrome_executable=chrome_executable,
            font_files=font_files,
            decoded_pixel_budget=decoded_pixel_budget,
            inspect_svg=inspect_original_mermaid_svg,
            env=env,
            deadline=deadline,
            run_id=run_id,
            on_original_tool=custodian.observe_actual_tool,
            runtime_admission=runtime_admission,
        )
        verify_actual_office_mermaid_fonts(reference, font_bodies, deadline=deadline)
    pdfium_runtime.verify()
    source.verify_correspondence(source.reference, root, reader, deadline)
    remaining(deadline)
    return OfficeMermaidAdmission(
        reference,
        admit_process,
        decoded_pixel_budget,
        pdfium_runtime,
    )
