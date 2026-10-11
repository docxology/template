"""Source-aware complete manuscript projection adapter for native dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_slide_reference import (
    manuscript_slide_source_plan,
    observe_manuscript_slide_source,
    compile_beamer_source_reference,
)
from infrastructure.reporting.native_slide_source import compile_slide_source_contract, instrument_slide_source
from infrastructure.reporting.native_slide_checks import inspect_manuscript_slide_reference
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def observe_manuscript_projection(
    root: Path,
    leaf: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    reference_displays: dict[str, str] | None = None,
    source_reference_numbers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """All declared native Beamer pages, source occurrences and reference pixels.

    `leaf` is the original fresh observer directory admitted by the dispatcher.
    Unknown source constructs remain explicit source diagnostics. Setup/tool
    failures propagate; they cannot be promoted into controlled oracle failures.
    """
    if artifact.format != "pdf" or not artifact.id.endswith(":slides") or snapshot.relative != artifact.path:
        raise ValueError("manuscript projection adapter requires its exact current native Beamer artifact")
    plan = manuscript_slide_source_plan(root, scope, artifact, reader)
    source = observe_manuscript_slide_source(
        root, leaf / "source", plan, env=env, deadline=deadline, run_id=run_id, reference_displays=reference_displays
    )
    ast = reader.read(source["ast"]["path"]).content
    contract = compile_slide_source_contract(
        artifact.id,
        (plan.source, plan.config, *plan.bibliographies),
        ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=reference_displays,
    )
    reference = compile_beamer_source_reference(
        root,
        leaf / "reference",
        plan,
        ast,
        contract,
        env=env,
        deadline=deadline,
        run_id=run_id,
        source_reference_numbers=source_reference_numbers,
        reference_displays=reference_displays,
    )
    reference_displays = reference["reference_displays"]
    projected_ast = ast
    if plan.profile == "accessible":
        import yaml
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering._slides_accessibility import compose_accessible_pandoc_document

        config = RenderingConfig.from_project_config(yaml.safe_load(plan.config[1]), env={})
        composed = compose_accessible_pandoc_document(
            json.loads(ast),
            policy=config.accessible_slide_policy(),
            source=plan.source[0],
            authorized_image_roots=(plan.manuscript_directory, plan.figures_directory),
            figure_image_root=plan.figures_directory,
        )
        projected_ast = (json.dumps(composed.document, sort_keys=True, ensure_ascii=False) + "\n").encode()
        contract = compile_slide_source_contract(
            artifact.id,
            (plan.source, plan.config, *plan.bibliographies),
            projected_ast,
            profile=plan.profile,
            title_font_pt=plan.title_font_pt,
            body_font_pt=plan.body_font_pt,
            reference_displays=reference_displays,
        )
    contract = compile_slide_source_contract(
        artifact.id,
        (plan.source, plan.config, *plan.bibliographies),
        projected_ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=reference_displays,
    )
    _, bindings = instrument_slide_source(projected_ast, contract, target="beamer")
    raster = audit_pdf_raster(
        root,
        leaf,
        snapshot,
        parse_native_bytes("pdf", snapshot.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])

    def native(label: str) -> tuple[bytes, tuple[bytes, ...]]:
        recorded = reference["references"][label]
        return reader.read(recorded["pdf"]["path"]).content, tuple(
            reader.read(row["path"]).content for row in recorded["raster"]["rasters"]
        )

    reference_pdf, reference_pixels = native("source")
    marked_pdf, marked_pixels = native("marked")
    from infrastructure.reporting.native_slide_assets import source_slide_images

    images = source_slide_images(root, plan, contract, reader)
    observed = inspect_manuscript_slide_reference(
        snapshot.content,
        pixels,
        reference_pdf,
        reference_pixels,
        marked_pdf,
        marked_pixels,
        contract,
        bindings,
        deadline=deadline,
        source_images=images,
    )
    if not reader.unchanged():
        raise ValueError("complete current source projection custody changed during native observation")
    return {"source": source, "reference": reference, "raster": raster, "observation": observed}
