"""Independent whole-PDF control replay under genuine original Source custody.

Every child is authenticated before its observations are interpreted. Complete
current Source reconstruction and actual original native effects cannot replace
unresolved scientific, renderer, runtime or writer obligations.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeArtifact,
    create_private_native_directory,
    native_artifact_contract,
)
from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs, pdf_source_inputs
from infrastructure.reporting.native_hydration_reconstruction import replay_native_pdf_recomposition
from infrastructure.reporting.native_pdf_whole_control_effect import inspect_whole_pdf_native_effect
from infrastructure.reporting.native_pdf_whole_control_run import SCHEMA as OBSERVATION_SCHEMA
from infrastructure.reporting.native_pdf_whole_control_run import raster_bytes
from infrastructure.reporting.native_pdf_whole_control_supervisor import SUITE_REMAINING
from infrastructure.reporting.native_pdf_whole_controls import mutate_whole_pdf_native
from infrastructure.reporting.native_pdf_whole_reference_replay import replay_whole_pdf_reference
from infrastructure.reporting.native_pdf_whole_source_witness import observe_whole_pdf_source_predicates
from infrastructure.reporting.native_print_child_custody import WholePDFControlReaderOperation
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SUITE_SCHEMA = "template-source-owned-whole-pdf-control-suite-v1"
_SOURCE_FIELDS = {
    "schema_version",
    "source_inputs",
    "markdown",
    "ast",
    "parser_artifact",
    "citation_engine",
    "blockers",
    "contract",
}
_BASELINE_FIELDS = {
    "artifact",
    "declared_formats",
    "pdf",
    "ordered_pdf_contract",
    "source",
    "hydration_reconstruction",
    "reference",
    "native_raster",
    "every_page_parity",
    "source_predicates",
}
_OBSERVATION_FIELDS = {
    "schema_version",
    "scope",
    "run_id",
    "name",
    "baseline",
    "selected_control",
    "mutant",
    "native_effect",
    "every_page_parity",
    "source_predicates",
    "intended_diagnostic",
    "oracle_exit_code",
    "remaining",
    "worker_pid",
    "worker_platform",
}


def _source_inputs(inputs: PDFSourceInputs) -> list[dict[str, str]]:
    return [
        {"role": role, "path": path, "sha256": hashlib.sha256(content).hexdigest()}
        for role, values in (
            ("manuscript", inputs.sources),
            ("config", (inputs.config,)),
            ("preamble", (inputs.preamble,) if inputs.preamble else ()),
            ("bibliography", inputs.bibliographies),
            ("auxiliary", inputs.auxiliary),
        )
        for path, content in values
    ]


def _replay_source(
    root: Path,
    scope: str,
    source: dict[str, Any],
    inputs: PDFSourceInputs,
    reader: SnapshotReader,
    authority: dict[str, Any],
    *,
    run_id: str,
    env: dict[str, str],
    deadline: float,
) -> bytes:
    """Authenticate the actual original parser and independently run current Source."""
    if (
        set(source) != _SOURCE_FIELDS
        or source["schema_version"] != "template-native-pdf-source-only-v1"
        or source["source_inputs"] != _source_inputs(inputs)
        or source["blockers"] != list(inputs.blockers)
        or source["citation_engine"] != "natbib/plainnat (original AST has no citeproc)"
        or _file(source["markdown"], reader).content != inputs.content
    ):
        raise ValueError("whole PDF control Source input census differs from genuine complete current Source")
    original_root = Path(authority["source"]["current_mirror"]["root"])
    original_parser = _tool(
        source["parser_artifact"],
        reader,
        run_id,
        "pandoc",
        "pdf-source-original-ast",
        [
            str(original_root / source["markdown"]["path"]),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=json",
        ],
    )
    with current_pandoc_reader(root, reader, env=env, deadline=deadline, purpose="whole-pdf-control-ast") as current:
        frozen = current.runtime.freeze("source.md", inputs.content)
        parsed = current.tool(
            "pandoc",
            [str(frozen), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"],
            "whole-control-current-source-ast",
        )
        stdout = parsed["stdout"]
        if not isinstance(stdout, str):
            raise ValueError("whole PDF current Source parser stdout is not text")
        ast = stdout.encode()
    if (
        original_parser["stdout"].encode() != ast
        or _file(source["ast"], reader).content != ast
        or any(original_parser[key] != parsed[key] for key in ("executable", "executable_sha256"))
        or source["contract"] != semantic_content_contract_from_ast("manuscript:pdf", inputs.sources, ast).to_dict()
    ):
        raise ValueError("whole PDF actual original parser differs from independently nominated current Source parse")
    return ast


def _parity(
    snapshot: ArtifactSnapshot,
    pixels: tuple[bytes, ...],
    reference: dict[str, Any],
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    return inspect_pdf_reference_parity(
        snapshot.content,
        _file(reference["pdf"], reader).content,
        pixels,
        tuple(_file(row, reader).content for row in reference["rasters"]),
        deadline=deadline,
    )


def _predicates(
    root: Path,
    scope: str,
    inputs: PDFSourceInputs,
    ast: bytes,
    snapshot: ArtifactSnapshot,
    pixels: tuple[bytes, ...],
    reference: dict[str, Any],
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    return observe_whole_pdf_source_predicates(
        root,
        scope,
        "manuscript:pdf",
        inputs,
        ast,
        snapshot.content,
        pixels,
        reader,
        reference_pdf=_file(reference["pdf"], reader).content,
        reference_rasters=tuple(_file(row, reader).content for row in reference["rasters"]),
        deadline=deadline,
    )


def _native_raster(
    raster: dict[str, Any],
    snapshot: ArtifactSnapshot,
    directory: Path,
    reference: dict[str, Any],
    reader: SnapshotReader,
    authority: dict[str, Any],
    *,
    run_id: str,
) -> tuple[bytes, ...]:
    versions = {
        name: _file(binding, reader).json_object()
        for name, binding in zip(("pdftoppm", "pdffonts"), reference["raster"]["tool_artifacts"], strict=True)
    }
    _raster(
        {"raster": raster},
        snapshot,
        0,
        directory,
        reader,
        run_id,
        versions,
        authority["source"]["current_mirror"],
    )
    return raster_bytes(raster, reader)


def _baseline(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    artifact: NativeArtifact,
    baseline: dict[str, Any],
    reader: SnapshotReader,
    authority: dict[str, Any],
    current_directory: Path,
    contract: list[dict[str, str]],
    hydration: dict[str, Any],
    pdf_body: bytes,
    *,
    run_id: str,
    env: dict[str, str],
    deadline: float,
) -> tuple[PDFSourceInputs, bytes, ArtifactSnapshot, tuple[bytes, ...], dict[str, Any], dict[str, Any]]:
    if (
        set(baseline) != _BASELINE_FIELDS
        or baseline["artifact"] != {"id": artifact.id, "format": artifact.format, "path": artifact.path}
        or baseline["declared_formats"] != list(formats)
        or baseline["ordered_pdf_contract"] != contract
        or baseline["hydration_reconstruction"] != hydration
    ):
        raise ValueError("whole PDF original child baseline changed complete Source/artifact/hydration selection")
    original_pdf = reader.read(artifact.path)
    if baseline["pdf"] != {"path": original_pdf.relative, "sha256": original_pdf.sha256}:
        raise ValueError("whole PDF original child baseline consumed another pipeline PDF")
    original_directory = reader.root / authority["specification"]["directory"]
    if (
        _file(baseline["reference"], reader).path != original_directory / "baseline/reference/reference.json"
        or _file(baseline["source"]["markdown"], reader).path != original_directory / "baseline/source/source-only.md"
        or _file(baseline["source"]["ast"], reader).path != original_directory / "baseline/source/source-only.ast.json"
    ):
        raise ValueError("whole PDF original child baseline grafted another child's Source/reference graph")
    inputs = pdf_source_inputs(root, current_directory / "source", scope, artifact, reader)
    if inputs.content != pdf_body:
        raise ValueError("whole PDF controls lack independent complete current PDF recomposition")
    ast = _replay_source(
        root, scope, baseline["source"], inputs, reader, authority, run_id=run_id, env=env, deadline=deadline
    )
    replayed = replay_whole_pdf_reference(
        root,
        current_directory / "reference",
        scope,
        baseline["reference"],
        inputs,
        ast,
        reader,
        run_id=run_id,
        env=env,
        deadline=deadline,
    )
    original_reference = _file(baseline["reference"], reader).json_object()
    current_reference = replayed["current_reference"]
    if any(ref.get("component_status") != "pass" for ref in (original_reference, current_reference)):
        raise ValueError("whole PDF controls require actual complete noninterfering original/current references")
    old, fresh = (ref["references"]["uninstrumented"] for ref in (original_reference, current_reference))
    pixels = _native_raster(
        baseline["native_raster"],
        original_pdf,
        original_directory / "baseline/native",
        old,
        reader,
        authority,
        run_id=run_id,
    )
    parity = _parity(original_pdf, pixels, old, reader, deadline=deadline)
    predicates = _predicates(root, scope, inputs, ast, original_pdf, pixels, old, reader, deadline=deadline)
    current_parity = _parity(original_pdf, pixels, fresh, reader, deadline=deadline)
    current_predicates = _predicates(root, scope, inputs, ast, original_pdf, pixels, fresh, reader, deadline=deadline)
    if (
        baseline["every_page_parity"] != parity
        or baseline["source_predicates"] != predicates
        or current_parity != parity
        or current_predicates != predicates
        or parity["status"] != "pass"
        or parity["findings"]
        or predicates["findings"]
    ):
        raise ValueError("whole PDF actual positive baseline lacks exact independent full Source/page reproduction")
    return inputs, ast, original_pdf, pixels, old, fresh


def _child(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    artifact: NativeArtifact,
    item: dict[str, Any],
    reader: SnapshotReader,
    context: WholePDFControlReaderOperation,
    directory: Path,
    contract: list[dict[str, str]],
    hydration: dict[str, Any],
    pdf_body: bytes,
    suite: dict[str, Any],
    suite_authority: dict[str, Any],
    *,
    env: dict[str, str],
    deadline: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = context.child(item, reader)
    spec = authority["specification"]
    raw = authority["event"].json_object()
    run_id = context.run_id
    name = item["name"]
    expected_exit = 0 if name == "baseline" else 1
    expected_platform = suite_authority["process"]["host_before"]["system"]
    if (
        set(raw) != _OBSERVATION_FIELDS
        or raw["schema_version"] != OBSERVATION_SCHEMA
        or raw["scope"] != scope
        or raw["run_id"] != run_id
        or raw["name"] != name
        or type(raw["oracle_exit_code"]) is not int
        or raw["oracle_exit_code"] != expected_exit
        or type(raw["worker_pid"]) is not int
        or raw["worker_pid"] != authority["process"]["pid"]
        or raw["worker_platform"] != expected_platform
        or spec["parent_platform"] != expected_platform
        or authority["source"] != suite_authority["source"]
        or spec["artifact_id"] != artifact.id
        or spec["declared_formats"] != list(formats)
        or spec["pipeline_run_id"] != suite["pipeline_run_id"]
        or spec["plan_digest"] != suite["plan_digest"]
        or spec["expected_exit"] != expected_exit
    ):
        raise ValueError("whole PDF original child changed its exact Source/role/OS outcome")
    inputs, ast, original_pdf, old_pixels, old_reference, fresh_reference = _baseline(
        root,
        scope,
        formats,
        artifact,
        raw["baseline"],
        reader,
        authority,
        directory,
        contract,
        hydration,
        pdf_body,
        run_id=run_id,
        env=env,
        deadline=deadline,
    )
    requirements = raw["baseline"]["source_predicates"]["control_requirements"]
    controls = [row for row in requirements["controls"] if row["identity"] == name]
    if (
        len(controls) != 1
        or controls[0]["unsupported"] is not None
        or raw["selected_control"] != controls[0]
        or spec["requirements_digest"] != requirements["content_digest"]
    ):
        raise ValueError("whole PDF original child is not the complete Source-selected native control")
    selected = controls[0]
    changed = mutate_whole_pdf_native(original_pdf.content, requirements, name, deadline=deadline)
    mutant = raw["mutant"]
    if set(mutant) != {"pdf", "native_raster"}:
        raise ValueError("whole PDF original native mutant omitted complete input/raster custody")
    snapshot = _file(mutant["pdf"], reader)
    original_directory = reader.root / spec["directory"]
    if snapshot.path != original_directory / "mutant/control.pdf" or snapshot.content != changed:
        raise ValueError("whole PDF original bytes differ from independent current Source-defined mutation")
    pixels = _native_raster(
        mutant["native_raster"],
        snapshot,
        original_directory / "mutant/native",
        old_reference,
        reader,
        authority,
        run_id=run_id,
    )
    effect = inspect_whole_pdf_native_effect(
        original_pdf.content, snapshot.content, old_pixels, pixels, selected, deadline=deadline
    )
    parity = _parity(snapshot, pixels, old_reference, reader, deadline=deadline)
    predicates = _predicates(root, scope, inputs, ast, snapshot, pixels, old_reference, reader, deadline=deadline)
    current_parity = _parity(snapshot, pixels, fresh_reference, reader, deadline=deadline)
    current_predicates = _predicates(
        root, scope, inputs, ast, snapshot, pixels, fresh_reference, reader, deadline=deadline
    )
    intended = selected["intended_diagnostic"]
    codes = {row["code"] for row in [*parity["findings"], *predicates["findings"]]}
    expected_remaining = [*raw["baseline"]["source_predicates"]["blockers"], *predicates["blockers"]]
    if (
        raw["native_effect"] != effect
        or raw["every_page_parity"] != parity
        or raw["source_predicates"] != predicates
        or current_parity != parity
        or current_predicates != predicates
        or raw["intended_diagnostic"] != intended
        or raw["remaining"] != expected_remaining
        or (intended is None and (codes or expected_exit != 0))
        or (intended is not None and (intended not in codes or expected_exit != 1))
    ):
        raise ValueError(
            "whole PDF original control did not reach its independently current intended native diagnostic"
        )
    context.verify(reader)
    return requirements, {
        "name": name,
        "original_exit_code": expected_exit,
        "selected_control": selected,
        "native_effect": effect,
        "every_page_parity": parity,
        "current_every_page_parity": current_parity,
        "source_predicates": predicates,
        "current_source_predicates": current_predicates,
        "remaining": expected_remaining,
    }


def replay_whole_pdf_source_controls(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Reproduce every actual supported original child; preserve all unresolved rows."""
    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    owner = current_native_producer_operation()
    if (
        original is None
        or owner is None
        or reader.native_control_operation is not None
        or reader.native_producer_operation is not None
        or owner.source is not operation.source
        or owner.run_id != operation.source.bindings.run_id
        or owner.run_id == original.run_id
        or owner.deadline != deadline
        or operation.deadline != deadline
        or reader.root != root.resolve()
    ):
        raise ValueError(
            "whole PDF control replay needs actual external original and distinct fresh current Source owner"
        )
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    authority = authenticate_original_native_artifact(
        binding,
        reader,
        run_id=original.run_id,
        required_sdk_modules=("reporting/native_pdf_whole_control_supervisor.py",),
    )
    raw = authority["event"].json_object()
    artifacts = tuple(row for row in native_artifact_contract(root, scope, formats, reader) if row.format == "pdf")
    if not artifacts:
        raise ValueError("whole PDF control replay requires the complete nonempty Source PDF contract")
    contract = [{"id": row.id, "format": row.format, "path": row.path} for row in artifacts]
    native_execution = reader.read(original.native_execution_relative)
    if native_execution.sha256 != original.native_execution_sha256:
        raise ValueError("whole PDF control suite enclosing execution changed from externally held original")
    hydration, pdf_body = replay_native_pdf_recomposition(scope, native_execution, reader)
    if (
        set(raw)
        != {
            "schema_version",
            "scope",
            "run_id",
            "declared_formats",
            "pipeline_run_id",
            "plan_digest",
            "ordered_pdf_contract",
            "artifacts",
            "remaining",
        }
        or raw["schema_version"] != SUITE_SCHEMA
        or raw["scope"] != scope
        or raw["run_id"] != original.run_id
        or raw["declared_formats"] != list(formats)
        or raw["pipeline_run_id"] != hydration["pipeline_run_id"]
        or raw["plan_digest"] != hydration["plan_digest"]
        or raw["ordered_pdf_contract"] != contract
        or raw["remaining"] != list(SUITE_REMAINING)
        or not isinstance(raw["artifacts"], list)
        or len(raw["artifacts"]) != len(artifacts)
    ):
        raise ValueError("whole PDF control suite omitted or reordered complete Source/artifact/hydration obligations")
    current_directory = (
        root / "output/readiness/current-native-readers" / owner.run_id / ("whole-pdf-controls-" + uuid4().hex)
    )
    create_private_native_directory(root, current_directory)
    results = []
    seen_children: set[str] = set()
    for ordinal, (artifact, row) in enumerate(zip(artifacts, raw["artifacts"], strict=True)):
        remaining(deadline)
        if (
            not isinstance(row, dict)
            or set(row) != {"id", "format", "path", "role", "requirements", "children", "unsupported"}
            or {key: row[key] for key in ("id", "format", "path")} != contract[ordinal]
        ):
            raise ValueError("whole PDF control artifact differs from complete current Source contract")
        if artifact.id != "manuscript:pdf":
            unsupported = [artifact.id + ": complete original/current Source-writer reference is unimplemented"]
            if (
                row["role"] != "unsupported-writer"
                or row["requirements"] is not None
                or row["children"] != []
                or row["unsupported"] != unsupported
            ):
                raise ValueError("whole PDF suite concealed an explicitly unsupported Source writer")
            results.append({"id": artifact.id, "role": row["role"], "children": [], "unsupported": unsupported})
            continue
        if (
            row["role"] != "whole-manuscript-source-controls"
            or pdf_body is None
            or not isinstance(row["children"], list)
            or not 1 <= len(row["children"]) <= 100_501
        ):
            raise ValueError("whole PDF supported Source writer lacks complete genuine original controls")
        context = WholePDFControlReaderOperation(
            operation.source,
            reader,
            row["children"],
            scope=scope,
            run_id=original.run_id,
            deadline=deadline,
        )
        control_reader = SnapshotReader(
            root, hosted_origin=reader.hosted_origin, native_operation=operation, native_control_operation=context
        )
        reproduced = []
        requirements = None
        for index, item in enumerate(row["children"]):
            leaf = current_directory / f"artifact-{ordinal:04d}" / f"control-{index:06d}"
            create_private_native_directory(root, leaf)
            actual_requirements, result = _child(
                root,
                scope,
                formats,
                artifact,
                item,
                control_reader,
                context,
                leaf,
                contract,
                hydration,
                pdf_body,
                raw,
                authority,
                env=env,
                deadline=deadline,
            )
            child_path = _file(item["specification_artifact"], control_reader).relative
            if child_path in seen_children or requirements is not None and actual_requirements != requirements:
                raise ValueError("whole PDF control child was duplicated or changed the complete Source requirements")
            seen_children.add(child_path)
            requirements = actual_requirements
            reproduced.append(result)
        if requirements is None:
            raise ValueError("whole PDF complete Source control requirements are absent")
        names = [control["identity"] for control in requirements["controls"] if control["unsupported"] is None]
        unsupported = [control for control in requirements["controls"] if control["unsupported"] is not None]
        if (
            row["requirements"] != requirements
            or row["unsupported"] != unsupported
            or [result["name"] for result in reproduced] != names
            or not control_reader.unchanged()
        ):
            raise ValueError("whole PDF suite omitted, added, reordered or changed Source/page controls")
        context.verify(control_reader)
        results.append({"id": artifact.id, "role": row["role"], "children": reproduced, "unsupported": unsupported})
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("whole PDF suite Source/native/original custody changed during independent replay")
    remaining(deadline)
    return {
        "schema_version": "template-source-owned-whole-pdf-control-suite-current-v1",
        "scope": scope,
        "original_run_id": original.run_id,
        "current_run_id": owner.run_id,
        "ordered_pdf_contract": contract,
        "artifacts": results,
        "remaining": list(SUITE_REMAINING),
        "status": "blocked",
    }
