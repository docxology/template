"""Real Source-bound whole-PDF control preparation and native predicates.

Original control execution is supervised by a fixed selected-SDK child. This
component retains unsupported Source/domain edges after actual comparisons.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_artifact_contract,
)
from infrastructure.reporting.native_format_acceptance_validation import _file
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_format_pdf_source import observe_pdf_source, pdf_source_inputs
from infrastructure.reporting.native_format_pdf_whole_reference import observe_pdf_whole_reference
from infrastructure.reporting.native_hydration_reconstruction import observe_native_pdf_recomposition
from infrastructure.reporting.native_pdf_whole_control_effect import inspect_whole_pdf_native_effect
from infrastructure.reporting.native_pdf_whole_controls import mutate_whole_pdf_native
from infrastructure.reporting.native_pdf_whole_source_witness import observe_whole_pdf_source_predicates
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-whole-pdf-control-observation-v1"


def raster_bytes(raster: dict[str, Any], reader: SnapshotReader) -> tuple[bytes, ...]:
    return tuple(_file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in raster["rasters"])


def observe_whole_pdf_control_baseline(
    root: Path,
    directory: Path,
    scope: str,
    formats: tuple[str, ...],
    *,
    artifact_id: str,
    pipeline_run_id: str,
    plan_digest: str,
    reader: SnapshotReader,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Compile a fresh full reference before selecting any native mutation.

    The whole contract is recomputed from actual Source. Caller declarations,
    generated combined receipts and data callbacks cannot supply authority.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline or reader.root != root:
        raise ValueError("whole PDF control baseline requires its actual enclosing Source/run/clock")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    artifacts = tuple(row for row in native_artifact_contract(root, scope, formats, reader) if row.format == "pdf")
    selected = [row for row in artifacts if row.id == artifact_id]
    if len(selected) != 1 or artifact_id != "manuscript:pdf":
        raise ValueError("whole PDF controls require one supported Source writer in the complete PDF contract")
    artifact = selected[0]
    create_private_native_directory(root, directory)
    hydration, pdf_body = observe_native_pdf_recomposition(
        owner.source, scope, pipeline_run_id, plan_digest, reader, deadline=deadline
    )
    inputs = pdf_source_inputs(root, directory / "whole-source", scope, artifact, reader)
    if pdf_body is None or inputs.content != pdf_body:
        raise ValueError("whole PDF control lacks independently reconstructed complete PDF hydration bytes")
    _, source = observe_pdf_source(
        root, directory / "source", scope, artifact, reader, env=env, deadline=deadline, run_id=run_id
    )
    ast = _file(source["ast"], reader).content
    reference = observe_pdf_whole_reference(
        root,
        directory / "reference",
        inputs,
        ast,
        env=env,
        deadline=deadline,
        run_id=run_id,
        sdk_context=json.loads(owner.source.descriptor(scope, deadline=deadline)),
        source_scope=scope,
    )
    if reference.get("component_status") != "pass" or "uninstrumented" not in reference.get("references", {}):
        raise ValueError("whole PDF control requires a complete noninterfering actual native reference")
    reference_binding = write_json(root, directory / "reference/reference.json", reference)
    uninstrumented = reference["references"]["uninstrumented"]
    reference_pdf = _file(uninstrumented["pdf"], reader).content
    reference_rasters = tuple(_file(binding, reader).content for binding in uninstrumented["rasters"])
    original = reader.read(artifact.path)
    create_private_native_directory(root, directory / "native")
    native = audit_pdf_raster(
        root,
        directory / "native",
        original,
        parse_native_bytes("pdf", original.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    rasters = raster_bytes(native, reader)
    parity = inspect_pdf_reference_parity(
        original.content, reference_pdf, rasters, reference_rasters, deadline=deadline
    )
    predicates = observe_whole_pdf_source_predicates(
        root,
        scope,
        artifact.id,
        inputs,
        ast,
        original.content,
        rasters,
        reader,
        reference_pdf=reference_pdf,
        reference_rasters=reference_rasters,
        deadline=deadline,
    )
    if parity["findings"] or predicates["findings"]:
        raise ValueError("whole PDF control original positive baseline has real Source/native findings")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    return {
        "artifact": {"id": artifact.id, "format": artifact.format, "path": artifact.path},
        "declared_formats": list(formats),
        "pdf": {"path": original.relative, "sha256": original.sha256},
        "ordered_pdf_contract": [{"id": row.id, "format": row.format, "path": row.path} for row in artifacts],
        "source": source,
        "hydration_reconstruction": hydration,
        "reference": reference_binding,
        "native_raster": native,
        "every_page_parity": parity,
        "source_predicates": predicates,
    }


def run_whole_pdf_native_control(
    root: Path,
    directory: Path,
    scope: str,
    baseline: dict[str, Any],
    name: str,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Run the complete native predicate only after proving actual effect.

    A missing position, blank/no-op image, parser/setup/custody error or absent
    intended diagnostic raises. None can acquire the expected negative exit.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline:
        raise ValueError("whole PDF mutation lacks its genuine current Source/tool owner")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    requirements = baseline["source_predicates"]["control_requirements"]
    selected = [row for row in requirements["controls"] if row["identity"] == name]
    if len(selected) != 1 or selected[0]["unsupported"] is not None:
        raise ValueError("whole PDF original control is absent or explicitly unsupported")
    control = selected[0]
    original = _file(baseline["pdf"], reader)
    changed = mutate_whole_pdf_native(original.content, requirements, name, deadline=deadline)
    create_private_native_directory(root, directory)
    atomic_write_bytes_confined(root, directory / "control.pdf", changed, mode=0o600)
    mutant = reader.read((directory / "control.pdf").relative_to(root).as_posix())
    create_private_native_directory(root, directory / "native")
    raster = audit_pdf_raster(
        root,
        directory / "native",
        mutant,
        parse_native_bytes("pdf", mutant.content),
        env=env,
        deadline=deadline,
        run_id=run_id,
        ordinal=0,
    )
    old_rasters, new_rasters = raster_bytes(baseline["native_raster"], reader), raster_bytes(raster, reader)
    effect = inspect_whole_pdf_native_effect(
        original.content, mutant.content, old_rasters, new_rasters, control, deadline=deadline
    )
    reference = _file(baseline["reference"], reader).json_object()["references"]["uninstrumented"]
    reference_pdf = _file(reference["pdf"], reader).content
    reference_rasters = tuple(_file(binding, reader).content for binding in reference["rasters"])
    artifact_id = baseline["artifact"]["id"]
    artifacts = native_artifact_contract(root, scope, tuple(baseline["declared_formats"]), reader)
    artifacts = tuple(row for row in artifacts if row.id == artifact_id and row.format == "pdf")
    if len(artifacts) != 1:
        raise ValueError("whole PDF mutation no longer belongs to the complete Source PDF contract")
    inputs = pdf_source_inputs(root, directory / "source", scope, artifacts[0], reader)
    ast = _file(baseline["source"]["ast"], reader).content
    parity = inspect_pdf_reference_parity(
        mutant.content, reference_pdf, new_rasters, reference_rasters, deadline=deadline
    )
    predicates = observe_whole_pdf_source_predicates(
        root,
        scope,
        artifact_id,
        inputs,
        ast,
        mutant.content,
        new_rasters,
        reader,
        reference_pdf=reference_pdf,
        reference_rasters=reference_rasters,
        deadline=deadline,
    )
    codes = {row["code"] for row in [*parity["findings"], *predicates["findings"]]}
    intended = control["intended_diagnostic"]
    if (intended is None and codes) or (intended is not None and intended not in codes):
        raise ValueError("actual whole PDF control did not reach its intended Source/native diagnostic")
    remaining(deadline)
    owner.verify(reader, run_id=run_id, deadline=deadline)
    return {
        "schema_version": SCHEMA,
        "scope": scope,
        "run_id": run_id,
        "name": name,
        "baseline": baseline,
        "selected_control": control,
        "mutant": {"pdf": {"path": mutant.relative, "sha256": mutant.sha256}, "native_raster": raster},
        "native_effect": effect,
        "every_page_parity": parity,
        "source_predicates": predicates,
        "intended_diagnostic": intended,
        "oracle_exit_code": int(intended is not None),
        "remaining": [*baseline["source_predicates"]["blockers"], *predicates["blockers"]],
    }
