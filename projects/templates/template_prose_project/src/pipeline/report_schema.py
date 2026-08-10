"""Strict schema validation for the prose evidence summary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = "template-prose/evidence-summary/1"
_TOP_LEVEL = frozenset({"schema_version", "status", "diagnostic_only", "metrics", "checks"})
_METRICS = frozenset({"readability", "citations", "bibliography", "structure", "quality_flags"})
_READABILITY = frozenset({"avg_flesch_reading_ease", "avg_flesch_kincaid_grade", "avg_gunning_fog"})
_CITATIONS = frozenset({"unique_keys", "citation_count", "density_per_1000"})
_STRUCTURE = frozenset({"files_with_h1", "files_with_skipped_levels", "heading_count"})
_QUALITY = frozenset({"long_sentence_count", "passive_count", "hedge_count"})
_BIBLIOGRAPHY = frozenset({"missing", "unused", "cited_count", "bib_count", "bib_path"})
_CHECK = frozenset({"name", "passed", "message", "details"})


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown or missing:
        raise ValueError(f"{label} keys mismatch: missing={missing}, unknown={unknown}")


def _number(value: object, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")


def _nonnegative_int(value: object, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def validate_evidence_summary(payload: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` when a summary violates the public report schema."""
    _exact_keys(payload, _TOP_LEVEL, "evidence summary")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Unsupported evidence summary schema: {payload['schema_version']!r}")
    if payload["status"] not in {"pass", "fail"}:
        raise ValueError("evidence summary status must be 'pass' or 'fail'")
    if payload["diagnostic_only"] is not True:
        raise ValueError("evidence summary diagnostic_only must remain true")

    metrics = _mapping(payload["metrics"], "metrics")
    _exact_keys(metrics, _METRICS, "metrics")
    readability = _mapping(metrics["readability"], "readability")
    _exact_keys(readability, _READABILITY, "readability")
    for key, value in readability.items():
        _number(value, f"readability.{key}")
    citations = _mapping(metrics["citations"], "citations")
    _exact_keys(citations, _CITATIONS, "citations")
    for key in ("unique_keys", "citation_count"):
        _nonnegative_int(citations[key], f"citations.{key}")
    _number(citations["density_per_1000"], "citations.density_per_1000")
    bibliography = _mapping(metrics["bibliography"], "bibliography")
    unknown_bib = sorted(set(bibliography) - _BIBLIOGRAPHY)
    if unknown_bib:
        raise ValueError(f"bibliography has unknown keys: {unknown_bib}")
    for key in ("missing", "unused"):
        if key in bibliography and not isinstance(bibliography[key], list):
            raise ValueError(f"bibliography.{key} must be a list")
    for key in ("cited_count", "bib_count"):
        if key in bibliography:
            _nonnegative_int(bibliography[key], f"bibliography.{key}")
    if "bib_path" in bibliography and not isinstance(bibliography["bib_path"], str):
        raise ValueError("bibliography.bib_path must be a string")
    structure = _mapping(metrics["structure"], "structure")
    _exact_keys(structure, _STRUCTURE, "structure")
    for key, value in structure.items():
        _nonnegative_int(value, f"structure.{key}")
    quality = _mapping(metrics["quality_flags"], "quality_flags")
    _exact_keys(quality, _QUALITY, "quality_flags")
    for key, value in quality.items():
        _nonnegative_int(value, f"quality_flags.{key}")

    checks = payload["checks"]
    if not isinstance(checks, list) or not checks:
        raise ValueError("evidence summary checks must be a non-empty list")
    for index, check in enumerate(checks):
        item = _mapping(check, f"checks[{index}]")
        _exact_keys(item, _CHECK, f"checks[{index}]")
        if not isinstance(item["name"], str) or not item["name"]:
            raise ValueError(f"checks[{index}].name must be a non-empty string")
        if not isinstance(item["passed"], bool):
            raise ValueError(f"checks[{index}].passed must be boolean")
        if not isinstance(item["message"], str):
            raise ValueError(f"checks[{index}].message must be a string")
        if not isinstance(item["details"], Mapping):
            raise ValueError(f"checks[{index}].details must be a mapping")


__all__ = ["SCHEMA_VERSION", "validate_evidence_summary"]
