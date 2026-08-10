"""Fail-closed claim-binding inventory and source-pin validation.

The regression pin files already carry manuscript locations, verifier
producers, inputs, tolerances, and revision metadata. This module adds the
missing roster-level contract: every public exemplar must explicitly declare
whether it has bound pins, external-data claims, or no quantitative claim lane.
Silence is not a valid release state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, cast

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

CLAIM_BINDING_SCHEMA = "template-claim-binding/v1"
CLAIM_BINDING_RECEIPT_SCHEMA = "template-claim-binding-receipt/v1"
ClaimBindingState = Literal["bound", "not_applicable", "external_data"]


@dataclass(frozen=True)
class ClaimBindingRecord:
    """Roster-level claim-binding declaration for one public exemplar."""

    project: str
    state: ClaimBindingState
    pin_file: str = ""
    claim_count: int = 0
    rationale: str = ""
    external_data_manifest: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe record."""
        return {
            "project": self.project,
            "state": self.state,
            "pin_file": self.pin_file,
            "claim_count": self.claim_count,
            "rationale": self.rationale,
            "external_data_manifest": self.external_data_manifest,
        }


@dataclass(frozen=True)
class ClaimBindingReport:
    """Validation report for the complete public claim-binding inventory."""

    schema_version: str
    projects: tuple[ClaimBindingRecord, ...]
    errors: tuple[str, ...]

    @property
    def status(self) -> str:
        """Return pass or fail without promoting review states."""
        return "pass" if not self.errors else "fail"

    def to_dict(self) -> dict[str, object]:
        """Return deterministic receipt data."""
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "project_count": len(self.projects),
            "bound_count": sum(item.state == "bound" for item in self.projects),
            "not_applicable_count": sum(item.state == "not_applicable" for item in self.projects),
            "external_data_count": sum(item.state == "external_data" for item in self.projects),
            "projects": [item.to_dict() for item in sorted(self.projects, key=lambda item: item.project)],
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class ClaimBindingReceipt:
    """Versioned receipt that binds the roster report to its manifest digest."""

    report: ClaimBindingReport
    manifest_sha256: str
    schema_version: str = CLAIM_BINDING_RECEIPT_SCHEMA

    def validate(self) -> list[str]:
        """Return report or digest-drift errors without promoting claims."""
        errors = list(self.report.errors)
        if self.schema_version != CLAIM_BINDING_RECEIPT_SCHEMA:
            errors.append(f"claim-binding receipt schema must be {CLAIM_BINDING_RECEIPT_SCHEMA}")
        if len(self.manifest_sha256) != 64:
            errors.append("claim-binding receipt manifest_sha256 must be a SHA-256 digest")
        elif self.manifest_sha256 != claim_binding_digest(self.report):
            errors.append("claim-binding receipt digest does not match the report")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return deterministic typed receipt data."""
        return {
            "schema_version": self.schema_version,
            "manifest_sha256": self.manifest_sha256,
            "report": self.report.to_dict(),
        }


def _load_records(path: Path) -> tuple[list[ClaimBindingRecord], list[str]]:
    """Parse a JSON inventory without accepting unknown shapes."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"cannot read claim-binding manifest: {exc}"]
    if not isinstance(raw, Mapping) or raw.get("schema_version") != CLAIM_BINDING_SCHEMA:
        return [], [f"claim-binding manifest must declare {CLAIM_BINDING_SCHEMA}"]
    rows = raw.get("projects")
    if not isinstance(rows, list):
        return [], ["claim-binding manifest projects must be a list"]
    records: list[ClaimBindingRecord] = []
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"project row {index} is not an object")
            continue
        state = row.get("state")
        if state not in {"bound", "not_applicable", "external_data"}:
            errors.append(f"project row {index} has invalid state: {state!r}")
            continue
        try:
            records.append(
                ClaimBindingRecord(
                    project=str(row["project"]),
                    state=cast(ClaimBindingState, state),
                    pin_file=str(row.get("pin_file", "")),
                    claim_count=int(row.get("claim_count", 0)),
                    rationale=str(row.get("rationale", "")),
                    external_data_manifest=str(row.get("external_data_manifest", "")),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"project row {index} is malformed: {exc}")
    return records, errors


def _pin_rows(
    repo_root: Path,
    record: ClaimBindingRecord,
) -> tuple[list[tuple[str, Mapping[str, object]]], Mapping[str, Mapping[str, object]], list[str]]:
    """Load one pin file and return claim rows plus actionable errors."""
    pin_path = (repo_root / record.pin_file).resolve()
    try:
        pin_path.relative_to(repo_root.resolve())
    except ValueError:
        return [], {}, [f"{record.project}: pin file escapes repository: {record.pin_file}"]
    if not pin_path.is_file():
        return [], {}, [f"{record.project}: missing pin file: {record.pin_file}"]
    try:
        raw = json.loads(pin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], {}, [f"{record.project}: unreadable pin file: {exc}"]
    if not isinstance(raw, Mapping):
        return [], {}, [f"{record.project}: pin file root must be an object"]
    rows = [
        (str(key), value) for key, value in raw.items() if not str(key).startswith("_") and isinstance(value, Mapping)
    ]
    provenance_raw = raw.get("_provenance", {})
    provenance = (
        {str(key): value for key, value in provenance_raw.items() if isinstance(value, Mapping)}
        if isinstance(provenance_raw, Mapping)
        else {}
    )
    return rows, provenance, []


def validate_claim_bindings(repo_root: Path | str, manifest_path: Path | str | None = None) -> ClaimBindingReport:
    """Validate the complete public claim-binding inventory."""
    root = Path(repo_root).resolve()
    path = Path(manifest_path) if manifest_path is not None else root / "tests/regression/claim_bindings.json"
    records, errors = _load_records(path)
    names = [record.project for record in records]
    expected = set(PUBLIC_PROJECT_NAMES)
    actual = set(names)
    if len(names) != len(actual):
        errors.append("claim-binding manifest contains duplicate projects")
    for missing in sorted(expected - actual):
        errors.append(f"missing public claim-binding row: {missing}")
    for extra in sorted(actual - expected):
        errors.append(f"claim-binding row is outside public scope: {extra}")

    for record in records:
        if record.state not in {"bound", "not_applicable", "external_data"}:
            errors.append(f"{record.project}: invalid claim-binding state {record.state!r}")
            continue
        if record.claim_count < 0:
            errors.append(f"{record.project}: claim_count must be non-negative")
        if record.state == "not_applicable":
            if record.claim_count != 0:
                errors.append(f"{record.project}: not_applicable rows cannot claim bound values")
            if not record.rationale.strip():
                errors.append(f"{record.project}: not_applicable rows need a rationale")
            continue
        if record.state == "external_data":
            if not record.external_data_manifest.strip():
                errors.append(f"{record.project}: external_data rows need a provenance manifest")
            continue
        if not record.pin_file:
            errors.append(f"{record.project}: bound rows need pin_file")
            continue
        rows, provenance, pin_errors = _pin_rows(root, record)
        errors.extend(pin_errors)
        if len(rows) != record.claim_count:
            errors.append(f"{record.project}: manifest claims {record.claim_count} pins but file contains {len(rows)}")
        for index, (key, row) in enumerate(rows):
            required = (
                "manuscript_section",
                "verifier_function",
                "verifier_args",
                "pinned_on",
                "pinned_at_commit",
            )
            missing_fields = [field for field in required if not row.get(field)]
            if not (row.get("abs_tolerance") is not None or row.get("rel_tolerance") is not None):
                missing_fields.append("abs_tolerance|rel_tolerance")
            pin_provenance = provenance.get(key, {})
            if not (row.get("reason") or row.get("refresh_reason") or row.get("note") or pin_provenance.get("reason")):
                missing_fields.append("reason|refresh_reason|note")
            if missing_fields:
                errors.append(f"{record.project}: pin {index} missing {', '.join(missing_fields)}")

    return ClaimBindingReport(CLAIM_BINDING_SCHEMA, tuple(records), tuple(sorted(set(errors))))


def claim_binding_digest(report: ClaimBindingReport) -> str:
    """Return the deterministic digest of a claim-binding report."""
    raw = json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_claim_binding_receipt(report: ClaimBindingReport) -> ClaimBindingReceipt:
    """Build a typed receipt for a validated or review-required report."""
    return ClaimBindingReceipt(report=report, manifest_sha256=claim_binding_digest(report))


__all__ = [
    "CLAIM_BINDING_SCHEMA",
    "CLAIM_BINDING_RECEIPT_SCHEMA",
    "ClaimBindingRecord",
    "ClaimBindingReport",
    "ClaimBindingReceipt",
    "ClaimBindingState",
    "build_claim_binding_receipt",
    "claim_binding_digest",
    "validate_claim_bindings",
]
