"""Project adapter for running the shared SIA harness.

Layer 1 owns the generation state machine in :mod:`infrastructure.sia`.
This module owns the template-specific configuration, fixture location, and
post-run artifact orchestration. CLI parsing and presentation stay in
``scripts/run_sia_loop.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.sia import GenerationArtifacts, RunConfig, run_sia_loop

from .artifact_manifest import collect_run_artifact_paths, write_artifact_manifest
from .figures import write_all_figures
from .loop_config import load_sia_settings
from .manuscript_variables import save_variables
from .reports import write_loop_report


@dataclass(frozen=True)
class SiaLoopResult:
    """Result of a completed project-level SIA loop."""

    artifacts: tuple[GenerationArtifacts, ...]
    run_summary: Path
    report_path: Path
    manifest_path: Path
    figure_paths: tuple[Path, ...]


def fixtures_dir(project_root: Path) -> Path:
    """Return the directory containing recorded generation fixtures."""
    return project_root / "src" / "fixtures" / "recorded_generations"


def build_run_config(project_root: Path, *, live: bool | None = None) -> RunConfig:
    """Build the shared harness configuration from project-owned settings."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    effective_live = settings.live if live is None else live
    return RunConfig(
        task_dir=project_root / settings.task_dir,
        output_dir=project_root / "output",
        run_id=settings.run_id,
        max_generations=settings.max_generations,
        live=effective_live,
        fixtures_dir=None if effective_live else fixtures_dir(project_root),
        target_timeout_sec=settings.target_timeout_sec,
        llm_model=settings.llm_model,
    )


def run_sia_loop_project(project_root: Path, *, live: bool | None = None) -> SiaLoopResult:
    """Run the shared harness and write this exemplar's derived artifacts."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    config = build_run_config(project_root, live=live)
    artifacts = tuple(run_sia_loop(config))
    report_path = write_loop_report(project_root)
    save_variables(project_root)
    figure_paths = tuple(write_all_figures(project_root))
    summary_path = project_root / "output" / "runs" / f"run_{config.run_id}" / "run_summary.json"
    manifest_paths = collect_run_artifact_paths(project_root, run_id=settings.run_id)
    manifest_path = write_artifact_manifest(project_root, manifest_paths)
    return SiaLoopResult(
        artifacts=artifacts,
        run_summary=summary_path,
        report_path=report_path,
        manifest_path=manifest_path,
        figure_paths=figure_paths,
    )


__all__ = [
    "SiaLoopResult",
    "build_run_config",
    "fixtures_dir",
    "run_sia_loop_project",
]
