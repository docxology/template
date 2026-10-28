"""Own HTML hydration ordinals in genuine body and original-source parsers.

The two Source AST identities stay distinct. Complete annotated AST equality
joins the actual byte ordinals; existing whole browser/source/font/style/ink,
scientific, loader, controls and closing predicates remain required. No Core,
Common suite, owner, renderer or raster is created here.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering._web_markdown_preprocess import html_safe_markdown
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts, require_shared_hydration
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_complete_ordinal_ast_equivalence,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_crossref_pair import parent_launcher_binding, parent_observation
from infrastructure.reporting.native_crossref_pandoc import source_crossref_pandoc
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_html_source_metadata import HTML_WITNESS_SCHEMA
from infrastructure.reporting.native_format_joint_source import source_environment
from infrastructure.reporting.native_format_semantic_original import original_source_bytes
from infrastructure.reporting.native_format_semantic_source import semantic_source_plan
from infrastructure.reporting.native_hydration_reconstruction import observe_native_hydration_reconstruction
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

PARSER_ARGUMENTS = ("--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json")
BODY_PURPOSE = "source-html-hydration-ordinal-ast"
ORIGINAL_PURPOSE = "source-html-original-hydration-ordinal-ast"


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def _held(value: dict[str, Any], reader: SnapshotReader) -> ArtifactSnapshot:
    snapshot = reader.read(value["path"])
    if value != {"path": snapshot.relative, "sha256": snapshot.sha256} and value != _binding(snapshot):
        raise ValueError("HTML ordinal evidence changed its complete held byte binding")
    return snapshot


def compose_html_ordinal_input(bodies: tuple[bytes, ...], *, combined: bool) -> bytes:
    """Use the actual HTML writer transforms, without reopening manuscript paths."""
    if not combined and len(bodies) != 1:
        raise ValueError("a Source-selected HTML section requires exactly one complete input")
    body = combine_held_manuscripts(bodies, separator="\n---\n\n") if combined else bodies[0]
    return html_safe_markdown(body.decode(), render_citations=not combined, preserve_crossrefs=True).encode()


def _selected_occurrences(
    sources: tuple[tuple[str, bytes], ...],
    hydration: dict[str, Any],
    reader: SnapshotReader,
    source: NativeSourceContext,
) -> tuple[list[tuple[int, int, str, int, int, str]], list[dict[str, Any]]]:
    """Select complete own-format inputs from the authenticated scope roster."""
    rows = hydration["ordered_inputs"]
    if not isinstance(rows, list) or len({row["consumed"]["path"] for row in rows}) != len(rows):
        raise ValueError("HTML ordinal hydration repeated an actual Source input")
    by_path = {row["consumed"]["path"]: row for row in rows}
    if any(path not in by_path for path, _ in sources):
        raise ValueError("HTML ordinal Source input is absent from the complete hydration roster")
    own_rows = [by_path[path] for path, _ in sources]
    if [row["ordinal"] for row in own_rows] != sorted(row["ordinal"] for row in own_rows):
        raise ValueError("HTML ordinal input order differs from actual Source hydration")
    variables = hydration.get("variables")
    values = _held(variables, reader).json_object() if variables is not None else {}
    selected, occurrences = [], []
    for index, (row, (path, content)) in enumerate(zip(own_rows, sources, strict=True)):
        consumed = reader.read(path)
        if consumed.content != content or _binding(consumed) != row["consumed"]:
            raise ValueError("HTML ordinal input differs from actual complete consumed Source bytes")
        if row["transformation"] == "Source-generated-transmission-boundary":
            # The genuine full graph reconstruction checks the Source factory,
            # ledger/absence/history and complete bookend; it grants no scalar.
            continue
        authored = _held(row["source"], reader)
        if source.reference.read(authored.relative) != authored.content:
            raise ValueError("HTML ordinal authored input differs from its admitted Source")
        if row["transformation"] == "exact-authored-source-body":
            if authored.content != content:
                raise ValueError("HTML ordinal exact authored body changed")
            continue
        if (
            row["transformation"] != "shared-uppercase-token-hydration"
            or variables is None
            or require_shared_hydration(authored.content, values, content).data() != row["hydration"]
        ):
            raise ValueError("HTML ordinal needs its exact independently checked Source hydration adapter")
        for ordinal, token in enumerate(row["hydration"]["occurrences"], 1):
            if token["ordinal"] != ordinal or token["resolved"] is not True:
                raise ValueError("HTML ordinal omitted/reordered an actual resolved Source occurrence")
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
            occurrences.append({"source": row["source"], "consumed": row["consumed"], **token})
    return selected, occurrences


def _actual_parser(
    packet: dict[str, Any], expected: bytes, purpose: str, reader: SnapshotReader, owner: Any, *, cwd: Path
) -> tuple[ArtifactSnapshot, ArtifactSnapshot, dict[str, Any], dict[str, Any]]:
    markdown, ast = _held(packet["source"], reader), _held(packet["ast"], reader)
    tool = _held(packet["tool"]["artifact"], reader).json_object()
    owner.validate_tool(packet["tool"]["artifact"], tool, reader, run_id=owner.run_id)
    process = _held(tool["native_process_artifact"], reader).json_object()
    if (
        markdown.content != expected
        or tool["tool"] != "pandoc"
        or tool["purpose"] != purpose
        or tool["exit_code"] != 0
        or tool["original_exit_code"] != 0
        or tool["timed_out"] is not False
        or tool["custody_refused"] is not False
        or tool["diagnostic"] != ""
        or tool["stdout"].encode() != ast.content
        or process["cwd"] != str(cwd)
    ):
        raise ValueError("HTML ordinal input/AST is not its genuine completed Source parser")
    return markdown, ast, tool, process


def _body_arguments(
    body: dict[str, Any],
    markdown: ArtifactSnapshot,
    bibliographies: tuple[tuple[str, bytes], ...],
    reader: SnapshotReader,
    runtime: CitationRuntime,
    source: NativeSourceContext,
) -> tuple[list[str], list[Path], str | None]:
    """Authenticate original filter/bibliography operands against current Source."""
    from infrastructure.rendering._pandoc_filters import formalism_filter_args

    arguments = [str(markdown.path), *PARSER_ARGUMENTS]
    inputs = [markdown.path]
    filters = body["filters"]
    selected_filters = formalism_filter_args()[1::2]
    if not isinstance(filters, list) or len(filters) != len(selected_filters):
        raise ValueError("HTML ordinal parser omitted a Source-selected Lua filter")
    sdk_root = Path(__file__).absolute().parents[2]
    for index, (row, path) in enumerate(zip(filters, selected_filters, strict=True)):
        relative = Path(path).relative_to(sdk_root).as_posix()
        current = source.current_source_reader.read(relative)
        consumed = _held(row["consumed"], reader)
        if (
            row["source"] != {"path": relative, "sha256": current.sha256}
            or source.reference.read(relative) != current.content
            or consumed.content != current.content
            or consumed.path != markdown.path.parent / f"semantic-filter-{index}.lua"
        ):
            raise ValueError("HTML ordinal Lua input differs from the actual current Source filter")
        arguments.extend(["--lua-filter", str(consumed.path)])
        inputs.append(consumed.path)
    if body["bibliographies"] != [
        {"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in bibliographies
    ]:
        raise ValueError("HTML ordinal omitted/reordered Source bibliography inputs")
    for index, (_, data) in enumerate(bibliographies):
        bib = reader.read(
            (markdown.path.parent / f"semantic-bibliography-{index}.bib").relative_to(reader.root).as_posix()
        )
        if bib.content != data:
            raise ValueError("HTML ordinal consumed bibliography changed")
        arguments.append(f"--bibliography={bib.path}")
        inputs.append(bib.path)
    if bibliographies:
        arguments.extend(["--citeproc", "--metadata=link-citations:true"])
    nominated = (
        shutil.which("pandoc-crossref", path=runtime.env.get("PATH")) if body["crossref_filter"] is not None else None
    )
    if body["crossref_filter"] is not None:
        graph = parent_observation(body["crossref_filter"], reader)
        specification = _held(graph["specification"], reader).json_object()
        wrapper = _held(parent_launcher_binding(graph), reader)
        if nominated is None or specification["crossref"] != file_observation(Path(nominated).resolve(strict=True)):
            raise ValueError("HTML ordinal Crossref differs from the actual Source-selected executable")
        arguments.extend(["--filter", str(wrapper.path)])
    return arguments, inputs, nominated


def observe_html_hydration_ordinals(
    scope: str,
    artifact: NativeArtifact,
    html_source: dict[str, Any],
    hydration: dict[str, Any],
    reader: SnapshotReader,
    runtime: CitationRuntime,
    *,
    source: NativeSourceContext,
) -> dict[str, Any]:
    """One own filtered and one original parser shared by all selected values."""
    owner = current_native_producer_operation()
    if (
        not isinstance(source, NativeSourceContext)
        or type(artifact) is not NativeArtifact
        or artifact.format != "html"
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
        or html_source.get("schema_version") != HTML_WITNESS_SCHEMA
        or set(html_source) != {"schema_version", "body", "source_metadata"}
        or hydration.get("schema_version") != "template-native-hydration-reconstruction-v3"
        or hydration.get("scope") != scope
        or hydration.get("source_binding") != [source.reference.commit, source.reference.source_identity]
        or hydration.get("content_digest")
        != canonical_digest({key: value for key, value in hydration.items() if key != "content_digest"})
    ):
        raise ValueError("HTML ordinal parser requires actual live Source, same scope/clock and held complete inputs")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    source.verify_correspondence(source.reference, reader.root, reader, owner.deadline)
    runtime.unchanged()
    reconstructed = observe_native_hydration_reconstruction(
        source, scope, hydration["pipeline_run_id"], hydration["plan_digest"], reader, deadline=owner.deadline
    )
    if reconstructed != hydration:
        raise ValueError("HTML ordinal differs from the genuine complete Source hydration reconstruction")
    content, sources, bibliographies = semantic_source_plan(reader.root, scope, artifact, reader)
    combined = artifact.id == "manuscript:html"
    if not combined and not (artifact.id.startswith("section:") and artifact.id.endswith(":html")):
        raise ValueError("HTML ordinal requires its actual complete manuscript or Source-relative section")
    bodies = tuple(data for _, data in sources)
    if compose_html_ordinal_input(bodies, combined=combined) != content:
        raise ValueError("HTML ordinal own held input composition differs from the actual HTMLsafe writer")
    body = html_source["body"]
    body_cwd = (
        _held(body["source"], reader).path.parent / "semantic-crossref-owner"
        if body["crossref_filter"] is not None
        else reader.root
    )
    markdown, ast, original_tool, _ = _actual_parser(body, content, "semantic-pandoc", reader, owner, cwd=body_cwd)
    arguments, inputs, crossref = _body_arguments(body, markdown, bibliographies, reader, runtime, source)
    expected_env = {**runtime.env, **source_environment(source)} if crossref is not None else runtime.env
    if original_tool["command"][1:] != arguments or original_tool["environment_digest"] != canonical_digest(
        expected_env
    ):
        raise ValueError("HTML ordinal original parser changed exact Source-selected arguments/environment")
    if crossref is not None and not combined:
        raise ValueError("HTML section parser cannot acquire an unselected Crossref child")
    original = body["original_source"]
    raw_markdown, raw_ast, raw_tool, _ = _actual_parser(
        original, original_source_bytes(sources), "semantic-original-pandoc", reader, owner, cwd=reader.root
    )
    if (
        raw_tool["command"][1:] != [str(raw_markdown.path), *PARSER_ARGUMENTS]
        or raw_tool["environment_digest"] != canonical_digest(runtime.env)
        or any(raw_tool[key] != original_tool[key] for key in ("executable", "executable_sha256"))
    ):
        raise ValueError("HTML original source parser changed its actual unfiltered Source profile")
    selected, occurrences = _selected_occurrences(sources, hydration, reader, source)
    attempt: dict[str, Any] = {
        "scope": scope,
        "artifact_id": artifact.id,
        "run_id": owner.run_id,
        "source_binding": [source.reference.commit, source.reference.source_identity],
        "hydration_digest": hydration["content_digest"],
        "source_inputs": [_binding(reader.read(path)) for path, _ in sources],
        "dotted_variables": hydration.get("dotted_variables"),
        "actual_parser_input": _binding(markdown),
        "actual_parser_ast": _binding(ast),
        "actual_parser_tool": body["tool"]["artifact"],
        "actual_original_input": _binding(raw_markdown),
        "actual_original_ast": _binding(raw_ast),
        "actual_original_tool": original["tool"]["artifact"],
        "tool_bindings": [],
        "comparison_completed": False,
        "occurrences": [],
    }
    try:
        if selected:
            annotated_bodies, anchors = annotate_manuscript_ordinals(bodies, tuple(selected))
            annotated = compose_html_ordinal_input(annotated_bodies, combined=combined)
            ranges = require_unannotated_parser_bytes(annotated, markdown.content, anchors)
            local = runtime.freeze("html-ordinal-source.md", annotated)
            local_args = [str(local), *arguments[1:]]
            current_crossref = None
            if crossref is not None:
                local_args[local_args.index("--filter") + 1] = crossref
                result, current_crossref = source_crossref_pandoc(
                    runtime,
                    scope,
                    local_args,
                    BODY_PURPOSE,
                    output_format="json",
                    input_paths=(local, *inputs[1:]),
                    cwd=body_cwd,
                )
            else:
                result = runtime.tool(
                    "pandoc", local_args, BODY_PURPOSE, input_paths=(local, *inputs[1:]), cwd=body_cwd
                )
            owner.validate_tool(runtime.tools[-1], result, reader, run_id=owner.run_id)
            attempt["annotated_parser_tool"] = runtime.tools[-1]
            if any(result[key] != original_tool[key] for key in ("executable", "executable_sha256")):
                raise ValueError("HTML annotated body changed the actual Source-selected parser bytes")
            local_ast = runtime.freeze("html-ordinal-source.ast.json", result["stdout"].encode())
            positions = require_complete_ordinal_ast_equivalence(result["stdout"].encode(), ast.content, anchors)
            raw_content = original_source_bytes(
                tuple((path, data) for (path, _), data in zip(sources, annotated_bodies, strict=True))
            )
            raw_ranges = require_unannotated_parser_bytes(raw_content, raw_markdown.content, anchors)
            raw_local = runtime.freeze("html-ordinal-original.md", raw_content)
            raw_result = runtime.tool(
                "pandoc",
                [str(raw_local), *PARSER_ARGUMENTS],
                ORIGINAL_PURPOSE,
                input_paths=(raw_local,),
                cwd=reader.root,
            )
            owner.validate_tool(runtime.tools[-1], raw_result, reader, run_id=owner.run_id)
            attempt["annotated_original_tool"] = runtime.tools[-1]
            if any(raw_result[key] != raw_tool[key] for key in ("executable", "executable_sha256")):
                raise ValueError("HTML annotated original changed the genuine unfiltered parser bytes")
            raw_local_ast = runtime.freeze("html-ordinal-original.ast.json", raw_result["stdout"].encode())
            raw_positions = require_complete_ordinal_ast_equivalence(
                raw_result["stdout"].encode(), raw_ast.content, anchors
            )
            attempt.update(
                {
                    "annotated_markdown": _binding(reader.read(local.relative_to(reader.root).as_posix())),
                    "annotated_ast": _binding(reader.read(local_ast.relative_to(reader.root).as_posix())),
                    "annotated_original_markdown": _binding(reader.read(raw_local.relative_to(reader.root).as_posix())),
                    "annotated_original_ast": _binding(reader.read(raw_local_ast.relative_to(reader.root).as_posix())),
                    "crossref_filter": current_crossref,
                    "occurrences": [
                        {
                            "hydration": token,
                            "parser_byte_range": list(span),
                            "parser_carrier_byte_range": [span[0] - len(anchor.prefix), span[1] + len(anchor.suffix)],
                            "ast": position,
                            "original_parser_byte_range": list(raw_span),
                            "original_parser_carrier_byte_range": [
                                raw_span[0] - len(anchor.prefix),
                                raw_span[1] + len(anchor.suffix),
                            ],
                            "original_ast": raw_position,
                        }
                        for token, span, position, raw_span, raw_position, anchor in zip(
                            occurrences, ranges, positions, raw_ranges, raw_positions, anchors, strict=True
                        )
                    ],
                }
            )
        owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
        source.verify_correspondence(source.reference, reader.root, reader, owner.deadline)
        runtime.unchanged()
        if not reader.unchanged():
            raise ValueError("HTML ordinal complete Source/parser/native custody changed before closing")
        remaining(owner.deadline)
        attempt["comparison_completed"] = True
        attempt["tool_bindings"] = list(runtime.tools)
        return {
            **attempt,
            "claim_boundary": "own HTML complete byte/AST ordinals; native whole-role predicates remain required",
        }
    except BaseException as error:
        attempt["tool_bindings"] = list(runtime.tools)
        if not hasattr(error, "native_ordinal_attempt"):
            setattr(error, "native_ordinal_attempt", attempt)
        raise


def replay_html_hydration_ordinals(
    artifact: NativeArtifact,
    ordinal: dict[str, Any],
    hydration: dict[str, Any],
    inputs: list[dict[str, Any]],
    reader: SnapshotReader,
    *,
    custody: dict[str, Any],
    run_id: str,
    html_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read back both exact Original ASTs under genuine transported custody.

    This executes neither parser nor Core. The enclosing independently checked
    browser Source packet is required, so retained argv cannot select filters,
    bibliographies or a Crossref owner. Fresh Current observations stay separate.
    """
    from infrastructure.reporting.native_format_acceptance_evidence import _tool
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_format_portable_custody import producer_path
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation

    operation = require_native_operation(reader)
    scope = ordinal["scope"]
    if (
        scope not in operation.originals
        or ordinal["run_id"] != run_id
        or ordinal["artifact_id"] != artifact.id
        or artifact.format != "html"
        or ordinal["source_binding"] != [operation.source.reference.commit, operation.source.reference.source_identity]
        or ordinal["hydration_digest"] != hydration["content_digest"]
        or ordinal["comparison_completed"] is not True
        or ordinal["dotted_variables"] != hydration.get("dotted_variables")
        or ordinal["source_inputs"] != inputs
        or html_source is None
        or html_source.get("schema_version") != HTML_WITNESS_SCHEMA
    ):
        raise ValueError("HTML ordinal readback differs from its actual Source/scope/Original custody")
    content, sources, bibliographies = semantic_source_plan(reader.root, scope, artifact, reader)
    if [_binding(reader.read(path)) for path, _ in sources] != inputs:
        raise ValueError("HTML ordinal readback omitted/reordered own Source inputs")
    selected, tokens = _selected_occurrences(sources, hydration, reader, operation.source)
    body = html_source["body"]
    markdown, ast = _held(ordinal["actual_parser_input"], reader), _held(ordinal["actual_parser_ast"], reader)
    raw_markdown, raw_ast = (
        _held(ordinal["actual_original_input"], reader),
        _held(ordinal["actual_original_ast"], reader),
    )
    if (
        markdown.content != content
        or raw_markdown.content != original_source_bytes(sources)
        or _held(body["source"], reader) != markdown
        or _held(body["ast"], reader) != ast
        or _held(body["original_source"]["source"], reader) != raw_markdown
        or _held(body["original_source"]["ast"], reader) != raw_ast
        or ordinal["actual_parser_tool"] != body["tool"]["artifact"]
        or ordinal["actual_original_tool"] != body["original_source"]["tool"]["artifact"]
    ):
        raise ValueError("HTML ordinal readback changed its own filtered/original Source AST identity")
    args = [str(producer_path(custody, reader.root, markdown.path)), *PARSER_ARGUMENTS]
    filters = body["filters"]
    from infrastructure.rendering._pandoc_filters import formalism_filter_args

    selected_filters = formalism_filter_args()[1::2]
    if not isinstance(filters, list) or len(filters) != len(selected_filters):
        raise ValueError("HTML ordinal readback changed the exact Source Lua roster")
    sdk_root = Path(__file__).absolute().parents[2]
    for index, (row, path) in enumerate(zip(filters, selected_filters, strict=True)):
        current = operation.source.current_source_reader.read(Path(path).relative_to(sdk_root).as_posix())
        copied = _held(row["consumed"], reader)
        if (
            row["source"] != {"path": current.relative, "sha256": current.sha256}
            or current.content != operation.source.reference.read(current.relative)
            or copied.content != current.content
            or copied.path != markdown.path.parent / f"semantic-filter-{index}.lua"
        ):
            raise ValueError("HTML ordinal readback changed actual Source Lua bytes")
        args.extend(["--lua-filter", str(producer_path(custody, reader.root, copied.path))])
    if body["bibliographies"] != [
        {"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in bibliographies
    ]:
        raise ValueError("HTML ordinal readback changed Source bibliography identity/order")
    for index, (_, data) in enumerate(bibliographies):
        bib = reader.read(
            (markdown.path.parent / f"semantic-bibliography-{index}.bib").relative_to(reader.root).as_posix()
        )
        if bib.content != data:
            raise ValueError("HTML ordinal readback consumed different bibliography bytes")
        args.append(f"--bibliography={producer_path(custody, reader.root, bib.path)}")
    if bibliographies:
        args.extend(["--citeproc", "--metadata=link-citations:true"])
    if body["crossref_filter"] is not None:
        CrossrefFilterReaderOperation(
            operation.source, body["crossref_filter"], reader, scope=scope, run_id=run_id, deadline=operation.deadline
        ).replay()
        wrapper = _held(parent_launcher_binding(parent_observation(body["crossref_filter"], reader)), reader)
        if artifact.id != "manuscript:html":
            raise ValueError("HTML ordinal section readback acquired an unselected Crossref child")
        args.extend(["--filter", str(producer_path(custody, reader.root, wrapper.path))])
    actual = _tool(ordinal["actual_parser_tool"], reader, run_id, "pandoc", "semantic-pandoc", args)
    raw_actual = _tool(
        ordinal["actual_original_tool"],
        reader,
        run_id,
        "pandoc",
        "semantic-original-pandoc",
        [str(producer_path(custody, reader.root, raw_markdown.path)), *PARSER_ARGUMENTS],
    )
    if actual["stdout"].encode() != ast.content or raw_actual["stdout"].encode() != raw_ast.content:
        raise ValueError("HTML ordinal original AST bytes differ from genuine OS stdout")
    if not selected:
        if ordinal["occurrences"] or ordinal["tool_bindings"] or any(key.startswith("annotated_") for key in ordinal):
            raise ValueError("HTML ordinal absence claimed an unselected fresh parser")
    else:
        bodies, anchors = annotate_manuscript_ordinals(tuple(data for _, data in sources), tuple(selected))
        annotated = compose_html_ordinal_input(bodies, combined=artifact.id == "manuscript:html")
        raw_annotated = original_source_bytes(
            tuple((path, data) for (path, _), data in zip(sources, bodies, strict=True))
        )
        ranges = require_unannotated_parser_bytes(annotated, markdown.content, anchors)
        raw_ranges = require_unannotated_parser_bytes(raw_annotated, raw_markdown.content, anchors)
        local, local_ast = _held(ordinal["annotated_markdown"], reader), _held(ordinal["annotated_ast"], reader)
        raw_local, raw_local_ast = (
            _held(ordinal["annotated_original_markdown"], reader),
            _held(ordinal["annotated_original_ast"], reader),
        )
        if local.content != annotated or raw_local.content != raw_annotated:
            raise ValueError("HTML annotated original readback differs from full Source byte transforms")
        local_args = [str(producer_path(custody, reader.root, local.path)), *args[1:]]
        crossref = ordinal["crossref_filter"]
        if crossref is not None:
            if body["crossref_filter"] is None:
                raise ValueError("HTML annotated parser acquired an unselected filter")
            CrossrefFilterReaderOperation(
                operation.source, crossref, reader, scope=scope, run_id=run_id, deadline=operation.deadline
            ).replay()
            wrapper = _held(parent_launcher_binding(parent_observation(crossref, reader)), reader)
            local_args[local_args.index("--filter") + 1] = str(producer_path(custody, reader.root, wrapper.path))
        elif body["crossref_filter"] is not None:
            raise ValueError("HTML annotated parser omitted its actual Source filter")
        annotated_tool = _tool(ordinal["annotated_parser_tool"], reader, run_id, "pandoc", BODY_PURPOSE, local_args)
        original_tool = _tool(
            ordinal["annotated_original_tool"],
            reader,
            run_id,
            "pandoc",
            ORIGINAL_PURPOSE,
            [str(producer_path(custody, reader.root, raw_local.path)), *PARSER_ARGUMENTS],
        )
        if (
            annotated_tool["stdout"].encode() != local_ast.content
            or original_tool["stdout"].encode() != raw_local_ast.content
            or any(
                annotated_tool[key] != actual[key] or original_tool[key] != raw_actual[key]
                for key in ("executable", "executable_sha256")
            )
            or ordinal["annotated_parser_tool"] not in ordinal["tool_bindings"]
            or ordinal["annotated_original_tool"] not in ordinal["tool_bindings"]
        ):
            raise ValueError("HTML annotated readback changed genuine ToolAPI/parser identity")
        positions = require_complete_ordinal_ast_equivalence(local_ast.content, ast.content, anchors)
        raw_positions = require_complete_ordinal_ast_equivalence(raw_local_ast.content, raw_ast.content, anchors)
        expected = [
            {
                "hydration": token,
                "parser_byte_range": list(span),
                "parser_carrier_byte_range": [span[0] - len(anchor.prefix), span[1] + len(anchor.suffix)],
                "ast": position,
                "original_parser_byte_range": list(raw_span),
                "original_parser_carrier_byte_range": [
                    raw_span[0] - len(anchor.prefix),
                    raw_span[1] + len(anchor.suffix),
                ],
                "original_ast": raw_position,
            }
            for token, span, position, raw_span, raw_position, anchor in zip(
                tokens, ranges, positions, raw_ranges, raw_positions, anchors, strict=True
            )
        ]
        if ordinal["occurrences"] != expected:
            raise ValueError("HTML ordinal readback changed/omitted/reordered actual complete occurrence sites")
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("HTML ordinal transported Original custody changed before closing")
    remaining(operation.deadline)
    return ordinal


def _node_at(document: Any, path: list[str | int]) -> Any:
    if len(path) > 100:
        raise ValueError("HTML ordinal native role exceeds its Source AST path bound")
    for member in path:
        document = document[member]
    return document


def _table_native_projection(
    original_id: str,
    projected_roles: list[dict[str, Any]],
    original_tables: list[dict[str, Any]],
    filtered_tables: list[dict[str, Any]],
    native_tables: list[dict[str, Any]],
    allocations: list[dict[str, Any]],
    observed_allocations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Join two actual ordinal identities to every cell of their checked table."""
    index = [i for i, row in enumerate(original_tables) if row["source_id"] == original_id]
    if len(index) != 1 or len(original_tables) != len(filtered_tables):
        return None
    selected = index[0]
    expected = filtered_tables[selected]
    paths = [
        row["ast_path"]
        for row in projected_roles
        if row["kind"] == "Table" and "ast:" + "/".join(map(str, row["ast_path"])) == expected["source_id"]
    ]
    actual = [row for row in native_tables if row["source_id"] == expected["source_id"]]
    cells = [cell["source_id"] for row in expected["rows"] for cell in row["cells"]]
    if (
        len(paths) != 1
        or len(actual) != 1
        or not cells
        or [cell["source_id"] for cell in actual[0]["cells"]] != cells
        or [row["source_id"] for row in allocations] != [row["source_id"] for row in original_tables]
        or len(observed_allocations) != len(original_tables)
        or [row["source_digest"] for row in observed_allocations] != [row["digest"] for row in allocations]
    ):
        return None
    return {
        "role": "complete-HTML-Table",
        "original_table": original_tables[selected],
        "projected_table": expected,
        "table": actual[0],
        "filtered_ast_path": paths[0],
        "column_allocation": observed_allocations[selected],
    }


def html_native_endpoints(
    ast: bytes,
    mapping: dict[str, Any],
    observer: dict[str, Any],
    reader: SnapshotReader,
    *,
    ordinal_occurrence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project checked own-original ordinals to existing complete browser roles.

    Caller first performs its genuine whole browser replay. This DATA projection
    consumes that checked packet; it cannot authenticate a browser from JSON.
    Calibrated Source characters are reconstructed with the existing pure
    adapter from the already authenticated held reference, never recalibrated.
    """
    from infrastructure.reporting.native_code_native_endpoints import selected_ast_roles
    from infrastructure.reporting.native_format_html_glyph_contours import map_source_character_runs
    from infrastructure.reporting.native_format_html_style_calibration import apply_source_style_calibration
    from infrastructure.reporting.native_format_pdf_semantic_plan import strict_ast
    from infrastructure.reporting.native_format_joint_source import require_native_operation

    producer: NativeProducerOperation | None = reader.native_producer_operation
    if producer is not None:
        if current_native_producer_operation() is not producer:
            raise ValueError("HTML endpoints lost their actual live Source owner")
        producer.verify(reader, run_id=producer.run_id, deadline=producer.deadline)
        deadline = producer.deadline
    else:
        deadline = require_native_operation(reader).deadline
    remaining(deadline)
    document = strict_ast(ast)
    browser = observer["observation"]
    source = browser["source_fidelity"]
    if (
        not isinstance(source, dict)
        or source["original_ast_sha256"] != hashlib.sha256(ast).hexdigest()
        or source["characters"]["source_ast_sha256"] != hashlib.sha256(ast).hexdigest()
        or source["digest"] != canonical_digest({key: value for key, value in source.items() if key != "digest"})
        or (ordinal_occurrence is not None and ordinal_occurrence["original_ast"] != mapping)
    ):
        raise ValueError("HTML endpoints require their actual own pre-transform Source AST identity")
    roles = selected_ast_roles(ast, mapping)
    results = []
    residuals: list[str] = []
    filtered_ast = _held(observer["semantic_source"]["body"]["ast"], reader).content
    projected_roles = [] if ordinal_occurrence is None else selected_ast_roles(filtered_ast, ordinal_occurrence["ast"])
    original_contract = observer["semantic_source"]["body"]["original_source"]["survival"]["contract"]
    original_math = observer["semantic_source"]["body"]["original_source"]["survival"]["contract"][
        "mathematical_sources"
    ]
    projected_math = observer["content_contract"]["mathematical_sources"]
    for viewport in browser["viewports"]:
        width = viewport["dom"]["width"]
        dom, fidelity = viewport["dom"], viewport["fidelity"]
        calibrated = source
        if fidelity.get("style_calibration") is not None:
            calibration = _held(fidelity["style_calibration"]["reference"]["native"], reader).json_object()
            calibrated = apply_source_style_calibration(source, calibration["dom"], deadline=deadline)
        characters = calibrated["characters"]
        mapped = map_source_character_runs(characters, dom)
        components, scene, ink = fidelity["components"], fidelity["components"]["glyph_scene"], fidelity["glyph_ink"]
        if components["source_digest"] != calibrated["digest"]:
            raise ValueError("HTML endpoint calibration changed the checked whole Source identity")
        if scene is not None and (
            scene["source_digest"] != characters["digest"]
            or scene["digest"] != canonical_digest({key: value for key, value in scene.items() if key != "digest"})
        ):
            raise ValueError("HTML native glyph scene belongs to another Source character contract")
        if ink is not None and (scene is None or ink["scene_digest"] != scene["digest"]):
            raise ValueError("HTML native glyph ink belongs to another complete Source scene")
        # Preserve actual full Source/semantic/style/paint failures. A located
        # containing role does not substitute for these independent predicates.
        residuals.extend(
            f"HTML:{width}:" + str(value)
            for value in [
                *viewport["findings"],
                *viewport["blockers"],
                *viewport["pixels"]["findings"],
                *viewport["pixels"]["blockers"],
                *fidelity["findings"],
                *fidelity["blockers"],
                *mapped["findings"],
                *mapped["blockers"],
            ]
        )
        run_by_id = {row["source_id"]: row for row in characters["runs"]}
        if len(run_by_id) != len(characters["runs"]):
            raise ValueError("HTML Source character contract repeated a run identity")
        for role in roles:
            path, kind = role["ast_path"], role["kind"]
            identity = "/".join(map(str, path))
            endpoints = []
            if kind in {"Str", "Code", "CodeBlock", "Space", "SoftBreak", "LineBreak"}:
                run = run_by_id.get("glyph-source:" + identity)
                if run is not None:
                    expected = [index for index, char in enumerate(run["text"]) if not char.isspace()]
                    actual = [row for row in mapped["characters"] if row.get("source_run_id") == run["source_id"]]
                    offsets = [row["source_character_offset"] for row in actual]
                    native_ok = offsets == expected and all(
                        dom["text"][row["text_index"]]["characters"][row["character_index"]]["character"]
                        == row["character"]
                        and row["character"] == run["text"][row["source_character_offset"]]
                        and dom["text"][row["text_index"]]["characters"][row["character_index"]]["boxes"]
                        == row["boxes"]
                        and dom["text"][row["text_index"]]["characters"][row["character_index"]]["offset_utf16"]
                        == row["offset_utf16"]
                        for row in actual
                    )
                    lines = (
                        []
                        if scene is None
                        else [
                            row
                            for row in scene["glyphs"]
                            if row.get("shaped_run", {}).get("source_run_id") == run["source_id"]
                        ]
                    )
                    observed = (
                        []
                        if ink is None
                        else [
                            row for row in ink["glyphs"] if any(row["source_id"] == line["source_id"] for line in lines)
                        ]
                    )
                    coverage = [
                        offset
                        for offset in expected
                        if sum(
                            line["shaped_run"]["source_start"] <= offset < line["shaped_run"]["source_end"]
                            for line in lines
                        )
                        == 1
                    ]
                    if (
                        native_ok
                        and expected
                        and coverage == expected
                        and [row["source_id"] for row in observed] == [row["source_id"] for row in lines]
                    ):
                        endpoints.append(
                            {
                                "role": "complete-HTML-Source-run",
                                "source_run": run,
                                "native_characters": actual,
                                "shaped_lines": lines,
                                "native_ink": observed,
                            }
                        )
                    elif native_ok and not expected and kind in {"Space", "SoftBreak", "LineBreak"}:
                        endpoints.append(
                            {
                                "role": "Source-nonpainting-space-in-complete-character-flow",
                                "source_run": run,
                                "flow": run["flow"],
                                "source_digest": characters["digest"],
                            }
                        )
            elif kind == "Table":
                table = _table_native_projection(
                    "ast:" + identity,
                    projected_roles,
                    original_contract["table_sources"],
                    observer["content_contract"]["table_sources"],
                    viewport["structure"]["tables"],
                    source["column_allocation"],
                    components["column_allocation"],
                )
                if table is not None and _node_at(document, path)["t"] == "Table":
                    endpoints.append(table)
            elif kind == "Math":
                # Exact complete ordered Source Math rosters select ordinals;
                # equal payloads never select a first matching native equation.
                expected = [tex for _, tex in original_math]
                regions = viewport["pixels"]["math_regions"]
                if (
                    expected == [tex for _, tex in projected_math] == dom["source_math"]
                    and len(dom["math"]) == len(expected)
                    and [row["math_index"] for row in regions] == list(range(len(expected)))
                ):
                    positions = [
                        index for index, (source_id, _) in enumerate(original_math) if source_id == "ast:" + identity
                    ]
                    if len(positions) == 1:
                        index = positions[0]
                        endpoints.append(
                            {
                                "role": "complete-HTML-ordered-Source-Math-location",
                                "source": original_math[index],
                                "projected": projected_math[index],
                                "native": dom["math"][index],
                                "native_ink_region": regions[index],
                                "claim_boundary": "native location; independent MathJax shaping/ink residuals retained",
                            }
                        )
            if endpoints:
                results.append({**role, "viewport_width": width, "endpoints": endpoints})
            else:
                residuals.append(f"selected-HTML-native-containing-role:{width}:{identity}:{kind}")
    remaining(deadline)
    if not reader.unchanged():
        raise ValueError("HTML endpoint Source/native evidence changed during complete projection")
    return {"roles": results, "residuals": residuals}
