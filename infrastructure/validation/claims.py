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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, cast

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

CLAIM_BINDING_SCHEMA = "template-claim-binding/v1"
CLAIM_BINDING_RECEIPT_SCHEMA = "template-claim-binding-receipt/v1"
ClaimBindingState = Literal["bound", "not_applicable", "external_data"]
_REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
_LOCATION_SPLIT_RE = re.compile(r"\s*(?:\+|,|;)\s*")


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
    if (repo_root / record.pin_file).is_symlink():
        return [], {}, [f"{record.project}: pin file must not be a symlink: {record.pin_file}"]
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
        if not record.rationale.strip():
            errors.append(f"{record.project}: claim-binding rows need a rationale")
        if record.state == "not_applicable":
            if record.claim_count != 0:
                errors.append(f"{record.project}: not_applicable rows cannot claim bound values")
            continue
        if record.state == "external_data":
            if not record.external_data_manifest.strip():
                errors.append(f"{record.project}: external_data rows need a provenance manifest")
            elif not _safe_repo_file(root, record.external_data_manifest):
                errors.append(f"{record.project}: external_data manifest must be a repository file")
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
                "pinned_by",
                "pinned_at_commit",
            )
            missing_fields = [field for field in required if not row.get(field)]
            if not (row.get("abs_tolerance") is not None or row.get("rel_tolerance") is not None):
                missing_fields.append("abs_tolerance|rel_tolerance")
            pin_provenance = provenance.get(key, {})
            if not (row.get("reason") or row.get("refresh_reason") or row.get("note") or pin_provenance.get("reason")):
                missing_fields.append("reason|refresh_reason|note")
            revision = str(row.get("pinned_at_commit", ""))
            if revision and not _REVISION_RE.fullmatch(revision):
                missing_fields.append("pinned_at_commit (7-64 hex characters)")
            verifier_args = row.get("verifier_args")
            if verifier_args is not None and not isinstance(verifier_args, Mapping):
                missing_fields.append("verifier_args (mapping)")
            manuscript_section = str(row.get("manuscript_section", ""))
            project_root = root / "projects" / record.project
            manuscript_paths = _declared_location_paths(project_root, manuscript_section)
            if manuscript_section and not manuscript_paths:
                missing_fields.append("manuscript_section (existing source file)")
            producer = str(row.get("verifier_function", ""))
            if producer and not _producer_source_exists(root, record.project, producer):
                missing_fields.append("verifier_function (existing producer source)")
            if missing_fields:
                errors.append(f"{record.project}: pin {index} missing {', '.join(missing_fields)}")

    return ClaimBindingReport(CLAIM_BINDING_SCHEMA, tuple(records), tuple(sorted(set(errors))))


def _safe_repo_file(root: Path, relative: str) -> bool:
    """Return whether a declared evidence file is real, confined, and non-symlinked."""
    if not relative.strip():
        return False
    candidate = root / relative
    if candidate.is_symlink() or not candidate.is_file():
        return False
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _declared_location_paths(project_root: Path, section: str) -> tuple[str, ...]:
    """Return existing source paths named by a pin's compact location field.

    Pin locations intentionally permit a short, human-readable list such as
    ``manuscript/00_abstract.md, 02_introduction.md``.  Resolve bare names
    relative to the manuscript directory while still accepting project-root
    paths such as ``data/claim_ledger.yaml``.  A location is valid only when
    every declared path is a confined, non-symlinked file.
    """
    location = section.split(" / ", 1)[0].strip()
    if not location:
        return ()
    candidates: list[str] = []
    for token in _LOCATION_SPLIT_RE.split(location):
        relative = token.strip()
        if not relative:
            continue
        if "/" not in relative:
            relative = f"manuscript/{relative}"
        candidates.append(relative)
    if not candidates or not all(_safe_repo_file(project_root, item) for item in candidates):
        return ()
    return tuple(candidates)


def _producer_source_exists(root: Path, project: str, producer: str) -> bool:
    """Resolve a producer and callable suffix to a source file.

    The pin inventory uses both ``module.callable`` and
    ``module::callable`` spellings.  Resolve the longest existing module
    prefix without importing optional project code, and support explicit
    repository-relative paths for infrastructure producers.
    """
    raw = producer.strip()
    if not raw:
        return False
    module = raw.split("::", 1)[0].strip()
    if "::" not in raw:
        module = _longest_existing_module(module, root, project)
    if not module:
        return False
    if module.startswith("infrastructure.") or module.startswith("scripts."):
        return _module_file_exists(root, module)
    project_root = root / "projects" / project
    if module.startswith("src."):
        return _module_file_exists(project_root, "src." + module.removeprefix("src."))
    return _module_file_exists(project_root, "src." + module)


def _longest_existing_module(module: str, root: Path, project: str) -> str:
    """Find the longest module prefix represented by a repository file."""
    parts = module.split(".")
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate.startswith("infrastructure.") or candidate.startswith("scripts."):
            if _module_file_exists(root, candidate):
                return candidate
            continue
        project_root = root / "projects" / project
        source_module = candidate.removeprefix("src.") if candidate.startswith("src.") else candidate
        if _module_file_exists(project_root, "src." + source_module):
            return candidate
    return ""


def _module_file_exists(root: Path, module: str) -> bool:
    """Check a dotted module as either a Python file or package initializer."""
    relative = module.replace(".", "/")
    return _safe_repo_file(root, relative + ".py") or _safe_repo_file(root, relative + "/__init__.py")


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
