"""Bounded actual source-only Beamer references with complete source custody."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_slide_source import (
    SlideSourceContract,
    compile_slide_source_contract,
    instrument_slide_source,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class SlideSourcePlan:
    source: tuple[str, bytes]
    config: tuple[str, bytes]
    bibliographies: tuple[tuple[str, bytes], ...]
    manuscript_directory: Path
    figures_directory: Path
    profile: str
    title_font_pt: float
    body_font_pt: float
    artifact_id: str
    data_root: Path

    def record(self) -> dict[str, Any]:
        return {
            "schema_version": "template-native-slide-source-plan-v1",
            "artifact_id": self.artifact_id,
            "profile": self.profile,
            "title_font_pt": self.title_font_pt,
            "body_font_pt": self.body_font_pt,
            "source": {"path": self.source[0], "sha256": hashlib.sha256(self.source[1]).hexdigest()},
            "config": {"path": self.config[0], "sha256": hashlib.sha256(self.config[1]).hexdigest()},
            "bibliographies": [{"path": p, "sha256": hashlib.sha256(b).hexdigest()} for p, b in self.bibliographies],
        }


def manuscript_slide_source_plan(
    root: Path, scope: str, artifact: NativeArtifact, reader: SnapshotReader
) -> SlideSourcePlan:
    """Select exactly the current hydrated source-owned section, without output reads."""
    import yaml
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.rendering._bibliography import resolve_bibliography
    from infrastructure.validation.output.render_formats import render_config_manuscript_dir
    from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance

    if scope not in PUBLIC_PROJECT_NAMES or not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("manuscript slides require exact admitted current source hydration")
    kind = "slides" if artifact.format == "pdf" else "reveal" if artifact.format == "html" else ""
    parts = artifact.id.split(":")
    if len(parts) != 3 or parts[0] != "section" or parts[2] != kind or not kind:
        raise ValueError("manuscript slide artifact is outside its source-owned exact identities")
    project = root / "projects" / scope
    config_snapshot = reader.read(f"projects/{scope}/manuscript/config.yaml")
    config = RenderingConfig.from_project_config(yaml.safe_load(config_snapshot.content), env={})
    if not config.enable_slides or (kind == "reveal" and config.slides_profile != "accessible"):
        raise ValueError("manuscript slide artifact is not enabled by its current source configuration")
    manuscript = render_config_manuscript_dir(project)
    matches = [
        p
        for p in discover_manuscript_files(manuscript)
        if p.relative_to(manuscript).as_posix() == parts[1] and p.suffix == ".md"
    ]
    if len(matches) != 1:
        raise ValueError("manuscript slide source selection is missing or ambiguous")
    snapshot = reader.read(matches[0].relative_to(root).as_posix())
    if b"<!-- render:skip-beamer -->" in snapshot.content:
        raise ValueError("manuscript slide source is explicitly outside projection selection")
    expected = f"projects/{scope}/output/slides/{matches[0].stem}_slides.{artifact.format}"
    if artifact.path != expected:
        raise ValueError("manuscript slide path differs from its current source-owned exact path")
    bibs = tuple(
        (s.relative, s.content)
        for s in (reader.read(p.relative_to(root).as_posix()) for p in resolve_bibliography(manuscript))
    )
    preamble = manuscript / "preamble.md"
    if preamble.exists():
        reader.read(preamble.relative_to(root).as_posix())
    if not reader.unchanged():
        raise ValueError("manuscript slide source changed during exact source admission")
    return SlideSourcePlan(
        (snapshot.relative, snapshot.content),
        (config_snapshot.relative, config_snapshot.content),
        bibs,
        manuscript,
        project / "output/figures",
        config.slides_profile,
        float(config.slides_title_font_pt),
        float(config.slides_body_font_pt),
        artifact.id,
        root,
    )


def _bind(root: Path, path: Path, reader: SnapshotReader) -> dict[str, str]:
    snapshot = reader.read(path.relative_to(root).as_posix())
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def observe_manuscript_slide_source(
    root: Path,
    directory: Path,
    plan: SlideSourcePlan,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    reference_displays: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Actual source/bibliography parsing, retaining both original and citeproc ASTs."""
    from infrastructure.rendering._bibliography import pandoc_bibliography_args
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    if time.monotonic() >= deadline:
        raise TimeoutError("manuscript slide source exhausted original deadline")
    create_private_native_directory(root, directory)
    runtime = CitationRuntime(root, directory / "parser", env=env, deadline=deadline, run_id=run_id)
    source = runtime.freeze("original-source.md", plan.source[1])
    frozen_bibs = tuple(
        runtime.freeze(f"source-{number:03d}.bib", content) for number, (_, content) in enumerate(plan.bibliographies)
    )
    bibliography_args = (
        ["--citeproc", *pandoc_bibliography_args(frozen_bibs), "--metadata", "suppress-bibliography=true"]
        if frozen_bibs
        else []
    )
    # Original source nodes remain available for complete citation/key/raw census.
    original = runtime.tool("pandoc", [str(source), "--to=json"], "original-source-ast", input_paths=(source,))
    resolved = runtime.tool(
        "pandoc",
        [str(source), "--to=json", *bibliography_args],
        "resolved-source-ast",
        input_paths=(source, *frozen_bibs),
    )
    original_ast = original["stdout"].encode()
    resolved_document = json.loads(resolved["stdout"])
    # These exact command-generated metadata paths are consumed by citeproc;
    # they are not publication source metadata and cannot leak producer paths
    # into the independently reconstructed portable AST.
    if frozen_bibs:
        resolved_document.get("meta", {}).pop("bibliography", None)
        resolved_document.get("meta", {}).pop("suppress-bibliography", None)
    ast = (json.dumps(resolved_document, sort_keys=True, ensure_ascii=False) + "\n").encode()
    source_inputs = (plan.source, plan.config, *plan.bibliographies)
    original_contract = compile_slide_source_contract(
        plan.artifact_id,
        source_inputs,
        original_ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=reference_displays,
    )
    contract = compile_slide_source_contract(
        plan.artifact_id,
        source_inputs,
        ast,
        profile=plan.profile,
        title_font_pt=plan.title_font_pt,
        body_font_pt=plan.body_font_pt,
        reference_displays=reference_displays,
    )

    def keys(value: SlideSourceContract) -> list[str]:
        return [row.source for row in value.occurrences if row.kind == "citation"]

    if keys(original_contract) != keys(contract):
        raise ValueError("slide citeproc changed or omitted an original source citation identity")
    ast_path = directory / "resolved-source.ast.json"
    original_path = directory / "original-source.ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    atomic_write_bytes_confined(root, original_path, original_ast, mode=0o600)
    reader = SnapshotReader(root)
    runtime.unchanged()
    return {
        "schema_version": "template-native-slide-source-observation-v1",
        "plan": plan.record(),
        "original_ast": _bind(root, original_path, reader),
        "ast": _bind(root, ast_path, reader),
        "original_contract": original_contract.record(),
        "contract": contract.record(),
        "reference_displays": reference_displays or {},
        "tool_artifacts": runtime.tools,
    }


def compile_beamer_source_reference(
    root: Path,
    directory: Path,
    plan: SlideSourcePlan,
    ast: bytes,
    contract: SlideSourceContract,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference_numbers: dict[str, str] | None = None,
    reference_displays: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compile exact unmarked/marked source with observed before/after dependencies.

    Actual XeTeX/xdvipdfmx FLS and successful file-open observations provide font
    and style hashes. No installed dependency or font binary is redistributed.
    Every process inherits the original caller deadline and existing120s ceiling.
    """
    import yaml
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering._slides_accessibility import compose_accessible_pandoc_document
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    create_private_native_directory(root, directory)
    if any("independent source reference display required" not in item for item in contract.blockers):
        raise ValueError("source Beamer reference has unadmitted original source forms or expansions")
    config = RenderingConfig.from_project_config(yaml.safe_load(plan.config[1]), env={})
    from infrastructure.reporting.native_slide_assets import source_slide_images, freeze_source_slide_figures

    asset_reader = SnapshotReader(root)
    source_images = source_slide_images(root, plan, contract, asset_reader)
    freeze_source_slide_figures(root, directory / "figures", source_images)
    original = ast
    composition_record = None
    if plan.profile == "accessible":
        composition = compose_accessible_pandoc_document(
            json.loads(ast),
            policy=config.accessible_slide_policy(),
            source=plan.source[0],
            authorized_image_roots=(plan.manuscript_directory, plan.figures_directory),
            figure_image_root=plan.figures_directory,
        )
        original = (json.dumps(composition.document, sort_keys=True, ensure_ascii=False) + "\n").encode()
        # Accessible composition has explicit source-owned excerpt/reader policy.
        # The enclosing reader must independently recompose; no original-source
        # occurrence can be erased by supplying a recorded composed document.
        contract = compile_slide_source_contract(
            plan.artifact_id,
            (plan.source, plan.config, *plan.bibliographies),
            original,
            profile=plan.profile,
            title_font_pt=plan.title_font_pt,
            body_font_pt=plan.body_font_pt,
            reference_displays=reference_displays,
        )
        composition_record = {
            "frame_count": composition.frame_count,
            "source_ast_sha256": hashlib.sha256(ast).hexdigest(),
            "composed_ast_sha256": hashlib.sha256(original).hexdigest(),
        }
    marked, bindings = instrument_slide_source(original, contract, target="beamer")
    references = {}
    depths: list[int] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Header":
                depths.append(int(value["c"][0]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(json.loads(original))
    level = 2 if plan.profile == "accessible" else min(4, max(depths, default=2))
    dependencies_before = None
    displays = dict(reference_displays or {})
    from infrastructure.reporting.native_slide_tex_source import archive_source_section_labels

    archive_labels = archive_source_section_labels(original) if plan.profile == "archive" else ()
    for label in ("source", "marked"):
        if label == "marked":
            contract = compile_slide_source_contract(
                plan.artifact_id,
                (plan.source, plan.config, *plan.bibliographies),
                original,
                profile=plan.profile,
                title_font_pt=plan.title_font_pt,
                body_font_pt=plan.body_font_pt,
                reference_displays=displays,
            )
            marked, bindings = instrument_slide_source(original, contract, target="beamer")
        document = original if label == "source" else marked
        runtime = CitationRuntime(root, directory / label, env=env, deadline=deadline, run_id=run_id)
        from infrastructure.reporting.native_slide_tex_runtime import prepare_source_beamer_writer

        prepared = prepare_source_beamer_writer(runtime, plan, config, document, level, source_reference_numbers)
        input_ast, tex_path, original_writer = (prepared[k] for k in ("ast", "tex", "writer_tex"))
        from infrastructure.reporting.native_slide_tex_runtime import compile_source_slide_tex
        from infrastructure.reporting.native_slide_tex_source import source_slide_reference_displays

        dependency_custody = compile_source_slide_tex(runtime, tex_path)
        external = dependency_custody["before"]
        if label == "source":
            displays = source_slide_reference_displays(
                runtime.read(original_writer).decode(),
                runtime.directory / "oracle.aux",
                contract,
                source_reference_numbers,
                displays,
                archive_section_labels=archive_labels,
            )
        if dependencies_before is None:
            dependencies_before = external
        elif dependencies_before != external:
            raise ValueError("source/marked Beamer native styles or fonts changed during original observation")
        reader = SnapshotReader(root)
        pdf = reader.read((runtime.directory / "oracle.pdf").relative_to(root).as_posix())
        raster = audit_pdf_raster(
            root,
            runtime.directory,
            pdf,
            parse_native_bytes("pdf", pdf.content),
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
        references[label] = {
            "ast": _bind(root, input_ast, reader),
            "tex": _bind(root, tex_path, reader),
            "writer_tex": _bind(root, original_writer, reader),
            "pdf": {"path": pdf.relative, "sha256": pdf.sha256},
            "raster": raster,
            "tool_artifacts": runtime.tools,
            "dependencies": external,
            "dependency_custody": dependency_custody,
            "writer_dependencies_before": prepared["dependencies_before"],
            "writer_dependencies_after": prepared["dependencies_after"],
            "aux": _bind(root, runtime.directory / "oracle.aux", reader),
            "log": _bind(root, runtime.directory / "oracle.log", reader),
        }
        runtime.unchanged()
    if time.monotonic() >= deadline:
        raise TimeoutError("source Beamer reference exhausted original deadline")
    if not asset_reader.unchanged():
        raise ValueError("source slide original figure assets changed during native compilation")
    return {
        "schema_version": "template-native-beamer-source-reference-v1",
        "contract": contract.record(),
        "bindings": list(bindings),
        "composition": composition_record,
        "slide_level": level,
        "source_reference_numbers": source_reference_numbers or {},
        "reference_displays": displays,
        "archive_source_section_labels": list(archive_labels),
        "resource_roots": [
            {"absolute": str(p), "relative": p.relative_to(plan.data_root).as_posix()}
            for p in (plan.manuscript_directory, plan.figures_directory)
        ],
        "references": references,
        "dependency_before": dependencies_before,
        "dependency_after": external,
    }


def re_unsafe_tex(tex: str) -> bool:
    """Reject source-independent I/O; declared Pandoc graphics remain explicit inputs."""
    import re

    return bool(re.search(r"\\(?:write18|openin|openout|catcode)\b", tex))
