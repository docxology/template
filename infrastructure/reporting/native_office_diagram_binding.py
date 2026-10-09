"""Actual original Office Mermaid source admission for native visibility.

Every retained graph, real producer command, SVG-only original paint, runtime
and font binding is admitted by the existing source verifier. PDF geometry and
visible ink remain independently recomputed by the diagram observer/replayer.
"""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_mermaid_svg_topology import (
    inspect_original_mermaid_svg,
)
from infrastructure.reporting.native_office_diagram_geometry import (
    DiagramSource,
    diagram_source,
)
from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
    office_original_mermaid_sources,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def admitted_office_diagram_sources(
    source: dict[str, Any],
    scope: str,
    reader: SnapshotReader,
    admission: OfficeMermaidAdmission | None,
) -> tuple[DiagramSource, ...]:
    """Reopen exact source bytes; a producer status flag cannot admit pixels."""
    from infrastructure.reporting.native_mermaid_source_reference import (
        validate_original_mermaid_sources,
    )

    projection = source["mermaid"]
    original = reader.read(source["original_source"]["path"]) if source["original_source"] else None
    expected = () if original is None else office_original_mermaid_sources(original.content.decode(), scope)
    if projection is None:
        if expected:
            raise ValueError("original Office diagram source has no genuine original-source paint admission")
        return ()
    if (
        original is None
        or original.sha256 != source["original_source"]["sha256"]
        or admission is None
        or projection["reference"] != admission.reference
    ):
        raise ValueError("native Office diagram source custody/admission differs from the complete original source")

    def artifact_bytes(binding: dict[str, Any]) -> bytes:
        value = reader.read(binding["path"])
        if value.sha256 != binding["sha256"] or len(value.content) != binding["bytes"]:
            raise ValueError("original native Office diagram artifact bytes/identity differ")
        return value.content

    validate_original_mermaid_sources(
        admission.reference,
        expected,
        artifact_reader=artifact_bytes,
        admit_original_process=admission.admit_original_process,
        inspect_svg=inspect_original_mermaid_svg,
        decoded_pixel_budget=admission.decoded_pixel_budget,
    )
    if [row["identity"] for row in projection["occurrences"]] != [identity for identity, _ in expected]:
        raise ValueError("original Office diagram projection dropped or renamed a source occurrence")
    return tuple(
        diagram_source(
            row["identity"],
            artifact_bytes(row["artifacts"]["png"]),
            artifact_bytes(row["artifacts"]["svg"]),
            row["paint"],
            budget=admission.decoded_pixel_budget,
        )
        for row in admission.reference["occurrences"]
    )


def diagram_witness_budget(
    admission: OfficeMermaidAdmission | None,
) -> SourceImageDecodeBudget:
    """Share the admitted source budget; never reset per diagram or package."""
    if admission is None:
        raise ValueError("native diagram visibility requires the existing shared original decode budget")
    return admission.decoded_pixel_budget


def diagram_witness_runtime(admission: OfficeMermaidAdmission | None, deadline: float) -> PDFiumRuntimeAdmission:
    """Use the genuine caller's preimport provider admission and original clock."""
    if admission is None or admission.pdfium_runtime is None or admission.pdfium_runtime.deadline != deadline:
        raise ValueError("native diagram visibility requires genuine original PDFium provider admission")
    admission.pdfium_runtime.verify()
    return admission.pdfium_runtime


def diagram_visibility_residuals(source: dict[str, Any], witnesses: dict[str, Any] | None) -> list[str]:
    """Replace only exact native visibility/height residuals after both checks.

    This does not admit supervised controls or remove source/process/library,
    package/font/glyph/image/frontmatter/EPUB/native-layout obligations.
    """
    from infrastructure.reporting.native_office_mermaid_binding import (
        office_mermaid_native_residuals,
    )

    residuals = office_mermaid_native_residuals(source)
    if not residuals:
        if witnesses is not None:
            raise ValueError("native diagram witness exists without any original diagram source obligation")
        return []
    if witnesses is None or set(witnesses) != {"reference", "candidate"}:
        return residuals
    # These objects must be actual fresh observer results, or fully recomputed
    # by replay_office_diagram_visibility immediately before this combination.
    if any(value["status"] != "pass" or value["findings"] or value["blockers"] for value in witnesses.values()):
        return residuals
    return []
