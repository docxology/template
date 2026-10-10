"""Complete PDF Source occurrence predicates with actual whole-reference bytes.

The caller holds genuine original/current Source and native execution. Unknown
scientific/asset/raw predicates remain explicit blockers after page equality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_pdf_source_witness import inspect_pdf_source_witness
from infrastructure.reporting.native_format_scientific_pdf_observer import compile_scientific_pdf_assets
from infrastructure.reporting.native_pdf_whole_controls import compile_whole_pdf_control_requirements
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact


def observe_whole_pdf_source_predicates(
    root: Path,
    scope: str,
    artifact_id: str,
    inputs: PDFSourceInputs,
    ast: bytes,
    pdf: bytes,
    rasters: tuple[bytes, ...],
    reader: SnapshotReader,
    *,
    reference_pdf: bytes,
    reference_rasters: tuple[bytes, ...],
    whole_reference: dict[str, Any] | None = None,
    deadline: float,
) -> dict[str, Any]:
    """Apply complete Source predicates plus every-page glyph/vector/pixel parity.

    The full reference supplies geometry after genuine compile/FLS/SDK/process
    admission. It cannot replace independent scientific Math/Cite/raw analysis.
    """
    remaining(deadline)
    from infrastructure.reporting.native_pdf_whole_semantic_references import whole_pdf_semantic_inputs

    citation, mathematics, semantic_blockers = whole_pdf_semantic_inputs(
        inputs, ast, whole_reference, reader, deadline=deadline
    )
    plan = compile_pdf_semantic_plan(artifact_id, inputs.sources, ast, citation_reference=citation)
    asset_blockers = []
    try:
        assets = compile_scientific_pdf_assets(root, scope, inputs, plan, reader, deadline=deadline)
    except ProjectionSourceUnsupported as error:
        assets = {}
        asset_blockers.append(str(error))
    witness = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets={
            identity: (binding["path"], reader.read(binding["path"]).content) for identity, binding in assets.items()
        },
        full_source_reference={"pdf": reference_pdf, "rasters": reference_rasters, "source_plan_digest": plan.digest},
        citation_reference=citation,
        mathematical_inputs=mathematics,
        deadline=deadline,
    )
    controls = compile_whole_pdf_control_requirements(plan, witness, deadline=deadline)
    remaining(deadline)
    return {
        "schema_version": "template-native-whole-pdf-source-predicates-v2",
        "source_plan": plan.to_dict(),
        "assets": assets,
        "witness": witness,
        "control_requirements": controls,
        "blockers": [
            *inputs.blockers,
            *semantic_blockers,
            *asset_blockers,
            *witness["blockers"],
            *controls["remaining"],
        ],
        "findings": witness["findings"],
        "status": "fail" if witness["findings"] else "blocked",
    }


def observe_current_whole_pdf_predicates(
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raster: dict[str, Any],
    scientific: dict[str, Any],
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    pipeline_run_id: str,
    plan_digest: str,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Observe a supported full Source reference against the fresh Current PDF.

    The caller already admitted the separate Current Core/stage and Original.
    Reuse its actual AST and candidate raster. Source projections with missing
    figure/external/Mermaid inputs keep explicit residuals and no reference
    witness. This adjunct never changes the base observer or grants acceptance.
    """
    import json

    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_pdf_source import pdf_source_inputs
    from infrastructure.reporting.native_format_pdf_source_replay import replay_pdf_source_witness
    from infrastructure.reporting.native_format_pdf_whole_reference import observe_pdf_whole_reference
    from infrastructure.reporting.native_hydration_reconstruction import observe_native_pdf_recomposition
    from infrastructure.reporting.native_pdf_whole_semantic_references import whole_pdf_semantic_inputs
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation
    from infrastructure.project.public_acceptance_evidence import write_json

    owner = current_native_producer_operation()
    root = reader.root
    if (
        not isinstance(source, NativeSourceContext)
        or owner is None
        or owner.source is not source
        or reader.native_producer_operation is not owner
        or reader.native_operation is not None
        or root != source.bindings.current_root
        or deadline != owner.deadline
        or artifact.id != "manuscript:pdf"
        or artifact.format != "pdf"
        or snapshot.relative != artifact.path
        or reader.read(snapshot.relative) != snapshot
    ):
        raise ValueError("fresh Current whole PDF needs its actual Source/owner/artifact and existing clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    consumed = _file(raster["input_artifact"], reader)
    leaf = consumed.path.parent
    if (
        leaf.parent != owner.stage_scope_directory(scope) / "current-native-artifacts"
        or consumed.content != snapshot.content
        or raster["dpi"] != 150
        or len(raster["tool_artifacts"]) != 2
    ):
        raise ValueError("fresh Current whole PDF cannot substitute its actual candidate raster input")
    for binding, name, purpose, arguments in (
        (
            raster["tool_artifacts"][0],
            "pdftoppm",
            "raster-0000",
            ["-r", "150", "-png", str(leaf / "input-0000.pdf"), str(leaf / "raster-0000")],
        ),
        (raster["tool_artifacts"][1], "pdffonts", "fonts-0000", [str(leaf / "input-0000.pdf")]),
    ):
        _tool(binding, reader, owner.run_id, name, purpose, arguments)
    directory = leaf / "whole-source-current"
    create_private_native_directory(root, directory)
    inputs = pdf_source_inputs(root, directory / "source", scope, artifact, reader)
    old_source = scientific["source"]
    markdown, ast = _file(old_source["markdown"], reader), _file(old_source["ast"], reader)
    parser = _tool(
        old_source["parser_artifact"],
        reader,
        owner.run_id,
        "pandoc",
        "pdf-source-original-ast",
        [str(markdown.path), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"],
    )
    if markdown.content != inputs.content or parser["stdout"].encode() != ast.content:
        raise ValueError("fresh Current whole PDF requires the actual complete Source parser inputs/stdout")
    hydration, composed = observe_native_pdf_recomposition(
        source, scope, pipeline_run_id, plan_digest, reader, deadline=deadline
    )
    reference = None
    predicates = None
    blockers = [*hydration["unresolved_edges"], *inputs.blockers]
    if composed is None:
        blockers.append("fresh Current complete Source PDF hydration/composition body remains unresolved")
    elif composed != inputs.content:
        raise ValueError("fresh Current whole PDF differs from its independently reconstructed PDF composition")
    else:
        reference = observe_pdf_whole_reference(
            root,
            directory / "reference",
            inputs,
            ast.content,
            env=env,
            deadline=deadline,
            run_id=owner.run_id,
            sdk_context=json.loads(source.descriptor(scope, deadline=deadline)),
            source_scope=scope,
        )
        blockers.extend(reference["blockers"])
        # Authenticate real Current registrations before any byte interpreter.
        # The builder itself closes dependency/FLS and instrumentation custody.
        for binding in owner.retained_tool_bindings:
            owner.validate_tool(binding, _file(binding, reader).json_object(), reader, run_id=owner.run_id)
        native = reference.get("references", {}).get("uninstrumented")
        if native is None or "rasters" not in native:
            blockers.append("fresh Current Source reference has no complete native every-page observations")
        else:
            candidate_rasters = tuple(
                _file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in raster["rasters"]
            )
            predicates = observe_whole_pdf_source_predicates(
                root,
                scope,
                artifact.id,
                inputs,
                ast.content,
                snapshot.content,
                candidate_rasters,
                reader,
                reference_pdf=_file(native["pdf"], reader).content,
                reference_rasters=tuple(_file(binding, reader).content for binding in native["rasters"]),
                whole_reference=reference,
                deadline=deadline,
            )
            citation, mathematics, _ = whole_pdf_semantic_inputs(
                inputs, ast.content, reference, reader, deadline=deadline
            )
            portable_math = None
            if mathematics is not None:
                interpreted = reference["semantic_references"]["mathematics"]
                portable_math = {
                    "source_tex": reference["projection"]["source_tex"],
                    "instrumented_pdf": reference["references"]["instrumented"]["pdf"],
                    "interpreted_pdf": interpreted["reference"]["pdf"],
                    "interpreted_rasters": [
                        {"path": row["path"], "sha256": row["sha256"]} for row in interpreted["raster"]["rasters"]
                    ],
                }
            replay_pdf_source_witness(
                predicates["witness"],
                artifact_id=artifact.id,
                sources=inputs.sources,
                ast_bytes=ast.content,
                pdf={"path": snapshot.relative, "sha256": snapshot.sha256},
                rasters=tuple({"path": row["path"], "sha256": row["sha256"]} for row in raster["rasters"]),
                assets=predicates["assets"],
                read_artifact=lambda binding: _file(binding, reader).content,
                citation_reference=citation,
                mathematical_inputs=portable_math,
                full_source_reference={
                    "pdf": native["pdf"],
                    "rasters": tuple(native["rasters"]),
                    "source_plan_digest": predicates["witness"]["source_plan_digest"],
                },
                deadline=deadline,
            )
    source.verify_correspondence(source.reference, root, reader, deadline)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    if not reader.unchanged():
        raise ValueError("fresh Current whole PDF Source/reference/native inputs changed across replay")
    remaining(deadline)
    return {
        "reference": None if reference is None else write_json(root, directory / "reference.json", reference),
        "source_predicates": predicates,
        "blockers": blockers,
    }
