"""Coverage JSON export, heatmap PNG, and manuscript page orchestration."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.coverage import emit_coverage_artifacts
from manuscript.sheaf.report import write_coverage_page


def _coverage_input_paths(project_root: Path) -> list[Path]:
    root = project_root.resolve()
    return [
        p
        for p in (
            root / "manuscript" / "sheaf" / "manifest.yaml",
            root / "manuscript" / "sheaf" / "tracks.yaml",
        )
        if p.is_file()
    ]


def _is_stale(artifact: Path, inputs: list[Path]) -> bool:
    if not artifact.is_file():
        return True
    artifact_mtime = artifact.stat().st_mtime
    return any(inp.stat().st_mtime > artifact_mtime for inp in inputs if inp.is_file())


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


def ensure_coverage_artifacts(
    project_root: Path,
    *,
    json_path: Path | None = None,
    heatmap_path: Path | None = None,
    write_page: bool = True,
    json_only: bool = False,
    render_heatmap: bool = False,
    force: bool = False,
) -> tuple[Path, Path | None, Path | None]:
    """Ensure coverage JSON exists; optionally render heatmap and coverage page."""
    root = project_root.resolve()
    json_out = (json_path or root / "output" / "data" / "sheaf_coverage_matrix.json").resolve()
    png_out_path = (heatmap_path or root / "output" / "figures" / "sheaf_coverage_heatmap.png").resolve()
    inputs = _coverage_input_paths(root)

    if force or _is_stale(json_out, inputs):
        json_out = emit_coverage_artifacts(root, json_path=json_out)

    if json_only:
        return json_out, None, None

    png_out: Path | None = None
    if render_heatmap and (force or _is_stale(png_out_path, [json_out])):
        png_out, _ = run_coverage_figures_and_page(
            root,
            heatmap_path=png_out_path,
            write_page=False,
        )
    elif render_heatmap and png_out_path.is_file():
        png_out = png_out_path

    page_path = root / "manuscript" / "00_00_sheaf_coverage.md"
    page_out: Path | None = None
    if write_page and (force or _is_stale(page_path, [json_out])):
        page_out = write_coverage_page(root)
    elif write_page and page_path.is_file():
        page_out = page_path

    return json_out, png_out, page_out


def run_coverage_pipeline(
    project_root: Path,
    *,
    json_path: Path | None = None,
    heatmap_path: Path | None = None,
    write_page: bool = True,
) -> tuple[Path, Path | None, Path | None]:
    """Write coverage JSON, heatmap PNG, and coverage manuscript page."""
    return ensure_coverage_artifacts(
        project_root,
        json_path=json_path,
        heatmap_path=heatmap_path,
        write_page=write_page,
        render_heatmap=True,
        force=True,
    )
