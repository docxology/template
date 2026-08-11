"""Pure contracts for multi-phase boundaries, calibration, and provenance."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def validate_phase_boundaries(search_phases: Any) -> list[dict[str, str]]:
    """Validate phase-owned temporal/filter boundaries before replay."""
    if not isinstance(search_phases, dict):
        return [{"phase": "<root>", "code": "phases_not_mapping", "message": "search_phases must be a mapping"}]
    issues: list[dict[str, str]] = []
    for phase_id, raw in search_phases.items():
        phase = str(phase_id)
        if not isinstance(raw, dict):
            issues.append({"phase": phase, "code": "phase_not_mapping", "message": "phase must be a mapping"})
            continue
        queries = raw.get("queries")
        if not isinstance(queries, list) or any(not isinstance(query, str) or not query.strip() for query in queries):
            issues.append(
                {"phase": phase, "code": "invalid_queries", "message": "queries must be a list of non-empty strings"}
            )
        filters = raw.get("deterministic_filters", {})
        if filters is None:
            filters = {}
        if not isinstance(filters, dict):
            issues.append(
                {"phase": phase, "code": "invalid_filters", "message": "deterministic_filters must be a mapping"}
            )
            continue
        boundary = raw.get("temporal_boundary", filters)
        if not isinstance(boundary, dict):
            issues.append(
                {"phase": phase, "code": "invalid_temporal_boundary", "message": "temporal_boundary must be a mapping"}
            )
            continue
        values: dict[str, int] = {}
        for key in ("min_year", "max_year"):
            value = boundary.get(key)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
                issues.append(
                    {"phase": phase, "code": "invalid_temporal_bound", "message": f"{key} must be an integer year"}
                )
                continue
            values[key] = int(value)
        if "min_year" in values and "max_year" in values and values["min_year"] > values["max_year"]:
            issues.append(
                {
                    "phase": phase,
                    "code": "invalid_year_bounds",
                    "message": f"min_year {values['min_year']} is greater than max_year {values['max_year']}",
                }
            )
    return issues


def validate_cross_phase_conflicts(assertions: Any) -> list[str]:
    """Return conflicts where one paper/claim has incompatible polarities."""
    if not isinstance(assertions, list):
        return ["assertions must be a list"]
    polarities: dict[tuple[str, str], set[str]] = defaultdict(set)
    issues: list[str] = []
    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict):
            issues.append(f"assertions[{index}] must be a mapping")
            continue
        paper_id = str(assertion.get("paper_id", "")).strip()
        claim_id = str(assertion.get("claim_id", "")).strip()
        polarity = str(assertion.get("polarity", "")).strip().lower()
        if not paper_id or not claim_id or polarity not in {"support", "contradict", "uncertain"}:
            issues.append(f"assertions[{index}] requires paper_id, claim_id, and a valid polarity")
            continue
        polarities[(paper_id, claim_id)].add(polarity)
    for (paper_id, claim_id), values in sorted(polarities.items()):
        if "support" in values and "contradict" in values:
            issues.append(f"conflicting polarity for {paper_id}/{claim_id}: support and contradict")
    return issues


def validate_phase_provenance(records: Any, phase_order: Any) -> list[str]:
    """Validate phase ownership for assertion or artifact provenance rows.

    A phase label alone is not provenance.  Every row must identify the phase,
    artifact, producer, and source mode so a later report cannot silently
    collapse fixture evidence and live retrieval evidence into one claim.
    """
    if not isinstance(phase_order, list) or any(
        not isinstance(phase, str) or not phase.strip() for phase in phase_order
    ):
        return ["phase_order must be a list of phase IDs"]
    if not phase_order:
        return [] if records == [] else ["empty phase_order cannot carry provenance records"]
    known = set(phase_order)
    if len(known) != len(phase_order):
        return ["phase_order must contain unique phase IDs"]
    if not isinstance(records, list) or not records:
        return ["phase provenance records must be a non-empty list"]

    issues: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            issues.append(f"provenance[{index}] must be a mapping")
            continue
        phase = str(raw.get("phase", "")).strip()
        artifact = str(raw.get("artifact", "")).strip()
        producer = str(raw.get("producer", "")).strip()
        source = str(raw.get("source", "")).strip()
        if phase not in known:
            issues.append(f"provenance[{index}] references unknown phase {phase!r}")
        if not artifact or artifact.startswith("/") or ".." in artifact.split("/"):
            issues.append(f"provenance[{index}] has an unsafe or empty artifact")
        if not producer:
            issues.append(f"provenance[{index}] requires a producer")
        if not source:
            issues.append(f"provenance[{index}] requires a source mode or revision")
        key = (phase, artifact)
        if key in seen:
            issues.append(f"duplicate phase provenance: {phase}/{artifact}")
        seen.add(key)
    return issues


def build_cross_phase_conflict_report(assertions: Any, phase_order: list[str]) -> dict[str, Any]:
    """Build a reviewable conflict report without converting overlap to support."""
    if assertions is None:
        return {
            "schema_version": "advanced-literature-review/cross-phase-conflicts/1",
            "status": "not_configured",
            "conflicts": [],
            "issues": [],
        }
    issues = validate_cross_phase_conflicts(assertions)
    if isinstance(assertions, list):
        for index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict):
                continue
            phase = str(assertion.get("phase", "")).strip()
            source = str(assertion.get("source", "")).strip()
            if phase not in phase_order:
                issues.append(f"assertions[{index}] references unknown phase {phase!r}")
            if not source:
                issues.append(f"assertions[{index}] requires a source artifact or revision")
    conflicts = [issue for issue in issues if "conflicting polarity" in issue]
    return {
        "schema_version": "advanced-literature-review/cross-phase-conflicts/1",
        "status": "invalid" if len(conflicts) != len(issues) and issues else ("review" if conflicts else "pass"),
        "conflicts": sorted(conflicts),
        "issues": sorted(issues),
        "assertion_count": len(assertions) if isinstance(assertions, list) else 0,
    }


def validate_llm_calibration(cases: Any, *, allowed_labels: tuple[str, ...] = ("yes", "no")) -> list[str]:
    """Validate a small, offline calibration fixture for an optional LLM filter."""
    if not isinstance(cases, list) or not cases:
        return ["calibration cases must be a non-empty list"]
    issues: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            issues.append(f"cases[{index}] must be a mapping")
            continue
        case_id = str(case.get("id", "")).strip()
        if not case_id or case_id in seen:
            issues.append(f"cases[{index}] has a missing or duplicate id")
        seen.add(case_id)
        if not str(case.get("abstract", "")).strip():
            issues.append(f"cases[{index}].abstract must be non-empty")
        expected = str(case.get("expected", "")).strip().lower()
        if expected not in allowed_labels:
            issues.append(f"cases[{index}].expected must be one of {allowed_labels}")
    return issues


def score_llm_calibration(cases: list[dict[str, Any]], predictions: dict[str, str]) -> dict[str, Any]:
    """Score predictions against the offline calibration fixture."""
    issues = validate_llm_calibration(cases)
    if issues:
        return {"status": "invalid", "issues": issues, "n": 0, "accuracy": None}
    expected = {str(case["id"]): str(case["expected"]).strip().lower() for case in cases}
    missing = sorted(set(expected) - set(predictions))
    unknown = sorted(set(predictions) - set(expected))
    correct = sum(
        1 for case_id, label in expected.items() if str(predictions.get(case_id, "")).strip().lower() == label
    )
    return {
        "status": "review" if missing or unknown else "pass",
        "issues": ([f"missing predictions: {missing}"] if missing else [])
        + ([f"unknown predictions: {unknown}"] if unknown else []),
        "n": len(expected),
        "correct": correct,
        "accuracy": correct / len(expected),
    }


def validate_phase_artifact_manifest(manifest: Any, *, artifact_root: Path | None = None) -> list[str]:
    """Validate phase attribution and, optionally, on-disk artifact identity.

    ``artifact_root`` turns the structural contract into a source-of-truth
    check: every declared artifact must be a regular file beneath that root,
    and its recorded digest and byte count must match the current file.  The
    root is optional so callers can still validate hand-authored manifests
    without touching the filesystem.
    """
    if not isinstance(manifest, dict):
        return ["manifest must be a mapping"]
    phases = manifest.get("phase_order")
    artifacts = manifest.get("artifacts")
    if (
        not isinstance(phases, list)
        or any(not isinstance(phase, str) or not phase.strip() for phase in phases)
        or len(phases) != len(set(phases))
    ):
        return ["phase_order must be a list of unique phase IDs"]
    if not isinstance(artifacts, list):
        return ["artifacts must be a list"]
    issues: list[str] = []
    seen_paths: set[str] = set()
    known = set(phases)
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            issues.append(f"artifacts[{index}] must be a mapping")
            continue
        path = str(artifact.get("path", ""))
        attributed = artifact.get("phases")
        if not path or path.startswith("/") or ".." in path.split("/"):
            issues.append(f"artifacts[{index}] has an unsafe path")
        if path in seen_paths:
            issues.append(f"duplicate artifact path: {path}")
        seen_paths.add(path)
        if not isinstance(attributed, list) or (not attributed and known):
            issues.append(f"artifacts[{index}] must name at least one phase")
        elif any(phase not in known for phase in attributed):
            issues.append(f"artifacts[{index}] references an unknown phase")
        digest = artifact.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            issues.append(f"artifacts[{index}].sha256 must be a lowercase SHA-256 digest")
        size_bytes = artifact.get("size_bytes")
        if size_bytes is not None and (
            isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0
        ):
            issues.append(f"artifacts[{index}].size_bytes must be a non-negative integer")
        if artifact_root is not None and not path.startswith("/") and ".." not in path.split("/"):
            candidate = artifact_root / path
            if candidate.is_symlink():
                issues.append(f"artifacts[{index}] must not be a symlink")
                continue
            try:
                resolved = candidate.resolve()
                resolved.relative_to(artifact_root.resolve())
            except (OSError, ValueError):
                issues.append(f"artifacts[{index}] resolves outside the artifact root")
                continue
            if not candidate.is_file():
                issues.append(f"artifacts[{index}] is missing from the artifact root")
                continue
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                issues.append(f"artifacts[{index}] requires a digest when artifact_root is supplied")
            elif hashlib.sha256(candidate.read_bytes()).hexdigest() != digest:
                issues.append(f"artifacts[{index}] sha256 does not match the current file")
            if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
                issues.append(f"artifacts[{index}] requires size_bytes when artifact_root is supplied")
            elif candidate.stat().st_size != size_bytes:
                issues.append(f"artifacts[{index}] size_bytes does not match the current file")
    provenance = manifest.get("provenance")
    if provenance is not None:
        issues.extend(validate_phase_provenance(provenance, phases))
    return issues


__all__ = [
    "build_cross_phase_conflict_report",
    "score_llm_calibration",
    "validate_cross_phase_conflicts",
    "validate_llm_calibration",
    "validate_phase_artifact_manifest",
    "validate_phase_boundaries",
    "validate_phase_provenance",
]
