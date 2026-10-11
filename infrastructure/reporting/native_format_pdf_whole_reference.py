"""Callable bounded complete-source PDF reference and zero-glyph math custody."""

from __future__ import annotations

import hashlib
import importlib
import json
import time
from pathlib import Path
from typing import Any, cast

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import (
    audit_pdf_raster,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_pdf_positions import (
    instrument_source_math_positions,
    source_math_paint_from_pdf,
    source_math_positions_from_aux,
)
from infrastructure.reporting.native_format_pdf_projection import observe_pdf_source_projection
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_scientific_math import scientific_math_from_ast
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, compile_reference
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def _binding(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _raw_obligations(ast: bytes) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    count = 0

    def walk(value: Any, path: str) -> None:
        nonlocal count
        count += 1
        if count > 100_000:
            raise ValueError("complete-source raw node census exceeds its finite budget")
        if isinstance(value, dict):
            if value.get("t") in {"RawInline", "RawBlock"}:
                kind, source = value["c"]
                rows.append({"identity": path, "format": kind, "sha256": hashlib.sha256(source.encode()).hexdigest()})
            for key, child in value.items():
                walk(child, f"{path}/{key}")
        elif isinstance(value, list):
            for ordinal, child in enumerate(value):
                walk(child, f"{path}/{ordinal}")

    walk(json.loads(ast), "source")
    return rows


def observe_pdf_whole_reference(
    root: Path,
    directory: Path,
    inputs: PDFSourceInputs,
    ast_bytes: bytes,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    sdk_context: dict[str, Any] | None = None,
    declared_tex_dependencies: tuple[dict[str, Any], ...] = (),
    source_scope: str | None = None,
) -> dict[str, Any]:
    """Retain a real complete reference and prove instrumentation noninterference.

    The directory must be fresh. The enclosing worker must independently admit
    hydrated source/domain provenance and complete SDK custody. This component
    retains those unresolved obligations; it cannot admit a publication itself.
    """
    started = time.monotonic()
    budget = deadline - started
    if not 0 < budget <= 3600:
        raise ValueError("complete-source reference requires an original finite budget")
    create_private_native_directory(root, directory)
    ast_path = directory / "admitted-original.ast.json"
    atomic_write_bytes_confined(root, ast_path, ast_bytes, mode=0o600)
    implementations: list[dict[str, Any]] = []
    for ordinal, name in enumerate(
        (
            __name__,
            observe_pdf_source_projection.__module__,
            instrument_source_math_positions.__module__,
            inspect_pdf_reference_parity.__module__,
            scientific_math_from_ast.__module__,
            CitationRuntime.__module__,
            "infrastructure.reporting.native_pdf_whole_semantic_references",
            "infrastructure.reporting.native_pdf_citations",
            "infrastructure.reporting.native_pdf_citation_replay",
            "infrastructure.reporting.native_scientific_reference_replay",
            "infrastructure.reporting.native_scientific_reference_reproduction",
        )
    ):
        path = Path(cast(str, importlib.import_module(name).__file__)).resolve(strict=True)
        content = path.read_bytes()
        retained = directory / "implementation" / f"{ordinal:02d}-{path.name}.bin"
        atomic_write_bytes_confined(root, retained, content, mode=0o600)
        implementations.append(
            {
                "original_path": str(path),
                "sha256": hashlib.sha256(content).hexdigest(),
                "artifact": _binding(root, retained),
            }
        )
    projection = observe_pdf_source_projection(
        root, directory / "projection", inputs, env=env, deadline=deadline, run_id=run_id, source_scope=source_scope
    )
    original_parser = native_tool_record(
        root,
        directory,
        "pandoc",
        [
            str(root / projection["markdown"]["path"]),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=json",
        ],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="whole-reference-original-source-ast",
    )
    parser_receipt = json.loads(SnapshotReader(root).read(original_parser["artifact"]["path"]).content)
    if (
        parser_receipt["original_exit_code"] != 0
        or parser_receipt["exit_code"] != 0
        or parser_receipt["stdout"].encode() != ast_bytes
    ):
        raise ValueError("complete-source reference AST differs from actual original source parsing")
    nodes = scientific_math_from_ast(ast_bytes)
    original_tex = SnapshotReader(root).read(projection["source_tex"]["path"]).content
    instrumented, bindings, position_blockers = instrument_source_math_positions(original_tex.decode(), nodes)
    blockers = [*projection["blockers"], *projection["custody_blockers"], *position_blockers]
    raw = _raw_obligations(ast_bytes)
    if raw:
        blockers.append("original raw source nodes require independent per-node semantic/layout admission")
    blockers.append(
        "source/domain/hydrated provenance and portable original process replay require enclosing admission"
    )
    if sdk_context is None:
        blockers.append("complete SDK source custody requires the enclosing authenticated native specification")
    common = {
        "schema_version": "template-native-whole-source-pdf-reference-v3",
        "source_scope": source_scope,
        "run_id": run_id,
        "source_ast": _binding(root, ast_path),
        "source_ast_parser_artifact": original_parser["artifact"],
        "projection": projection,
        "implementation": implementations,
        "sdk_context": sdk_context,
        "raw_source_obligations": raw,
        "math_bindings": list(bindings),
        "semantic_references": None,
        "blockers": blockers,
        "execution_budget_seconds": budget,
    }
    # Never compile unresolved external inputs or silently partial Math ledgers.
    if projection["blockers"] or position_blockers or len(bindings) != len(nodes):
        return {**common, "component_status": "blocked", "elapsed_seconds": time.monotonic() - started}
    if not inputs.bibliographies:
        return {
            **common,
            "component_status": "blocked",
            "blockers": blockers + ["full BibTeX source reference requires declared bibliography inputs"],
            "elapsed_seconds": time.monotonic() - started,
        }
    references = {}
    native_inputs = {}
    environment = dict(env)
    for variable, name in (("TEXMFHOME", "texmfhome"), ("TEXMFCONFIG", "texmfconfig"), ("TEXMFVAR", "texmfvar")):
        private = directory / name
        private.mkdir(mode=0o700)
        environment[variable] = str(private)
    environment.update({"openin_any": "p", "openout_any": "p"})
    if len(declared_tex_dependencies) > 128:
        raise ValueError("declared private TeX package closure exceeds its finite file budget")
    package_inputs = []
    package_bytes = 0
    package_names = set()
    for dependency in declared_tex_dependencies:
        relative = Path(dependency["texmf_relative"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[:2] != ("tex", "latex")
            or relative.suffix != ".sty"
        ):
            raise ValueError("declared private TeX package path is not a confined style input")
        if relative.as_posix() in package_names:
            raise ValueError("declared private TeX packages have ambiguous paths")
        package_names.add(relative.as_posix())
        snapshot = SnapshotReader(root).read(dependency["artifact"]["path"])
        if snapshot.sha256 != dependency["artifact"]["sha256"]:
            raise ValueError("declared private TeX package bytes differ from their retained identity")
        package_bytes += len(snapshot.content)
        if package_bytes > 8 * 1024 * 1024:
            raise ValueError("declared private TeX package closure exceeds its aggregate byte budget")
        target = Path(environment["TEXMFHOME"]) / relative
        atomic_write_bytes_confined(root, target, snapshot.content, mode=0o600)
        package_inputs.append(
            {
                "texmf_relative": relative.as_posix(),
                "declared_artifact": dependency["artifact"],
                "consumed_artifact": _binding(root, target),
            }
        )

    for label, tex in (("uninstrumented", original_tex), ("instrumented", instrumented.encode())):
        runtime = CitationRuntime(root, directory / label, env=environment, deadline=deadline, run_id=run_id)
        for bibliography_path, content in inputs.bibliographies:
            runtime.freeze(Path(bibliography_path).name, content)
        pdf, custody = compile_reference(runtime, tex)
        reader = SnapshotReader(root)
        pdf_snapshot = reader.read((runtime.directory / "oracle.pdf").relative_to(root).as_posix())
        if pdf_snapshot.content != pdf:
            raise ValueError("complete-source compiled PDF changed before bounded raster admission")
        try:
            preflight_pdf_streams(pdf, deadline=deadline, max_objects=4_000_000)
        except ValueError as error:
            references[label] = {
                "pdf": {"path": pdf_snapshot.relative, "sha256": pdf_snapshot.sha256},
                "dependency_custody": custody,
                "tool_artifacts": runtime.tools,
            }
            return {
                **common,
                "references": references,
                "declared_tex_dependencies": package_inputs,
                "component_status": "blocked",
                "admission_status": "blocked",
                "blockers": [*blockers, str(error)],
                "elapsed_seconds": time.monotonic() - started,
            }
        raster = audit_pdf_raster(
            root,
            runtime.directory,
            pdf_snapshot,
            parse_native_bytes("pdf", pdf),
            env=environment,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
        raster_bindings = [{"path": row["path"], "sha256": row["sha256"]} for row in raster["rasters"]]
        held = []
        for binding in raster_bindings:
            snapshot = reader.read(binding["path"])
            if snapshot.sha256 != binding["sha256"]:
                raise ValueError("complete-source raster changed after bounded inspection")
            held.append(snapshot.content)
        if not reader.unchanged():
            raise ValueError("complete-source raster inputs changed during inspection")
        native_inputs[label] = pdf, tuple(held)
        references[label] = {
            "pdf": _binding(root, runtime.directory / "oracle.pdf"),
            "tex": _binding(root, runtime.directory / "oracle.tex"),
            "aux": _binding(root, runtime.directory / "oracle.aux"),
            "dependency_custody": custody,
            "tool_artifacts": runtime.tools,
            "raster_tool_artifact": raster["tool_artifacts"][0],
            "raster_tool_artifacts": raster["tool_artifacts"],
            "rasters": raster_bindings,
            "raster": raster,
        }
    positions = source_math_positions_from_aux((directory / "instrumented" / "oracle.aux").read_bytes(), bindings)
    paint = source_math_paint_from_pdf(native_inputs["instrumented"][0], bindings, deadline=deadline)
    parity = inspect_pdf_reference_parity(
        native_inputs["instrumented"][0],
        native_inputs["uninstrumented"][0],
        native_inputs["instrumented"][1],
        native_inputs["uninstrumented"][1],
        deadline=deadline,
    )
    semantic = None
    if source_scope is not None:
        from infrastructure.reporting.native_pdf_whole_semantic_references import observe_whole_pdf_semantic_references

        semantic = observe_whole_pdf_semantic_references(
            root,
            directory / "semantics",
            inputs,
            ast_bytes,
            scope=source_scope,
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
    for row in implementations:
        if hashlib.sha256(Path(row["original_path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("actual loaded complete-source reference implementation changed during execution")
    if time.monotonic() >= deadline:
        raise TimeoutError("complete-source reference exhausted its original finite budget")
    return {
        **common,
        "references": references,
        "math_positions": list(positions),
        "semantic_references": semantic,
        "declared_tex_dependencies": package_inputs,
        "math_paint": list(paint),
        "instrumentation_noninterference": parity,
        "environment": {
            name: environment[name] for name in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR", "openin_any", "openout_any")
        },
        "elapsed_seconds": time.monotonic() - started,
        "component_status": "pass" if parity["status"] == "pass" else "fail",
        "admission_status": "blocked",
    }
