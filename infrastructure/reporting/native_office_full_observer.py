"""Actual complete-source native Office observation with explicit source witnesses."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeArtifact,
    create_private_native_directory,
)
from infrastructure.reporting.native_office_content_witness import (
    inspect_office_source_survival,
)
from infrastructure.reporting.native_office_reference import (
    build_office_source_reference,
    inspect_office_package_reference,
    read_office_package_ast,
)
from infrastructure.reporting.native_office_reference_visual import (
    inspect_office_reference_projection,
    observe_reference_conversion,
)
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)

from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
)

from infrastructure.reporting.native_office_diagram_binding import (
    admitted_office_diagram_sources,
    diagram_visibility_residuals,
    diagram_witness_budget,
    diagram_witness_runtime,
)

from infrastructure.reporting.native_office_diagram_visibility import (
    observe_office_diagram_visibility,
)

SCHEMA = "template-native-office-complete-source-observer-v2"


def office_full_outcome(
    source: dict[str, Any],
    survival: dict[str, Any],
    reference_survival: dict[str, Any],
    package: dict[str, Any],
    projection: dict[str, Any],
    diagram_visibility: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combine actual independently reconstructed checks, retaining all residuals.

    The enclosing acceptance gate must additionally admit genuine supervised
    scientific and layout controls. This observer does not grant that gate.
    """
    diagrams = tuple((diagram_visibility or {}).values())
    findings = [
        row for result in (survival, reference_survival, package, projection, *diagrams) for row in result["findings"]
    ]
    blockers = [
        *source["blockers"],
        *survival["blockers"],
        *reference_survival["blockers"],
        *diagram_visibility_residuals(source, diagram_visibility),
        *(reason for result in diagrams for reason in result["blockers"]),
    ]
    return {
        "schema_version": SCHEMA,
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "findings": findings,
        "blockers": list(dict.fromkeys(blockers)),
        "source_survival": survival,
        "reference_source_survival": reference_survival,
        "package_parity": package,
        "native_page_parity": projection,
        "native_diagram_visibility": None
        if diagram_visibility is None
        else {
            name: {
                key: result[key]
                for key in (
                    "schema_version",
                    "pdf_sha256",
                    "status",
                    "findings",
                    "blockers",
                )
            }
            for name, result in diagram_visibility.items()
        },
        "assurance": (
            "complete independently accounted source/package content and actual all-page native glyph/vector/pixel "
            "comparison; supervised controls remain mandatory"
        ),
    }


def observe_office_full_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
    mermaid_admission: OfficeMermaidAdmission | None = None,
) -> dict[str, Any]:
    """Read every original source occurrence and convert both genuine packages.

    Source reference construction cannot consume the candidate. All actual
    package readers, LibreOffice/Calibre, EPUBCheck and original raster/font
    processes retain their existing receipts and before/after runtime custody.
    """
    if artifact.format not in {"docx", "epub"} or artifact.id != f"manuscript:{artifact.format}":
        raise ValueError("complete Office source observer requires configured combined manuscript")
    leaves = {
        name: directory / name
        for name in (
            "source-reference",
            "reference-readback",
            "candidate-readback",
            "reference-native",
            "candidate-native",
        )
    }
    for leaf in leaves.values():
        create_private_native_directory(root, leaf)
    reference = build_office_source_reference(
        root,
        leaves["source-reference"],
        scope,
        artifact,
        reader,
        env=env,
        deadline=deadline,
        run_id=run_id,
        mermaid_admission=mermaid_admission,
    )
    candidate = {"path": snapshot.relative, "sha256": snapshot.sha256}
    readbacks = {
        name: read_office_package_ast(
            root,
            leaves[f"{name}-readback"],
            package,
            artifact.format,
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
        for name, package in (
            ("reference", reference["package"]),
            ("candidate", candidate),
        )
    }
    native = {
        name: observe_reference_conversion(
            root,
            leaves[f"{name}-native"],
            package,
            artifact.format,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_engine=frozen_epub_engine,
        )
        for name, package in (
            ("reference", reference["package"]),
            ("candidate", candidate),
        )
    }
    import yaml

    source = reference["source"]
    unfiltered = reader.read(source["source_coverage_ast"]["path"]).content
    filtered = reader.read(source["ast"]["path"]).content
    reference_ast = reader.read(readbacks["reference"]["ast"]["path"]).content
    candidate_ast = reader.read(readbacks["candidate"]["ast"]["path"]).content
    figures = tuple(reader.read(row["consumed"]["path"]).content for row in reference["figures"])
    metadata = yaml.safe_load(reader.read(reference["metadata"]["path"]).content)
    reference_package = reader.read(reference["package"]["path"]).content
    cover = reader.read(reference["cover"]["consumed"]["path"]).content if reference["cover"] else None
    survival = inspect_office_source_survival(
        unfiltered,
        filtered,
        candidate_ast,
        snapshot.content,
        artifact.format,
        figures,
        metadata,
        cover,
    )
    reference_survival = inspect_office_source_survival(
        unfiltered,
        filtered,
        reference_ast,
        reference_package,
        artifact.format,
        figures,
        metadata,
        cover,
    )
    parity = inspect_office_package_reference(reference_ast, candidate_ast, source["source_coverage"])
    # Legacy reference parity intentionally has unresolved census blockers.
    # Replace them only with the independent source survival result above.
    package_parity = {
        **parity,
        "status": "failed" if parity["findings"] else "observed",
        "blockers": [],
    }
    pdfs = {name: reader.read(row["conversion"]["pdf"]["path"]).content for name, row in native.items()}
    rasters = {
        name: tuple(reader.read(row["path"]).content for row in value["raster"]["rasters"])
        for name, value in native.items()
    }
    projection = inspect_office_reference_projection(
        pdfs["reference"],
        rasters["reference"],
        pdfs["candidate"],
        rasters["candidate"],
        deadline=deadline,
    )
    diagram_visibility = None
    if source["mermaid"] is not None:
        diagram_sources = admitted_office_diagram_sources(source, scope, reader, mermaid_admission)
        diagram_visibility = {
            name: observe_office_diagram_visibility(
                root,
                directory / f"{name}-diagram-visibility",
                data,
                rasters[name],
                diagram_sources,
                budget=diagram_witness_budget(mermaid_admission),
                pdfium_runtime=diagram_witness_runtime(mermaid_admission, deadline),
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
            for name, data in pdfs.items()
        }
    result = office_full_outcome(
        source,
        survival,
        reference_survival,
        package_parity,
        projection,
        diagram_visibility,
    )
    from infrastructure.reporting.native_office_image_ink import (
        inspect_office_cover,
        inspect_office_native_images,
    )

    assets = figures
    covers = None
    if reference["cover"]:
        cover = reader.read(reference["cover"]["consumed"]["path"]).content
        assets = (cover, *figures)
        covers = {
            name: inspect_office_cover(data, cover, reference["cover"]["alt"])
            for name, data in (
                ("reference", reference_package),
                ("candidate", snapshot.content),
            )
        }
    image_ink = {name: inspect_office_native_images(data, assets, deadline=deadline) for name, data in pdfs.items()}
    result["native_source_images"] = image_ink
    result["covers"] = covers
    for extra in (*image_ink.values(), *(covers or {}).values()):
        result["findings"].extend(extra["findings"])
        result["blockers"].extend(extra["blockers"])
    result["status"] = "failed" if result["findings"] else "blocked" if result["blockers"] else "observed"
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("complete Office original source/package/native custody changed")
    return {
        "schema_version": SCHEMA,
        "reference": reference,
        "readbacks": readbacks,
        "native": native,
        "diagram_visibility": diagram_visibility,
        "observation": result,
    }
