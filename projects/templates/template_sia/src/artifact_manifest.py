"""Artifact manifest writer for SIA loop outputs."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256


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
    manifest = ArtifactManifest(entries=tuple(sorted(entries, key=lambda item: item.path)), issues=())
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


__all__ = ["collect_run_artifact_paths", "write_artifact_manifest"]
