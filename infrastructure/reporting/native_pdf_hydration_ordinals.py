"""One annotated Source parser under the existing live Original/Current owner.

This joins exact hydration byte ordinals to an admitted complete unfiltered AST.
It executes no Core/Common/render/raster and creates no owner. Existing whole
native occurrence, scientific, loader, controls and closing predicates remain
required; the returned DATA alone cannot clear any native-location residual.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE
from infrastructure.rendering._pdf_title_page_config import _rendering_options
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts, require_shared_hydration
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_complete_ordinal_ast_equivalence,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_hydration_reconstruction import observe_native_pdf_recomposition
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PARSER_ARGUMENTS = ("--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json")
PURPOSE = "source-hydration-ordinal-ast"


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def observe_pdf_hydration_ordinals(
    scope: str,
    inputs: PDFSourceInputs,
    hydration: dict[str, Any],
    parser_markdown: ArtifactSnapshot,
    parser_ast: ArtifactSnapshot,
    parser_tool: dict[str, str],
    reader: SnapshotReader,
    runtime: CitationRuntime,
    *,
    source: NativeSourceContext,
) -> dict[str, Any]:
    """Reuse actual composition/preprocessing and one genuine Pandoc ToolAPI.

    Caller supplies the direct PDFSourceInputs and independently authenticated
    unfiltered parser input/result, never candidate AST or receipt-created
    authority. This call runs once per actual complete parser input, shared by
    all selected values and qualified native occurrence consumers.
    """
    owner = current_native_producer_operation()
    if (
        not isinstance(source, NativeSourceContext)
        or not isinstance(inputs, PDFSourceInputs)
        or type(runtime) is not CitationRuntime
        or owner is None
        or owner.source is not source
        or reader.native_producer_operation is not owner
        or owner.owner_pid != os.getpid()
        or owner.run_id != source.bindings.run_id
        or runtime.run_id != owner.run_id
        or runtime.deadline != owner.deadline
        or reader.root != source.bindings.current_root
        or runtime.root != reader.root
        or not runtime.directory.is_relative_to(owner.stage_scope_directory(scope))
        or inputs.content != parser_markdown.content
        or reader.read(parser_markdown.relative) != parser_markdown
        or reader.read(parser_ast.relative) != parser_ast
        or hydration.get("schema_version") != "template-native-hydration-reconstruction-v3"
        or hydration.get("scope") != scope
        or hydration.get("source_binding") != [source.reference.commit, source.reference.source_identity]
        or hydration.get("content_digest")
        != canonical_digest({key: value for key, value in hydration.items() if key != "content_digest"})
    ):
        raise ValueError("ordinal parser requires actual live Source/clock, direct inputs and held complete AST")
    remaining(owner.deadline)
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    source.verify_correspondence(source.reference, reader.root, reader, owner.deadline)
    runtime.unchanged()
    reconstructed, pdf_body = observe_native_pdf_recomposition(
        source, scope, hydration["pipeline_run_id"], hydration["plan_digest"], reader, deadline=owner.deadline
    )
    if reconstructed != hydration or pdf_body != parser_markdown.content:
        raise ValueError("ordinal parser differs from complete actual Source hydration and PDF composition")
    original_tool = reader.read(parser_tool["path"])
    if original_tool.sha256 != parser_tool["sha256"]:
        raise ValueError("ordinal parser changed its actual unfiltered ToolAPI binding")
    original_raw = original_tool.json_object()
    owner.validate_tool(parser_tool, original_raw, reader, run_id=owner.run_id)
    process_binding = original_raw["native_process_artifact"]
    original_process = reader.read(process_binding["path"])
    if original_process.sha256 != process_binding["sha256"]:
        raise ValueError("ordinal parser changed its actual native process binding")
    original_cwd = original_process.json_object()["cwd"]
    if (
        original_raw["tool"] != "pandoc"
        or original_raw["purpose"] != "pdf-source-original-ast"
        or original_raw["exit_code"] != 0
        or original_raw["original_exit_code"] != 0
        or original_raw["timed_out"] is not False
        or original_raw["custody_refused"] is not False
        or original_raw["diagnostic"] != ""
        or original_raw["command"][1:] != [str(parser_markdown.path), *PARSER_ARGUMENTS]
        or original_raw["stdout"].encode() != parser_ast.content
        or canonical_digest(runtime.env) != original_raw["environment_digest"]
    ):
        raise ValueError("ordinal input/AST is not the genuine complete unfiltered Source parser result")
    rows = hydration["ordered_inputs"]
    if (
        not isinstance(rows, list)
        or len(rows) != len(inputs.sources)
        or [row["consumed"]["path"] for row in rows] != [path for path, _ in inputs.sources]
    ):
        raise ValueError("ordinal parser changed the complete actual hydration input order")
    selected = []
    occurrence_data = []
    variable_binding = hydration.get("variables")
    variable_values: dict[str, str] = {}
    if variable_binding is not None:
        variables_snapshot = reader.read(variable_binding["path"])
        if _binding(variables_snapshot) != variable_binding:
            raise ValueError("ordinal parser changed actual completed hydration variables")
        variable_values = variables_snapshot.json_object()
    for index, (row, (path, content)) in enumerate(zip(rows, inputs.sources, strict=True)):
        snapshot = reader.read(path)
        if row["ordinal"] != index + 1 or snapshot.content != content or _binding(snapshot) != row["consumed"]:
            raise ValueError("ordinal parser changed an actual held hydration input")
        if row["transformation"] == "Source-generated-transmission-boundary":
            # The actual Source adapter above rebuilt the complete bookend,
            # absence/history bindings and residuals. Keep its held bytes in
            # composition; it supplies no shared-token/native-location grant.
            continue
        authored = reader.read(row["source"]["path"])
        if _binding(authored) != row["source"] or source.reference.read(authored.relative) != authored.content:
            raise ValueError("ordinal parser changed the authored Source occurrence binding")
        if row["transformation"] == "exact-authored-source-body":
            if authored.content != content:
                raise ValueError("ordinal parser changed an exact authored Source body")
            continue
        if row["transformation"] != "shared-uppercase-token-hydration":
            raise ValueError("ordinal parser requires the independently checked actual shared hydration adapter")
        if (
            variable_binding is None
            or require_shared_hydration(authored.content, variable_values, content).data() != row["hydration"]
        ):
            raise ValueError("ordinal parser differs from complete actual Source hydration occurrence reconstruction")
        for ordinal, token in enumerate(row["hydration"]["occurrences"], 1):
            if token["ordinal"] != ordinal or token["resolved"] is not True:
                raise ValueError("ordinal parser omitted or reordered a resolved Source occurrence")
            selected.append(
                (
                    index,
                    ordinal,
                    token["key"],
                    token["output_start_byte"],
                    token["output_end_byte"],
                    token["replacement_sha256"],
                )
            )
            occurrence_data.append({"source": row["source"], "consumed": row["consumed"], **token})
    if not selected:
        raise ValueError("ordinal parser has no selected generated occurrence; Source absence requires no extra parser")
    config = reader.read(inputs.config[0])
    if config.content != inputs.config[1] or _binding(config) != hydration.get("config"):
        raise ValueError("ordinal parser changed its actual Source config")
    settings = yaml.safe_load(config.content)
    if not isinstance(settings, dict):
        raise ValueError("ordinal parser Source config is not a mapping")
    separator = "\n```{=latex}\n\\newpage\n```\n" if _rendering_options(settings)["section_breaks"] else ""
    annotated_bodies, anchors = annotate_manuscript_ordinals(tuple(body for _, body in inputs.sources), tuple(selected))
    combined = combine_held_manuscripts(annotated_bodies, separator=separator).decode()
    if _MERMAID_BLOCK_RE.search(combined):
        raise ValueError("ordinal parser retains selected Mermaid transformation custody until its exact span adapter")
    variables = [row for row in inputs.auxiliary if Path(row[0]).name == "manuscript_vars.yaml"]
    if len(variables) > 1:
        raise ValueError("ordinal parser repeated actual dotted variable input")
    for path, content in variables:
        if reader.read(path).content != content:
            raise ValueError("ordinal parser changed actual Source dotted variables")
        runtime.freeze("manuscript_vars.yaml", content)
    annotated = preprocess_combined_markdown(combined, manuscript_dir=runtime.directory).content.encode()
    parser_ranges = require_unannotated_parser_bytes(annotated, parser_markdown.content, anchors)
    markdown = runtime.freeze("ordinal-source.md", annotated)
    attempt: dict[str, Any] = {
        "scope": scope,
        "run_id": owner.run_id,
        "source_binding": [source.reference.commit, source.reference.source_identity],
        "hydration_digest": hydration["content_digest"],
        "actual_parser_input": _binding(parser_markdown),
        "actual_parser_ast": _binding(parser_ast),
        "actual_parser_tool": parser_tool,
        "tool_bindings": [],
        "comparison_completed": False,
    }
    try:
        arguments = [str(markdown), *PARSER_ARGUMENTS]
        raw = runtime.tool("pandoc", arguments, PURPOSE, input_paths=tuple(runtime.inputs), cwd=Path(original_cwd))
        binding = runtime.tools[-1]
        owner.validate_tool(binding, raw, reader, run_id=owner.run_id)
        if (
            raw["tool"] != "pandoc"
            or raw["purpose"] != PURPOSE
            or raw["command"][1:] != arguments
            or raw["executable"] != original_raw["executable"]
            or raw["executable_sha256"] != original_raw["executable_sha256"]
            or raw["cwd"] != original_cwd
            or raw["environment_digest"] != original_raw["environment_digest"]
        ):
            raise ValueError("ordinal parser changed its genuine selected ToolAPI/profile")
        ast = runtime.freeze("ordinal-source.ast.json", raw["stdout"].encode())
        markdown_snapshot = reader.read(markdown.relative_to(reader.root).as_posix())
        ast_snapshot = reader.read(ast.relative_to(reader.root).as_posix())
        if markdown_snapshot.content != annotated or ast_snapshot.content != raw["stdout"].encode():
            raise ValueError("ordinal parser changed its actual frozen input/output before AST comparison")
        mapping = require_complete_ordinal_ast_equivalence(ast_snapshot.content, parser_ast.content, anchors)
        owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
        source.verify_correspondence(source.reference, reader.root, reader, owner.deadline)
        runtime.unchanged()
        if not reader.unchanged():
            raise ValueError("Source ordinal input/native evidence changed before complete closing")
        remaining(owner.deadline)
        attempt["comparison_completed"] = True
        return {
            **attempt,
            "tool_bindings": list(runtime.tools),
            "annotated_markdown": _binding(markdown_snapshot),
            "annotated_ast": _binding(ast_snapshot),
            "occurrences": [
                {
                    "hydration": original,
                    "parser_byte_range": list(span),
                    "parser_carrier_byte_range": [span[0] - len(anchor.prefix), span[1] + len(anchor.suffix)],
                    "ast": position,
                }
                for original, span, position, anchor in zip(
                    occurrence_data, parser_ranges, mapping, anchors, strict=True
                )
            ],
            "claim_boundary": (
                "complete Source byte/AST ordinal concordance; native whole-occurrence predicates still required"
            ),
        }
    except BaseException as error:
        attempt["tool_bindings"] = list(runtime.tools)
        if not hasattr(error, "native_ordinal_attempt"):
            setattr(error, "native_ordinal_attempt", attempt)
        raise
