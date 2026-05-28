"""Configurable coverage report and heatmap settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import CoverageMatrix, ImradBlock, SheafManifest


@dataclass(frozen=True)
class HeatmapConfig:
    indent_prefix: str = "  "
    group_separator: bool = True
    row_height: float = 0.42
    dpi: int = 160
    show_row_coverage_pct: bool = True


@dataclass(frozen=True)
class CoverageColorConfig:
    present: str = "#111827"
    absent: str = "#ffffff"
    missing: str = "#94a3b8"


@dataclass(frozen=True)
class ReportConfig:
    title: str = "Sheaf Track Coverage"
    show_imrad_headers: bool = True
    show_summary_stats: bool = True
    show_track_legend: bool = True
    heatmap_figure_path: str = "../output/figures/sheaf_coverage_heatmap.png"


@dataclass(frozen=True)
class CoverageConfig:
    report: ReportConfig = field(default_factory=ReportConfig)
    heatmap: HeatmapConfig = field(default_factory=HeatmapConfig)
    colors: CoverageColorConfig = field(default_factory=CoverageColorConfig)


@dataclass(frozen=True)
class CoverageReport:
    matrix: CoverageMatrix
    manifest: SheafManifest
    config: CoverageConfig
    total_bound: int
    total_present: int
    total_missing: int
    row_stats: tuple[tuple[str, int, int, int], ...]


def load_coverage_config(path: Path, *, project_root: Path | None = None) -> CoverageConfig:
    if not path.is_file():
        base = CoverageConfig()
    else:
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        report_raw = raw.get("report") or {}
        heatmap_raw = raw.get("heatmap") or {}
        colors_raw = raw.get("colors") or {}
        base = CoverageConfig(
            report=ReportConfig(
                title=str(report_raw.get("title", "Sheaf Track Coverage")),
                show_imrad_headers=bool(report_raw.get("show_imrad_headers", True)),
                show_summary_stats=bool(report_raw.get("show_summary_stats", True)),
                show_track_legend=bool(report_raw.get("show_track_legend", True)),
                heatmap_figure_path=str(
                    report_raw.get("heatmap_figure_path", "../output/figures/sheaf_coverage_heatmap.png")
                ),
            ),
            heatmap=HeatmapConfig(
                indent_prefix=str(heatmap_raw.get("indent_prefix", "  ")),
                group_separator=bool(heatmap_raw.get("group_separator", True)),
                row_height=float(heatmap_raw.get("row_height", 0.42)),
                dpi=int(heatmap_raw.get("dpi", 160)),
                show_row_coverage_pct=bool(heatmap_raw.get("show_row_coverage_pct", True)),
            ),
            colors=CoverageColorConfig(
                present=str(colors_raw.get("present", "#111827")),
                absent=str(colors_raw.get("absent", "#ffffff")),
                missing=str(colors_raw.get("missing", "#94a3b8")),
            ),
        )
    if project_root is None:
        return base
    from visualizations.figure_style import load_figure_style

    style = load_figure_style(project_root)
    return CoverageConfig(
        report=base.report,
        heatmap=base.heatmap,
        colors=CoverageColorConfig(
            present=style.color("primary"),
            absent=base.colors.absent,
            missing=style.color("muted"),
        ),
    )


def default_coverage_config_path(project_root: Path) -> Path:
    return project_root.resolve() / "manuscript" / "sheaf" / "coverage.yaml"


def build_coverage_report(
    matrix: CoverageMatrix,
    manifest: SheafManifest,
    config: CoverageConfig,
) -> CoverageReport:
    total_bound = total_present = total_missing = 0
    row_stats: list[tuple[str, int, int, int]] = []
    for row in matrix.sections:
        bound = present = missing = 0
        for cell in row.cells:
            if cell.bound:
                bound += 1
                if cell.color == "black":
                    present += 1
                elif cell.color == "gray":
                    missing += 1
        total_bound += bound
        total_present += present
        total_missing += missing
        row_stats.append((row.section_id, bound, present, missing))
    return CoverageReport(
        matrix=matrix,
        manifest=manifest,
        config=config,
        total_bound=total_bound,
        total_present=total_present,
        total_missing=total_missing,
        row_stats=tuple(row_stats),
    )


def _imrad_heading(imrad: ImradBlock) -> str:
    return imrad.replace("_", " ").title()


def render_report_markdown(report: CoverageReport, *, project_root: Path) -> str:
    cfg = report.config.report
    lines = [f"# {cfg.title} {{#sec:sheaf_coverage}}", ""]
    lines.append(
        "This page summarizes which **sheaf fragment tracks** are bound for each IMRAD "
        "row in `manuscript/sheaf/manifest.yaml`. The matrix is regenerated at compose time."
    )
    lines.append("")
    if cfg.show_summary_stats:
        lines.append(
            "**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing (gray)."
        )
        lines.append("")
    if cfg.show_track_legend:
        lines.append("| Color | Meaning |")
        lines.append("| --- | --- |")
        lines.append("| Black | Track **present** (bound and fragment exists) |")
        lines.append("| White | **Absent** (not bound for this row) |")
        lines.append("| Gray | **Missing** (bound but fragment file absent) |")
        lines.append("")
    if cfg.show_imrad_headers:
        current_imrad: ImradBlock | None = None
        for section in report.manifest.sections:
            if section.imrad != current_imrad:
                current_imrad = section.imrad
                lines.append(f"## {_imrad_heading(section.imrad)}")
                lines.append("")
            indent = "  " * section.depth if section.depth else ""
            kind_label = " *(group)*" if section.kind == "group" else ""
            lines.append(f"- {indent}**{section.title}**{kind_label}")
        lines.append("")
    from visualizations.figure_registry import render_section_figures

    figure_md = render_section_figures(project_root, "coverage_page")
    if not figure_md.strip():
        raise ValueError("figures.yaml must declare section_figures.coverage_page for the sheaf coverage page")
    lines.append(figure_md)
    lines.append("")
    appendix = next(
        (section for section in report.manifest.sections if section.id == "appendix_full_sheaf"),
        None,
    )
    appendix_name = appendix.output_name if appendix else "appendix_full_sheaf.md"
    lines.append(
        f"Appendix row `{appendix_name}` binds {{{{appendix_sheaf_track_count}}}} fragment "
        "track types as a composability proof (registry defines "
        "{{sheaf_track_count}} types; optional `layers` is methods-only)."
    )
    lines.append("")
    return "\n".join(lines)


def write_coverage_page(project_root: Path) -> Path:
    from manuscript.sheaf.coverage import load_sheaf_coverage_context

    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    config = load_coverage_config(default_coverage_config_path(root), project_root=root)
    report = build_coverage_report(ctx.matrix, ctx.manifest, config)
    out = root / "manuscript" / "00_00_sheaf_coverage.md"
    out.write_text(render_report_markdown(report, project_root=root), encoding="utf-8")
    return out
