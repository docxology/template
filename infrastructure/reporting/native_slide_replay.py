"""Independent portable current-source manuscript slide reference readback."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_slide_checks import inspect_manuscript_slide_reference
from infrastructure.reporting.native_slide_source import compile_slide_source_contract, instrument_slide_source
from infrastructure.reporting.native_slide_reference import (
    manuscript_slide_source_plan,
    observe_manuscript_slide_source,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def replay_manuscript_slide_reference(
    root: Path,
    scope: str,
    artifact: NativeArtifact,
    candidate_pdf: bytes,
    candidate_rasters: tuple[bytes, ...],
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    read_artifact: Callable[[dict[str, str]], bytes],
    validate_original_tool: Callable[[dict[str, Any]], None],
    env: dict[str, str],
    deadline: float,
    run_id: str,
    reference_displays: dict[str, str] | None = None,
    source_reference_numbers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Reparse source independently; original host paths/fonts are never accessed.

    The enclosing authenticated native specification must supply original tool
    validation (actual worker/source/provider/executable/guardian linkage) and
    exact artifact transport validation. Receipt status fields grant no authority.
    Fresh current Pandoc source parsing is mandatory; recorded ASTs alone cannot
    substitute for independent current source reconstruction.
    """
    plan = manuscript_slide_source_plan(root, scope, artifact, reader)
    source = raw["source"]
    if source.get("plan") != plan.record():
        raise ValueError("portable slide source plan differs from complete current source DATA")
    # The selected reader's provider performs its own finite parse using the
    # same held source DATA. Transport/process bindings vary; source semantics
    # and original occurrence multiplicity may not.
    with tempfile.TemporaryDirectory(prefix="native-slide-source-replay-", dir=root / "output/readiness") as private:
        directory = Path(private) / "source"
        # Source plan contains explicit immutable Path consumers in `root`;
        # they never appear on Python's import path and remain read-only.
        independent = observe_manuscript_slide_source(
            root,
            directory,
            plan,
            env=env,
            deadline=deadline,
            run_id=run_id,
            reference_displays=reference_displays,
        )
    for field in ("contract", "original_contract", "reference_displays"):
        if source.get(field) != independent.get(field):
            raise ValueError("portable slide original/resolved source semantics differ")
    for binding in source["tool_artifacts"]:
        validate_original_tool(json.loads(read_artifact(binding)))
    ast = read_artifact(source["ast"])
    read_artifact(source["original_ast"])
    if (
        independent["ast"]["sha256"] != source["ast"]["sha256"]
        or independent["original_ast"]["sha256"] != source["original_ast"]["sha256"]
    ):
        raise ValueError("portable original/resolved native source parse bytes differ")
    reference = raw["reference"]
    if reference.get("source_reference_numbers") != (source_reference_numbers or {}):
        raise ValueError("portable slide whole-source numeric reference admission differs")
    if plan.profile == "accessible":
        import yaml
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering._slides_accessibility_composition import compose_accessible_pandoc_document

        config = RenderingConfig.from_project_config(yaml.safe_load(plan.config[1]), env={})
        composed = compose_accessible_pandoc_document(
            json.loads(ast),
            policy=config.accessible_slide_policy(),
            source=plan.source[0],
            authorized_image_roots=(plan.manuscript_directory, plan.figures_directory),
            figure_image_root=plan.figures_directory,
        )
        ast = (json.dumps(composed.document, sort_keys=True, ensure_ascii=False) + "\n").encode()
    initial_contract = compile_slide_source_contract(
        plan.artifact_id,
        (plan.source, plan.config, *plan.bibliographies),
        ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=reference_displays,
    )
    # Authenticate the actual source-only auxiliary output before it can bind
    # local deck counters. Its source TeX is independently regenerated below.
    recorded_source = reference["references"]["source"]
    for binding in recorded_source["tool_artifacts"]:
        validate_original_tool(json.loads(read_artifact(binding)))
    from infrastructure.reporting.native_slide_tex_source import (
        archive_source_section_labels,
        source_slide_reference_displays,
    )

    archive_labels = archive_source_section_labels(ast) if plan.profile == "archive" else ()
    if reference.get("archive_source_section_labels") != list(archive_labels):
        raise ValueError("portable archive section-label fallback census differs")

    with tempfile.TemporaryDirectory(prefix="native-slide-label-replay-") as private:
        auxiliary = Path(private) / "source-only.aux"
        auxiliary.write_bytes(read_artifact(recorded_source["aux"]))
        displays = source_slide_reference_displays(
            read_artifact(recorded_source["writer_tex"]).decode(),
            auxiliary,
            initial_contract,
            source_reference_numbers,
            reference_displays,
            archive_section_labels=archive_labels,
        )
    if reference.get("reference_displays") != displays:
        raise ValueError("portable source-only local/foreign reference display differs")
    contract = compile_slide_source_contract(
        plan.artifact_id,
        (plan.source, plan.config, *plan.bibliographies),
        ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=displays,
    )
    marked, bindings = instrument_slide_source(ast, contract, target="beamer")
    if reference.get("contract") != contract.record() or reference.get("bindings") != json.loads(
        json.dumps(list(bindings))
    ):
        raise ValueError("portable complete native source reference contract/markers differ")
    for label, expected_ast in (("source", ast), ("marked", marked)):
        recorded = reference["references"][label]
        if read_artifact(recorded["ast"]) != expected_ast:
            raise ValueError("portable native reference compiled a different source AST")
        for binding in recorded["tool_artifacts"]:
            validate_original_tool(json.loads(read_artifact(binding)))
        if recorded["dependencies"] != reference["dependency_before"]:
            raise ValueError("portable source reference dependency ledger differs")
        custody = recorded.get("dependency_custody", {})
        if custody.get("before") != recorded["dependencies"] or custody.get("after") != recorded["dependencies"]:
            raise ValueError("portable source reference lacks fresh native dependency custody")
        if recorded.get("writer_dependencies_before") != recorded.get("writer_dependencies_after"):
            raise ValueError("portable source writer/filter/header dependencies changed")
    if reference.get("dependency_before") != reference.get("dependency_after"):
        raise ValueError("portable source native style/font inputs changed during original observation")
    _reconstruct_writer(
        root,
        plan,
        ast,
        marked,
        reference,
        read_artifact,
        env=env,
        deadline=deadline,
        run_id=run_id,
        source_reference_numbers=source_reference_numbers,
    )

    def native(label: str) -> tuple[bytes, tuple[bytes, ...]]:
        recorded = reference["references"][label]
        pdf = read_artifact(recorded["pdf"])
        for tool in recorded["raster"]["tool_artifacts"]:
            validate_original_tool(json.loads(read_artifact(tool["artifact"])))
        rasters = tuple(
            read_artifact({"path": r["path"], "sha256": r["sha256"]}) for r in recorded["raster"]["rasters"]
        )
        return pdf, rasters

    pdf, pixels = native("source")
    marked_pdf, marked_pixels = native("marked")
    from infrastructure.reporting.native_slide_assets import source_slide_images

    source_images = source_slide_images(root, plan, contract, reader)
    observed = inspect_manuscript_slide_reference(
        candidate_pdf,
        candidate_rasters,
        pdf,
        pixels,
        marked_pdf,
        marked_pixels,
        contract,
        bindings,
        deadline=deadline,
        source_images=source_images,
    )
    if raw.get("observation") != observed:
        raise ValueError("portable native slide source/paint/noninterference/page replay differs")
    if not reader.unchanged():
        raise ValueError("portable current slide source DATA changed during readback")
    return observed


def _reconstruct_writer(
    root: Path,
    plan: Any,
    ast: bytes,
    marked: bytes,
    reference: dict[str, Any],
    read_artifact: Callable[[dict[str, str]], bytes],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference_numbers: dict[str, str] | None,
) -> None:
    """Fresh Pandoc source writers must reproduce actual original TeX outputs."""
    import yaml
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
    from infrastructure.reporting.native_slide_tex_runtime import prepare_source_beamer_writer

    config = RenderingConfig.from_project_config(yaml.safe_load(plan.config[1]), env={})
    depths = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Header":
                depths.append(int(value["c"][0]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(json.loads(ast))
    level = 2 if plan.profile == "accessible" else min(4, max(depths, default=2))
    if reference.get("slide_level") != level:
        raise ValueError("portable writer used a different original source heading level")
    current_roots = (plan.manuscript_directory, plan.figures_directory)
    original_roots = reference.get("resource_roots", [])
    if [item.get("relative") for item in original_roots] != [p.relative_to(root).as_posix() for p in current_roots]:
        raise ValueError("portable writer's original source resource consumers differ")

    def normalized(content: bytes, roots: tuple[Path, ...]) -> bytes:
        text = content.decode()
        for index, path in enumerate(roots):
            text = text.replace(path.as_posix(), f"<SOURCE-RESOURCE-{index}>")
        return text.encode()

    with tempfile.TemporaryDirectory(prefix="native-slide-writer-replay-", dir=root / "output/readiness") as private:
        for label, document in (("source", ast), ("marked", marked)):
            runtime = CitationRuntime(root, Path(private) / label, env=env, deadline=deadline, run_id=run_id)
            prepared = prepare_source_beamer_writer(runtime, plan, config, document, level, source_reference_numbers)
            recorded = reference["references"][label]
            old_roots = tuple(Path(item["absolute"]) for item in original_roots)
            for field in ("writer_tex", "tex"):
                if normalized(runtime.read(prepared[field]), current_roots) != normalized(
                    read_artifact(recorded[field]), old_roots
                ):
                    raise ValueError("portable fresh source-owned Pandoc/transform TeX differs")
