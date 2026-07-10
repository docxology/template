"""Artifact manifests for advisory pipeline reproducibility controls."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.pipeline.types import StageContract

_IGNORED_OUTPUT_PARTS = frozenset(
    {".checkpoints", ".pipeline", "logs", "hitl", "snapshots", "__pycache__", "llm", "translations"}
)
_IGNORED_OUTPUT_FILENAMES = frozenset(
    {
        "artifact_manifest.json",
        "evidence_registry.json",
        "snapshot_compare.json",
        "snapshot_compare.md",
    }
)
_IGNORED_OUTPUT_SUFFIXES = frozenset({".aux", ".log", ".nav", ".snm", ".toc", ".vrb"})


@dataclass(frozen=True)
class ArtifactManifestEntry:
    """One generated artifact recorded with deterministic provenance."""

    path: str
    size_bytes: int
    sha256: str
    stage_num: int
    stage_name: str
    contract_match: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass(frozen=True)
class ArtifactManifest:
    """Stage or aggregate artifact manifest."""

    entries: tuple[ArtifactManifestEntry, ...]
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "entries": [asdict(entry) for entry in self.entries],
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class ArtifactValidationReport:
    """Validation result for an artifact manifest."""

    issues: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return True if the artifact is valid."""
        return not self.issues


def compute_sha256(path: Path) -> str:
    """Compute a SHA256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_stage_artifact_manifest(
    *,
    repo_root: Path,
    project_dir: Path,
    stage_num: int,
    stage_name: str,
    contract: StageContract,
) -> ArtifactManifest:
    """Write a stage-specific artifact manifest and return it."""
    output_dir = project_dir / "output"
    declared_paths = _declared_output_paths(repo_root, project_dir, contract)
    entries: list[ArtifactManifestEntry] = []
    issues: list[str] = []

    for declared in declared_paths:
        if not declared.exists():
            issues.append(f"missing declared output: {_display_path(repo_root, declared)}")

    if output_dir.exists():
        for path in sorted(output_dir.rglob("*")):
            if not path.is_file() or _is_ignored_output(path, output_dir):
                continue
            relative_path = str(path.relative_to(project_dir))
            digest = compute_sha256(path)
            contract_match = not declared_paths or any(_is_relative_to(path, declared) for declared in declared_paths)
            entries.append(
                ArtifactManifestEntry(
                    path=relative_path,
                    size_bytes=path.stat().st_size,
                    sha256=digest,
                    stage_num=stage_num,
                    stage_name=stage_name,
                    contract_match=contract_match,
                )
            )

    manifest = ArtifactManifest(entries=tuple(entries), issues=tuple(issues))
    manifest_path = _stage_manifest_path(output_dir, stage_num, stage_name)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def aggregate_artifact_manifests(output_dir: Path) -> ArtifactManifest:
    """Aggregate all stage manifests into ``output/reports/artifact_manifest.json``."""
    stage_dir = output_dir / ".pipeline" / "artifacts"
    project_dir = output_dir.parent
    entries: list[ArtifactManifestEntry] = []
    issues: list[str] = []
    if stage_dir.exists():
        for manifest_path in sorted(stage_dir.glob("stage-*.json")):
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(f"cannot read stage artifact manifest: {manifest_path.name}: {exc}")
                continue
            entries.extend(_entries_from_payload(payload))
            issues.extend(str(issue) for issue in payload.get("issues", []))

    if not entries and output_dir.exists():
        for path in sorted(output_dir.rglob("*")):
            if not path.is_file() or _is_ignored_output(path, output_dir):
                continue
            entries.append(
                ArtifactManifestEntry(
                    path=str(path.relative_to(project_dir)),
                    size_bytes=path.stat().st_size,
                    sha256=compute_sha256(path),
                    stage_num=0,
                    stage_name="standalone-output-scan",
                    contract_match=True,
                )
            )

    aggregate = ArtifactManifest(entries=tuple(entries), issues=tuple(issues))
    report_path = output_dir / "reports" / "artifact_manifest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(aggregate.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return aggregate


def validate_artifact_manifest(
    manifest: ArtifactManifest, *, project_dir: Path | None = None
) -> ArtifactValidationReport:
    """Validate manifest issues and optionally verify current file hashes."""
    issues = list(manifest.issues)
    if project_dir is not None:
        latest_entries = {entry.path: entry for entry in manifest.entries}
        for entry in latest_entries.values():
            path = project_dir / entry.path
            if not path.exists():
                issues.append(f"missing artifact: {entry.path}")
                continue
            if compute_sha256(path) != entry.sha256:
                issues.append(f"changed artifact: {entry.path}")
            if not entry.contract_match:
                issues.append(f"undeclared artifact: {entry.path}")
    return ArtifactValidationReport(issues=tuple(issues))


def _entries_from_payload(payload: dict[str, object]) -> list[ArtifactManifestEntry]:
    entries: list[ArtifactManifestEntry] = []
    for row in payload.get("entries", []):
        if isinstance(row, dict):
            entries.append(
                ArtifactManifestEntry(
                    path=str(row.get("path", "")),
                    size_bytes=int(row.get("size_bytes", 0) or 0),
                    sha256=str(row.get("sha256", "")),
                    stage_num=int(row.get("stage_num", 0) or 0),
                    stage_name=str(row.get("stage_name", "")),
                    contract_match=bool(row.get("contract_match", False)),
                    timestamp=str(row.get("timestamp", "")),
                )
            )
    return entries


def _declared_output_paths(repo_root: Path, project_dir: Path, contract: StageContract) -> tuple[Path, ...]:
    paths: list[Path] = []
    project_slug = _project_slug(repo_root, project_dir)
    for raw in contract.output_artifacts:
        rendered = raw.replace("{project}", project_slug).rstrip("/")
        if rendered.startswith("projects/"):
            paths.append(repo_root / rendered)
        elif rendered == f"output/{project_slug}" or rendered.startswith(f"output/{project_slug}/"):
            paths.append(repo_root / rendered)
        elif rendered.startswith("output/"):
            paths.append(project_dir / rendered)
        else:
            paths.append(project_dir / rendered)
    return tuple(paths)


def _project_slug(repo_root: Path, project_dir: Path) -> str:
    projects_root = repo_root / "projects"
    for candidate in (project_dir, project_dir.absolute()):
        try:
            return candidate.relative_to(projects_root).as_posix()
        except ValueError:
            continue
    try:
        return project_dir.resolve().relative_to(projects_root.resolve()).as_posix()
    except ValueError:
        pass
    resolved_project = project_dir.resolve()
    for candidate in _project_slug_candidates(projects_root):
        try:
            if candidate.resolve() == resolved_project:
                return candidate.relative_to(projects_root).as_posix()
        except OSError:
            continue
    return project_dir.name


def _project_slug_candidates(projects_root: Path) -> tuple[Path, ...]:
    if not projects_root.exists():
        return ()
    candidates: list[Path] = []
    for child in projects_root.iterdir():
        if child.name.startswith("."):
            continue
        candidates.append(child)
        if child.is_dir() or child.is_symlink():
            try:
                candidates.extend(grandchild for grandchild in child.iterdir() if not grandchild.name.startswith("."))
            except OSError:
                continue
    return tuple(sorted(candidates, key=lambda path: path.as_posix()))


def _stage_manifest_path(output_dir: Path, stage_num: int, stage_name: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in stage_name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return output_dir / ".pipeline" / "artifacts" / f"stage-{stage_num:02d}-{slug}.json"


def _is_ignored_output(path: Path, output_dir: Path) -> bool:
    rel_parts = path.relative_to(output_dir).parts
    return (
        any(part in _IGNORED_OUTPUT_PARTS for part in rel_parts)
        or path.name in _IGNORED_OUTPUT_FILENAMES
        or path.suffix in _IGNORED_OUTPUT_SUFFIXES
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        pass
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _display_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)
