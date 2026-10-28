"""Original whole-PDF native custody and fresh current full-reference replay.

An externally held original operation supplies authority. Reference equality
does not discharge unsupported Source nodes, scientific values or controls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_pdf_whole_reference import observe_pdf_whole_reference
from infrastructure.reporting.native_pdf_citation_runtime import dependency_identity
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _dependencies(original: dict[str, Any], current: dict[str, Any], reader: SnapshotReader) -> None:
    for raw in (original, current):
        if (
            raw["schema_version"] != "template-native-citation-dependency-observation-v1"
            or raw["phase"] != "fresh-reference-after-discovery"
            or raw["before"] != raw["after"]
            or raw["style_before"] != raw["style_after"]
            or raw["dependency_identity"] != dependency_identity(raw["before"])
            or len(raw["retained"]) != len(raw["before"]) + 1
        ):
            raise ValueError("whole PDF original/current dependency/FLS custody differs")
        for retained, observed in zip(raw["retained"], [*raw["before"], raw["style_before"]], strict=True):
            if {key: retained[key] for key in ("path", "name", "sha256", "bytes")} != observed:
                raise ValueError("whole PDF retained dependency census differs from actual observation")
            content = _file(retained["artifact"], reader)
            if content.sha256 != observed["sha256"] or len(content.content) != observed["bytes"]:
                raise ValueError("whole PDF retained package/font bytes changed")
    if original["dependency_identity"] != current["dependency_identity"] or dependency_identity(
        [original["style_before"]]
    ) != dependency_identity([current["style_before"]]):
        raise ValueError("whole PDF independently current package/font/style bytes differ from original")


def _compile_tools(original: dict[str, Any], current: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
    xelatex = [
        "-fmt=xelatex",
        "-progname=xelatex",
        "-no-pdf",
        "-recorder",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-no-shell-escape",
        "oracle.tex",
    ]
    expected = []
    for phase in ("discovery", "reference"):
        for ordinal, tool in enumerate(("xelatex", "bibtex", "xelatex", "xelatex"), 1):
            expected.append((tool, f"{phase}-{ordinal:02d}-{tool}", xelatex if tool == "xelatex" else ["oracle"]))
        expected.append(
            ("xdvipdfmx", phase + "-native-backend", ["--kpathsea-debug=4", "-vv", "-o", "oracle.pdf", "oracle.xdv"])
        )
        if phase == "discovery":
            expected.append(("kpsewhich", "style-resolution", ["plainnat.bst"]))
    if len(original["tool_artifacts"]) != len(expected) or len(current["tool_artifacts"]) != len(expected):
        raise ValueError("whole PDF reference lacks its complete actual compile/backend/style process cohort")
    for binding, fresh, (tool, purpose, arguments) in zip(
        original["tool_artifacts"], current["tool_artifacts"], expected, strict=True
    ):
        actual = _tool(binding, reader, run_id, tool, purpose, arguments)
        new = _file(fresh, reader).json_object()
        if any(actual[key] != new[key] for key in ("executable", "executable_sha256")):
            raise ValueError("whole PDF reference independently nominated current executable differs")


def _raster(
    original: dict[str, Any],
    current: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    original_directory: Path,
) -> None:
    held = original["raster"]
    fresh = current["raster"]
    if set(held) != {"dpi", "input_artifact", "rasters", "tool_artifacts"} or held["dpi"] != 150:
        raise ValueError("whole PDF reference raster omitted its complete native input/page/tool witness")
    consumed = _file(held["input_artifact"], reader)
    if consumed.content != _file(original["pdf"], reader).content or len(held["tool_artifacts"]) != 2:
        raise ValueError("whole PDF reference raster consumed another original PDF")
    if [{"path": row["path"], "sha256": row["sha256"]} for row in held["rasters"]] != original["rasters"]:
        raise ValueError("whole PDF complete raster identities differ")
    for binding, fresh_binding, (tool, purpose, arguments) in zip(
        held["tool_artifacts"],
        fresh["tool_artifacts"],
        (
            (
                "pdftoppm",
                "raster-0000",
                [
                    "-r",
                    "150",
                    "-png",
                    str(original_directory / "input-0000.pdf"),
                    str(original_directory / "raster-0000"),
                ],
            ),
            ("pdffonts", "fonts-0000", [str(original_directory / "input-0000.pdf")]),
        ),
        strict=True,
    ):
        actual = _tool(binding, reader, run_id, tool, purpose, arguments)
        current_tool = _file(fresh_binding, reader).json_object()
        if any(actual[key] != current_tool[key] for key in ("executable", "executable_sha256")):
            raise ValueError("whole PDF raster current independently nominated executable differs")


def replay_whole_pdf_reference(
    root: Path,
    directory: Path,
    scope: str,
    original_binding: dict[str, str],
    inputs: PDFSourceInputs,
    current_ast: bytes,
    reader: SnapshotReader,
    *,
    run_id: str,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Recompile actual complete Source and compare every original native page."""
    operation = require_native_operation(reader)
    owner = current_native_producer_operation()
    if (
        deadline != operation.deadline
        or owner is None
        or owner.source is not operation.source
        or owner.run_id != operation.source.bindings.run_id
        or owner.deadline != deadline
        or reader.native_producer_operation is not None
    ):
        raise ValueError("whole PDF replay needs separate genuine original and live current Source ownership")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    authority = authenticate_original_native_artifact(
        original_binding,
        reader,
        run_id=run_id,
        required_sdk_modules=(
            "reporting/native_format_pdf_whole_reference.py",
            "reporting/native_format_pdf_projection.py",
            "reporting/native_tool_process.py",
            "reporting/native_pdf_whole_semantic_references.py",
            "reporting/native_pdf_citations.py",
            "reporting/native_pdf_citation_replay.py",
            "reporting/native_scientific_reference_replay.py",
            "reporting/native_scientific_reference_reproduction.py",
        ),
    )
    original = authority["event"].json_object()
    if (
        original["schema_version"] != "template-native-whole-source-pdf-reference-v3"
        or original["run_id"] != run_id
        or original["source_scope"] != scope
        or original["sdk_context"] != authority["source"]
        or _file(original["source_ast"], reader).content != current_ast
    ):
        raise ValueError("whole PDF reference differs from actual complete current Source AST")
    current_reader = SnapshotReader(root, native_operation=operation, native_producer_operation=owner)
    current = observe_pdf_whole_reference(
        root,
        directory,
        inputs,
        current_ast,
        env=env,
        deadline=deadline,
        run_id=owner.run_id,
        sdk_context=json.loads(operation.source.descriptor(scope, deadline=deadline)),
        source_scope=scope,
        declared_tex_dependencies=tuple(
            {"texmf_relative": row["texmf_relative"], "artifact": row["declared_artifact"]}
            for row in original.get("declared_tex_dependencies", ())
        ),
    )
    # Every original path is a label. The current rerun reads only current
    # admitted Source and portable retained dependency/input bytes.
    old_projection, new_projection = original["projection"], current["projection"]
    if len(original["implementation"]) != len(current["implementation"]):
        raise ValueError("whole PDF complete retained Source implementation roster differs")
    for retained, actual in zip(original["implementation"], current["implementation"], strict=True):
        if (
            set(retained) != {"original_path", "sha256", "artifact"}
            or Path(retained["original_path"]).name != Path(actual["original_path"]).name
            or retained["sha256"] != actual["sha256"]
            or _file(retained["artifact"], reader).sha256 != retained["sha256"]
        ):
            raise ValueError("whole PDF original retained helper bytes differ from genuine current Source")
    for field in ("source_inputs", "blockers", "custody_blockers", "source_scope"):
        if old_projection[field] != new_projection[field]:
            raise ValueError("whole PDF original/current complete Source projection differs")
    old_markdown = _file(old_projection["markdown"], reader)
    if (
        old_markdown.content != inputs.content
        or _file(new_projection["markdown"], current_reader).content != inputs.content
    ):
        raise ValueError("whole PDF projection consumed different complete reconstructed Markdown")
    original_root = Path(authority["source"]["current_mirror"]["root"])
    original_directory = original_root / Path(original_binding["path"]).parent
    original_parser = _tool(
        original["source_ast_parser_artifact"],
        reader,
        run_id,
        "pandoc",
        "whole-reference-original-source-ast",
        [
            str(original_root / old_projection["markdown"]["path"]),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=json",
        ],
    )
    if original_parser["stdout"].encode() != current_ast:
        raise ValueError("whole PDF original actual parser stdout differs from current complete Source")
    if len(old_projection["tool_artifacts"]) != 2 or len(new_projection["tool_artifacts"]) != 2:
        raise ValueError("whole PDF projection omitted its actual Crossref/Pandoc cohort")
    _tool(
        old_projection["tool_artifacts"][0], reader, run_id, "pandoc-crossref", "source-crossref-version", ["--version"]
    )
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation

    CrossrefFilterReaderOperation(
        operation.source, old_projection["crossref_filter"], reader, scope=scope, run_id=run_id, deadline=deadline
    ).replay()
    old_arguments = old_projection["pandoc_arguments"]
    current_arguments = new_projection["pandoc_arguments"]
    old_child = _file(old_projection["crossref_filter"], reader).json_object()
    current_child = _file(new_projection["crossref_filter"], current_reader).json_object()
    old_wrapper = str(original_root / old_child["launcher"]["path"])
    new_wrapper = str(root / current_child["launcher"]["path"])
    old_projection_directory = original_directory / "projection"
    new_projection_directory = directory / "projection"
    normalized = [
        old_wrapper
        if argument == new_wrapper
        else argument.replace(str(new_projection_directory), str(old_projection_directory))
        for argument in current_arguments
    ]
    if normalized != old_arguments:
        raise ValueError("whole PDF original Source-selected writer argv differs from fresh current Source")
    _tool(old_projection["tool_artifacts"][1], reader, run_id, "pandoc", "source-only-pdf-projection", old_arguments)
    if (
        _file(old_projection["source_tex"], reader).content
        != _file(new_projection["source_tex"], current_reader).content
        or original["math_bindings"] != current["math_bindings"]
        or original["raw_source_obligations"] != current["raw_source_obligations"]
        or original["blockers"] != current["blockers"]
    ):
        raise ValueError("whole PDF exact Source TeX/math/raw obligation reconstruction differs")
    parity = {}
    old_refs, new_refs = original.get("references", {}), current.get("references", {})
    if set(old_refs) != set(new_refs):
        raise ValueError("whole PDF complete original/current reference cohort differs")
    for label in ("uninstrumented", "instrumented"):
        if label not in old_refs:
            continue
        old, fresh = old_refs[label], new_refs[label]
        _dependencies(old["dependency_custody"], fresh["dependency_custody"], reader)
        _compile_tools(old, fresh, reader, run_id=run_id)
        if "raster" not in old or "raster" not in fresh:
            raise ValueError("whole PDF compiled reference lacks a complete original/current native raster")
        _raster(old, fresh, reader, run_id=run_id, original_directory=original_directory / label)
        parity[label] = inspect_pdf_reference_parity(
            _file(old["pdf"], reader).content,
            _file(fresh["pdf"], current_reader).content,
            tuple(_file(binding, reader).content for binding in old["rasters"]),
            tuple(_file(binding, current_reader).content for binding in fresh["rasters"]),
            deadline=deadline,
        )
        if parity[label]["status"] != "pass":
            raise ValueError("whole PDF current independently reproduced reference differs on native pages")
    if set(old_refs) == {"uninstrumented", "instrumented"}:
        noninterference = inspect_pdf_reference_parity(
            _file(old_refs["instrumented"]["pdf"], reader).content,
            _file(old_refs["uninstrumented"]["pdf"], reader).content,
            tuple(_file(binding, reader).content for binding in old_refs["instrumented"]["rasters"]),
            tuple(_file(binding, reader).content for binding in old_refs["uninstrumented"]["rasters"]),
            deadline=deadline,
        )
        if original["instrumentation_noninterference"] != noninterference:
            raise ValueError("whole PDF retained original instrumentation parity differs from actual native bytes")
    from infrastructure.reporting.native_pdf_whole_semantic_references import replay_whole_pdf_semantic_references

    semantic_replay = replay_whole_pdf_semantic_references(
        inputs,
        current_ast,
        original,
        current,
        reader,
        current_reader,
        scope=scope,
        original_run_id=run_id,
        current_run_id=owner.run_id,
        original_root=original_root,
        current_root=root,
        original_directory=original_directory,
        current_directory=directory,
        deadline=deadline,
    )
    owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
    operation.verify(reader)
    remaining(deadline)
    return {
        "schema_version": "template-native-whole-pdf-current-reproduction-v1",
        "original_run_id": run_id,
        "current_run_id": owner.run_id,
        "current_reference": current,
        "every_page_reproduction": parity,
        "original_blockers": original["blockers"],
        "semantic_reproduction": semantic_replay,
        "status": "blocked",
    }
