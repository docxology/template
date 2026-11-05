"""Source target requirement bindings and finite checked-result DATA projection.

Typed held Office children select their complete authenticated census. Pitch
uses the shared genuine Source selector. Neither a requirement nor normalized
DATA grants an owner or replaces an actual native/control replay.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_oracle_obligation_spec import (
    NativeControlSuiteRequirement,
    NativeControlTargetRequirement,
    NativeOracleSpecification,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_office_control_custody import (
        NativeOfficeControlOriginal,
        OfficeControlReaderOperation,
    )

OfficeRequirementCohort = tuple[
    tuple["NativeOfficeControlOriginal", ...], "OfficeControlReaderOperation", SnapshotReader
]


def bind_office_control_target_requirements(
    specification: NativeOracleSpecification,
    cohorts: dict[str, OfficeRequirementCohort] | None,
    *,
    source: NativeSourceContext,
    deadline: float,
) -> NativeOracleSpecification:
    """Bind every target to a genuine held complete census; never observe pass.

    Called once after the phase's Office children finish. Reader compilation
    uses its independently executed Current census. An absent nomination stays
    unbound and residual; an empty arbitrary DATA list cannot prove absence.
    """
    if cohorts is None:
        return specification
    from infrastructure.reporting.native_office_control_custody import OfficeControlReaderOperation
    from infrastructure.reporting.native_office_diagram_cohort import _authenticated_cohort

    office_artifacts = tuple(artifact for artifact in specification.artifacts if artifact.format in {"docx", "epub"})
    selected = {artifact.format: artifact for artifact in office_artifacts}
    if len(selected) != len(office_artifacts):
        raise ValueError("Office requirement census needs each complete fixed Source artifact role")
    if set(cohorts) - set(selected):
        raise ValueError("Office Source requirement received a foreign configured native artifact")
    suites = {suite.id: suite for suite in specification.suites}
    for kind, (originals, operation, reader) in cohorts.items():
        remaining(deadline)
        if (
            type(operation) is not OfficeControlReaderOperation
            or reader.root != operation.source.bindings.current_root
            or operation.source.reference.commit != source.reference.commit
            or operation.source.reference.source_identity != source.reference.source_identity
            or operation.source.bindings.expected_implementation_bytes != source.bindings.expected_implementation_bytes
            or operation.source.bindings.selected_sdk_package_root != source.bindings.selected_sdk_package_root
        ):
            raise ValueError("Office complete requirement census belongs to another genuine Source/SDK")
        census, _ = _authenticated_cohort(
            originals, operation, reader, scope=specification.scope, kind=kind, deadline=deadline
        )
        applicability = specification.diagram_applicability
        if (
            applicability is None
            or census["artifact"] != asdict(selected[kind])
            or tuple((row["path"], row["sha256"]) for row in census["inputs"]["ordered_manuscripts"])
            != applicability.ordered_document_inputs
            or tuple(row["identity"] for row in census["source_fences"]) != applicability.occurrence_identities
        ):
            raise ValueError(
                "Office native target census differs from the full independently compiled Source selection"
            )
        suite_id = kind + "_diagrams"
        if not applicability.occurrence_identities:
            if census["targets"] or census["occurrences"] or suite_id in suites:
                raise ValueError("Office target absence differs from both complete Source censuses")
            operation.verify(reader)
            operation.source.verify_correspondence(operation.source.reference, reader.root, reader, deadline)
            if not reader.unchanged():
                raise ValueError("Office Source-derived target absence custody changed at closing")
            continue
        suite = suites[suite_id]
        if not census["targets"]:
            raise ValueError("Office full Source occurrences require every actual native placement target")
        controls = tuple(
            replace(
                control,
                target_requirements=tuple(
                    NativeControlTargetRequirement(
                        {"artifact_id": selected[kind].id, **target},
                        control.original_exit_code,
                        control.intended_diagnostic,
                    )
                    for target in census["targets"]
                ),
            )
            for control in suite.controls
        )
        suites[suite_id] = replace(suite, controls=controls)
        operation.verify(reader)
        operation.source.verify_correspondence(operation.source.reference, reader.root, reader, deadline)
        if not reader.unchanged():
            raise ValueError("Office Source target requirement custody changed at closing")
    remaining(deadline)
    return replace(specification, suites=tuple(suites[suite.id] for suite in specification.suites))


def normalize_checked_source_control_suite(
    specification: NativeOracleSpecification,
    suite: NativeControlSuiteRequirement,
    checked: dict[str, Any],
    *,
    original_run_id: str,
) -> dict[str, Any]:
    """Normalize only already completed native Original/current checked returns.

    The caller retains the actual replay return in memory. This is DATA shape
    projection, not authentication of a transported producer packet. Every
    original and Current signed code, target and diagnostic remains explicit.
    """
    source_binding = list(specification.source_binding)
    if (
        checked.get("scope") != specification.scope
        or checked.get("original_run_id") != original_run_id
        or not isinstance(checked.get("current_run_id"), str)
        or not checked["current_run_id"]
        or checked["current_run_id"] == original_run_id
    ):
        raise ValueError("checked configured suite lost actual Original/current scope and distinct runs")
    if suite.id == "configured_pitch":
        if (
            checked.get("schema_version") != "template-native-pitch-complete-control-replay-v1"
            or checked.get("source_binding") != source_binding
            or checked["plan"]["scope"] != specification.scope
            or checked["plan"]["formats"] != list(specification.declared_formats)
            or [row["artifact"]["id"] for row in checked["plan"]["artifacts"]] != list(suite.related_artifact_ids)
            or checked["plan"]["active_controls"] != [control.name for control in suite.controls]
        ):
            raise ValueError("checked configured Pitch result differs from its complete Source selector")
        outcomes = []
        for row, control in zip(checked["outcomes"], suite.controls, strict=True):
            outcomes.append(
                {
                    "name": row["name"],
                    "original_exit_code": row["original_exit_code"],
                    "reconstructed_exit_code": row["current_exit_code"],
                    "intended_diagnostic": control.intended_diagnostic,
                    "targets": row["targets"],
                    "target_outcomes": [
                        {**target, "reconstructed_exit_code": target["current_exit_code"]}
                        for target in row["target_outcomes"]
                    ],
                }
            )
    elif suite.id in {"docx_diagrams", "epub_diagrams"}:
        kind = suite.id.removesuffix("_diagrams")
        if (
            checked.get("schema_version") != "template-native-office-complete-diagram-cohort-checked-v1"
            or checked.get("kind") != kind
            or checked.get("source") != {"commit": source_binding[0], "source_identity": source_binding[1]}
            or checked.get("artifact") not in [asdict(artifact) for artifact in specification.artifacts]
            or checked["artifact"]["id"] not in suite.related_artifact_ids
        ):
            raise ValueError("checked Office matrix differs from its actual Source/artifact role")
        cases = checked["checked_cases"]
        expected = [(target, control.name) for target in checked["targets"] for control in suite.controls]
        if [(row["target"], row["control"]) for row in cases] != expected:
            raise ValueError("checked Office matrix omitted or reordered a complete placement/control pair")
        outcomes = []
        for control in suite.controls:
            rows = [row for row in cases if row["control"] == control.name]
            if not rows:
                raise ValueError("applicable Office configured control lacks every actual signed target case")
            targets = [{"artifact_id": checked["artifact"]["id"], **row["target"]} for row in rows]
            outcomes.append(
                {
                    "name": control.name,
                    "original_exit_code": rows[0]["original_exit_code"],
                    "reconstructed_exit_code": rows[0]["current_exit_code"],
                    "intended_diagnostic": control.intended_diagnostic,
                    "targets": targets,
                    "target_outcomes": [
                        {
                            "target": target,
                            "original_exit_code": row["original_exit_code"],
                            "current_exit_code": row["current_exit_code"],
                            "reconstructed_exit_code": row["current_exit_code"],
                            "intended_diagnostic": row["intended_finding"],
                        }
                        for target, row in zip(targets, rows, strict=True)
                    ],
                }
            )
    else:
        raise ValueError("configured target normalization cannot substitute for a literal capability suite")
    return {
        "suite_id": suite.id,
        "scope": specification.scope,
        "original_run_id": original_run_id,
        "current_run_id": checked["current_run_id"],
        "source_binding": source_binding,
        "outcomes": outcomes,
    }
