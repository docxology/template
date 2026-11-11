"""Bind original Office diagram occurrences to genuine source-only graphics.

This pure planner admits retained original processes and independently decoded
SVG/paint bytes. Portable admission additionally reproduces the source with
explicit reader-local tools; no retained boolean can substitute for that run.
"""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from infrastructure.reporting.native_mermaid_svg_topology import (
    inspect_original_mermaid_svg,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_mermaid_font_bodies import (
    NativeMermaidFontSelection,
    source_mermaid_font_bodies_operation,
)
from infrastructure.reporting.native_office_mermaid_font_binding import (
    verify_actual_office_mermaid_fonts,
)

from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidRuntimeAdmission,
    source_mermaid_runtime_operation,
)
from infrastructure.reporting.native_citation_process_custody import (
    CitationOriginalProcessCustodian,
)

from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.rendering._pdf_mermaid import (
    _MERMAID_BLOCK_RE,
    _caption_text,
    _first_alt,
)


@dataclass(frozen=True)
class OfficeMermaidAdmission:
    """Root supplies its actual original process verifier, never a pass flag."""

    reference: dict[str, Any]
    admit_original_process: Callable[[dict[str, Any]], None]
    decoded_pixel_budget: SourceImageDecodeBudget
    pdfium_runtime: PDFiumRuntimeAdmission | None = None


@dataclass(frozen=True)
class OfficeMermaidReaderRuntime:
    """Explicit portable reader roots and Root's original process verifier."""

    directory: Path
    package_root: Path
    node_executable: Path
    chrome_executable: Path
    font_files: tuple[Path, ...]
    admit_original_process: Callable[[dict[str, Any]], None]
    decoded_pixel_budget: SourceImageDecodeBudget
    pdfium_runtime: PDFiumRuntimeAdmission | None = None
    source_mermaid_runtime: NativeMermaidRuntimeAdmission | None = None


def office_original_mermaid_sources(content: str, scope: str) -> tuple[tuple[str, bytes], ...]:
    """Stable source-only identities include ordinal and exact original body."""
    if len(content.encode()) > 32 * 1024 * 1024:
        raise ValueError("original Office Mermaid source exceeds finite byte bound")
    matches = tuple(_MERMAID_BLOCK_RE.finditer(content))
    if len(matches) > 100:
        raise ValueError("original Office Mermaid source exceeds finite occurrence bound")
    result = []
    for ordinal, match in enumerate(matches):
        source = match.group("source").encode()
        if not source.strip():
            raise ValueError("original Office Mermaid source occurrence is empty")
        result.append(
            (
                f"{scope}:mermaid:{ordinal:04d}:{hashlib.sha256(source).hexdigest()}",
                source,
            )
        )
    return tuple(result)


def _artifact_reader(reader: SnapshotReader) -> Callable[[dict[str, Any]], bytes]:
    def read(binding: dict[str, Any]) -> bytes:
        if set(binding) not in ({"path", "sha256"}, {"path", "sha256", "bytes"}):
            raise ValueError("original Office Mermaid artifact binding is incomplete")
        value = reader.read(binding["path"])
        if value.sha256 != binding["sha256"] or ("bytes" in binding and len(value.content) != binding["bytes"]):
            raise ValueError("original Office Mermaid actual artifact custody differs")
        return value.content

    return read


def project_admitted_office_mermaid_sources(
    root: Path,
    manuscript: Path,
    content: str,
    scope: str,
    reader: SnapshotReader,
    admission: OfficeMermaidAdmission,
) -> tuple[str, dict[str, Any]]:
    """Replace only original fences, preserving exact caption/alternative roles.

    Actual native package-image and PDF-placement checks remain the full Office
    observer's obligations. This function executes no renderer or source data.
    """
    from infrastructure.reporting.native_mermaid_source_reference import (
        validate_original_mermaid_sources,
    )

    sources = office_original_mermaid_sources(content, scope)
    validate_original_mermaid_sources(
        admission.reference,
        sources,
        artifact_reader=_artifact_reader(reader),
        admit_original_process=admission.admit_original_process,
        inspect_svg=inspect_original_mermaid_svg,
        decoded_pixel_budget=admission.decoded_pixel_budget,
    )
    rows = admission.reference["occurrences"]
    pieces: list[str] = []
    occurrences: list[dict[str, Any]] = []
    previous = 0
    for ordinal, (match, row, (identity, source)) in enumerate(
        zip(_MERMAID_BLOCK_RE.finditer(content), rows, sources, strict=True)
    ):
        png = reader.read(row["artifacts"]["png"]["path"])
        # A relative path is identical after relocation of the whole root.
        target = Path(os.path.relpath(png.path, manuscript)).as_posix()
        if any(character in target for character in "\n\r<>"):
            raise ValueError("portable original Mermaid target cannot be represented as a literal path")
        caption = _caption_text(match)
        alternative = _first_alt(match.group("alts")) or caption or "Mermaid diagram"
        visible = caption or alternative
        if any(character in visible + alternative for character in "\n\r"):
            raise ValueError("original Mermaid caption/alternative requires an unsupported multiline projection")
        projected = (
            f"\n![{visible}](<{target}>)"
            f"{{width=82% data-template-max-height=4.2in "
            f'style="max-height: 4.2in; height: auto; object-fit: contain;" '
            f"alt={json.dumps(alternative, ensure_ascii=False)}}}\n"
        )
        pieces.extend((content[previous : match.start()], projected))
        previous = match.end()
        occurrences.append(
            {
                "ordinal": ordinal,
                "identity": identity,
                "source_range": [match.start(), match.end()],
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "png": row["artifacts"]["png"],
                "svg": row["artifacts"]["svg"],
                "image_target": target,
                "caption": visible,
                "alternative": alternative,
                "projected_markdown_sha256": hashlib.sha256(projected.encode()).hexdigest(),
                "native_height_limit_requires_layout_witness": True,
            }
        )
    pieces.append(content[previous:])
    return "".join(pieces), {
        "schema_version": "template-native-office-original-mermaid-projection-v1",
        "original_source_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "reference": admission.reference,
        "occurrences": occurrences,
    }


def original_office_mermaid_ast_occurrences(
    original_ast: bytes, original_content: str, scope: str
) -> list[dict[str, Any]]:
    """Account actual original Pandoc CodeBlocks before image projection."""
    document = json.loads(original_ast)
    occurrences = []

    def walk(value: Any, location: list[str | int]) -> None:
        if isinstance(value, dict):
            if value.get("t") == "CodeBlock" and "mermaid" in value["c"][0][1]:
                occurrences.append((location, value["c"][1].encode()))
            for key, child in value.items():
                walk(child, [*location, key])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, [*location, index])

    walk(document.get("blocks"), ["blocks"])
    sources = office_original_mermaid_sources(original_content, scope)
    if len(occurrences) != len(sources):
        raise ValueError("original Office AST Mermaid census differs from original source fence census")
    result = []
    for (location, actual), (identity, expected) in zip(occurrences, sources, strict=True):
        # Fenced CodeBlock parsing removes outer fence whitespace. Retain both
        # actual body hashes; only that declared boundary whitespace can differ.
        if actual.strip() != expected.strip():
            raise ValueError("original Office actual Pandoc Mermaid source bytes differ")
        result.append(
            {
                "identity": identity,
                "ast_location": location,
                "source_sha256": hashlib.sha256(expected).hexdigest(),
                "ast_content_sha256": hashlib.sha256(actual).hexdigest(),
                "normalization": "outer fenced CodeBlock whitespace only",
            }
        )
    return result


def replay_office_original_mermaid_sources(
    root: Path,
    original_content: str,
    scope: str,
    projection: dict[str, Any],
    reader: SnapshotReader,
    runtime: OfficeMermaidReaderRuntime,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> OfficeMermaidAdmission:
    """Run genuine portable source reproduction with explicit reader roots."""
    from infrastructure.reporting.native_mermaid_source_reference import (
        replay_original_mermaid_sources,
    )

    sources = office_original_mermaid_sources(original_content, scope)
    current_run_id = (
        runtime.source_mermaid_runtime.source.bindings.run_id if runtime.source_mermaid_runtime is not None else run_id
    )
    current_custodian = (
        CitationOriginalProcessCustodian(
            root,
            runtime.source_mermaid_runtime.source,
            run_id=current_run_id,
            deadline=deadline,
        )
        if runtime.source_mermaid_runtime is not None
        else None
    )
    with (
        source_mermaid_runtime_operation(
            runtime.source_mermaid_runtime,
            source=runtime.source_mermaid_runtime.source,
            deadline=deadline,
        )
        if runtime.source_mermaid_runtime is not None
        else nullcontext()
    ):
        font_source = (
            runtime.source_mermaid_runtime.source
            if runtime.source_mermaid_runtime is not None
            else runtime.pdfium_runtime.source
            if runtime.pdfium_runtime is not None
            else None
        )
        if font_source is None:
            raise ValueError("Office fresh font body observation requires its genuine current Source capability")
        with source_mermaid_font_bodies_operation(
            NativeMermaidFontSelection(runtime.font_files), font_source, deadline=deadline
        ) as font_bodies:
            reproduced = replay_original_mermaid_sources(
                projection["reference"],
                sources,
                artifact_reader=_artifact_reader(reader),
                admit_original_process=runtime.admit_original_process,
                root=root,
                directory=runtime.directory,
                package_root=runtime.package_root,
                node_executable=runtime.node_executable,
                chrome_executable=runtime.chrome_executable,
                font_files=runtime.font_files,
                inspect_svg=inspect_original_mermaid_svg,
                decoded_pixel_budget=runtime.decoded_pixel_budget,
                env=env,
                deadline=deadline,
                run_id=current_run_id,
                runtime_admission=runtime.source_mermaid_runtime,
                on_original_tool=current_custodian.observe_actual_tool if current_custodian is not None else None,
            )
            verify_actual_office_mermaid_fonts(reproduced, font_bodies, deadline=deadline)
    if reproduced["blockers"]:
        raise ValueError("portable original Office Mermaid fresh source reproduction retains blockers")
    return OfficeMermaidAdmission(
        projection["reference"],
        runtime.admit_original_process,
        runtime.decoded_pixel_budget,
        runtime.pdfium_runtime,
    )


def office_mermaid_native_residuals(source: dict[str, Any]) -> list[str]:
    """Keep independent native occurrence visibility/height obligations exact.

    Decoded embedded image equality and same-writer full-page parity cannot
    independently prove common clipping, occlusion or the declared height cap.
    A future actual native placement/visible-ink witness must replace this gate.
    """
    projection = source.get("mermaid")
    if projection is None:
        return []
    return [
        f"original Mermaid {row['identity']} requires independent native visible placement and 4.2in height witness"
        for row in projection["occurrences"]
    ]
