"""Coverage JSON export, heatmap PNG, and manuscript page orchestration."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import emit_coverage_artifacts
from manuscript.sheaf.report import write_coverage_page


def run_coverage_figures_and_page(
    project_root: Path,
    *,
    heatmap_path: Path | None = None,
    write_page: bool = True,
) -> tuple[Path | None, Path | None]:
    """Render heatmap PNG and coverage page from existing coverage JSON."""
    root = project_root.resolve()
    from visualizations.figures_sheaf import figure_sheaf_coverage_heatmap

    png_out = figure_sheaf_coverage_heatmap(
        root,
        output_path=heatmap_path or root / "output" / "figures" / "sheaf_coverage_heatmap.png",
    )
    page_out = write_coverage_page(root) if write_page else None
    return png_out, page_out


def run_coverage_pipeline(
    project_root: Path,
    *,
    json_path: Path | None = None,
    heatmap_path: Path | None = None,
    write_page: bool = True,
) -> tuple[Path, Path | None, Path | None]:
    """Write coverage JSON, heatmap PNG, and coverage manuscript page."""
    root = project_root.resolve()
    json_out = emit_coverage_artifacts(root, json_path=json_path)
    png_out, page_out = run_coverage_figures_and_page(
        root,
        heatmap_path=heatmap_path,
        write_page=write_page,
    )
    return json_out, png_out, page_out
