"""Real native PDF mutations for independent Office diagram visibility controls.

Inputs are the genuine original native PDF and Root-admitted original diagram
sources. Each child paints the real PDF through the existing native raster and
font tools; it never fabricates the supervising process receipt.
"""

from __future__ import annotations

from infrastructure.reporting.native_office_nested_custody import OfficeNestedReaderOperation

import hashlib
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import (
    audit_pdf_raster,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_office_diagram_geometry import (
    MAX_HEIGHT_PT,
    DiagramSource,
    inspect_diagram_pdf_geometry,
)
from infrastructure.reporting.native_office_diagram_visibility import (
    observe_office_diagram_visibility,
)
from infrastructure.reporting.native_office_control_custody import OfficeControlReaderOperation
from infrastructure.reporting.native_office_diagram_positive import (
    OfficeDiagramNativePositive,
)
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CONTROL_CODES = {
    "half-clip": "office.diagram.clipped",
    "zero-opacity": "office.diagram.hidden",
    "white-overlay": "office.diagram.visible_ink",
    "remove-paint": "office.diagram.occurrence_count",
    "over-height": "office.diagram.height",
    "tiny-labels": "office.diagram.font_floor",
}


def mutate_office_diagram_pdf(pdf: bytes, placement: dict[str, Any], control: str) -> bytes:
    """Mutate an actual Do instruction, preserving original source image bytes.

    Shared Form resources can paint the selected instruction more than once. The
    actual geometry census and pixel oracle account every resulting occurrence;
    the control does not claim a one-occurrence mutation when a Form is shared.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ContentStream, DictionaryObject, FloatObject, NameObject

    if control not in CONTROL_CODES:
        raise ValueError("unknown original native Office diagram control")
    reader = PdfReader(BytesIO(pdf), strict=True)
    writer = PdfWriter(clone_from=reader)
    page = writer.pages[placement["page"] - 1]
    owner: Any = page
    resources = page["/Resources"].get_object()
    path = placement["resource_path"]
    for name in path[:-1]:
        owner = resources["/XObject"][name].get_object()
        if owner.get("/Subtype") != "/Form":
            raise ValueError("native control target is not the independently parsed actual Form path")
        resources = owner.get("/Resources", resources).get_object()
    content = ContentStream(page.get_contents() if owner is page else owner, writer)
    index = placement["stream_operation_index"]
    operands, operator = content.operations[index]
    if operator != b"Do" or str(operands[0]) != path[-1]:
        raise ValueError("native control target differs from the independently parsed actual Do occurrence")

    def operations(data: bytes) -> list[Any]:
        from pypdf.generic import DecodedStreamObject

        stream = DecodedStreamObject()
        stream.set_data(data)
        return list(ContentStream(stream, writer).operations)

    original = (operands, operator)
    if control == "remove-paint":
        replacement = []
    elif control == "half-clip":
        replacement = [*operations(b"q 0 0 .5 1 re W n"), original, *operations(b"Q")]
    elif control == "zero-opacity":
        graphic_states = resources.get("/ExtGState")
        if graphic_states is None:
            graphic_states = DictionaryObject()
            resources[NameObject("/ExtGState")] = graphic_states
        graphic_states = graphic_states.get_object()
        name = "/OriginalDiagramVisibilityZero"
        if name in graphic_states:
            raise ValueError("actual native PDF already owns the private control graphics-state name")
        graphic_states[NameObject(name)] = DictionaryObject({NameObject("/ca"): FloatObject(0)})
        replacement = [
            *operations(f"q {name} gs".encode("ascii")),
            original,
            *operations(b"Q"),
        ]
    elif control == "white-overlay":
        replacement = [original, *operations(b"q 1 1 1 rg 0 0 1 1 re f Q")]
    else:
        box = placement["box_pt"]
        factor = (
            MAX_HEIGHT_PT / (box[3] - box[1]) + 0.05
            if control == "over-height"
            else min(0.25, 4.5 / placement["minimum_label_font_pt"])
        )
        replacement = [
            *operations(f"q {factor:.17g} 0 0 {factor:.17g} 0 0 cm".encode("ascii")),
            original,
            *operations(b"Q"),
        ]
    content.operations[index : index + 1] = replacement
    if owner is page:
        page[NameObject("/Contents")] = writer._add_object(content)
    else:
        owner.set_data(content.get_data())
    output = BytesIO()
    writer.write(output)
    mutated = output.getvalue()
    if mutated == pdf:
        raise ValueError("actual native diagram control did not change its target PDF bytes")
    return mutated


def run_office_diagram_control(
    root: Path,
    directory: Path,
    original_pdf: bytes,
    sources: tuple[DiagramSource, ...],
    control: str,
    *,
    target_ordinal: int,
    budget: SourceImageDecodeBudget,
    positive: OfficeDiagramNativePositive,
    pdfium_runtime: PDFiumRuntimeAdmission,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[int, dict[str, Any]]:
    """Return real child exit0/1/2 to an external genuine Root supervisor.

    Original-source admission and baseline are mandatory before each mutation.
    The supervisor must bind original child command, inputs, before/after source
    guards, runtime/libraries, time/RSS/output caps and complete process cleanup.
    No record returned here replaces that supervisor's original receipt.
    """
    if control != "baseline" and control not in CONTROL_CODES:
        raise ValueError("unknown actual Office diagram control")
    positive.verify(deadline)
    if (
        positive.pdf != original_pdf
        or positive.sources != sources
        or positive.decoded_pixel_budget is not budget
        or positive.source is not pdfium_runtime.source
    ):
        raise ValueError("Office mutation requires this actual original Source/PDF/native positive and shared budget")
    baseline = positive.record["visibility"]["geometry"]
    if baseline["status"] != "pass" or not baseline["placements"]:
        raise ValueError("native diagram control requires a supported genuine original geometry baseline")
    from infrastructure.reporting.native_office_diagram_census import select_diagram_control_targets

    targets = select_diagram_control_targets(sources, baseline, deadline=deadline)
    if type(target_ordinal) is not int or not 0 <= target_ordinal < len(targets):
        raise ValueError("Office control requires one exact Source-census placement ordinal")
    target = targets[target_ordinal]
    data = (
        original_pdf if control == "baseline" else mutate_office_diagram_pdf(original_pdf, target["placement"], control)
    )
    create_private_native_directory(root, directory)
    path = directory / "actual-native-control.pdf"
    atomic_write_bytes_confined(root, path, data, mode=0o600)
    reader = SnapshotReader(root)
    artifact = reader.read(path.relative_to(root).as_posix())
    raster = audit_pdf_raster(
        root,
        directory,
        artifact,
        parse_native_bytes("pdf", data),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    pages = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    witness = observe_office_diagram_visibility(
        root,
        directory / "source-stencils",
        data,
        pages,
        sources,
        budget=budget,
        pdfium_runtime=pdfium_runtime,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    common_parity = None
    if control == "white-overlay":
        from infrastructure.reporting.native_office_reference_visual import (
            inspect_office_reference_projection,
        )

        common_parity = inspect_office_reference_projection(data, pages, data, pages, deadline=deadline)
        if common_parity["findings"]:
            raise ValueError("real common-overlay equal-page control failed its actual parity precondition")
    intended = CONTROL_CODES.get(control)
    codes = {row["code"] for row in witness["findings"]}
    code = (
        0
        if control == "baseline" and witness["status"] == "pass"
        else 1
        if control != "baseline" and intended in codes and not witness["blockers"]
        else 2
    )
    positive.verify(deadline)
    pdfium_runtime.verify()
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("actual native Office diagram control source/raster changed")
    return code, {
        "schema_version": "template-native-office-diagram-genuine-control-v3",
        "run_id": run_id,
        "control": control,
        "scope": positive.scope,
        "kind": positive.kind,
        "original_pdf_sha256": hashlib.sha256(original_pdf).hexdigest(),
        "positive": positive.record,
        "mutated_pdf": {"path": artifact.relative, "sha256": artifact.sha256},
        "targets": targets,
        "target": target,
        "raster": raster,
        "visibility": witness,
        "expected_finding": intended,
        "oracle_exit_code": code,
        "common_parity_demonstration": common_parity,
        "assurance": (
            "requires external original supervised child/process/source/runtime/font/library/control admission"
        ),
    }


def replay_office_diagram_control(
    root: Path,
    directory: Path,
    original_pdf: bytes,
    sources: tuple[DiagramSource, ...],
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    budget: SourceImageDecodeBudget,
    current_positive: OfficeDiagramNativePositive,
    pdfium_runtime: PDFiumRuntimeAdmission,
    deadline: float,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    env: dict[str, str],
    reader_directory: Path,
    original_child: dict[str, Any],
    original_operation: OfficeControlReaderOperation | OfficeNestedReaderOperation,
) -> None:
    """Recompute mutations, admit original tools and genuinely repaint source.

    The fixed genuine reader role authenticates the externally held child,
    exact original Source/target and independently reaped intended exit.
    Current execution of the complete cohort is required by the enclosing
    cohort adapter; this per-case replay never claims to supply that execution.
    """
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _raster,
    )
    from infrastructure.reporting.native_office_diagram_visibility import (
        replay_office_diagram_visibility,
    )

    expected_fields = {
        "schema_version",
        "run_id",
        "control",
        "scope",
        "kind",
        "original_pdf_sha256",
        "positive",
        "mutated_pdf",
        "target",
        "targets",
        "raster",
        "visibility",
        "expected_finding",
        "oracle_exit_code",
        "common_parity_demonstration",
        "assurance",
    }
    if (
        set(raw) != expected_fields
        or raw["schema_version"] != "template-native-office-diagram-genuine-control-v3"
        or raw["run_id"] != run_id
    ):
        raise ValueError("portable original native diagram control schema differs")
    if (
        type(original_operation) not in (OfficeControlReaderOperation, OfficeNestedReaderOperation)
        or original_operation.deadline != deadline
    ):
        raise ValueError("Office control replay requires the exact externally held original reader role")
    original_operation.verify(reader)
    current_positive.verify(deadline)
    if current_positive.decoded_pixel_budget is not budget or current_positive.source is not pdfium_runtime.source:
        raise ValueError("portable Office control requires the actual reader's shared Source/native positive")
    positive = raw["positive"]
    if (
        positive["source"] != current_positive.record["source"]
        or positive["scope"] != current_positive.scope
        or positive["kind"] != current_positive.kind
        or positive["occurrences"] != [value.identity for value in sources]
    ):
        raise ValueError("portable original positive Source/diagram occurrence closure differs")
    positive_pdf = _file(positive["pdf"], reader)
    if positive_pdf.content != original_pdf:
        raise ValueError("portable Office original control PDF differs from genuine source-only positive")
    positive_directory = directory / "positive-native"
    native_directory = positive_directory / "native-conversion"
    _raster(
        {"raster": positive["native"]["raster"]},
        positive_pdf,
        0,
        native_directory,
        reader,
        run_id,
        versions,
        custody,
    )
    positive_pages = tuple(
        _file({"path": row["path"], "sha256": row["sha256"]}, reader).content
        for row in positive["native"]["raster"]["rasters"]
    )
    replay_office_diagram_visibility(
        root,
        positive_directory / "source-stencils",
        original_pdf,
        positive_pages,
        sources,
        positive["visibility"],
        reader,
        budget=budget,
        pdfium_runtime=pdfium_runtime,
        run_id=run_id,
        custody=custody,
        versions=versions,
        deadline=deadline,
        reader_directory=reader_directory / "positive-stencils",
        env=env,
    )
    if (
        positive["visibility"]["status"] != "pass"
        or positive["visibility"]["findings"]
        or positive["visibility"]["blockers"]
    ):
        raise ValueError("portable original real Source-only native positive failed before mutation")
    control = raw["control"]
    if control != "baseline" and control not in CONTROL_CODES:
        raise ValueError("portable original native diagram control kind differs")
    geometry = inspect_diagram_pdf_geometry(original_pdf, sources, budget=budget, deadline=deadline)
    from infrastructure.reporting.native_office_diagram_census import select_diagram_control_targets

    targets = select_diagram_control_targets(sources, geometry, deadline=deadline)
    target = raw["target"]
    ordinal = target.get("ordinal") if isinstance(target, dict) else None
    if (
        type(ordinal) is not int
        or not 0 <= ordinal < len(targets)
        or raw["targets"] != targets
        or target != targets[ordinal]
        or geometry["status"] != "pass"
        or not geometry["placements"]
        or raw["original_pdf_sha256"] != hashlib.sha256(original_pdf).hexdigest()
    ):
        raise ValueError("portable native diagram control target/original source geometry differs")
    expected = (
        original_pdf if control == "baseline" else mutate_office_diagram_pdf(original_pdf, target["placement"], control)
    )
    mutated = _file(raw["mutated_pdf"], reader)
    if mutated.path != directory / "actual-native-control.pdf" or mutated.content != expected:
        raise ValueError("portable native diagram control did not apply the exact meaningful real-PDF mutation")
    _raster(
        {"raster": raw["raster"]},
        mutated,
        0,
        directory,
        reader,
        run_id,
        versions,
        custody,
    )
    pages = tuple(
        _file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in raw["raster"]["rasters"]
    )
    replay_office_diagram_visibility(
        root,
        directory / "source-stencils",
        mutated.content,
        pages,
        sources,
        raw["visibility"],
        reader,
        budget=budget,
        pdfium_runtime=pdfium_runtime,
        run_id=run_id,
        custody=custody,
        versions=versions,
        deadline=deadline,
        reader_directory=reader_directory,
        env=env,
    )
    common_parity = None
    if control == "white-overlay":
        from infrastructure.reporting.native_office_reference_visual import (
            inspect_office_reference_projection,
        )

        common_parity = inspect_office_reference_projection(
            mutated.content, pages, mutated.content, pages, deadline=deadline
        )
    if raw["common_parity_demonstration"] != common_parity or (common_parity is not None and common_parity["findings"]):
        raise ValueError("portable common-overlay control did not retain actual identical-page parity")
    witness = raw["visibility"]
    intended = CONTROL_CODES.get(control)
    code = (
        0
        if control == "baseline" and witness["status"] == "pass"
        else 1
        if control != "baseline"
        and intended in {row["code"] for row in witness["findings"]}
        and not witness["blockers"]
        else 2
    )
    if raw["expected_finding"] != intended or raw["oracle_exit_code"] != code:
        raise ValueError("portable original native diagram control outcome differs")
    original_operation.admit_original_child(
        original_child,
        control,
        hashlib.sha256(original_pdf).hexdigest(),
        code,
        reader=reader,
        scope=raw["scope"],
        kind=raw["kind"],
        target=target,
    )
    current_positive.verify(deadline)
    pdfium_runtime.verify()
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("portable diagram control terminal custody or original deadline changed")
