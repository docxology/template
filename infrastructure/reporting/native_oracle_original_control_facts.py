"""Retain completed Original controller returns without reader or owner fabrication."""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_oracle_obligation_spec import NativeOracleSpecification
from infrastructure.reporting.native_office_diagram_cohort import _authenticated_cohort
from infrastructure.reporting.native_source_control_targets import OfficeRequirementCohort
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _file(value: dict[str, str], reader: SnapshotReader) -> dict[str, Any]:
    snapshot = reader.read(value["path"])
    if snapshot.sha256 != value["sha256"]:
        raise ValueError("completed Original control observation changed")
    return snapshot.json_object()


def _codes(value: object) -> set[str]:
    """Read actual finding DATA, never convert required names/codes into outcomes."""
    result: set[str] = set()
    if isinstance(value, dict):
        findings = value.get("findings", [])
        if isinstance(findings, list):
            for finding in findings:
                if isinstance(finding, dict) and isinstance(finding.get("code"), str):
                    result.add(finding["code"])
        for key, child in value.items():
            if key != "findings":
                result.update(_codes(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_codes(child))
    return result


def _diagnostic(payload: dict[str, Any], diagnostic: str | None) -> str | None:
    codes = _codes(payload)
    if diagnostic is None:
        if codes:
            raise ValueError("completed Original baseline has actual native findings")
        return None
    if diagnostic not in codes:
        raise ValueError("completed Original mutant lacks its actual intended finding")
    return diagnostic


def collect_original_native_controls(
    requirements: NativeOracleSpecification,
    raw: dict[str, Any],
    reader: SnapshotReader,
    office: dict[str, OfficeRequirementCohort],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Only call after the real supervisors, tool exits, audit and closing checks.

    The actual caller holds these in-memory returned records. Original process
    codes come from those supervised returns; no required code is copied into
    an observed result, and no future Current/reconstruction result is made.
    """
    suites: dict[str, Any] = {}
    controls = raw["observer_controls"]
    for suite in requirements.suites:
        outcomes: list[dict[str, Any]] = []
        if suite.id in {"docx_diagrams", "epub_diagrams"}:
            kind = suite.id.removesuffix("_diagrams")
            children, role, child_reader = office[kind]
            census, cases = _authenticated_cohort(
                children, role, child_reader, scope=requirements.scope, kind=kind, deadline=deadline
            )
            for control in suite.controls:
                actual = [(held, event) for held, event in cases if held.control == control.name]
                targets = [{"artifact_id": census["artifact"]["id"], **event["target"]} for _, event in actual]
                if not actual:
                    raise ValueError("completed Original Office control omitted its full target roster")
                outcomes.append(
                    {
                        "name": actual[0][0].control,
                        "original_exit_code": actual[0][1]["oracle_exit_code"],
                        "intended_diagnostic": actual[0][1]["expected_finding"],
                        "targets": targets,
                        "target_outcomes": [
                            {
                                "target": target,
                                "original_exit_code": event["oracle_exit_code"],
                                "intended_diagnostic": event["expected_finding"],
                            }
                            for target, (_, event) in zip(targets, actual, strict=True)
                        ],
                    }
                )
        else:
            selected = (
                raw["pdf_negative_controls"]
                if suite.id == "pdf"
                else controls.get("office_scientific", {}).get(suite.id.removesuffix("_scientific"))
                if suite.id.endswith("_scientific")
                else controls.get(
                    {"configured_print": "print", "manuscript_slides": "slide_source"}.get(suite.id, suite.id)
                )
            )
            if not isinstance(selected, list):
                # Missing real Original adapters are explicit projector residuals.
                continue
            if [row["name"] for row in selected] != [row.name for row in suite.controls]:
                raise ValueError("completed Original suite omitted/reordered actual Source controls")
            for record, control in zip(selected, suite.controls, strict=True):
                payload = _file(record.get("artifact", record.get("result")), reader)
                code = record.get("original_exit_code", record.get("observed_exit_code"))
                if type(code) is not int:
                    raise ValueError("completed Original control omitted its observed signed code")
                if suite.id == "configured_pitch":
                    target_diagnostics = [
                        _diagnostic(row["observation"], row["target"]["intended_diagnostic"]) for row in payload["rows"]
                    ]
                    distinct = set(target_diagnostics)
                    diagnostic = target_diagnostics[0] if len(distinct) == 1 else None
                else:
                    diagnostic = _diagnostic(payload, control.intended_diagnostic)
                name = record["name"]
                target_outcomes: list[dict[str, Any]] = []
                if suite.id == "configured_pitch":
                    targets = [row["target"] for row in payload["rows"]]
                    target_outcomes = [
                        {
                            "target": row["target"],
                            "original_exit_code": row["oracle_exit_code"],
                            "intended_diagnostic": _diagnostic(
                                row["observation"], row["target"]["intended_diagnostic"]
                            ),
                        }
                        for row in payload["rows"]
                    ]
                elif suite.id == "configured_print":
                    targets = [row["artifact"] for row in payload["rows"]]
                elif suite.id.endswith("_scientific"):
                    kind = suite.id.removesuffix("_scientific")
                    targets = [{"fixture": "scientific-" + kind, "control": row["name"]} for row in payload["controls"]]
                else:
                    fixture = {
                        "pdf": "invented-control:pdf",
                        "html": "browser-control",
                        "html_semantic": "browser-semantic",
                        "manuscript_slides": "two-page-source-pdf",
                    }.get(suite.id, suite.id)
                    targets = [{"fixture": fixture, "name": name}]
                outcomes.append(
                    {
                        "name": name,
                        "original_exit_code": code,
                        "intended_diagnostic": diagnostic,
                        "targets": targets,
                        "target_outcomes": target_outcomes,
                    }
                )
        suites[suite.id] = {
            "suite_id": suite.id,
            "scope": requirements.scope,
            "original_run_id": raw["run_id"],
            "outcomes": outcomes,
        }
    return {
        "scope": requirements.scope,
        "source_binding": list(requirements.source_binding),
        "original_run_id": raw["run_id"],
        "suites": suites,
        "original_refusals": [
            {"name": row["name"], "original_exit_code": row["observed_exit_code"]} for row in raw["negative_controls"]
        ],
    }
