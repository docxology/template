"""Preregistration and deviation-ledger validation."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any

_REQUIRED_SECTIONS = ("title", "version", "hypotheses", "outcomes", "exclusion_rules", "analysis_plan")
_REGISTERED_REPORT_STAGES = {
    "stage_1",
    "stage_1_in_principle_acceptance",
    "stage_2",
    "replication",
    "registered_report",
}
_ETHICS_STATUSES = {"not_required", "approved", "exempt", "pending"}
_SENSITIVITY_DECISIONS = {"robust", "fragile", "exploratory", "not_applicable"}


@dataclass(frozen=True)
class RegistrationFinding:
    """One finding in a registered-report audit."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class RegistrationReport:
    """Summary of analysis adherence to a frozen registration."""

    valid: bool
    integrity_score: float
    registration_hash: str
    findings: tuple[RegistrationFinding, ...]


@dataclass(frozen=True)
class DeviationLedgerRow:
    """One row in the preregistration deviation ledger."""

    kind: str
    target: str
    registered: bool
    documented: bool
    rationale: str
    severity: str


def registration_hash(registration: dict[str, Any]) -> str:
    """Return a canonical hash for a registration payload."""
    payload = json.dumps(registration, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_registration(registration: dict[str, Any]) -> dict[str, Any]:
    """Return an immutable-by-convention copy with a self hash."""
    frozen = copy.deepcopy(registration)
    frozen.pop("registration_hash", None)
    frozen["registration_hash"] = registration_hash(frozen)
    return frozen


def validate_registration(registration: dict[str, Any]) -> tuple[RegistrationFinding, ...]:
    """Validate preregistration completeness before results are known."""
    findings: list[RegistrationFinding] = []
    for section in _REQUIRED_SECTIONS:
        if section not in registration:
            findings.append(RegistrationFinding("error", "missing_section", f"missing section: {section}"))
    _check_hypotheses(registration, findings)
    _check_outcomes(registration, findings)
    _check_analysis_plan(registration, findings)
    _check_stage_metadata(registration, findings)
    if "registration_hash" in registration:
        unhashed = dict(registration)
        supplied = str(unhashed.pop("registration_hash", ""))
        if supplied != registration_hash(unhashed):
            findings.append(RegistrationFinding("error", "hash_mismatch", "registration_hash does not match content"))
    return tuple(findings)


def compare_analysis_to_registration(
    registration: dict[str, Any],
    executed: dict[str, Any],
    deviations: list[dict[str, str]] | None = None,
) -> RegistrationReport:
    """Compare executed outcomes and models to a registered plan."""
    findings = list(validate_registration(registration))
    deviations = deviations or []
    registered_outcomes = {str(outcome.get("name", "")) for outcome in registration.get("outcomes", [])}
    executed_outcomes = set(str(name) for name in executed.get("outcomes", []))
    for outcome in sorted(executed_outcomes - registered_outcomes):
        if not _has_deviation(deviations, "outcome", outcome):
            findings.append(
                RegistrationFinding("error", "unregistered_outcome", f"executed unregistered outcome: {outcome}")
            )
    registered_model = str(registration.get("analysis_plan", {}).get("primary_model", ""))
    executed_model = str(executed.get("primary_model", ""))
    if registered_model and executed_model and registered_model != executed_model:
        severity = "warning" if _has_deviation(deviations, "model", executed_model) else "error"
        findings.append(
            RegistrationFinding(severity, "model_deviation", f"executed model {executed_model} differs from plan")
        )
    for deviation in deviations:
        if not deviation.get("rationale"):
            findings.append(RegistrationFinding("error", "deviation_without_rationale", "deviation lacks rationale"))
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    score = max(0.0, round(1.0 - len(errors) * 0.25 - len(warnings) * 0.10, 3))
    return RegistrationReport(
        valid=not errors,
        integrity_score=score,
        registration_hash=registration.get("registration_hash") or registration_hash(registration),
        findings=tuple(findings),
    )


def build_deviation_ledger(
    registration: dict[str, Any],
    executed: dict[str, Any],
    deviations: list[dict[str, str]] | None = None,
) -> tuple[DeviationLedgerRow, ...]:
    """Build an explicit confirmatory/exploratory/deviation ledger."""
    deviations = deviations or []
    rows: list[DeviationLedgerRow] = []
    registered_outcomes = _registered_outcomes(registration)
    executed_outcomes = set(str(name) for name in executed.get("outcomes", []))
    for outcome in sorted(executed_outcomes):
        documented = _has_deviation(deviations, "outcome", outcome)
        registered = outcome in registered_outcomes
        rows.append(
            DeviationLedgerRow(
                kind="outcome",
                target=outcome,
                registered=registered,
                documented=documented,
                rationale=_deviation_rationale(deviations, "outcome", outcome),
                severity="ok" if registered else ("warning" if documented else "error"),
            )
        )
    registered_model = str(registration.get("analysis_plan", {}).get("primary_model", ""))
    executed_model = str(executed.get("primary_model", ""))
    if registered_model and executed_model:
        documented = _has_deviation(deviations, "model", executed_model)
        rows.append(
            DeviationLedgerRow(
                kind="model",
                target=executed_model,
                registered=registered_model == executed_model,
                documented=documented,
                rationale=_deviation_rationale(deviations, "model", executed_model),
                severity="ok" if registered_model == executed_model else ("warning" if documented else "error"),
            )
        )
    seen = {(row.kind, row.target) for row in rows}
    for deviation in deviations:
        key = (str(deviation.get("kind", "")), str(deviation.get("target", "")))
        if key in seen:
            continue
        rows.append(
            DeviationLedgerRow(
                kind=key[0],
                target=key[1],
                registered=False,
                documented=bool(deviation.get("rationale")),
                rationale=str(deviation.get("rationale", "")),
                severity="warning" if deviation.get("rationale") else "error",
            )
        )
    return tuple(rows)


def validate_sensitivity_table(
    registration: dict[str, Any],
    sensitivity_rows: list[dict[str, Any]] | None,
) -> tuple[RegistrationFinding, ...]:
    """Validate a sensitivity-analysis table against registered outcomes and models."""
    findings: list[RegistrationFinding] = []
    rows = sensitivity_rows or []
    if not rows:
        return (RegistrationFinding("warning", "missing_sensitivity_table", "sensitivity table is recommended"),)
    registered_targets = _registered_outcomes(registration) | {
        str(registration.get("analysis_plan", {}).get("primary_model", ""))
    }
    for row in rows:
        if not isinstance(row, dict):
            findings.append(RegistrationFinding("error", "bad_sensitivity_row", "sensitivity rows must be mappings"))
            continue
        if not all(row.get(key) for key in ("name", "target", "model", "decision")):
            findings.append(
                RegistrationFinding(
                    "error", "incomplete_sensitivity_row", "sensitivity rows need name/target/model/decision"
                )
            )
            continue
        target = str(row["target"])
        if target not in registered_targets:
            findings.append(
                RegistrationFinding(
                    "warning", "unregistered_sensitivity_target", f"sensitivity target not registered: {target}"
                )
            )
        if row.get("decision") not in _SENSITIVITY_DECISIONS:
            findings.append(
                RegistrationFinding("error", "bad_sensitivity_decision", f"unsupported decision: {row.get('decision')}")
            )
    return tuple(findings)


def build_review_packet(
    registration: dict[str, Any],
    executed: dict[str, Any],
    deviations: list[dict[str, str]] | None = None,
    sensitivity_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic registered-report review packet for publication checks."""
    deviations = deviations or []
    if sensitivity_rows is None:
        raw_rows = registration.get("sensitivity_analyses", [])
        sensitivity_rows = raw_rows if isinstance(raw_rows, list) else []
    adherence = compare_analysis_to_registration(registration, executed, deviations)
    sensitivity_findings = validate_sensitivity_table(registration, sensitivity_rows)
    findings = adherence.findings + sensitivity_findings
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    review_score = max(0.0, round(1.0 - len(errors) * 0.25 - len(warnings) * 0.10, 3))
    registered = _registered_outcomes(registration)
    executed_outcomes = set(str(name) for name in executed.get("outcomes", []))
    return {
        "title": str(registration.get("title", "")),
        "registration_hash": adherence.registration_hash,
        "valid": not errors,
        "integrity_score": adherence.integrity_score,
        "review_score": review_score,
        "confirmatory_outcomes": tuple(sorted(executed_outcomes & registered)),
        "exploratory_outcomes": tuple(sorted(executed_outcomes - registered)),
        "deviation_ledger": tuple(row.__dict__ for row in build_deviation_ledger(registration, executed, deviations)),
        "sensitivity_analyses": tuple(dict(row) for row in sensitivity_rows if isinstance(row, dict)),
        "findings": tuple(finding.__dict__ for finding in findings),
    }


def _check_hypotheses(registration: dict[str, Any], findings: list[RegistrationFinding]) -> None:
    hypotheses = registration.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses:
        findings.append(RegistrationFinding("error", "missing_hypotheses", "hypotheses must be a non-empty list"))
        return
    seen: set[str] = set()
    for item in hypotheses:
        if not isinstance(item, dict) or not item.get("id") or not item.get("claim"):
            findings.append(RegistrationFinding("error", "bad_hypothesis", "hypotheses need id and claim"))
            continue
        hypothesis_id = str(item["id"])
        if hypothesis_id in seen:
            findings.append(
                RegistrationFinding("error", "duplicate_hypothesis", f"duplicate hypothesis: {hypothesis_id}")
            )
        seen.add(hypothesis_id)


def _check_outcomes(registration: dict[str, Any], findings: list[RegistrationFinding]) -> None:
    outcomes = registration.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        findings.append(RegistrationFinding("error", "missing_outcomes", "outcomes must be a non-empty list"))
        return
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            findings.append(RegistrationFinding("error", "bad_outcome", "outcome entries must be mappings"))
            continue
        if not all(outcome.get(key) for key in ("name", "measure", "analysis")):
            findings.append(RegistrationFinding("error", "incomplete_outcome", "outcomes need name, measure, analysis"))


def _check_analysis_plan(registration: dict[str, Any], findings: list[RegistrationFinding]) -> None:
    plan = registration.get("analysis_plan")
    if not isinstance(plan, dict) or not plan.get("primary_model"):
        findings.append(
            RegistrationFinding("error", "missing_primary_model", "analysis_plan.primary_model is required")
        )
    if isinstance(plan, dict) and "seed" not in plan:
        findings.append(RegistrationFinding("warning", "missing_seed", "analysis_plan.seed is recommended"))


def _check_stage_metadata(registration: dict[str, Any], findings: list[RegistrationFinding]) -> None:
    stage = registration.get("registered_report_stage")
    if not stage:
        findings.append(
            RegistrationFinding("warning", "missing_registered_report_stage", "registered_report_stage is recommended")
        )
    elif stage not in _REGISTERED_REPORT_STAGES:
        findings.append(RegistrationFinding("warning", "unknown_registered_report_stage", f"unknown stage: {stage}"))
    ethics = registration.get("ethics_review")
    if ethics is None:
        findings.append(
            RegistrationFinding("warning", "missing_ethics_review", "ethics_review metadata is recommended")
        )
        return
    if not isinstance(ethics, dict):
        findings.append(RegistrationFinding("error", "bad_ethics_review", "ethics_review must be a mapping"))
        return
    if ethics.get("status") not in _ETHICS_STATUSES:
        findings.append(RegistrationFinding("error", "bad_ethics_status", "ethics_review.status is unsupported"))


def _has_deviation(deviations: list[dict[str, str]], kind: str, target: str) -> bool:
    return any(
        item.get("kind") == kind and item.get("target") == target and item.get("rationale") for item in deviations
    )


def _deviation_rationale(deviations: list[dict[str, str]], kind: str, target: str) -> str:
    for item in deviations:
        if item.get("kind") == kind and item.get("target") == target:
            return str(item.get("rationale", ""))
    return ""


def _registered_outcomes(registration: dict[str, Any]) -> set[str]:
    return {str(outcome.get("name", "")) for outcome in registration.get("outcomes", []) if isinstance(outcome, dict)}
