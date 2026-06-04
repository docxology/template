"""Figure render context and loop-bound visual artifact writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from src.diagnostics import diagnostic_bundle
from src.figures.figure_quality import write_figure_quality_report
from src.figures.figure_registry import figure_registry_payload
from src.figures.figure_style import apply_style, load_figure_style
from src.ml.task import MLTaskResult
from src.models import AutoResearchLoopResult

from .figure_dispatch import FigureRenderContext, render_all_figures, render_figure_batch
from .io import write_json


def build_figure_render_context(
    project_root: Path,
    ml_result: MLTaskResult,
    *,
    loop_result: AutoResearchLoopResult | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> FigureRenderContext:
    """Build figure render context, computing diagnostics at most once per ML result."""
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    resolved = diagnostics if diagnostics is not None else diagnostic_bundle(project_root, ml_result)
    return FigureRenderContext(
        project_root=project_root,
        figures_dir=figures_dir,
        loop_result=loop_result,
        ml_result=ml_result,
        diagnostics=resolved,
    )


def write_loop_bound_figures(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
    """Render loop-state figures that depend on claims and readiness payloads."""
    figure_ctx = build_figure_render_context(project_root, ml_result, loop_result=result, diagnostics=diagnostics)
    style = load_figure_style(project_root)
    with apply_style(style):
        return cast(list[Path], render_figure_batch(figure_ctx, include_loop_only=True))


def write_final_visual_artifacts(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
    """Refresh all figures, registry metadata, and figure-quality validation."""
    data_dir = project_root / "output" / "data"
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    resolved = diagnostics if diagnostics is not None else diagnostic_bundle(project_root, ml_result)
    registry_payload = figure_registry_payload(result, ml_result)
    figure_ctx = build_figure_render_context(project_root, ml_result, loop_result=result, diagnostics=resolved)
    style = load_figure_style(project_root)
    with apply_style(style):
        return [
            write_json(
                data_dir / "figure_style.json",
                {"generated_at": result.generated_at, **style.to_dict()},
            ),
            *render_all_figures(
                figure_ctx,
                include_security=result.config.security_profile.enabled,
            ),
            write_json(figures_dir / "figure_registry.json", registry_payload),
            write_figure_quality_report(
                data_dir / "figure_quality_report.json",
                project_root,
                registry_payload,
                generated_at=result.generated_at,
                require_all_registered=True,
            ),
        ]
