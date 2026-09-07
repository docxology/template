"""Fail-closed receipts for validated rendered public exemplars."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.validation.output.artifacts import read_artifact_manifest
from infrastructure.validation.rendered_snapshot import (
    CurrentRenderedSnapshot,
    EvidenceFile,
    Fingerprint,
    ManuscriptConsumption,
    RenderedSnapshotError,
    build_current_rendered_snapshot,
    read_committed_validation_report,
    rendered_manuscript_paths,
)

SCHEMA_VERSION = "template-rendered-provenance-v2"
EVIDENCE_MODE = "validated-co-snapshot-fingerprint-bridge"
RECEIPT_RELATIVE_PATH = Path("output/reports/rendered_provenance.json")
RenderedProvenanceError = RenderedSnapshotError
_HEX_DIGITS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class RenderedProvenanceReceipt:
    """One deterministic receipt bound to a complete validated snapshot."""

    project: str
    stage: Fingerprint
    source: Fingerprint
    config: Fingerprint
    output: Fingerprint
    artifact_manifest: EvidenceFile
    validation_report: EvidenceFile
    composition_manifest: EvidenceFile
    combined_manuscript: EvidenceFile
    consumed_manuscript: tuple[ManuscriptConsumption, ...]
    schema_version: str = SCHEMA_VERSION
    evidence_mode: str = EVIDENCE_MODE

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "evidence_mode": self.evidence_mode,
            "project": self.project,
            "fingerprints": {
                "stage": asdict(self.stage),
                "source": asdict(self.source),
                "config": asdict(self.config),
                "output": asdict(self.output),
            },
            "evidence_files": {
                "artifact_manifest": asdict(self.artifact_manifest),
                "validation_report": asdict(self.validation_report),
                "composition_manifest": asdict(self.composition_manifest),
                "combined_manuscript": asdict(self.combined_manuscript),
            },
            "consumed_manuscript": [asdict(row) for row in self.consumed_manuscript],
        }


@dataclass(frozen=True)
class RenderedProvenanceIssue:
    """One fail-closed receipt validation issue."""

    code: str
    message: str


@dataclass(frozen=True)
class RenderedProvenanceValidation:
    """Validation result for one rendered provenance receipt."""

    issues: tuple[RenderedProvenanceIssue, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether the receipt is complete and current."""
        return not self.issues


def _receipt_from_snapshot(
    current: CurrentRenderedSnapshot,
    validation_report: EvidenceFile,
) -> RenderedProvenanceReceipt:
    return RenderedProvenanceReceipt(
        project=current.project,
        stage=current.stage,
        source=current.source,
        config=current.config,
        output=current.output,
        artifact_manifest=current.artifact_manifest,
        validation_report=validation_report,
        composition_manifest=current.composition_manifest,
        combined_manuscript=current.combined_manuscript,
        consumed_manuscript=current.consumed_manuscript,
    )


def build_rendered_provenance_receipt(
    repo_root: Path | str,
    project: str,
) -> RenderedProvenanceReceipt:
    """Build a receipt only when a green report commits to the current snapshot."""
    current = build_current_rendered_snapshot(repo_root, project)
    report = read_committed_validation_report(repo_root, project, current)
    return _receipt_from_snapshot(current, report)


def write_rendered_provenance_receipt(
    repo_root: Path | str,
    project: str,
) -> RenderedProvenanceReceipt:
    """Write a deterministic receipt through a confined atomic boundary."""
    root = Path(repo_root).resolve()
    project_root = resolve_project_root(root, project)
    receipt = build_rendered_provenance_receipt(root, project)
    target = project_root / RECEIPT_RELATIVE_PATH
    content = json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n"
    atomic_write_text_confined(project_root, target, content)
    return receipt


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in _HEX_DIGITS for character in value)


def _parse_fingerprint(payload: object, label: str) -> Fingerprint:
    if not isinstance(payload, Mapping) or set(payload) != {"file_count", "sha256"}:
        raise ValueError(f"{label} fingerprint must contain only file_count and sha256")
    file_count = payload.get("file_count")
    sha256 = payload.get("sha256")
    if not isinstance(file_count, int) or isinstance(file_count, bool) or file_count <= 0:
        raise ValueError(f"{label} fingerprint file_count must be positive")
    if not _valid_sha256(sha256):
        raise ValueError(f"{label} fingerprint sha256 is invalid")
    assert isinstance(sha256, str)
    return Fingerprint(sha256, file_count)


def _parse_evidence_file(payload: object, label: str) -> EvidenceFile:
    if not isinstance(payload, Mapping) or set(payload) != {"path", "size_bytes", "sha256"}:
        raise ValueError(f"{label} evidence must contain path, size_bytes, and sha256")
    path = payload.get("path")
    size_bytes = payload.get("size_bytes")
    sha256 = payload.get("sha256")
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError(f"{label} evidence path is invalid")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
        raise ValueError(f"{label} evidence size_bytes is invalid")
    if not _valid_sha256(sha256):
        raise ValueError(f"{label} evidence sha256 is invalid")
    assert isinstance(sha256, str)
    return EvidenceFile(path, size_bytes, sha256)


def _optional_string(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"consumed manuscript {key} must be a string or null")
    return value


def _parse_consumption(payload: object) -> tuple[ManuscriptConsumption, ...]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("consumed_manuscript must be a non-empty list")
    rows: list[ManuscriptConsumption] = []
    expected = {"rendered_path", "rendered_sha256", "source_path", "source_sha256"}
    for raw in payload:
        if not isinstance(raw, Mapping) or set(raw) != expected:
            raise ValueError("consumed manuscript row has missing or unknown fields")
        rendered_path = raw.get("rendered_path")
        rendered_sha256 = raw.get("rendered_sha256")
        if not isinstance(rendered_path, str) or not rendered_path:
            raise ValueError("consumed manuscript rendered_path must be non-empty")
        if not _valid_sha256(rendered_sha256):
            raise ValueError("consumed manuscript rendered_sha256 is invalid")
        source_path = _optional_string(raw, "source_path")
        source_sha256 = _optional_string(raw, "source_sha256")
        if (source_path is None) != (source_sha256 is None):
            raise ValueError("consumed manuscript source path and digest must both be set or null")
        if source_sha256 is not None and not _valid_sha256(source_sha256):
            raise ValueError("consumed manuscript source_sha256 is invalid")
        assert isinstance(rendered_sha256, str)
        rows.append(
            ManuscriptConsumption(
                rendered_path=rendered_path,
                rendered_sha256=rendered_sha256,
                source_path=source_path,
                source_sha256=source_sha256,
            )
        )
    return tuple(rows)


def _parse_receipt(payload: Any, project: str) -> RenderedProvenanceReceipt:
    if not isinstance(payload, Mapping):
        raise ValueError("rendered provenance receipt must be a mapping")
    expected = {
        "schema_version",
        "evidence_mode",
        "project",
        "fingerprints",
        "evidence_files",
        "consumed_manuscript",
    }
    if set(payload) != expected:
        raise ValueError("rendered provenance receipt has missing or unknown fields")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if payload.get("evidence_mode") != EVIDENCE_MODE:
        raise ValueError(f"evidence_mode must be {EVIDENCE_MODE}")
    if payload.get("project") != project:
        raise ValueError(f"receipt project must be {project}")
    fingerprints = payload.get("fingerprints")
    if not isinstance(fingerprints, Mapping) or set(fingerprints) != {
        "stage",
        "source",
        "config",
        "output",
    }:
        raise ValueError("fingerprints must contain stage, source, config, and output")
    evidence = payload.get("evidence_files")
    if not isinstance(evidence, Mapping) or set(evidence) != {
        "artifact_manifest",
        "validation_report",
        "composition_manifest",
        "combined_manuscript",
    }:
        raise ValueError("evidence_files has missing or unknown fields")
    return RenderedProvenanceReceipt(
        project=project,
        stage=_parse_fingerprint(fingerprints["stage"], "stage"),
        source=_parse_fingerprint(fingerprints["source"], "source"),
        config=_parse_fingerprint(fingerprints["config"], "config"),
        output=_parse_fingerprint(fingerprints["output"], "output"),
        artifact_manifest=_parse_evidence_file(evidence["artifact_manifest"], "artifact_manifest"),
        validation_report=_parse_evidence_file(evidence["validation_report"], "validation_report"),
        composition_manifest=_parse_evidence_file(evidence["composition_manifest"], "composition_manifest"),
        combined_manuscript=_parse_evidence_file(evidence["combined_manuscript"], "combined_manuscript"),
        consumed_manuscript=_parse_consumption(payload.get("consumed_manuscript")),
    )


def _clean_index_issues(
    repo_root: Path,
    project_root: Path,
) -> tuple[str, ...]:
    """Return required release paths absent or different in Git's cached index."""
    if not (repo_root / ".git").exists():
        return ()
    try:
        project_prefix = project_root.relative_to(repo_root).as_posix()
    except ValueError:
        return ("project root is outside the release repository",)
    manifest = read_artifact_manifest(project_root / "output" / "reports" / "artifact_manifest.json")
    required = {f"{project_prefix}/{entry.path}" for entry in manifest.entries}
    required.update(
        {
            f"{project_prefix}/{relative.as_posix()}"
            for relative in (
                RECEIPT_RELATIVE_PATH,
                Path("output/reports/artifact_manifest.json"),
                Path("output/reports/manuscript_composition.json"),
                Path("output/reports/validation_report.json"),
                Path("output/web/_combined_manuscript.md"),
            )
        }
    )
    policy = SubprocessPolicy(
        policy_id="git-metadata",
        source_path="infrastructure/validation/publication/rendered_provenance.py",
        timeout_seconds=30,
        capture_output=True,
        credential_free=True,
    )
    try:
        cached_result = run_with_policy(["git", "ls-files", "--cached", "-z"], cwd=repo_root, env=None, policy=policy)
        dirty_result = run_with_policy(["git", "diff", "--name-only", "-z"], cwd=repo_root, env=None, policy=policy)
    except (OSError, ValueError) as exc:
        return (f"Git index is unavailable: {exc}",)
    if cached_result.returncode != 0 or dirty_result.returncode != 0:
        return ("Git index is unavailable for rendered evidence validation",)
    cached = {raw for raw in cached_result.stdout.split("\0") if raw}
    dirty = {raw for raw in dirty_result.stdout.split("\0") if raw}
    issues = [f"not cached: {path}" for path in sorted(required - cached)]
    issues.extend(f"working tree differs from cached evidence: {path}" for path in sorted(required & dirty))
    return tuple(issues)


def validate_rendered_provenance(
    repo_root: Path | str,
    project: str,
) -> RenderedProvenanceValidation:
    """Fail closed unless the stored receipt is well formed and exactly current."""
    root = Path(repo_root).resolve()
    project_root = resolve_project_root(root, project)
    path = project_root / RECEIPT_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return RenderedProvenanceValidation(
            (RenderedProvenanceIssue("MISSING", f"missing {RECEIPT_RELATIVE_PATH.as_posix()}"),)
        )
    except (OSError, json.JSONDecodeError) as exc:
        return RenderedProvenanceValidation(
            (RenderedProvenanceIssue("MALFORMED", f"cannot read rendered provenance receipt: {exc}"),)
        )
    try:
        stored = _parse_receipt(payload, project)
    except ValueError as exc:
        return RenderedProvenanceValidation((RenderedProvenanceIssue("MALFORMED", str(exc)),))
    try:
        current = build_rendered_provenance_receipt(root, project)
    except RenderedSnapshotError as exc:
        return RenderedProvenanceValidation((RenderedProvenanceIssue(exc.code, str(exc)),))
    issues: list[RenderedProvenanceIssue] = []
    if stored != current:
        for label in ("stage", "source", "config", "output"):
            if getattr(stored, label) != getattr(current, label):
                issues.append(
                    RenderedProvenanceIssue(
                        f"{label.upper()}_FINGERPRINT_DRIFT",
                        f"{label} files no longer match the validated rendered snapshot",
                    )
                )
        for label in (
            "artifact_manifest",
            "validation_report",
            "composition_manifest",
            "combined_manuscript",
        ):
            if getattr(stored, label) != getattr(current, label):
                issues.append(
                    RenderedProvenanceIssue(
                        f"{label.upper()}_DRIFT",
                        f"{label.replace('_', ' ')} no longer matches the validated rendered snapshot",
                    )
                )
        if stored.consumed_manuscript != current.consumed_manuscript:
            issues.append(
                RenderedProvenanceIssue(
                    "CONSUMPTION_DRIFT",
                    "manuscript consumption no longer matches the validated rendered snapshot",
                )
            )
        if not issues:
            issues.append(RenderedProvenanceIssue("RECEIPT_DRIFT", "rendered receipt differs from current evidence"))
    clean_index = _clean_index_issues(root, project_root)
    if clean_index:
        issues.append(
            RenderedProvenanceIssue(
                "CLEAN_INDEX_INCOMPLETE",
                "; ".join(clean_index[:10])
                + (f"; ... and {len(clean_index) - 10} more" if len(clean_index) > 10 else ""),
            )
        )
    return RenderedProvenanceValidation(tuple(issues))


__all__ = [
    "EVIDENCE_MODE",
    "RECEIPT_RELATIVE_PATH",
    "RenderedProvenanceError",
    "RenderedProvenanceIssue",
    "RenderedProvenanceReceipt",
    "RenderedProvenanceValidation",
    "build_rendered_provenance_receipt",
    "rendered_manuscript_paths",
    "validate_rendered_provenance",
    "write_rendered_provenance_receipt",
]
