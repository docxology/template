"""Reuse genuine whole-reference custody for Source citation/math predicates.

The enclosing whole reference authenticates Original and independently executes
Current. These records and byte adapters are DATA; they never create an owner.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan, strict_ast
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_scientific_math import (
    _math_body,
    observe_scientific_math_reference,
    scientific_math_from_ast,
)
from infrastructure.reporting.native_pdf_citation_replay import validate_natbib_reference_reproduction
from infrastructure.reporting.native_pdf_citations import citation_occurrences, observe_natbib_reference
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_scientific_reference_replay import replay_scientific_math_reference
from infrastructure.reporting.native_scientific_reference_reproduction import canonical_xdv
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-whole-pdf-semantic-references-v1"


def _manifest(inputs: PDFSourceInputs, ast: bytes) -> dict[str, Any]:
    def rows(items: tuple[tuple[str, bytes], ...]) -> list[dict[str, Any]]:
        return [{"path": path, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)} for path, body in items]

    return {
        "content_sha256": hashlib.sha256(inputs.content).hexdigest(),
        "ast_sha256": hashlib.sha256(ast).hexdigest(),
        "sources": rows(inputs.sources),
        "bibliographies": rows(inputs.bibliographies),
        "config": rows((inputs.config,)),
        "preamble": rows((inputs.preamble,) if inputs.preamble else ()),
        "auxiliary": rows(inputs.auxiliary),
    }


def source_crossref_keys(ast: bytes, *, deadline: float) -> tuple[str, ...]:
    """Only actual typed Source attributes declare fixed Crossref identities.

    A Cite key's prefix alone never excludes it. Dynamic raw labels, formalism
    macros, mixed groups and unselected node roles keep their existing residuals.
    """
    document = strict_ast(ast)
    keys: list[str] = []
    count = 0
    roles = {"Header": "sec:", "Image": "fig:", "Figure": "fig:", "Table": "tbl:", "CodeBlock": "lst:", "Span": "eq:"}

    def walk(value: Any, depth: int = 0) -> None:
        nonlocal count
        remaining(deadline)
        count += 1
        if count > 100_000 or depth > 256:
            raise ValueError("whole PDF declared Crossref census exceeds its existing AST bound")
        if isinstance(value, dict):
            kind, content = value.get("t"), value.get("c")
            if kind in roles:
                index = 1 if kind == "Header" else 0
                if not isinstance(content, list) or len(content) <= index:
                    raise ValueError("whole PDF declared Source attribute is malformed")
                attribute = content[index]
                if not isinstance(attribute, list) or len(attribute) != 3 or not isinstance(attribute[0], str):
                    raise ValueError("whole PDF declared Source attribute is malformed")
                identity = attribute[0]
                if identity.startswith(roles[kind]):
                    if identity in keys:
                        raise ValueError("whole PDF declared Source Crossref identity repeats")
                    keys.append(identity)
            if kind in {"Code", "CodeBlock", "RawInline", "RawBlock"}:
                return
            for child in value.values():
                walk(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1)

    walk(document["blocks"])
    return tuple(keys)


def _math_blockers(ast: bytes) -> list[str]:
    nodes = scientific_math_from_ast(ast)
    try:
        _math_body(nodes)
    except ValueError as error:
        # This pure Source preflight executes before any native invocation.
        # Native tool/clock/custody failures are never converted to unsupported.
        return [f"{node.identity}: independent equation Source interpretation unsupported: {error}" for node in nodes]
    return []


def _citation_blockers(
    inputs: PDFSourceInputs, ast: bytes, crossrefs: tuple[str, ...], *, deadline: float
) -> list[str]:
    """Keep unbound Source identities explicit before any native citation call.

    The ordinary Source bibliography parser supplies the complete declared key
    union. No key prefix, guessed label or subset projection admits a citation.
    """
    from infrastructure.rendering._bibliography import _BIB_ENTRY_RE

    declared: set[str] = set()
    for _, body in inputs.bibliographies:
        remaining(deadline)
        for key in _BIB_ENTRY_RE.findall(body.decode("utf-8")):
            if key.casefold() in declared:
                raise ValueError("whole PDF Source bibliography union repeats a case-insensitive key")
            declared.add(key.casefold())
    _, occurrences, nonvisible, _ = citation_occurrences(ast, deadline=deadline, crossref_keys=crossrefs)
    blockers = []
    for occurrence in occurrences:
        remaining(deadline)
        missing = [key for key in occurrence.keys if key.casefold() not in declared]
        if missing:
            blockers.append(
                f"{occurrence.id}: Source citation identities have no bibliography or "
                f"explicit typed Crossref declaration: {missing}"
            )
    for row in nonvisible:
        if row["kind"] == "nocite":
            missing = [key for key in row["original"]["keys"] if key != "*" and key.casefold() not in declared]
            if missing:
                blockers.append(
                    f"{row['path']}: Source nocite identities have no declared bibliography entries: {missing}"
                )
    return blockers


def _tool_bindings(semantic: dict[str, Any]) -> list[dict[str, str]]:
    tools = list(semantic["citations"]["tool_artifacts"]) if semantic["citations"] is not None else []
    math = semantic["mathematics"]
    if math is not None:
        tools.append(math["reference"]["template_tool_artifact"])
        tools.extend(record["artifact"] for record in math["reference"]["tool_artifacts"])
        tools.extend(math["raster"]["tool_artifacts"])
    return tools


def observe_whole_pdf_semantic_references(
    root: Path,
    directory: Path,
    inputs: PDFSourceInputs,
    ast: bytes,
    *,
    scope: str,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Execute existing independent natbib/math algorithms once for this Source.

    Existing whole-reference instrumented PDF supplies positions, while the
    existing mathematical reference independently interprets every equation.
    No second whole renderer, pipeline, Common suite or owner is introduced.
    """
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.run_id != run_id
        or owner.deadline != deadline
        or owner.source.bindings.current_root != root
    ):
        raise ValueError("whole PDF semantic references require the genuine enclosing live Source owner")
    reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(reader, run_id=run_id, deadline=deadline)
    create_private_native_directory(root, directory)
    crossrefs = source_crossref_keys(ast, deadline=deadline)
    citation_blockers = _citation_blockers(inputs, ast, crossrefs, deadline=deadline)
    citations = None
    if not citation_blockers:
        citations = observe_natbib_reference(
            root,
            directory / "citations",
            ast_bytes=ast,
            sources=inputs.sources,
            bibliographies=inputs.bibliographies,
            config=(inputs.config,),
            preamble=inputs.preamble,
            crossref_keys=crossrefs,
            env=env,
            deadline=deadline,
            run_id=run_id,
            artifact_id="manuscript:pdf",
        )
    mathematics = None
    math_blockers = _math_blockers(ast)
    nodes = scientific_math_from_ast(ast)
    if nodes and not math_blockers:
        leaf = directory / "mathematics"
        create_private_native_directory(root, leaf)
        interpreted = observe_scientific_math_reference(
            root, leaf, ast, inputs, env=env, deadline=deadline, run_id=run_id
        )
        pdf = _file(interpreted["pdf"], reader)
        mathematics = {
            "reference": interpreted,
            "raster": audit_pdf_raster(
                root,
                leaf,
                pdf,
                parse_native_bytes("pdf", pdf.content),
                env=env,
                deadline=deadline,
                run_id=run_id,
                ordinal=0,
            ),
        }
    result = {
        "schema_version": SCHEMA,
        "scope": scope,
        "artifact_id": "manuscript:pdf",
        "run_id": run_id,
        "inputs": _manifest(inputs, ast),
        "crossref_keys": list(crossrefs),
        "citations": citations,
        "citation_blockers": citation_blockers,
        "mathematics": mathematics,
        "math_blockers": math_blockers,
    }
    seen: set[str] = set()
    for binding in _tool_bindings(result):
        remaining(deadline)
        if binding["path"] in seen:
            raise ValueError("whole PDF semantic references repeat an actual ToolAPI event")
        seen.add(binding["path"])
        owner.validate_tool(binding, _file(binding, reader).json_object(), reader, run_id=run_id)
    if not reader.unchanged():
        raise ValueError("whole PDF independent semantic inputs/process/dependency bytes changed")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    return result


def _semantic(
    inputs: PDFSourceInputs, ast: bytes, reference: dict[str, Any], *, deadline: float
) -> dict[str, Any] | None:
    raw: dict[str, Any] | None = reference.get("semantic_references")
    if raw is None:
        return None
    if (
        set(raw)
        != {
            "schema_version",
            "scope",
            "artifact_id",
            "run_id",
            "inputs",
            "crossref_keys",
            "citations",
            "citation_blockers",
            "mathematics",
            "math_blockers",
        }
        or raw["schema_version"] != SCHEMA
        or raw["artifact_id"] != "manuscript:pdf"
        or raw["run_id"] != reference["run_id"]
        or raw["scope"] != reference["source_scope"]
        or raw["inputs"] != _manifest(inputs, ast)
        or raw["crossref_keys"] != list(source_crossref_keys(ast, deadline=deadline))
        or raw["math_blockers"] != _math_blockers(ast)
        or raw["citation_blockers"] != _citation_blockers(inputs, ast, tuple(raw["crossref_keys"]), deadline=deadline)
    ):
        raise ValueError("whole PDF semantic reference differs from exact complete Source/AST/run inputs")
    citation = raw["citations"]
    _, occurrences, nonvisible, blockers = citation_occurrences(
        ast, deadline=deadline, crossref_keys=tuple(raw["crossref_keys"])
    )
    if (citation is None) != bool(raw["citation_blockers"]):
        raise ValueError("whole PDF citation reference silently omits applicable complete Source occurrences")
    expected_inputs = {
        key: raw["inputs"][key] for key in ("sources", "bibliographies", "config", "preamble", "ast_sha256")
    }
    expected_inputs["crossref_keys"] = raw["crossref_keys"]
    if citation is not None and (
        citation["inputs"] != expected_inputs
        or citation["run_id"] != raw["run_id"]
        or citation["artifact_id"] != raw["artifact_id"]
        or citation["nonvisible"] != list(nonvisible)
        or citation["blockers"] != list(blockers)
        or [(row["id"], row["keys"], row["source"]) for row in citation["occurrences"]]
        != [(row.id, list(row.keys), row.source) for row in occurrences]
    ):
        raise ValueError("whole PDF independent citation occurrence ledger differs from its complete original AST")
    nodes = scientific_math_from_ast(ast)
    if (raw["mathematics"] is None) != (not nodes or bool(raw["math_blockers"])):
        raise ValueError("whole PDF mathematical reference silently omits selected Source equations")
    if raw["mathematics"] is not None:
        if set(raw["mathematics"]) != {"reference", "raster"}:
            raise ValueError("whole PDF independent equation reference/raster roles differ")
        math = raw["mathematics"]["reference"]
        if (
            math["nodes"] != [asdict(node) for node in nodes]
            or math["source_ast_sha256"] != raw["inputs"]["ast_sha256"]
        ):
            raise ValueError("whole PDF independent equation interpretation changes exact Source occurrences")
    return raw


def whole_pdf_semantic_inputs(
    inputs: PDFSourceInputs, ast: bytes, reference: dict[str, Any] | None, reader: SnapshotReader, *, deadline: float
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    """Select already authenticated reference bytes; this grants no authority."""
    remaining(deadline)
    semantic = _semantic(inputs, ast, reference, deadline=deadline) if reference is not None else None
    if semantic is None:
        _, citations, nonvisible, _ = citation_occurrences(
            ast, deadline=deadline, crossref_keys=source_crossref_keys(ast, deadline=deadline)
        )
        blockers = []
        if citations or any(row["kind"] != "declared-crossref" for row in nonvisible):
            blockers.append("same-Source original/current selected citation reference admission is absent")
        if scientific_math_from_ast(ast):
            blockers.append("same-Source original/current selected equation reference admission is absent")
        return None, None, blockers
    citation = semantic["citations"]
    mathematics = None
    if semantic["mathematics"] is not None:
        interpreted = semantic["mathematics"]["reference"]
        references = reference["references"] if reference is not None else {}
        if set(references) != {"instrumented", "uninstrumented"}:
            raise ValueError("whole PDF equation position reference omits instrumented/native whole Source")
        source_tex = _file(reference["projection"]["source_tex"], reader).content if reference is not None else b""
        mathematics = {
            "ast_bytes": ast,
            "source_tex": source_tex,
            "instrumented_pdf": _file(references["instrumented"]["pdf"], reader).content,
            "interpreted_pdf": _file(interpreted["pdf"], reader).content,
            "interpreted_rasters": tuple(
                _file({"path": row["path"], "sha256": row["sha256"]}, reader).content
                for row in semantic["mathematics"]["raster"]["rasters"]
            ),
        }
    remaining(deadline)
    return (
        citation,
        mathematics,
        [
            *(citation["blockers"] if citation is not None else semantic["citation_blockers"]),
            *semantic["math_blockers"],
        ],
    )


def _math_dependencies(math: dict[str, Any]) -> list[tuple[str, str, int]]:
    # Complete FLS/backend/current implementation validation runs through the
    # existing scientific reference reader before this portable identity compare.
    return sorted(
        (Path(row["resolved_path"]).name, row["sha256"], row["size_bytes"]) for row in math["dependencies_before"]
    )


def _math_rasters(
    math: dict[str, Any], reader: SnapshotReader, *, run_id: str, root_label: Path, directory: Path, deadline: float
) -> tuple[bytes, ...]:
    raw, reference = math["raster"], math["reference"]
    if set(raw) != {"dpi", "input_artifact", "rasters", "tool_artifacts"} or raw["dpi"] != 150:
        raise ValueError("whole PDF interpreted equation raster fieldset/scale differs")
    pdf = _file(reference["pdf"], reader)
    if _file(raw["input_artifact"], reader).content != pdf.content or len(raw["tool_artifacts"]) != 2:
        raise ValueError("whole PDF equation raster did not consume its actual independent reference PDF")
    tools = (
        (
            "pdftoppm",
            "raster-0000",
            ["-r", "150", "-png", str(directory / "input-0000.pdf"), str(directory / "raster-0000")],
        ),
        ("pdffonts", "fonts-0000", [str(directory / "input-0000.pdf")]),
    )
    for binding, (name, purpose, arguments) in zip(raw["tool_artifacts"], tools, strict=True):
        tool = _tool(binding, reader, run_id, name, purpose, arguments)
        native = _file(tool["native_process_artifact"], reader).json_object()
        if native["cwd"] != str(root_label):
            raise ValueError("whole PDF interpreted equation raster changes its genuine Source working directory")
    pages = parse_native_bytes("pdf", pdf.content)["pages"]
    rows = raw["rasters"]
    if len(rows) != pages:
        raise ValueError("whole PDF interpreted equation raster omits native pages or their order")
    rasters = []
    for index, row in enumerate(rows, 1):
        remaining(deadline)
        name = f"raster-0000-{index:0{len(str(pages))}d}.png"
        if row["path"] != (directory.relative_to(root_label) / name).as_posix():
            raise ValueError("whole PDF interpreted equation raster role differs from the fixed native command")
        rasters.append(_file({"path": row["path"], "sha256": row["sha256"]}, reader).content)
    return tuple(rasters)


def replay_whole_pdf_semantic_references(
    inputs: PDFSourceInputs,
    ast: bytes,
    original: dict[str, Any],
    current: dict[str, Any],
    reader: SnapshotReader,
    current_reader: SnapshotReader,
    *,
    scope: str,
    original_run_id: str,
    current_run_id: str,
    original_root: Path,
    current_root: Path,
    original_directory: Path,
    current_directory: Path,
    deadline: float,
) -> dict[str, Any]:
    """Authenticate Original tools and consume the one genuine fresh rerun."""
    before, after = (
        _semantic(inputs, ast, original, deadline=deadline),
        _semantic(inputs, ast, current, deadline=deadline),
    )
    if (before is None) != (after is None):
        raise ValueError("whole PDF current semantic reference applicability differs from Original")
    if before is None or after is None:
        return {"status": "blocked", "blockers": ["same-Source original/current semantic reference is unavailable"]}
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.run_id != current_run_id
        or owner.deadline != deadline
        or current_reader.native_producer_operation is not owner
        or before["scope"] != scope
        or after["scope"] != scope
        or before["run_id"] != original_run_id
        or after["run_id"] != current_run_id
    ):
        raise ValueError("whole PDF semantic replay lacks its actual enclosing Current owner/Source/run/clock")
    owner.verify(current_reader, run_id=current_run_id, deadline=deadline)
    for binding in _tool_bindings(after):
        owner.validate_tool(
            binding, _file(binding, current_reader).json_object(), current_reader, run_id=current_run_id
        )
    # Consume the one genuine fresh natbib cohort, avoiding another compile.
    old_citation, fresh_citation = before["citations"], after["citations"]
    if (old_citation is None) != (fresh_citation is None):
        raise ValueError("whole PDF current citation applicability differs from Original")
    if old_citation is not None and fresh_citation is not None:
        for binding in old_citation["tool_artifacts"]:
            value = _file(binding, reader).json_object()
            _tool(binding, reader, original_run_id, value["tool"], value["purpose"], value["command"][1:])
        validate_natbib_reference_reproduction(old_citation, reader, fresh_citation, fresh_reader=current_reader)
    old_math, fresh_math = before["mathematics"], after["mathematics"]
    parity = None
    if old_math is not None and fresh_math is not None:
        old_reference, fresh_reference = old_math["reference"], fresh_math["reference"]
        old_replay = replay_scientific_math_reference(
            old_reference,
            ast,
            inputs,
            read_artifact=lambda binding: _file(binding, reader).content,
            producer_path=lambda path: str(original_root) if path == "." else str(original_root / path),
            run_id=original_run_id,
            deadline=deadline,
            native_reader=reader,
        )
        fresh_replay = replay_scientific_math_reference(
            fresh_reference,
            ast,
            inputs,
            read_artifact=lambda binding: _file(binding, current_reader).content,
            producer_path=lambda path: str(current_root) if path == "." else str(current_root / path),
            run_id=current_run_id,
            deadline=deadline,
            native_reader=current_reader,
        )
        old_bindings = [
            old_reference["template_tool_artifact"],
            *(row["artifact"] for row in old_reference["tool_artifacts"]),
        ]
        new_bindings = [
            fresh_reference["template_tool_artifact"],
            *(row["artifact"] for row in fresh_reference["tool_artifacts"]),
        ]
        for old_binding, new_binding in zip(old_bindings, new_bindings, strict=True):
            old_tool, new_tool = (
                _file(old_binding, reader).json_object(),
                _file(new_binding, current_reader).json_object(),
            )
            # Both tools were authenticated by the existing scientific reader;
            # basic ToolAPI keeps actual CWD in its bound native process packet.
            old_process = _file(old_tool["native_process_artifact"], reader).json_object()
            new_process = _file(new_tool["native_process_artifact"], current_reader).json_object()
            if (
                old_tool["executable_sha256"] != new_tool["executable_sha256"]
                or old_process["cwd"] != str(original_root)
                or new_process["cwd"] != str(current_root)
            ):
                raise ValueError("whole PDF independent equation tool body/Source working directory differs")
        if _math_dependencies(old_reference) != _math_dependencies(fresh_reference):
            raise ValueError("whole PDF Current independent equation package/font byte closure differs")
        for label in ("discovery", "final"):
            if canonical_xdv(_file(old_reference["backend_inputs"][label], reader).content) != canonical_xdv(
                _file(fresh_reference["backend_inputs"][label], current_reader).content
            ):
                raise ValueError("whole PDF Current independently interpreted equation instructions differ")
        if (
            old_replay["source_nodes"] != fresh_replay["source_nodes"]
            or old_replay["reference_vectors"] != fresh_replay["reference_vectors"]
        ):
            raise ValueError("whole PDF Current independently interpreted equation Source/vector census differs")
        old_pixels = _math_rasters(
            old_math,
            reader,
            run_id=original_run_id,
            root_label=original_root,
            directory=original_directory / "semantics/mathematics",
            deadline=deadline,
        )
        fresh_pixels = _math_rasters(
            fresh_math,
            current_reader,
            run_id=current_run_id,
            root_label=current_root,
            directory=current_directory / "semantics/mathematics",
            deadline=deadline,
        )
        parity = inspect_pdf_reference_parity(
            _file(old_reference["pdf"], reader).content,
            _file(fresh_reference["pdf"], current_reader).content,
            old_pixels,
            fresh_pixels,
            deadline=deadline,
        )
        if parity["status"] != "pass" or parity["findings"]:
            raise ValueError("whole PDF Current interpreted equations differ in actual glyph/vector/every-page ink")
    if not reader.unchanged() or not current_reader.unchanged():
        raise ValueError("whole PDF original/current semantic process/input bytes changed during replay")
    owner.verify(current_reader, run_id=current_run_id, deadline=deadline)
    return {
        "status": "reproduced",
        "blockers": [
            *(fresh_citation["blockers"] if fresh_citation is not None else after["citation_blockers"]),
            *after["math_blockers"],
        ],
        "math_occurrences": len(scientific_math_from_ast(ast)),
        "citation_occurrences": len(fresh_citation["occurrences"]) if fresh_citation is not None else None,
        "interpreted_math_parity": parity,
    }


def citation_occurrence_positions(
    plan: PDFSemanticPlan, citations: dict[str, Any] | None, *, deadline: float
) -> dict[str, list[dict[str, Any]]]:
    """All actual supported citation glyphs supply their exact Source controls."""
    remaining(deadline)
    if citations is None:
        return {}
    matches = {row["occurrence_id"]: row for row in citations["matches"]}
    glyphs = {row["glyph_index"]: row for row in citations["observed_glyphs"]}
    if len(matches) != len(citations["matches"]) or len(glyphs) != len(citations["observed_glyphs"]):
        raise ValueError("whole PDF citation control glyph/occurrence membership is ambiguous")
    positions = {}
    for occurrence in plan.occurrences:
        remaining(deadline)
        ids = (
            [occurrence["citation_reference_id"]]
            if "citation_reference_id" in occurrence
            else occurrence.get("raw_citation_reference_ids", [])
        )
        if not ids:
            continue
        selected: list[dict[str, Any]] = []
        for identity in ids:
            match = matches.get(identity)
            indices = match["glyph_indices"] if match is not None else []
            if not indices or any(
                index not in glyphs
                or glyphs[index].get("geometry_supported") is not True
                or "roi_px" not in glyphs[index]
                for index in indices
            ):
                selected = []
                break
            selected.extend({"page": glyphs[index]["page"], "box_pt": glyphs[index]["box_pt"]} for index in indices)
        if selected:
            positions["occurrence:" + occurrence["identity"]] = selected
    return positions
