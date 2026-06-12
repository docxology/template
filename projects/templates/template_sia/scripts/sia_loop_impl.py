"""SIA harness orchestration — infrastructure imports confined to scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.sia import GenerationArtifacts, RunConfig, run_sia_loop

from src.artifact_manifest import collect_run_artifact_paths, write_artifact_manifest
from src.figures import write_all_figures
from src.loop_config import load_sia_settings
from src.manuscript_variables import save_variables
from src.reports import write_loop_report


@dataclass(frozen=True)
class SiaLoopResult:
    """Result of a completed SIA loop."""

    artifacts: tuple[GenerationArtifacts, ...]
    run_summary: Path
    report_path: Path
    manifest_path: Path
    figure_paths: tuple[Path, ...]


def fixtures_dir(project_root: Path) -> Path:
    """Return recorded generation fixtures."""
    return project_root / "src" / "fixtures" / "recorded_generations"


def build_run_config(project_root: Path, *, live: bool | None = None) -> RunConfig:
    """Build infrastructure RunConfig from project settings."""
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
    """Run the SIA harness for this exemplar."""
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
