"""Current rendered-input snapshot and validation-report commitments.

The repository-boundary scan lives in ``._scan`` and the record-set builders
in ``._records`` (split for the line-count gate). Every historical name is
re-imported here so this package remains the single public import path.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import (
    OutputInventoryMode,
    collect_current_artifact_manifest,
    compute_sha256,
    output_inventory_mode_for_project,
    validate_artifact_manifest,
)
from infrastructure.core.project_paths import (
    resolve_project_root,
    resolve_source_manuscript_dir,
)
from infrastructure.rendering.manuscript_composition import (
    COMPOSITION_RELATIVE_PATH,
    ManuscriptComposition,
    build_manuscript_composition,
    read_manuscript_composition,
)
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.output.artifacts import read_artifact_manifest
from infrastructure.validation.rendered_snapshot._records import (
    _fingerprint,
    _is_config_path,
    _project_records,
    _stage_records,
)
from infrastructure.validation.rendered_snapshot._scan import (
    FileRecord as _FileRecord,
    Fingerprint,
    RenderedSnapshotError,
    cached_records as _cached_records,  # legacy test alias
    cached_paths as _cached_paths,  # legacy alias (companion namespace)
    is_relative_to as _is_relative_to,
    iter_tree_files as _iter_tree_files,  # legacy test alias
    lexical_project_root_for_selection as _lexical_project_root_for_selection,
    relative_record as _relative_record,
    relative_to_permitted as _relative_to_permitted,
    repository_root_for as _repository_root_for,
    source_repository_boundary as _source_repository_boundary,
)

_GENERATED_MANUSCRIPT_NAMES = frozenset(
    {
        "00_00_transmission_begin.md",
        "99_zz_transmission_end.md",
    }
)


VALIDATED_INPUTS_SCHEMA_VERSION = "template-validated-rendered-inputs-v1"


@dataclass(frozen=True)
class EvidenceFile:
    """Digest-bound evidence file outside the recursive output fingerprint."""

    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ManuscriptConsumption:
    """Canonical source mapped to a hydrated input or actual combined artifact."""

    rendered_path: str
    rendered_sha256: str
    source_path: str | None
    source_sha256: str | None


@dataclass(frozen=True)
class CurrentRenderedSnapshot:
    """Current inputs and outputs that one validation run must commit."""

    project: str
    stage: Fingerprint
    source: Fingerprint
    config: Fingerprint
    output: Fingerprint
    artifact_manifest: EvidenceFile
    composition_manifest: EvidenceFile
    combined_manuscript: EvidenceFile
    consumed_manuscript: tuple[ManuscriptConsumption, ...]

    def validated_inputs_dict(self) -> dict[str, object]:
        """Return the exact deterministic commitment embedded in validation reports."""
        return {
            "schema_version": VALIDATED_INPUTS_SCHEMA_VERSION,
            "project": self.project,
            "fingerprints": {
                "stage": asdict(self.stage),
                "source": asdict(self.source),
                "config": asdict(self.config),
                "output": asdict(self.output),
            },
            "artifact_manifest": asdict(self.artifact_manifest),
            "composition_manifest": asdict(self.composition_manifest),
            "combined_manuscript": asdict(self.combined_manuscript),
            "consumed_manuscript": [asdict(row) for row in self.consumed_manuscript],
        }


def _evidence_file(project_root: Path, path: Path) -> EvidenceFile:
    try:
        relative = path.resolve().relative_to(project_root.resolve()).as_posix()
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("EVIDENCE_PATH_ESCAPE", f"evidence path escapes project: {path}") from exc
    return EvidenceFile(relative, path.stat().st_size, compute_sha256(path))


def _output_records(
    project_root: Path,
    *,
    inventory_mode: OutputInventoryMode,
) -> tuple[list[_FileRecord], EvidenceFile]:
    output_dir = project_root / "output"
    manifest_path = output_dir / "reports" / "artifact_manifest.json"
    try:
        stored = read_artifact_manifest(manifest_path)
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_MISSING", "artifact manifest is missing") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", f"cannot read artifact manifest: {exc}") from exc
    validation = validate_artifact_manifest(
        stored,
        project_dir=project_root,
        expected_inventory_mode=inventory_mode,
    )
    invalid_issues = tuple(issue for issue in validation.issues if not issue.startswith("unattested stable artifact: "))
    if invalid_issues:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", "; ".join(invalid_issues))
    try:
        current = collect_current_artifact_manifest(
            output_dir,
            inventory_mode=inventory_mode,
        )
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("OUTPUT_TREE_INVALID", str(exc)) from exc
    if current.issues:
        raise RenderedSnapshotError("OUTPUT_TREE_INVALID", "; ".join(current.issues))
    current_by_path = {entry.path: entry for entry in current.entries}
    stored_by_path = {entry.path: entry for entry in stored.entries}
    if len(stored_by_path) != len(stored.entries):
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INVALID", "artifact manifest has duplicate paths")
    stored_paths = set(stored_by_path)
    current_paths = set(current_by_path)
    if stored_paths != current_paths:
        missing = sorted(current_paths - stored_paths)
        extra = sorted(stored_paths - current_paths)
        details = []
        if missing:
            details.append("unattested stable output: " + ", ".join(missing))
        if extra:
            details.append("manifest-only output: " + ", ".join(extra))
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_INCOMPLETE", "; ".join(details))
    stale = sorted(
        path
        for path in current_paths
        if stored_by_path[path].size_bytes != current_by_path[path].size_bytes
        or stored_by_path[path].sha256 != current_by_path[path].sha256
    )
    if stale:
        raise RenderedSnapshotError(
            "ARTIFACT_MANIFEST_INVALID",
            "artifact manifest has stale hashes: " + ", ".join(stale),
        )
    if not current_by_path:
        raise RenderedSnapshotError("ARTIFACT_MANIFEST_EMPTY", "stable output tree is empty")
    records = [_FileRecord(path, project_root / path) for path in sorted(current_by_path)]
    return records, _evidence_file(project_root, manifest_path)


def _validate_composition(
    project_root: Path,
    project: str,
    rendered_inputs: list[Path],
) -> tuple[ManuscriptComposition, EvidenceFile, EvidenceFile]:
    path = project_root / COMPOSITION_RELATIVE_PATH
    try:
        stored = read_manuscript_composition(path)
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("COMPOSITION_MISSING", "render-boundary composition evidence is missing") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("COMPOSITION_INVALID", f"cannot read composition evidence: {exc}") from exc
    if stored.project != project:
        raise RenderedSnapshotError("COMPOSITION_INVALID", f"composition project must be {project}")
    combined_path = project_root / stored.combined_path
    try:
        current = build_manuscript_composition(
            project_root,
            project,
            rendered_inputs,
            combined_path,
            algorithm=stored.algorithm,
        )
    except (OSError, ValueError) as exc:
        raise RenderedSnapshotError("COMPOSITION_INVALID", str(exc)) from exc
    if stored != current:
        raise RenderedSnapshotError(
            "COMPOSITION_DRIFT",
            "ordered render inputs or tracked combined Markdown changed after composition",
        )
    return stored, _evidence_file(project_root, path), _evidence_file(project_root, combined_path)


def _manuscript_consumption(
    project_root: Path,
    project: str,
) -> tuple[tuple[ManuscriptConsumption, ...], EvidenceFile, EvidenceFile]:
    source_root = resolve_source_manuscript_dir(project_root)
    source_paths = discover_manuscript_files(source_root)
    source_by_relative = {path.relative_to(source_root).as_posix(): path for path in source_paths}
    if not source_by_relative:
        raise RenderedSnapshotError("MANUSCRIPT_SOURCE_MISSING", "no canonical manuscript inputs discovered")
    hydrated_root = project_root / "output" / "manuscript"
    hydrated_paths = discover_manuscript_files(hydrated_root) if hydrated_root.is_dir() else []
    rendered_inputs = hydrated_paths or source_paths
    composition, composition_file, combined_file = _validate_composition(project_root, project, rendered_inputs)

    rows: list[ManuscriptConsumption] = []
    if hydrated_paths:
        hydrated_relative = {path.relative_to(hydrated_root).as_posix() for path in hydrated_paths}
        missing = sorted(set(source_by_relative) - hydrated_relative)
        if missing:
            raise RenderedSnapshotError(
                "UNCONSUMED_MANUSCRIPT",
                "canonical inputs absent from hydrated render tree: " + ", ".join(missing),
            )
        for path in hydrated_paths:
            relative = path.relative_to(hydrated_root).as_posix()
            source = source_by_relative.get(relative)
            if source is None and path.name not in _GENERATED_MANUSCRIPT_NAMES:
                raise RenderedSnapshotError(
                    "UNDECLARED_RENDERED_MANUSCRIPT",
                    f"hydrated manuscript has no canonical source: {relative}",
                )
            rows.append(
                ManuscriptConsumption(
                    rendered_path=path.relative_to(project_root).as_posix(),
                    rendered_sha256=compute_sha256(path),
                    source_path=source.relative_to(project_root).as_posix() if source else None,
                    source_sha256=compute_sha256(source) if source else None,
                )
            )
    else:
        for source in source_paths:
            rows.append(
                ManuscriptConsumption(
                    rendered_path=composition.combined_path,
                    rendered_sha256=composition.combined_sha256,
                    source_path=source.relative_to(project_root).as_posix(),
                    source_sha256=compute_sha256(source),
                )
            )
    return tuple(rows), composition_file, combined_file


def build_current_rendered_snapshot(repo_root: Path | str, project: str) -> CurrentRenderedSnapshot:
    """Build the current complete rendered snapshot without reading its validation report."""
    root = Path(repo_root).resolve()
    try:
        project_root = resolve_project_root(root, project)
    except ValueError as exc:
        raise RenderedSnapshotError(
            "PROJECT_LINK_INVALID",
            f"cannot resolve project source alias: {exc}",
        ) from exc
    lexical_project_root = _lexical_project_root_for_selection(root, project, project_root)
    inventory_mode = output_inventory_mode_for_project(root, project_root)
    source_records, config_records = _project_records(
        root,
        project_root,
        lexical_project_root=lexical_project_root,
    )
    output_records, artifact_manifest = _output_records(
        project_root,
        inventory_mode=inventory_mode,
    )
    consumption, composition_manifest, combined_manuscript = _manuscript_consumption(project_root, project)
    return CurrentRenderedSnapshot(
        project=project,
        stage=_fingerprint(_stage_records(root)),
        source=_fingerprint(source_records),
        config=_fingerprint(config_records),
        output=_fingerprint(output_records),
        artifact_manifest=artifact_manifest,
        composition_manifest=composition_manifest,
        combined_manuscript=combined_manuscript,
        consumed_manuscript=consumption,
    )


def validate_green_report_payload(payload: Any, project: str) -> Mapping[str, object]:
    """Validate report check/summary consistency and return validated inputs."""
    if not isinstance(payload, Mapping):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation report must be a mapping")
    checks = payload.get("checks")
    figure_issues = payload.get("figure_issues")
    summary = payload.get("summary")
    if (
        not isinstance(checks, Mapping)
        or not checks
        or not all(isinstance(name, str) and isinstance(result, bool) for name, result in checks.items())
    ):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation checks must be a non-empty bool mapping")
    if not isinstance(figure_issues, list):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation figure_issues must be a list")
    if not isinstance(summary, Mapping):
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", "validation summary must be a mapping")
    passed = sum(result is True for result in checks.values())
    failed = sum(result is False for result in checks.values())
    expected = {
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "figure_issues_count": len(figure_issues),
        "all_passed": failed == 0 and not figure_issues,
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise RenderedSnapshotError("VALIDATION_REPORT_INCONSISTENT", "validation summary contradicts checks")
    if expected["all_passed"] is not True:
        raise RenderedSnapshotError("VALIDATION_NOT_GREEN", "validation checks are not fully green")
    validated_inputs = payload.get("validated_inputs")
    if not isinstance(validated_inputs, Mapping):
        raise RenderedSnapshotError(
            "VALIDATION_INPUTS_MISSING",
            "validation report lacks a rendered-input commitment",
        )
    if validated_inputs.get("project") != project:
        raise RenderedSnapshotError("VALIDATION_INPUTS_INVALID", f"validated input project must be {project}")
    return validated_inputs


def read_committed_validation_report(
    repo_root: Path | str,
    project: str,
    current: CurrentRenderedSnapshot,
) -> EvidenceFile:
    """Require an internally green report committed to the exact current snapshot."""
    root = Path(repo_root).resolve()
    project_root = resolve_project_root(root, project)
    path = project_root / "output" / "reports" / "validation_report.json"
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RenderedSnapshotError("VALIDATION_REPORT_MISSING", "validation report is missing") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderedSnapshotError("VALIDATION_REPORT_INVALID", f"cannot read validation report: {exc}") from exc
    validated_inputs = validate_green_report_payload(payload, project)
    if dict(validated_inputs) != current.validated_inputs_dict():
        raise RenderedSnapshotError(
            "VALIDATION_INPUTS_DRIFT",
            "validation report was not generated for the exact current rendered snapshot",
        )
    return _evidence_file(project_root, path)


def rendered_manuscript_paths(project_root: Path) -> tuple[Path, ...]:
    """Return combined Markdown first, then hydrated-only evidence paths."""
    paths: list[Path] = []
    combined = project_root / "output" / "web" / "_combined_manuscript.md"
    if combined.is_file():
        paths.append(combined)
    hydrated_root = project_root / "output" / "manuscript"
    if hydrated_root.is_dir():
        paths.extend(
            path for path in discover_manuscript_files(hydrated_root) if path.suffix.lower() in {".md", ".rmd"}
        )
    return tuple(dict.fromkeys(paths))


__all__ = [
    "CurrentRenderedSnapshot",
    "EvidenceFile",
    "Fingerprint",
    "ManuscriptConsumption",
    "RenderedSnapshotError",
    "VALIDATED_INPUTS_SCHEMA_VERSION",
    "build_current_rendered_snapshot",
    "read_committed_validation_report",
    "rendered_manuscript_paths",
    "validate_green_report_payload",
]
