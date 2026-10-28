"""Complete native PDF cohort observation and genuine current reproduction.

The cohort preserves every compiled artifact, delegated role and unsupported
scientific occurrence. It does not grant publication or resolve control gaps.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_artifact_contract,
)
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_pdf_candidate_raster import candidate_pdf_raster
from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_format_pdf_source import observe_pdf_source, pdf_source_inputs
from infrastructure.reporting.native_format_pdf_whole_reference import observe_pdf_whole_reference
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_hydration_reconstruction import (
    observe_native_pdf_recomposition,
    replay_native_pdf_recomposition,
)
from infrastructure.reporting.native_pdf_whole_reference_replay import replay_whole_pdf_reference
from infrastructure.reporting.native_pdf_whole_source_witness import observe_whole_pdf_source_predicates
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-whole-pdf-cohort-v2"
UNRESOLVED = (
    "complete-whole-scientific-pdf-source-semantic-original-control-selection-and-replay",
    "every-independent-Source-scientific-value-unit-sign-and-figure-native-predicate",
    "complete-current-original-TeX-section-writer-reference-and-native-semantic-adapter",
)


def _role(scope: str, artifact_id: str) -> str:
    if artifact_id.startswith("pitch:") or artifact_id.endswith(":slides"):
        return "existing-complete-projection-role"
    if scope in {"templates/template_newspaper", "templates/template_storybook"} and (
        artifact_id.startswith("newspaper:") or artifact_id.startswith("storybook:")
    ):
        return "existing-complete-print-role"
    if artifact_id == "manuscript:pdf":
        return "complete-manuscript-source-reference"
    if artifact_id.startswith("section:") and artifact_id.endswith(":pdf"):
        return "required-independent-TeX-section-reference"
    return "required-independent-source-writer-reference"


def observe_whole_pdf_cohort(
    root: Path,
    directory: Path,
    scope: str,
    formats: tuple[str, ...],
    reader: SnapshotReader,
    *,
    pipeline_run_id: str,
    plan_digest: str,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    candidate_rows: list[dict[str, Any]],
    candidate_tools: list[dict[str, str]],
    candidate_directory: Path,
) -> dict[str, str]:
    """Execute actual whole-reference pieces under the genuine original owner.

    TeX sections and other writers remain explicit records. Delegation records
    do not prove those roles; the whole native gate still replays their existing
    complete adapters and Source-owned original controls separately.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline or reader.root != root.resolve():
        raise ValueError("whole PDF cohort requires its actual current Source producer/run/original clock")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    if (
        candidate_directory != owner.stage_scope_directory(scope)
        or directory != candidate_directory / "whole-pdf-cohort"
    ):
        raise ValueError("whole PDF candidate rasters differ from the enclosing actual Source attempt")
    create_private_native_directory(root, directory)
    artifacts = tuple(row for row in native_artifact_contract(root, scope, formats, reader) if row.format == "pdf")
    if not artifacts:
        raise ValueError("whole PDF cohort requires the complete nonempty current declared PDF contract")
    hydration, combined = observe_native_pdf_recomposition(
        owner.source, scope, pipeline_run_id, plan_digest, reader, deadline=deadline
    )
    rows = []
    for ordinal, artifact in enumerate(artifacts):
        remaining(deadline)
        snapshot = reader.read(artifact.path)
        role = _role(scope, artifact.id)
        row: dict[str, Any] = {
            "id": artifact.id,
            "format": artifact.format,
            "path": artifact.path,
            "role": role,
            "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "source": None,
            "whole_reference": None,
            "native_raster": None,
            "every_page_parity": None,
            "source_predicates": None,
            "blockers": [],
            "findings": [],
        }
        if role == "complete-manuscript-source-reference":
            leaf = directory / f"artifact-{ordinal:04d}"
            create_private_native_directory(root, leaf)
            _, source = observe_pdf_source(
                root, leaf / "source", scope, artifact, reader, env=env, deadline=deadline, run_id=run_id
            )
            inputs = pdf_source_inputs(root, leaf / "whole-source", scope, artifact, reader)
            row["source"] = source
            if combined is None:
                row["blockers"].append("complete Source PDF hydration/composition body remains unresolved")
            elif inputs.content != combined:
                row["blockers"].append(
                    "whole PDF writer reconstruction differs from the independent PDF composition algorithm"
                )
            else:
                ast = _file(source["ast"], reader).content
                reference_directory = leaf / "whole-reference"
                reference = observe_pdf_whole_reference(
                    root,
                    reference_directory,
                    inputs,
                    ast,
                    env=env,
                    deadline=deadline,
                    run_id=run_id,
                    sdk_context=json.loads(owner.source.descriptor(scope, deadline=deadline)),
                    source_scope=scope,
                )
                row["whole_reference"] = write_json(root, reference_directory / "reference.json", reference)
                row["blockers"].extend(reference["blockers"])
                if (
                    "uninstrumented" in reference.get("references", {})
                    and "rasters" in reference["references"]["uninstrumented"]
                ):
                    raster = candidate_pdf_raster(
                        scope,
                        formats,
                        artifact,
                        candidate_rows,
                        candidate_tools,
                        reader,
                        directory=candidate_directory,
                        run_id=run_id,
                        custody=json.loads(owner.source.descriptor(scope, deadline=deadline))["current_mirror"],
                    )
                    uninstrumented = reference["references"]["uninstrumented"]
                    parity = inspect_pdf_reference_parity(
                        snapshot.content,
                        _file(uninstrumented["pdf"], reader).content,
                        tuple(
                            _file({"path": row["path"], "sha256": row["sha256"]}, reader).content
                            for row in raster["rasters"]
                        ),
                        tuple(_file(binding, reader).content for binding in uninstrumented["rasters"]),
                        deadline=deadline,
                    )
                    row["native_raster"], row["every_page_parity"] = raster, parity
                    row["findings"].extend(parity["findings"])
                    row["findings"].extend(reference.get("instrumentation_noninterference", {}).get("findings", []))
                    predicates = observe_whole_pdf_source_predicates(
                        root,
                        scope,
                        artifact.id,
                        inputs,
                        ast,
                        snapshot.content,
                        tuple(
                            _file({"path": item["path"], "sha256": item["sha256"]}, reader).content
                            for item in raster["rasters"]
                        ),
                        reader,
                        reference_pdf=_file(uninstrumented["pdf"], reader).content,
                        reference_rasters=tuple(
                            _file(binding, reader).content for binding in uninstrumented["rasters"]
                        ),
                        whole_reference=reference,
                        deadline=deadline,
                    )
                    row["source_predicates"] = predicates
                    row["blockers"].extend(predicates["blockers"])
                    row["findings"].extend(predicates["findings"])
                else:
                    row["blockers"].append("complete Source reference/native every-page comparison remains unavailable")
        elif role.startswith("required-independent"):
            row["blockers"].append(artifact.id + ": complete original/current Source-writer reference is unimplemented")
        rows.append(row)
    body = {
        "schema_version": SCHEMA,
        "scope": scope,
        "run_id": run_id,
        "declared_formats": list(formats),
        "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
        "hydration_reconstruction": hydration,
        "artifacts": rows,
        "remaining": [*UNRESOLVED, *hydration["unresolved_edges"]],
        "status": "fail" if any(row["findings"] for row in rows) else "blocked",
    }
    binding = write_json(root, directory / "cohort.json", body)
    owner.verify(reader, run_id=run_id, deadline=deadline)
    remaining(deadline)
    return binding


def replay_whole_pdf_cohort(
    root: Path,
    scope: str,
    formats: tuple[str, ...],
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Authenticate the original and recompile each supported full reference.

    The external original operation and separately held current Source owner
    must exist before this call. The retained cohort cannot create either one.
    """
    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    owner = current_native_producer_operation()
    if (
        original is None
        or deadline != operation.deadline
        or owner is None
        or owner.source is not operation.source
        or owner.run_id != operation.source.bindings.run_id
        or owner.deadline != deadline
        or reader.native_producer_operation is not None
    ):
        raise ValueError("whole PDF current cohort needs actual externally held original and independent Source owner")
    authority = authenticate_original_native_artifact(
        binding, reader, run_id=original.run_id, required_sdk_modules=("reporting/native_pdf_whole_cohort.py",)
    )
    raw = authority["event"].json_object()
    artifacts = tuple(row for row in native_artifact_contract(root, scope, formats, reader) if row.format == "pdf")
    if (
        set(raw)
        != {
            "schema_version",
            "scope",
            "run_id",
            "declared_formats",
            "source_binding",
            "hydration_reconstruction",
            "artifacts",
            "remaining",
            "status",
        }
        or raw["schema_version"] != SCHEMA
        or raw["scope"] != scope
        or raw["run_id"] != original.run_id
        or raw["declared_formats"] != list(formats)
        or raw["status"] != ("fail" if any(row["findings"] for row in raw["artifacts"]) else "blocked")
        or raw["source_binding"] != [operation.source.reference.commit, operation.source.reference.source_identity]
        or [row["id"] for row in raw["artifacts"]] != [row.id for row in artifacts]
    ):
        raise ValueError("whole PDF cohort omits/reorders Source artifacts or changes its genuine run/source")
    native = reader.read(original.native_execution_relative)
    if native.sha256 != original.native_execution_sha256:
        raise ValueError("whole PDF hydration differs from its externally held original execution")
    hydration, combined = replay_native_pdf_recomposition(scope, native, reader)
    if raw["hydration_reconstruction"] != hydration or raw["remaining"] != [
        *UNRESOLVED,
        *hydration["unresolved_edges"],
    ]:
        raise ValueError("whole PDF cohort changes the exact independently reconstructed Source/data gaps")
    current_directory = root / "output/readiness/current-native-readers" / owner.run_id / ("whole-pdf-" + uuid4().hex)
    create_private_native_directory(root, current_directory)
    results = []
    for ordinal, (artifact, row) in enumerate(zip(artifacts, raw["artifacts"], strict=True)):
        remaining(deadline)
        snapshot = _file(row["input"], reader)
        role = _role(scope, artifact.id)
        if set(row) != {
            "id",
            "format",
            "path",
            "role",
            "input",
            "source",
            "whole_reference",
            "native_raster",
            "every_page_parity",
            "source_predicates",
            "blockers",
            "findings",
        } or (
            row["format"] != artifact.format
            or row["path"] != artifact.path
            or row["role"] != role
            or snapshot.relative != artifact.path
        ):
            raise ValueError("whole PDF current artifact/role/input selection differs")
        reproduced = None
        expected_blockers = []
        findings = []
        if role == "complete-manuscript-source-reference":
            leaf = current_directory / f"artifact-{ordinal:04d}"
            inputs = pdf_source_inputs(root, leaf / "source", scope, artifact, reader)
            if combined is None:
                expected_blockers.append("complete Source PDF hydration/composition body remains unresolved")
            elif inputs.content != combined:
                expected_blockers.append(
                    "whole PDF writer reconstruction differs from the independent PDF composition algorithm"
                )
            else:
                if row["whole_reference"] is None:
                    raise ValueError("whole PDF supported Source manuscript omitted its actual original reference")
                with current_pandoc_reader(
                    root, reader, env=env, deadline=deadline, purpose="whole-pdf-ast"
                ) as current:
                    source = current.runtime.freeze("source.md", inputs.content)
                    parsed = current.tool(
                        "pandoc",
                        [str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"],
                        "whole-current-source-ast",
                    )
                    ast = parsed["stdout"].encode()
                if hashlib.sha256(ast).hexdigest() != row["source"]["ast"]["sha256"]:
                    raise ValueError("whole PDF fresh current Source parse differs from original source")
                reproduced = replay_whole_pdf_reference(
                    root,
                    leaf / "reference",
                    scope,
                    row["whole_reference"],
                    inputs,
                    ast,
                    reader,
                    run_id=original.run_id,
                    env=env,
                    deadline=deadline,
                )
                expected_blockers.extend(reproduced["original_blockers"])
                original_reference = _file(row["whole_reference"], reader).json_object()
                if (
                    "uninstrumented" in original_reference.get("references", {})
                    and "rasters" in original_reference["references"]["uninstrumented"]
                ):
                    reference = original_reference["references"]["uninstrumented"]
                    enclosing = native.json_object()
                    raster = candidate_pdf_raster(
                        scope,
                        formats,
                        artifact,
                        enclosing["artifacts"],
                        enclosing["tool_artifacts"],
                        reader,
                        directory=reader.root / Path(original.native_execution_relative).parent,
                        run_id=original.run_id,
                        custody=authority["source"]["current_mirror"],
                    )
                    if row["native_raster"] != raster:
                        raise ValueError("whole PDF candidate raster differs from the complete admitted enclosing run")
                    parity = inspect_pdf_reference_parity(
                        snapshot.content,
                        _file(reference["pdf"], reader).content,
                        tuple(
                            _file({"path": item["path"], "sha256": item["sha256"]}, reader).content
                            for item in row["native_raster"]["rasters"]
                        ),
                        tuple(_file(item, reader).content for item in reference["rasters"]),
                        deadline=deadline,
                    )
                    if row["every_page_parity"] != parity:
                        raise ValueError("whole PDF original candidate/reference every-page predicate differs")
                    fresh = reproduced["current_reference"]["references"]["uninstrumented"]
                    current_parity = inspect_pdf_reference_parity(
                        snapshot.content,
                        _file(fresh["pdf"], reader).content,
                        tuple(
                            _file({"path": item["path"], "sha256": item["sha256"]}, reader).content
                            for item in row["native_raster"]["rasters"]
                        ),
                        tuple(_file(item, reader).content for item in fresh["rasters"]),
                        deadline=deadline,
                    )
                    if current_parity["findings"] != parity["findings"]:
                        raise ValueError("whole PDF fresh current Source reference changes candidate native findings")
                    findings.extend(parity["findings"])
                    findings.extend(original_reference.get("instrumentation_noninterference", {}).get("findings", []))
                    reproduced["candidate_current_every_page_parity"] = current_parity
                    native_pixels = tuple(
                        _file({"path": item["path"], "sha256": item["sha256"]}, reader).content
                        for item in row["native_raster"]["rasters"]
                    )
                    predicates = observe_whole_pdf_source_predicates(
                        root,
                        scope,
                        artifact.id,
                        inputs,
                        ast,
                        snapshot.content,
                        native_pixels,
                        reader,
                        reference_pdf=_file(reference["pdf"], reader).content,
                        reference_rasters=tuple(_file(item, reader).content for item in reference["rasters"]),
                        whole_reference=original_reference,
                        deadline=deadline,
                    )
                    if row["source_predicates"] != predicates:
                        raise ValueError("whole PDF original complete Source/page/control selection differs")
                    current_predicates = observe_whole_pdf_source_predicates(
                        root,
                        scope,
                        artifact.id,
                        inputs,
                        ast,
                        snapshot.content,
                        native_pixels,
                        reader,
                        reference_pdf=_file(fresh["pdf"], reader).content,
                        reference_rasters=tuple(_file(item, reader).content for item in fresh["rasters"]),
                        whole_reference=reproduced["current_reference"],
                        deadline=deadline,
                    )
                    for field in ("source_plan", "assets", "control_requirements", "blockers", "findings", "status"):
                        if current_predicates[field] != predicates[field]:
                            raise ValueError("whole PDF fresh current Source semantic/control predicates differ")
                    expected_blockers.extend(predicates["blockers"])
                    findings.extend(predicates["findings"])
                    reproduced["candidate_current_source_predicates"] = current_predicates
                else:
                    expected_blockers.append(
                        "complete Source reference/native every-page comparison remains unavailable"
                    )
                    if (
                        row["native_raster"] is not None
                        or row["every_page_parity"] is not None
                        or row["source_predicates"] is not None
                    ):
                        raise ValueError("whole PDF unsupported reference cannot claim a native whole comparison")
        elif role.startswith("required-independent"):
            expected_blockers.append(
                artifact.id + ": complete original/current Source-writer reference is unimplemented"
            )
        if (
            row["blockers"] != expected_blockers
            or row["findings"] != findings
            or (
                role != "complete-manuscript-source-reference"
                and (
                    row["source"] is not None
                    or row["whole_reference"] is not None
                    or row["native_raster"] is not None
                    or row["every_page_parity"] is not None
                    or row["source_predicates"] is not None
                )
            )
        ):
            raise ValueError("whole PDF cohort conceals an unsupported original source/reference role")
        results.append(
            {
                "id": artifact.id,
                "role": role,
                "current_reproduction": reproduced,
                "source_predicates": row["source_predicates"],
                "every_page_parity": row["every_page_parity"],
                "whole_reference": row["whole_reference"],
                "blockers": expected_blockers,
                "findings": findings,
            }
        )
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    operation.verify(reader)
    remaining(deadline)
    return {
        "schema_version": "template-native-whole-pdf-cohort-current-v2",
        "scope": scope,
        "original_run_id": original.run_id,
        "current_run_id": owner.run_id,
        "artifacts": results,
        "remaining": raw["remaining"],
        "status": "fail" if any(row["findings"] for row in results) else "blocked",
    }
