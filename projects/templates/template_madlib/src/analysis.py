from __future__ import annotations

from pathlib import Path

from .analysis_figures import _figure_registry_entry, write_cover_overview_figure, write_token_density_figure
from .analysis_reports import _write_json
from .artifact_writers import write_core_artifacts
from .figure_specs import CONDITIONAL_FIGURE_SPECS, write_conditional_figures
from .run import build_run


def generate_artifacts(project_root: Path | str) -> dict[str, Path]:
    run = build_run(project_root)
    config = run.config
    plan = run.plan

    data_dir = run.project_root / "output" / "data"
    reports_dir = run.project_root / "output" / "reports"
    figures_dir = run.project_root / "output" / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    cover_overview = figures_dir / "madlib_cover_overview.png"
    figure = figures_dir / "token_density.png"
    figure_registry = figures_dir / "figure_registry.json"

    artifact_paths = write_core_artifacts(run)

    write_cover_overview_figure(config, plan, run.field_counts, cover_overview)
    write_token_density_figure(plan, figure)
    registry = {
        "fig:madlib-cover-overview": _figure_registry_entry(
            cover_overview.name,
            "Configuration-to-manuscript audit overview for the Madlib exemplar",
            "fig:madlib-cover-overview",
            "Cover",
        ),
        "fig:token-density": _figure_registry_entry(
            figure.name,
            "Token choices by lexicon category",
            "fig:token-density",
            "Results",
        ),
    }
    conditional_registry = write_conditional_figures(
        run,
        {spec.artifact_key: figures_dir / spec.filename for spec in CONDITIONAL_FIGURE_SPECS},
    )
    registry.update(conditional_registry)
    _write_json(figure_registry, registry)

    conditional_paths = {spec.artifact_key: figures_dir / spec.filename for spec in CONDITIONAL_FIGURE_SPECS}
    return {
        **artifact_paths,
        "cover_overview": cover_overview,
        "figure": figure,
        "figure_registry": figure_registry,
        **conditional_paths,
    }


__all__ = ["generate_artifacts"]
