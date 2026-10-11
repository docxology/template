"""Complete Source-scoped Office diagram original/Current execution and replay.

Use existing fixed child custody and native predicates. No record, callback,
status field or mutable roster can create an original or current owner here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_control_custody import (
    NativeOfficeControlOriginal,
    OfficeControlReaderOperation,
)
from infrastructure.reporting.native_office_control_supervisor import (
    OfficeNativeDependencies,
    supervise_office_diagram_cohort,
)
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
from infrastructure.reporting.native_office_diagram_census import (
    replay_diagram_census_inputs,
    validate_diagram_census_data,
)
from infrastructure.reporting.native_office_diagram_controls import CONTROL_CODES, replay_office_diagram_control
from infrastructure.reporting.native_office_nested_custody import OfficeNestedReaderOperation, RetainedOfficeControl
from infrastructure.reporting.native_office_diagram_positive import OfficeDiagramNativePositive
from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_office_mermaid_binding import office_original_mermaid_sources
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _authenticated_cohort(
    originals: tuple[NativeOfficeControlOriginal, ...] | tuple[RetainedOfficeControl, ...],
    operation: OfficeControlReaderOperation | OfficeNestedReaderOperation,
    reader: SnapshotReader,
    *,
    scope: str,
    kind: str,
    deadline: float,
) -> tuple[dict[str, Any], list[tuple[NativeOfficeControlOriginal | RetainedOfficeControl, dict[str, Any]]]]:
    """Require one complete, externally held, sealed, actual child roster."""
    remaining(deadline)
    if (
        type(operation) not in (OfficeControlReaderOperation, OfficeNestedReaderOperation)
        or operation.deadline != deadline
        or not isinstance(originals, tuple)
        or not originals
        or len(originals) > 701
        or any(type(value) not in (NativeOfficeControlOriginal, RetainedOfficeControl) for value in originals)
        or any(not any(value is held for held in operation.originals) for value in originals)
        or len({id(value) for value in originals}) != len(originals)
        or any(value.scope != scope or value.kind != kind for value in originals)
    ):
        raise ValueError("Office complete cohort requires the fixed reader and exact externally held children")
    operation.verify(reader)
    cases = []
    for original in originals:
        remaining(deadline)
        operation.authenticate_artifact(
            {"path": original.observation_relative, "sha256": original.artifact_hashes[original.observation_relative]},
            reader,
            run_id=original.run_id,
            required_sdk_modules=(
                "reporting/native_office_diagram_control_worker.py",
                "reporting/native_office_diagram_census.py",
            )
            + (
                ()
                if original.control == "diagram-census"
                else (
                    "reporting/native_office_diagram_controls.py",
                    "reporting/native_office_diagram_positive.py",
                )
            ),
        )
        raw = original._read(original.observation_relative, reader).json_object()
        specification = json.loads(original.specification_bytes)
        if (
            raw.get("scope") != scope
            or raw.get("kind") != kind
            or raw.get("control") != original.control
            or type(raw.get("oracle_exit_code")) is not int
            or raw["oracle_exit_code"] != original.expected_exit
            or specification["target"] != raw.get("target")
        ):
            raise ValueError("Office fixed child oracle/Source/target differs from the held prelaunch specification")
        cases.append((original, raw))
    census_original, census = cases[0]
    if census_original.control != "diagram-census" or census_original.expected_exit != 0:
        raise ValueError("Office complete cohort must begin with the actual successful whole-Source census")
    validate_diagram_census_data(census, scope=scope, kind=kind, source=operation.source, deadline=deadline)
    replay_diagram_census_inputs(census, reader, deadline=deadline)
    content = reader.read(census["original_source"]["path"])
    if content.sha256 != census["original_source"]["sha256"]:
        raise ValueError("Office actual composed Source census artifact changed")
    identities = [identity for identity, _ in office_original_mermaid_sources(content.content.decode("utf-8"), scope)]
    if census["occurrences"] != identities:
        raise ValueError("Office child omitted an actual complete composed Source Mermaid fence")
    expected = [(target, control) for target in census["targets"] for control in ("baseline", *CONTROL_CODES)]
    if len(cases) - 1 != len(expected):
        raise ValueError("Office whole-placement baseline/refusal roster is incomplete")
    for (original, raw), (target, control) in zip(cases[1:], expected, strict=True):
        remaining(deadline)
        if (
            original.control != control
            or original.expected_exit != (0 if control == "baseline" else 1)
            or raw.get("target") != target
            or raw.get("targets") != census["targets"]
            or raw.get("positive", {}).get("occurrences") != identities
            or raw.get("expected_finding") != CONTROL_CODES.get(control)
            or raw["positive"]["reference"]["source"]["original_source"]["sha256"]
            != census["original_source"]["sha256"]
        ):
            raise ValueError("Office whole Source/placement/control/intended-refusal roster differs")
    operation.verify(reader)
    return census, cases[1:]


def execute_current_office_diagram_cohort(
    current_root: Path,
    current_directory: Path,
    current_source: NativeSourceContext,
    provider: NativePDFiumProvider,
    dependencies: OfficeNativeDependencies,
    *,
    original_reader_root: Path,
    scope: str,
    kind: str,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
) -> tuple[NativeOfficeControlOriginal, ...]:
    """Run the whole Current fixed-child roster once, without parent imports.

    Root retains these actual completed objects in its validator locals after
    closing Current producer/Mermaid scope. They are not serialized authority.
    The existing preimport provider independently verifies every physical input;
    every child separately admits its own Source/provider/runtime and actual
    native mapping under the fixed selected-SDK audited bootstrap.
    """
    producer = current_native_producer_operation()
    if (
        not isinstance(current_source, NativeSourceContext)
        or type(provider) is not NativePDFiumProvider
        or producer is None
        or producer.source is not current_source
        or producer.deadline != deadline
        or current_source.bindings.current_root != current_root
        or current_root == original_reader_root
        or current_root.is_relative_to(original_reader_root)
        or original_reader_root.is_relative_to(current_root)
    ):
        raise ValueError("Office Current child cohort needs its distinct genuine Source/live owner and original clock")
    return supervise_office_diagram_cohort(
        current_root,
        current_directory,
        current_source,
        provider,
        dependencies,
        scope=scope,
        kind=kind,
        interpreter=interpreter,
        env=env,
        deadline=deadline,
    )


def replay_office_diagram_cohort(
    reader_root: Path,
    original_children: tuple[NativeOfficeControlOriginal, ...] | tuple[RetainedOfficeControl, ...],
    original_operation: OfficeControlReaderOperation | OfficeNestedReaderOperation,
    original_reader: SnapshotReader,
    current_children: tuple[NativeOfficeControlOriginal, ...],
    current_operation: OfficeControlReaderOperation | OfficeNestedReaderOperation,
    current_reader: SnapshotReader,
    *,
    scope: str,
    kind: str,
    reader_positive: OfficeDiagramNativePositive | None,
    pdfium_runtime: PDFiumRuntimeAdmission,
    env: dict[str, str],
    deadline: float,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    current_custody: dict[str, str],
    current_versions: dict[str, dict[str, Any]],
    reader_directory: Path,
) -> dict[str, Any]:
    """Authenticate two held complete rosters under the existing Office reader.

    Root first executes Current children once under the distinct Current owner,
    closes that owner, then enters its existing Office reader/provider/Mermaid
    context. The one genuine reader-local positive supplies fresh source paint.
    No parent provider is imported or newly admitted during Current-child setup;
    no full Core/Common or native control suite is duplicated during replay.
    """
    remaining(deadline)
    producer = current_native_producer_operation()
    if (
        type(original_operation) not in (OfficeControlReaderOperation, OfficeNestedReaderOperation)
        or type(current_operation) is not OfficeControlReaderOperation
        or producer is None
        or producer.source is not original_operation.source
        or producer.deadline != deadline
        or reader_root != original_reader.root
        or original_operation.source.bindings.current_root != reader_root
        or current_operation.source.bindings.current_root != current_reader.root
        or current_reader.root == reader_root
        or current_reader.root.is_relative_to(reader_root)
        or reader_root.is_relative_to(current_reader.root)
        or pdfium_runtime.source is not original_operation.source
        or pdfium_runtime.scope != scope
        or original_operation.deadline != deadline
        or current_operation.deadline != deadline
    ):
        raise ValueError(
            "Office paired replay needs its actual existing reader owner, separate Current originals and clock"
        )
    original, original_cases = _authenticated_cohort(
        original_children,
        original_operation,
        original_reader,
        scope=scope,
        kind=kind,
        deadline=deadline,
    )
    if bool(original["occurrences"]) != (reader_positive is not None):
        raise ValueError("Office Current positive nomination differs from genuine Source applicability")
    if reader_positive is not None:
        reader_positive.verify(deadline)
        if (
            reader_positive.source is not original_operation.source
            or reader_positive.scope != scope
            or reader_positive.kind != kind
        ):
            raise ValueError("Office Current positive belongs to another actual Source/artifact")
    current, current_cases = _authenticated_cohort(
        current_children,
        current_operation,
        current_reader,
        scope=scope,
        kind=kind,
        deadline=deadline,
    )
    for field in ("source", "scope", "kind", "artifact", "inputs", "occurrences", "source_fences", "targets"):
        if original[field] != current[field]:
            raise ValueError(f"Office original/Current full Source/native diagram census differs: {field}")
    original_source = original_reader.read(original["original_source"]["path"])
    current_source_body = current_reader.read(current["original_source"]["path"])
    if original_source.content != current_source_body.content:
        raise ValueError("Office fresh Current independently recomposed a different complete Source body")
    checked = []
    if reader_positive is not None:
        sources = reader_positive.sources
        budget = reader_positive.decoded_pixel_budget
        for ordinal, ((held, raw), (current_held, current_raw)) in enumerate(
            zip(original_cases, current_cases, strict=True)
        ):
            remaining(deadline)
            if raw["control"] != current_raw["control"] or raw["target"] != current_raw["target"]:
                raise ValueError("Office original/Current exact per-placement case order differs")
            for label, case, observed, operation, reader, tools, tool_versions in (
                ("original", held, raw, original_operation, original_reader, custody, versions),
                (
                    "current",
                    current_held,
                    current_raw,
                    current_operation,
                    current_reader,
                    current_custody,
                    current_versions,
                ),
            ):
                positive_pdf = reader.read(observed["positive"]["pdf"]["path"])
                if positive_pdf.sha256 != observed["positive"]["pdf"]["sha256"]:
                    raise ValueError("Office held genuine positive PDF changed before complete replay")
                replay_office_diagram_control(
                    reader_root,
                    reader.root / json.loads(case.specification_bytes)["directory"],
                    positive_pdf.content,
                    sources,
                    observed,
                    reader,
                    budget=budget,
                    current_positive=reader_positive,
                    pdfium_runtime=pdfium_runtime,
                    deadline=deadline,
                    run_id=case.run_id,
                    custody=tools,
                    versions=tool_versions,
                    env=env,
                    reader_directory=reader_directory / f"{ordinal:04d}-{label}",
                    original_child=json.loads(case.process_bytes),
                    original_operation=operation,
                )
            checked.append(
                {
                    "target": raw["target"],
                    "control": raw["control"],
                    "intended_finding": raw["expected_finding"],
                    "original_exit_code": held.expected_exit,
                    "current_exit_code": current_held.expected_exit,
                    "original_observation": {
                        "path": held.observation_relative,
                        "sha256": held.artifact_hashes[held.observation_relative],
                    },
                    "current_observation": {
                        "path": current_held.observation_relative,
                        "sha256": current_held.artifact_hashes[current_held.observation_relative],
                    },
                }
            )
        reader_positive.verify(deadline)
    original_operation.verify(original_reader)
    current_operation.verify(current_reader)
    pdfium_runtime.verify()
    current_operation.source.verify_correspondence(
        current_operation.source.reference,
        current_reader.root,
        current_reader,
        deadline,
    )
    if not original_reader.unchanged() or not current_reader.unchanged():
        raise ValueError("Office complete original/Current census/control closing custody changed")
    remaining(deadline)
    return {
        "schema_version": "template-native-office-complete-diagram-cohort-checked-v1",
        "scope": scope,
        "kind": kind,
        "source": current["source"],
        "artifact": current["artifact"],
        "original_run_id": original_children[0].run_id,
        "current_run_id": current_operation.source.bindings.run_id,
        "original_source_sha256": hashlib.sha256(original_source.content).hexdigest(),
        "current_source_sha256": hashlib.sha256(current_source_body.content).hexdigest(),
        "occurrences": current["occurrences"],
        "source_fences": current["source_fences"],
        "targets": current["targets"],
        "checked_cases": checked,
        "absence_derived_from_both_complete_source_censuses": not bool(current["occurrences"]),
        "claim_boundary": "checked DATA for Root obligation dispatch; not a reusable admission capability",
    }
