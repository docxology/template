"""Finite projection of fresh checked native DATA onto held Source requirements.

This module does not execute, authenticate or construct an owner. Callers retain
live checked returns in memory; transported producer outcomes are never inputs
for the reader. Missing axes remain residuals. Changed proofs still raise in the
existing adapter/control replays before this projection is invoked.
"""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_oracle_obligation_spec import NativeOracleSpecification
from infrastructure.reporting.native_source_control_targets import normalize_checked_source_control_suite
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def checked_native_observer_result(
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    original_run_id: str,
    reader: SnapshotReader,
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Retain actual computed findings after the specialized replay has closed.

    This report describes interpretation of the admitted Original bytes. It
    cannot stand in for separately executed Current native writer/converter
    outputs, a consuming-library qualification or unimplemented semantic axes.
    """
    from infrastructure.reporting.native_format_joint_source import require_native_operation

    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    if original is None or original.run_id != original_run_id or snapshot.relative != artifact.path:
        raise ValueError("checked native observer lost its externally held Original artifact/run")
    findings: list[dict[str, Any]] = []
    residuals: list[str] = []
    for result in observations:
        if not isinstance(result, dict) or not isinstance(result.get("findings"), list):
            raise ValueError("fresh native observer result omitted computed findings")
        blockers = result.get("blockers")
        if not isinstance(blockers, list) or any(not isinstance(row, str) or not row for row in blockers):
            raise ValueError("fresh native observer result omitted explicit source residuals")
        if any(
            not isinstance(row, dict) or not isinstance(row.get("code"), str) or not row["code"]
            for row in result["findings"]
        ):
            raise ValueError("fresh native observer findings are malformed")
        findings.extend(result["findings"])
        residuals.extend(blockers)
    if not observations:
        raise ValueError("fresh native observer report cannot be empty")
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("fresh native observer Source/evidence changed after replay")
    return {
        "scope": scope,
        "original_run_id": original_run_id,
        "source_binding": [operation.source.reference.commit, operation.source.reference.source_identity],
        "artifact_id": artifact.id,
        "format": artifact.format,
        "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "observations": observations,
        "findings": findings,
        "residuals": residuals,
        "claim_boundary": "fresh interpretation DATA; separate Current native cohort and coverage axes remain required",
    }


def _residuals(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError("checked axis residual DATA must be an ordered tuple of nonempty reasons")
    return value


def project_native_oracle_residuals(
    specification: NativeOracleSpecification,
    *,
    original_run_id: str,
    checked_axes: dict[str, Any],
    checked_controls: dict[str, Any],
    source_target_plans: dict[str, Any],
    phase: str = "reader",
) -> list[dict[str, str]]:
    """Project complete actual axis/control returns once per Original/reader phase.

    Axis tuples come only from the phase's actual specialized checks. Empty
    tuples describe completed checks, not requirements or producer declarations.
    The reserved Root collector joins actual artifact/Current/Source-role DATA
    before calling here. A missing collector entry never becomes a pass.

    Original requires completed actual Original predicates and signed outcomes;
    reader additionally requires independently reconstructed outcomes and real
    Current configured-target signed codes. Original does not invent a future
    Current process or apply a missing-future-run denial. Reader is the default.

    Target plans must be independently Source-selected in this phase, and must
    include baseline and every selected refusal. Generic fixtures retain their
    literal fixture targets; they are never promoted to configured artifacts.
    """
    if phase not in {"original", "reader"}:
        raise ValueError("native dispatch requires its explicit actual Original or reader phase")
    if not isinstance(specification, NativeOracleSpecification) or not original_run_id:
        raise ValueError("native residual projection requires its actual compiled Source contract/run")
    source_binding = list(specification.source_binding)
    for packet in (checked_axes, checked_controls, source_target_plans):
        if packet.get("scope") != specification.scope or packet.get("source_binding") != source_binding:
            raise ValueError("checked native DATA differs from its independently compiled Source/scope")
    if (
        checked_axes.get("original_run_id") != original_run_id
        or checked_controls.get("original_run_id") != original_run_id
    ):
        raise ValueError("checked native DATA differs from its externally held Original run")
    identities = [artifact.id for artifact in specification.artifacts]
    if (
        checked_axes.get("artifact_contract_digest") != specification.artifact_contract_digest
        or checked_axes.get("artifact_ids") != identities
        or source_target_plans.get("artifact_contract_digest") != specification.artifact_contract_digest
    ):
        raise ValueError("checked native DATA omitted or altered the exact complete Source artifact roster")
    findings = checked_axes.get("findings")
    if not isinstance(findings, list) or findings:
        raise ValueError("checked native axis findings must remain a failure before residual projection")
    artifact_axis_results = checked_axes["artifact_axis_results"]
    checked_suites = checked_controls["suites"]
    checked_refusals = checked_controls["original_refusals"]
    source_selected_targets = source_target_plans["suites"]
    if (
        not isinstance(artifact_axis_results, dict)
        or not isinstance(checked_suites, dict)
        or not isinstance(checked_refusals, (tuple, list))
        or not isinstance(source_selected_targets, dict)
    ):
        raise ValueError("checked native DATA projection omitted its finite axis/control/target collections")
    artifacts = {artifact.id: artifact for artifact in specification.artifacts}
    if set(artifact_axis_results) - set(artifacts) or set(checked_suites) - {s.id for s in specification.suites}:
        raise ValueError("checked native DATA names foreign artifacts or suites")
    required_axes: dict[str, tuple[str, ...]] = {}
    for obligation in specification.obligations:
        for witness in obligation.witnesses:
            prior = required_axes.setdefault(witness.artifact_id, witness.coverage_axes)
            if prior != witness.coverage_axes:
                raise ValueError("overlapping native requirements disagree on exact artifact axes")
    for identity, axes in artifact_axis_results.items():
        if set(axes) - set(required_axes[identity]):
            raise ValueError("native artifact result invents an undeclared coverage axis")
        for axis_reasons in axes.values():
            _residuals(axis_reasons)
    expected_refusals = specification.original_refusals
    if tuple(row.get("name") for row in checked_refusals) != tuple(row.name for row in expected_refusals):
        raise ValueError("native conformance original refusal roster changed or is incomplete")
    if any(
        type(row.get("original_exit_code")) is not int or row["original_exit_code"] != requirement.original_exit_code
        for row, requirement in zip(checked_refusals, expected_refusals, strict=True)
    ):
        raise ValueError("native original parser/tool refusal no longer preserves its required actual exit")
    suites = {suite.id: suite for suite in specification.suites}
    if set(source_selected_targets) - set(suites):
        raise ValueError("native target plan contains a foreign suite")
    suite_residuals: dict[str, list[str]] = {}
    for suite in specification.suites:
        suite_result = checked_suites.get(suite.id)
        suite_reasons: list[str] = []
        if suite_result is None:
            suite_reasons.append("complete checked suite/target replay is unavailable: " + suite.source_selector)
        else:
            if (
                phase == "reader"
                and suite.id in {"configured_pitch", "docx_diagrams", "epub_diagrams"}
                and suite_result.get("suite_id") is None
            ):
                suite_result = normalize_checked_source_control_suite(
                    specification, suite, suite_result, original_run_id=original_run_id
                )
            if suite_result.get("suite_id") != suite.id or suite_result.get("original_run_id") != original_run_id:
                raise ValueError("checked native suite lost its exact Source selector/run")
            if suite_result.get("scope") != specification.scope:
                raise ValueError("checked native suite belongs to another public Source scope")
            outcomes = suite_result.get("outcomes")
            if not isinstance(outcomes, list) or [row.get("name") for row in outcomes] != [
                r.name for r in suite.controls
            ]:
                raise ValueError("checked native suite omitted, repeated or reordered a required control")
            targets = source_selected_targets.get(suite.id)
            if targets is None:
                suite_reasons.append(
                    "independently Source-selected complete target plan is unavailable: " + suite.target_selector
                )
            elif tuple(targets) != tuple(r.name for r in suite.controls):
                raise ValueError("Source-selected native target plan omitted or reordered a control")
            if targets is not None and any(
                control.target_requirements
                and targets[control.name] != [target.target for target in control.target_requirements]
                for control in suite.controls
            ):
                raise ValueError("native target plan differs from the complete compiled Source target requirements")
            for row, requirement in zip(outcomes, suite.controls, strict=True):
                if (
                    type(row.get("original_exit_code")) is not int
                    or row["original_exit_code"] != requirement.original_exit_code
                    or phase == "reader"
                    and (
                        type(row.get("reconstructed_exit_code")) is not int
                        or row["reconstructed_exit_code"] != requirement.original_exit_code
                    )
                    or row.get("intended_diagnostic") != requirement.intended_diagnostic
                ):
                    raise ValueError("native checked control lost its original exit/intended independent diagnostic")
                if requirement.target_requirements:
                    target_outcomes = row.get("target_outcomes")
                    if not isinstance(target_outcomes, list) or len(target_outcomes) != len(
                        requirement.target_requirements
                    ):
                        raise ValueError("native configured control omitted its complete checked target outcomes")
                    for actual, target in zip(target_outcomes, requirement.target_requirements, strict=True):
                        if (
                            actual.get("target") != target.target
                            or type(actual.get("original_exit_code")) is not int
                            or actual["original_exit_code"] != target.original_exit_code
                            or phase == "reader"
                            and (
                                type(actual.get("reconstructed_exit_code")) is not int
                                or actual["reconstructed_exit_code"] != target.original_exit_code
                            )
                            or actual.get("intended_diagnostic") != target.intended_diagnostic
                            or phase == "reader"
                            and (
                                type(actual.get("current_exit_code")) is not int
                                or actual["current_exit_code"] != target.original_exit_code
                            )
                        ):
                            raise ValueError(
                                "native configured target lost its signed code or exact intended diagnostic"
                            )
                if targets is not None and row.get("targets") != targets[requirement.name]:
                    raise ValueError(
                        "checked native control targets differ from independently selected complete Source plan"
                    )
        suite_residuals[suite.id] = suite_reasons
    residual_rows: list[dict[str, str]] = []
    for obligation in specification.obligations:
        for witness in obligation.witnesses:
            axes = artifact_axis_results.get(witness.artifact_id, {})
            for axis in witness.coverage_axes:
                gap_reasons = axes.get(axis)
                if gap_reasons is None:
                    gap_reasons = ("actual checked axis/Source-role result is unavailable: " + witness.source_adapter,)
                for reason in gap_reasons:
                    residual_rows.append(
                        {"id": obligation.id, "artifact_id": witness.artifact_id, "axis": axis, "reason": reason}
                    )
        for suite_id in obligation.control_suite_ids:
            for reason in suite_residuals[suite_id]:
                residual_rows.append(
                    {
                        "id": obligation.id,
                        "suite_id": suite_id,
                        "axis": "complete-source-selected-original-and-current-control-suite",
                        "reason": reason,
                    }
                )
    return residual_rows
