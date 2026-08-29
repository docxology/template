"""Reproduction-bundle verification helpers (schema, entries, cardinality)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from infrastructure.publishing.repro_bundle import (
    COUNTS_RELPATH,
    SCHEMA_VERSION,
    VerifyReport,
    _ENTRY_REQUIRED_FIELDS,
    _KIND_ARTIFACT_MANIFEST,
    _KIND_CANONICAL_FACTS,
    _KIND_LOCKFILE,
    _KIND_OUTPUT_ARTIFACT,
    _KIND_PYPROJECT,
    _artifact_manifest_relpath,
    _declared_output_relpaths,
    _hash_relpath,
    _reproduce_commands,
    _resolve_repro_project,
    _validate_repro_project_name,
    _valid_generated_at,
)

_KNOWN_KINDS = {
    _KIND_LOCKFILE,
    _KIND_PYPROJECT,
    _KIND_ARTIFACT_MANIFEST,
    _KIND_CANONICAL_FACTS,
    _KIND_OUTPUT_ARTIFACT,
}


def collect_schema_findings(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """Return schema/project/reproduce mismatches and the normalized project name."""
    mismatches: list[dict[str, Any]] = []
    if raw.get("schema_version") != SCHEMA_VERSION:
        mismatches.append({"path": "<manifest>", "reason": "unsupported-schema"})
    if "generated_at" not in raw:
        mismatches.append({"path": "<manifest>", "reason": "missing-generated-at"})
    elif not _valid_generated_at(raw["generated_at"]):
        mismatches.append({"path": "<manifest>", "reason": "invalid-generated-at"})

    normalized_project: str | None = None
    raw_project = raw.get("project")
    if not isinstance(raw_project, str) or not raw_project.strip():
        mismatches.append({"path": "<manifest>", "reason": "missing-project"})
    else:
        try:
            candidate_project = _validate_repro_project_name(raw_project)
        except ValueError:
            mismatches.append({"path": "<manifest>", "reason": "invalid-project"})
        else:
            if candidate_project != raw_project:
                mismatches.append({"path": "<manifest>", "reason": "invalid-project"})
            else:
                normalized_project = candidate_project

    reproduce = raw.get("reproduce")
    if not isinstance(reproduce, list) or not reproduce:
        mismatches.append({"path": "<manifest>", "reason": "missing-reproduce-command"})
    elif normalized_project is not None and reproduce != _reproduce_commands(normalized_project):
        mismatches.append({"path": "<manifest>", "reason": "reproduce-command-mismatch"})
    return mismatches, normalized_project


def collect_expected_kinds(
    checkout_root: Path,
    normalized_project: str,
) -> tuple[list[dict[str, Any]], dict[str, str] | None, set[str], str | None]:
    """Resolve required kinds/paths for a verified project name."""
    mismatches: list[dict[str, Any]] = []
    expected_kinds_by_path: dict[str, str] | None = None
    expected_output_paths: set[str] = set()
    expected_artifact_manifest_path: str | None = None
    try:
        _normalized, project_dir = _resolve_repro_project(checkout_root, normalized_project)
    except ValueError as exc:
        mismatches.append(
            {
                "path": "<manifest>",
                "reason": "project-resolution-failed",
                "detail": str(exc),
            }
        )
        return mismatches, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path

    expected_artifact_manifest_path = _artifact_manifest_relpath(checkout_root, project_dir)
    if expected_artifact_manifest_path is None:
        mismatches.append({"path": "<manifest>", "reason": "missing-project-artifact-manifest"})
        return mismatches, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path

    try:
        expected_output_paths = set(_declared_output_relpaths(checkout_root, project_dir))
    except ValueError as exc:
        mismatches.append(
            {
                "path": "<manifest>",
                "reason": "invalid-project-artifact-manifest",
                "detail": str(exc),
            }
        )
        return mismatches, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path

    if not expected_output_paths:
        mismatches.append({"path": "<manifest>", "reason": "missing-project-output-artifacts"})
        return mismatches, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path

    expected_kinds_by_path = {
        "uv.lock": _KIND_LOCKFILE,
        "pyproject.toml": _KIND_PYPROJECT,
        COUNTS_RELPATH: _KIND_CANONICAL_FACTS,
        expected_artifact_manifest_path: _KIND_ARTIFACT_MANIFEST,
        **{path: _KIND_OUTPUT_ARTIFACT for path in expected_output_paths},
    }
    return mismatches, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path


def _path_is_unsafe_or_duplicate(path: str, seen_paths: set[str]) -> bool:
    path_obj = PurePosixPath(path)
    return (
        not path
        or path == "."
        or "\x00" in path
        or "\\" in path
        or path_obj.is_absolute()
        or (path_obj.parts and len(path_obj.parts[0]) == 2 and path_obj.parts[0][1] == ":")
        or ".." in path_obj.parts
        or path_obj.as_posix() != path
        or path in seen_paths
    )


def collect_entry_findings(
    entries: list[Any],
    *,
    checkout_root: Path,
    expected_kinds_by_path: dict[str, str] | None,
    expected_output_paths: set[str],
    expected_artifact_manifest_path: str | None,
) -> tuple[list[dict[str, Any]], int, set[str], dict[str, int], set[str], bool, bool]:
    """Validate each manifest entry and return per-entry state for cardinality."""
    mismatches: list[dict[str, Any]] = []
    checked = 0
    seen_paths: set[str] = set()
    kind_counts: dict[str, int] = {}
    observed_output_paths: set[str] = set()
    artifact_manifest_present = False
    output_artifact_present = False
    for entry in entries:
        if not isinstance(entry, dict):
            mismatches.append({"path": "<malformed>", "reason": "malformed-entry"})
            continue
        missing_fields = sorted(_ENTRY_REQUIRED_FIELDS - set(entry))
        if missing_fields:
            mismatches.append(
                {
                    "path": str(entry.get("path", "<malformed>")),
                    "reason": "missing-entry-fields",
                    "missing": missing_fields,
                }
            )
        path_value = entry.get("path")
        path = path_value if isinstance(path_value, str) else ""
        kind = str(entry.get("kind", ""))
        expected = entry.get("sha256")
        expected_present = entry.get("present")
        checked += 1

        if _path_is_unsafe_or_duplicate(path, seen_paths):
            mismatches.append({"path": path or "<empty>", "reason": "unsafe-or-duplicate-path"})
            continue
        seen_paths.add(path)
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if kind == _KIND_OUTPUT_ARTIFACT:
            observed_output_paths.add(path)
        if kind not in _KNOWN_KINDS:
            mismatches.append({"path": path, "reason": "unknown-kind"})
        if expected_kinds_by_path is not None:
            expected_kind = expected_kinds_by_path.get(path)
            if expected_kind is None:
                mismatches.append({"path": path, "reason": "unexpected-entry-path"})
            elif kind != expected_kind:
                mismatches.append(
                    {
                        "path": path,
                        "reason": "kind-path-mismatch",
                        "expected": expected_kind,
                        "actual": kind,
                    }
                )
        if not isinstance(expected_present, bool):
            mismatches.append({"path": path, "reason": "invalid-present-flag"})
            continue
        metadata_valid = True
        if expected_present:
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                mismatches.append({"path": path, "reason": "invalid-sha256"})
                metadata_valid = False
        elif expected is not None:
            mismatches.append({"path": path, "reason": "invalid-absent-sha256"})
            metadata_valid = False
        size_value = entry.get("size_bytes")
        if isinstance(size_value, bool) or not isinstance(size_value, int) or size_value < 0:
            mismatches.append({"path": path, "reason": "invalid-size"})
            continue
        if not expected_present and size_value != 0:
            mismatches.append({"path": path, "reason": "invalid-absent-size"})
            metadata_valid = False
        if not metadata_valid:
            continue

        actual, _size, present = _hash_relpath(checkout_root, path)

        if kind == _KIND_ARTIFACT_MANIFEST and path == expected_artifact_manifest_path and expected_present and present:
            artifact_manifest_present = True
        if kind == _KIND_OUTPUT_ARTIFACT and path in expected_output_paths and expected_present and present:
            output_artifact_present = True

        if kind == _KIND_OUTPUT_ARTIFACT and not present:
            mismatches.append({"path": path, "reason": "missing-declared-output"})
            continue
        if not expected_present:
            if present:
                mismatches.append({"path": path, "reason": "unexpected-present"})
            continue
        if not present:
            mismatches.append({"path": path, "reason": "missing"})
            continue
        if actual != expected:
            mismatches.append(
                {
                    "path": path,
                    "reason": "hash-changed",
                    "expected": expected,
                    "actual": actual,
                }
            )
        elif _size != size_value:
            mismatches.append({"path": path, "reason": "size-changed", "expected": size_value, "actual": _size})

    return (
        mismatches,
        checked,
        seen_paths,
        kind_counts,
        observed_output_paths,
        artifact_manifest_present,
        output_artifact_present,
    )


def collect_cardinality_findings(
    *,
    expected_kinds_by_path: dict[str, str] | None,
    expected_output_paths: set[str],
    seen_paths: set[str],
    observed_output_paths: set[str],
    kind_counts: dict[str, int],
    artifact_manifest_present: bool,
    output_artifact_present: bool,
) -> list[dict[str, Any]]:
    """Return missing-required-entry and kind-count mismatches."""
    mismatches: list[dict[str, Any]] = []
    if not artifact_manifest_present:
        mismatches.append({"path": "<manifest>", "reason": "missing-artifact-manifest"})
    if not output_artifact_present:
        mismatches.append({"path": "<manifest>", "reason": "missing-output-artifacts"})
    if expected_kinds_by_path is None:
        return mismatches
    missing_paths = sorted(set(expected_kinds_by_path) - seen_paths)
    if missing_paths:
        mismatches.append(
            {
                "path": "<manifest>",
                "reason": "missing-required-entries",
                "missing": missing_paths,
            }
        )
    if observed_output_paths != expected_output_paths:
        mismatches.append(
            {
                "path": "<manifest>",
                "reason": "output-artifact-set-mismatch",
                "missing": sorted(expected_output_paths - observed_output_paths),
                "unexpected": sorted(observed_output_paths - expected_output_paths),
            }
        )
    expected_kind_counts = {
        _KIND_LOCKFILE: 1,
        _KIND_PYPROJECT: 1,
        _KIND_ARTIFACT_MANIFEST: 1,
        _KIND_CANONICAL_FACTS: 1,
        _KIND_OUTPUT_ARTIFACT: len(expected_output_paths),
    }
    for kind, expected_count in expected_kind_counts.items():
        actual_count = kind_counts.get(kind, 0)
        if actual_count != expected_count:
            mismatches.append(
                {
                    "path": "<manifest>",
                    "reason": "kind-cardinality-mismatch",
                    "kind": kind,
                    "expected": expected_count,
                    "actual": actual_count,
                }
            )
    return mismatches


def verify_repro_bundle(manifest_path: Path, *, checkout_root: Path) -> VerifyReport:
    """Verify a manifest against *checkout_root*, failing closed on any drift.

    Each manifest entry is recomputed; an entry is a mismatch when the file is
    missing or its SHA-256 differs from the recorded value.

    Output artifacts (``kind == "output-artifact"``) are the *reproduced product*
    of the bundle, so a declared output that is missing is **always** a mismatch
    (REPRO-VERIFY-1): a bundle that "reproduces nothing" must never certify as
    reproducible, even if the output was already absent when the bundle was
    built. Infra inputs (lockfile, pyproject, canonical-facts) are legitimately
    allowed to be absent — if recorded ``present=False`` they must simply remain
    absent.

    Args:
        manifest_path: Path to a ``repro_manifest.json`` emitted by the builder.
        checkout_root: Root of the checkout to verify against.

    Returns:
        A :class:`VerifyReport` whose ``ok`` is ``True`` only when every entry
        matches.
    """
    checkout_root = checkout_root.resolve()
    try:
        raw: Any = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return VerifyReport(ok=False, checked=0, mismatches=[{"path": "<manifest>", "reason": f"unreadable: {exc}"}])
    if not isinstance(raw, dict):
        return VerifyReport(ok=False, checked=0, mismatches=[{"path": "<manifest>", "reason": "not-a-mapping"}])

    mismatches, normalized_project = collect_schema_findings(raw)
    expected_kinds_by_path: dict[str, str] | None = None
    expected_output_paths: set[str] = set()
    expected_artifact_manifest_path: str | None = None
    if normalized_project is not None:
        kind_findings, expected_kinds_by_path, expected_output_paths, expected_artifact_manifest_path = (
            collect_expected_kinds(checkout_root, normalized_project)
        )
        mismatches.extend(kind_findings)

    entries = raw.get("entries")
    if not isinstance(entries, list) or not entries:
        mismatches.append({"path": "<manifest>", "reason": "empty-or-missing-entries"})
        return VerifyReport(ok=False, checked=0, mismatches=mismatches)

    (
        entry_findings,
        checked,
        seen_paths,
        kind_counts,
        observed_output_paths,
        artifact_manifest_present,
        output_artifact_present,
    ) = collect_entry_findings(
        entries,
        checkout_root=checkout_root,
        expected_kinds_by_path=expected_kinds_by_path,
        expected_output_paths=expected_output_paths,
        expected_artifact_manifest_path=expected_artifact_manifest_path,
    )
    mismatches.extend(entry_findings)
    mismatches.extend(
        collect_cardinality_findings(
            expected_kinds_by_path=expected_kinds_by_path,
            expected_output_paths=expected_output_paths,
            seen_paths=seen_paths,
            observed_output_paths=observed_output_paths,
            kind_counts=kind_counts,
            artifact_manifest_present=artifact_manifest_present,
            output_artifact_present=output_artifact_present,
        )
    )
    return VerifyReport(ok=not mismatches, checked=checked, mismatches=mismatches)
