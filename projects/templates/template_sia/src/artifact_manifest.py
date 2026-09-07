"""Artifact manifest writer for SIA loop outputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _artifact_timestamp() -> str:
    """Return a reproducible timestamp or an explicit unavailable marker."""
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if raw.isdigit():
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat(timespec="seconds")
    return "not-recorded (set SOURCE_DATE_EPOCH)"


@dataclass(frozen=True)
class ArtifactManifestEntry:
    """Data container for ArtifactManifestEntry."""

    path: str
    size_bytes: int
    sha256: str
    stage_num: int
    stage_name: str
    contract_match: bool
    timestamp: str = field(default_factory=_artifact_timestamp)


@dataclass(frozen=True)
class ArtifactManifest:
    """Data container for ArtifactManifest."""

    entries: tuple[ArtifactManifestEntry, ...]
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "entries": [asdict(entry) for entry in self.entries],
            "issues": list(self.issues),
        }


def validate_artifact_manifest(payload: dict[str, object]) -> tuple[str, ...]:
    """Return path, digest, and duplicate-entry findings for a manifest."""
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        return ("entries must be a list",)
    issues: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            issues.append(f"entry {index} must be an object")
            continue
        path = str(raw.get("path", ""))
        if not path or Path(path).is_absolute() or ".." in Path(path).parts:
            issues.append(f"entry {index} has an unsafe path")
        if path in seen:
            issues.append(f"entry {index} duplicates path {path}")
        seen.add(path)
        digest = str(raw.get("sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            issues.append(f"entry {index} has an invalid sha256")
        if not isinstance(raw.get("size_bytes"), int) or int(raw["size_bytes"]) < 0:
            issues.append(f"entry {index} has an invalid size_bytes")
    return tuple(issues)


def compute_sha256(path: Path) -> str:
    """Process compute sha256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def write_artifact_manifest(project_root: Path, paths: list[Path]) -> Path:
    """Write output/reports/artifact_manifest.json for declared loop artifacts."""
    project_root = project_root.resolve()
    manifest_path = project_root / "output" / "reports" / "artifact_manifest.json"
    entries: list[ArtifactManifestEntry] = []
    seen: set[Path] = set()
    for index, raw_path in enumerate(paths, start=1):
        path = raw_path.resolve()
        if not path.is_file() or path in seen or path == manifest_path.resolve():
            continue
        seen.add(path)
        entries.append(
            ArtifactManifestEntry(
                path=_relative_path(project_root, path),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=index,
                stage_name="SIA loop",
                contract_match=True,
            )
        )
    ordered = tuple(sorted(entries, key=lambda item: item.path))
    manifest_payload: dict[str, object] = {"entries": [asdict(entry) for entry in ordered]}
    manifest = ArtifactManifest(entries=ordered, issues=validate_artifact_manifest(manifest_payload))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    return manifest_path


def collect_run_artifact_paths(project_root: Path, *, run_id: int) -> list[Path]:
    """Collect canonical SIA run artifact paths for manifest registration."""
    project_root = project_root.resolve()
    run_root = project_root / "output" / "runs" / f"run_{run_id}"
    paths: list[Path] = [
        project_root / "output" / "reports" / "sia_loop_report.md",
        project_root / "output" / "data" / "manuscript_variables.json",
        run_root / "run_summary.json",
        run_root / "context.md",
    ]
    if run_root.is_dir():
        for gen_dir in sorted(run_root.glob("gen_*")):
            for name in (
                "target_agent.py",
                "agent_execution.json",
                "improvement.md",
                "results.json",
            ):
                candidate = gen_dir / name
                if candidate.is_file():
                    paths.append(candidate)
    figures_dir = project_root / "output" / "figures"
    if figures_dir.is_dir():
        paths.extend(sorted(figures_dir.glob("*.png")))
    return paths


__all__ = [
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "collect_run_artifact_paths",
    "compute_sha256",
    "validate_artifact_manifest",
    "write_artifact_manifest",
]
