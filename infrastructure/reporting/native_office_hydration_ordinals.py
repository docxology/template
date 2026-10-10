"""Exact generated-field anchors through the actual Office Source filter chain.

One complete annotated parse serves all selected occurrences of this actual
format. It uses the existing live owner/clock and exact held filter command;
the unfiltered Source coverage AST remains separately bound. No PDF AST or
native package chooses the Source occurrence.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering._pdf_title_page_config import _rendering_options
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts, require_shared_hydration
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_complete_ordinal_ast_equivalence,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_hydration_reconstruction import observe_native_pdf_recomposition
from infrastructure.reporting.native_office_semantic_source import office_semantic_source_plan
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PURPOSE = "source-hydration-ordinal-office-ast"


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def observe_office_hydration_ordinals(
    scope: str,
    artifact: NativeArtifact,
    office_source: dict[str, Any],
    hydration: dict[str, Any],
    reader: SnapshotReader,
    runtime: CitationRuntime,
    *,
    source: NativeSourceContext,
) -> dict[str, Any]:
    """Hold own Source/unfiltered/filtered inputs and compare the complete AST.

    Existing Office Source survival, original filter/library custody, native
    image/math/layout and controls remain mandatory in the enclosing caller.
    This return establishes the byte-to-filtered-AST edge only.
    """
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source is not source
        or owner.owner_pid != os.getpid()
        or reader.native_producer_operation is not owner
        or reader.root != source.bindings.current_root
        or type(runtime) is not CitationRuntime
        or runtime.root != reader.root
        or runtime.run_id != owner.run_id
        or runtime.deadline != owner.deadline
        or not runtime.directory.is_relative_to(owner.stage_scope_directory(scope))
        or artifact.id != f"manuscript:{artifact.format}"
        or artifact.format not in {"docx", "epub"}
        or office_source.get("format") != artifact.format
        or office_source.get("artifact_id") != artifact.id
        or office_source.get("run_id") != owner.run_id
        or hydration.get("scope") != scope
        or hydration.get("source_binding") != [source.reference.commit, source.reference.source_identity]
        or hydration.get("content_digest")
        != canonical_digest({key: item for key, item in hydration.items() if key != "content_digest"})
    ):
        raise ValueError("Office ordinals require the actual own-format Source/owner/clock")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    reconstructed, _ = observe_native_pdf_recomposition(
        source, scope, hydration["pipeline_run_id"], hydration["plan_digest"], reader, deadline=owner.deadline
    )
    if reconstructed != hydration:
        raise ValueError("Office ordinals changed the complete independently reconstructed hydration graph")
    create_private_native_directory(reader.root, runtime.directory / "independent-source")
    plan = office_semantic_source_plan(
        reader.root, runtime.directory / "independent-source", scope, artifact, reader, deadline=owner.deadline
    )
    if plan.blockers or plan.mermaid is not None:
        raise ValueError("Office ordinal Mermaid projection requires its exact actual span adapter")
    snapshots = {}
    for key in ("source", "ast", "source_coverage_ast"):
        binding = office_source[key]
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("Office ordinal changed an actual held own-format Source parser body")
        snapshots[key] = snapshot
    if snapshots["source"].content != plan.content or office_source["sources"] != [
        {"path": path, "sha256": reader.read(path).sha256} for path, _ in plan.sources
    ]:
        raise ValueError("Office ordinal plan changed the complete actual selected Source input order/body")
    original_binding = office_source["tool"]["artifact"]
    original_snapshot = reader.read(original_binding["path"])
    if original_snapshot.sha256 != original_binding["sha256"]:
        raise ValueError("Office ordinal changed its actual Source filter ToolAPI binding")
    original = original_snapshot.json_object()
    owner.validate_tool(original_binding, original, reader, run_id=owner.run_id)
    process = reader.read(original["native_process_artifact"]["path"])
    if process.sha256 != original["native_process_artifact"]["sha256"]:
        raise ValueError("Office ordinal changed its actual Source filter native process")
    cwd = Path(process.json_object()["cwd"])
    if (
        original["purpose"] != "office-semantic-pandoc"
        or original["tool"] != "pandoc"
        or original["exit_code"] != 0
        or original["original_exit_code"] != 0
        or original["timed_out"] is not False
        or original["custody_refused"] is not False
        or original["stdout"].encode() != snapshots["ast"].content
        or original["command"][1] != str(snapshots["source"].path)
        or original["command"][2:5] != ["--from=markdown+yaml_metadata_block", "--to=json", "--standalone"]
        or canonical_digest(runtime.env) != original["environment_digest"]
    ):
        raise ValueError("Office ordinals require its genuine complete Source filter profile and OS0")
    crossref = office_source["crossref_runtime"]
    if crossref is not None:
        actual = file_observation(Path(crossref["path"]))
        if any(actual[name] != crossref[name] for name in ("path", "sha256", "bytes")):
            raise ValueError("Office ordinal changed its actual Source-selected crossref executable")
    selected = []
    occurrence_data = []
    rows = {row["consumed"]["path"]: row for row in hydration["ordered_inputs"]}
    if len(rows) != len(hydration["ordered_inputs"]):
        raise ValueError("Office ordinal repeated a complete consumed input")
    variable_snapshot = reader.read(hydration["variables"]["path"])
    if _binding(variable_snapshot) != hydration["variables"]:
        raise ValueError("Office ordinal changed complete actual hydration variables")
    variables = variable_snapshot.json_object()
    held_inputs = []
    for row in (*office_source["filters"], *office_source["bibliographies"]):
        for kind in ("source", "consumed"):
            binding = row[kind]
            snapshot = reader.read(binding["path"])
            if snapshot.sha256 != binding["sha256"]:
                raise ValueError("Office ordinal changed an actual held filter/bibliography body")
            held_inputs.append(snapshot.path)
    coverage_binding = office_source["source_coverage_tool"]["artifact"]
    coverage = reader.read(coverage_binding["path"])
    if coverage.sha256 != coverage_binding["sha256"]:
        raise ValueError("Office ordinal changed its genuine unfiltered Source ToolAPI")
    coverage_raw = coverage.json_object()
    owner.validate_tool(coverage_binding, coverage_raw, reader, run_id=owner.run_id)
    if (
        coverage_raw["purpose"] != "office-source-coverage-pandoc"
        or coverage_raw["stdout"].encode() != snapshots["source_coverage_ast"].content
        or coverage_raw["command"][1:]
        != [str(snapshots["source"].path), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"]
    ):
        raise ValueError("Office ordinal lost the genuine complete unfiltered Source coverage parse")
    for index, (path, body) in enumerate(plan.sources):
        row = rows[path]
        consumed = reader.read(path)
        if consumed.content != body or _binding(consumed) != row["consumed"]:
            raise ValueError("Office ordinal changed actual complete consumed input bytes")
        if row["transformation"] in {"Source-generated-transmission-boundary", "exact-authored-source-body"}:
            continue
        authored = reader.read(row["source"]["path"])
        if (
            row["transformation"] != "shared-uppercase-token-hydration"
            or _binding(authored) != row["source"]
            or source.reference.read(authored.relative) != authored.content
            or require_shared_hydration(authored.content, variables, body).data() != row["hydration"]
        ):
            raise ValueError("Office ordinal changed the actual shared Source hydration adapter")
        for token in row["hydration"]["occurrences"]:
            if token["resolved"] is not True:
                raise ValueError("Office ordinal retains unresolved selected Source values")
            selected.append(
                (
                    index,
                    token["ordinal"],
                    token["key"],
                    token["output_start_byte"],
                    token["output_end_byte"],
                    token["replacement_sha256"],
                )
            )
            occurrence_data.append({"source": row["source"], "consumed": row["consumed"], **token})
    annotated_bodies, anchors = annotate_manuscript_ordinals(tuple(body for _, body in plan.sources), tuple(selected))
    if not anchors:
        raise ValueError("Office ordinal has no actual selected generated occurrence")
    settings = yaml.safe_load(plan.config[1]) if plan.config is not None else None
    separator = "\n```{=latex}\n\\newpage\n```\n" if _rendering_options(settings)["section_breaks"] else ""
    joined = combine_held_manuscripts(annotated_bodies, separator=separator).decode()
    if plan.variables is not None:
        runtime.freeze("manuscript_vars.yaml", plan.variables[1])
    annotated = preprocess_combined_markdown(joined, manuscript_dir=runtime.directory).content.encode()
    ranges = require_unannotated_parser_bytes(annotated, snapshots["source"].content, anchors)
    markdown = runtime.freeze("ordinal-office-source.md", annotated)
    arguments = [str(markdown), *original["command"][2:]]
    attempt = {
        "scope": scope,
        "format": artifact.format,
        "run_id": owner.run_id,
        "tool_bindings": [],
        "comparison_completed": False,
    }
    try:
        observed = runtime.tool(
            "pandoc", arguments, PURPOSE, input_paths=tuple(dict.fromkeys((*runtime.inputs, *held_inputs))), cwd=cwd
        )
        owner.validate_tool(runtime.tools[-1], observed, reader, run_id=owner.run_id)
        if any(observed[name] != original[name] for name in ("executable", "executable_sha256", "environment_digest")):
            raise ValueError("Office ordinal changed its actual selected parser/filter runtime")
        if observed["cwd"] != str(cwd):
            raise ValueError("Office ordinal changed the actual own-filter working directory")
        if crossref is not None:
            actual = file_observation(Path(crossref["path"]))
            if any(actual[name] != crossref[name] for name in ("path", "sha256", "bytes")):
                raise ValueError("Office ordinal Source crossref executable changed before closing")
        ast_path = runtime.freeze("ordinal-office-source.ast.json", observed["stdout"].encode())
        ast = reader.read(ast_path.relative_to(reader.root).as_posix())
        mapping = require_complete_ordinal_ast_equivalence(ast.content, snapshots["ast"].content, anchors)
        owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
        runtime.unchanged()
        if not reader.unchanged():
            raise ValueError("Office ordinal Source/filter/native inputs changed before closing")
        remaining(owner.deadline)
        return {
            **attempt,
            "source_binding": [source.reference.commit, source.reference.source_identity],
            "hydration_digest": hydration["content_digest"],
            "comparison_completed": True,
            "actual_parser_input": _binding(snapshots["source"]),
            "actual_parser_ast": _binding(snapshots["ast"]),
            "unfiltered_source_ast": _binding(snapshots["source_coverage_ast"]),
            "actual_parser_tool": original_binding,
            "unfiltered_source_tool": coverage_binding,
            "dotted_variables": None
            if plan.variables is None
            else _binding(
                reader.read((runtime.directory / "manuscript_vars.yaml").relative_to(reader.root).as_posix())
            ),
            "annotated_markdown": _binding(reader.read(markdown.relative_to(reader.root).as_posix())),
            "annotated_ast": _binding(ast),
            "tool_bindings": list(runtime.tools),
            "occurrences": [
                {
                    "hydration": token,
                    "parser_byte_range": list(span),
                    "parser_carrier_byte_range": [span[0] - len(anchor.prefix), span[1] + len(anchor.suffix)],
                    "ast": position,
                }
                for token, span, position, anchor in zip(occurrence_data, ranges, mapping, anchors, strict=True)
            ],
            "claim_boundary": (
                "actual Source hydration through its complete own Office filter AST; native predicates remain mandatory"
            ),
        }
    except BaseException as error:
        attempt["tool_bindings"] = list(runtime.tools)
        if not hasattr(error, "native_ordinal_attempt"):
            setattr(error, "native_ordinal_attempt", attempt)
        raise
