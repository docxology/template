"""Validation logic for data descriptor release packets."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

_CHECKSUM_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_TOP_LEVEL = ("name", "version", "license", "files", "fields", "provenance")
_REQUIRED_FILE_KEYS = ("path", "media_type", "checksum", "rows")
_REQUIRED_FIELD_KEYS = ("name", "type", "nullable")
_FIELD_TYPES = {"string", "number", "integer", "boolean", "date", "category"}
_QUANTITATIVE_TYPES = {"number", "integer"}
_TEXT_TYPES = {"string", "category"}
_MEDIA_TYPES = {"text/csv", "application/json", "application/parquet", "application/x-parquet"}


@dataclass(frozen=True)
class DescriptorFinding:
    """One descriptor validation finding."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class DescriptorReport:
    """Machine-readable summary of descriptor readiness."""

    valid: bool
    readiness_score: float
    schema_fingerprint: str
    field_count: int
    file_count: int
    findings: tuple[DescriptorFinding, ...]


@dataclass(frozen=True)
class FieldConstraintSummary:
    """Release-facing summary of one field's unit and validation contract."""

    name: str
    field_type: str
    unit: str
    has_bounds: bool
    allowed_values_count: int
    has_pattern: bool


def descriptor_fingerprint(descriptor: dict[str, Any]) -> str:
    """Return a stable fingerprint of the field schema."""
    fields = descriptor.get("fields", [])
    normalized: list[dict[str, str | bool]] = [
        {
            "name": str(field.get("name", "")),
            "type": str(field.get("type", "")),
            "nullable": bool(field.get("nullable", False)),
        }
        for field in fields
        if isinstance(field, dict)
    ]
    normalized.sort(key=lambda item: str(item["name"]))
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_descriptor(descriptor: dict[str, Any]) -> tuple[DescriptorFinding, ...]:
    """Validate the descriptor shape and release boundaries."""
    findings: list[DescriptorFinding] = []
    _check_top_level(descriptor, findings)
    _check_files(descriptor, findings)
    _check_fields(descriptor, findings)
    _check_primary_key(descriptor, findings)
    _check_provenance(descriptor, findings)
    return tuple(findings)


def build_descriptor_report(descriptor: dict[str, Any]) -> DescriptorReport:
    """Build a compact descriptor-readiness report."""
    findings = validate_descriptor(descriptor)
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    penalty = len(errors) * 0.25 + len(warnings) * 0.10
    readiness_score = max(0.0, round(1.0 - penalty, 3))
    files = descriptor.get("files", [])
    fields = descriptor.get("fields", [])
    return DescriptorReport(
        valid=not errors,
        readiness_score=readiness_score,
        schema_fingerprint=descriptor_fingerprint(descriptor),
        field_count=len(fields) if isinstance(fields, list) else 0,
        file_count=len(files) if isinstance(files, list) else 0,
        findings=findings,
    )


def summarize_field_constraints(descriptor: dict[str, Any]) -> tuple[FieldConstraintSummary, ...]:
    """Return a compact summary of field-level units, bounds, enumerations, and patterns."""
    summaries: list[FieldConstraintSummary] = []
    fields = descriptor.get("fields", [])
    if not isinstance(fields, list):
        return ()
    for field in fields:
        if not isinstance(field, dict):
            continue
        constraints = field.get("constraints", {})
        if not isinstance(constraints, dict):
            constraints = {}
        allowed_values = constraints.get("allowed_values", ())
        allowed_count = len(allowed_values) if isinstance(allowed_values, list) else 0
        summaries.append(
            FieldConstraintSummary(
                name=str(field.get("name", "")),
                field_type=str(field.get("type", "")),
                unit=str(field.get("unit", "")),
                has_bounds=constraints.get("minimum") is not None or constraints.get("maximum") is not None,
                allowed_values_count=allowed_count,
                has_pattern=bool(constraints.get("pattern")),
            )
        )
    return tuple(summaries)


def build_release_bundle_manifest(descriptor: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, JSON-ready manifest for dataset release review.

    The manifest intentionally contains metadata and checksums, not the data files
    themselves. It is suitable for manuscript tables, release-readiness reports,
    and pre-publication review packets.
    """
    report = build_descriptor_report(descriptor)
    files = descriptor.get("files", [])
    provenance = descriptor.get("provenance", [])
    return {
        "name": str(descriptor.get("name", "")),
        "version": str(descriptor.get("version", "")),
        "license": str(descriptor.get("license", "")),
        "valid": report.valid,
        "readiness_score": report.readiness_score,
        "schema_fingerprint": report.schema_fingerprint,
        "file_count": report.file_count,
        "field_count": report.field_count,
        "files": tuple(_release_file_entry(item) for item in files if isinstance(item, dict)),
        "field_constraints": tuple(summary.__dict__ for summary in summarize_field_constraints(descriptor)),
        "provenance_steps": tuple(str(item.get("step", "")) for item in provenance if isinstance(item, dict)),
        "findings": tuple(finding.__dict__ for finding in report.findings),
        "descriptor_hash": _canonical_hash(descriptor),
        "release_boundary": "metadata-and-checksums-only",
    }


def _check_top_level(descriptor: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    for key in _REQUIRED_TOP_LEVEL:
        if key not in descriptor:
            findings.append(DescriptorFinding("error", "missing_top_level", f"missing top-level key: {key}"))
    if not str(descriptor.get("license", "")).strip():
        findings.append(DescriptorFinding("error", "missing_license", "license must declare a reuse boundary"))


def _check_files(descriptor: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    files = descriptor.get("files")
    if not isinstance(files, list) or not files:
        findings.append(DescriptorFinding("error", "missing_files", "files must be a non-empty list"))
        return
    paths: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            findings.append(DescriptorFinding("error", "invalid_file_entry", "file entries must be mappings"))
            continue
        for key in _REQUIRED_FILE_KEYS:
            if key not in item:
                findings.append(DescriptorFinding("error", "missing_file_key", f"file entry missing {key}"))
        path = str(item.get("path", ""))
        if path in paths:
            findings.append(DescriptorFinding("error", "duplicate_file_path", f"duplicate file path: {path}"))
        paths.append(path)
        if not path:
            findings.append(DescriptorFinding("error", "missing_file_path", "file path is required"))
        if path.startswith("/") or ".." in path.split("/"):
            findings.append(DescriptorFinding("error", "unsafe_file_path", f"unsafe file path: {path}"))
        if str(item.get("media_type", "")) not in _MEDIA_TYPES:
            findings.append(DescriptorFinding("warning", "unknown_media_type", f"{path or '<missing>'} media type"))
        if not _CHECKSUM_RE.match(str(item.get("checksum", ""))):
            findings.append(DescriptorFinding("error", "bad_checksum", f"{path or '<missing>'} lacks sha256 checksum"))
        if int(item.get("rows", 0) or 0) <= 0:
            findings.append(DescriptorFinding("warning", "nonpositive_rows", f"{path or '<missing>'} has no rows"))


def _check_fields(descriptor: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    fields = descriptor.get("fields")
    if not isinstance(fields, list) or not fields:
        findings.append(DescriptorFinding("error", "missing_fields", "fields must be a non-empty list"))
        return
    names: list[str] = []
    for field in fields:
        if not isinstance(field, dict):
            findings.append(DescriptorFinding("error", "invalid_field_entry", "field entries must be mappings"))
            continue
        for key in _REQUIRED_FIELD_KEYS:
            if key not in field:
                findings.append(DescriptorFinding("error", "missing_field_key", f"field entry missing {key}"))
        name = str(field.get("name", ""))
        if name in names:
            findings.append(DescriptorFinding("error", "duplicate_field", f"duplicate field name: {name}"))
        names.append(name)
        if field.get("type") not in _FIELD_TYPES:
            findings.append(DescriptorFinding("warning", "unknown_field_type", f"{name} has non-standard type"))
        _check_field_constraints(field, findings)


def _check_primary_key(descriptor: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    fields = descriptor.get("fields", [])
    field_names = {str(field.get("name", "")) for field in fields if isinstance(field, dict)}
    primary = descriptor.get("primary_key", [])
    if not primary:
        findings.append(DescriptorFinding("warning", "missing_primary_key", "primary_key is recommended"))
        return
    for key in primary:
        if key not in field_names:
            findings.append(DescriptorFinding("error", "unknown_primary_key", f"primary key not in fields: {key}"))


def _check_provenance(descriptor: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    provenance = descriptor.get("provenance")
    if not isinstance(provenance, list) or len(provenance) < 2:
        findings.append(
            DescriptorFinding("warning", "thin_provenance", "provenance should include collection and validation")
        )


def _check_field_constraints(field: dict[str, Any], findings: list[DescriptorFinding]) -> None:
    name = str(field.get("name", ""))
    field_type = str(field.get("type", ""))
    constraints = field.get("constraints", {})
    if constraints and not isinstance(constraints, dict):
        findings.append(DescriptorFinding("error", "bad_constraints", f"{name} constraints must be a mapping"))
        return
    constraints = constraints if isinstance(constraints, dict) else {}
    if field_type in _QUANTITATIVE_TYPES and not str(field.get("unit", "")).strip():
        findings.append(DescriptorFinding("warning", "missing_unit", f"{name} quantitative field lacks unit"))
    if field_type == "category" and not constraints.get("allowed_values"):
        findings.append(DescriptorFinding("warning", "missing_category_values", f"{name} lacks allowed values"))
    _check_numeric_bounds(name, field_type, constraints, findings)
    allowed_values = constraints.get("allowed_values")
    if allowed_values is not None and (not isinstance(allowed_values, list) or not allowed_values):
        findings.append(DescriptorFinding("error", "bad_allowed_values", f"{name} allowed_values must be non-empty"))
    if constraints.get("pattern") and field_type not in _TEXT_TYPES:
        findings.append(DescriptorFinding("warning", "pattern_on_non_text_field", f"{name} has non-text pattern"))


def _check_numeric_bounds(
    name: str,
    field_type: str,
    constraints: dict[str, Any],
    findings: list[DescriptorFinding],
) -> None:
    lower = constraints.get("minimum")
    upper = constraints.get("maximum")
    if lower is None and upper is None:
        return
    if field_type not in _QUANTITATIVE_TYPES:
        findings.append(DescriptorFinding("warning", "bounds_on_non_numeric_field", f"{name} has non-numeric bounds"))
        return
    if lower is not None and not isinstance(lower, int | float):
        findings.append(DescriptorFinding("error", "bad_numeric_bound", f"{name} minimum must be numeric"))
    if upper is not None and not isinstance(upper, int | float):
        findings.append(DescriptorFinding("error", "bad_numeric_bound", f"{name} maximum must be numeric"))
    if isinstance(lower, int | float) and isinstance(upper, int | float) and lower > upper:
        findings.append(DescriptorFinding("error", "invalid_numeric_range", f"{name} minimum exceeds maximum"))


def _release_file_entry(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(item.get("path", "")),
        "media_type": str(item.get("media_type", "")),
        "checksum": str(item.get("checksum", "")),
        "rows": int(item.get("rows", 0) or 0),
    }


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
