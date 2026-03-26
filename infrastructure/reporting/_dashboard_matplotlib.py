"""Dashboard orchestrator for executive reporting visualizations.

This module is the single entry point for generating all dashboard formats.
Chart generators, specialized visualizations, and CSV exports are delegated
to extracted submodules:

  - ``_dashboard_charts``       — base chart functions + multi-panel dashboard
  - ``_dashboard_specialized``  — health radar, pipeline efficiency, codebase complexity, etc.
  - ``_dashboard_csv``          — CSV export: project breakdowns, comparative analysis, recommendations

The Plotly interactive dashboard generator lives in this module because it
has no other downstream consumers and is small enough not to warrant a file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.manuscript_overview import generate_all_manuscript_overviews

# ── Re-exports from extracted modules ────────────────────────────────────────
# Callers that previously imported from this module will continue to work.
from infrastructure.reporting._dashboard_charts import (  # noqa: F401
    COLORS,
    create_coverage_chart,
    create_manuscript_complexity_chart,
    create_manuscript_size_chart,
    create_output_distribution_chart,
    create_performance_timeline_chart,
    create_pipeline_duration_chart,
    create_summary_table,
    create_test_count_chart,
    generate_matplotlib_dashboard,
)
from infrastructure.reporting._dashboard_specialized import (  # noqa: F401
    generate_codebase_comparison_chart,
    generate_codebase_complexity_chart,
    generate_health_comparison_chart,
    generate_health_radar_chart,
    generate_output_comparison_chart,
    generate_output_distribution_charts,
    generate_pipeline_bottlenecks_chart,
    generate_pipeline_efficiency_chart,
    generate_project_breakdowns,
)
from infrastructure.reporting._dashboard_csv import (  # noqa: F401
    generate_comparative_analysis_csv,
    generate_csv_data_tables,
    generate_detailed_project_breakdown_csv,
    generate_prioritized_recommendations_csv,
)

logger = get_logger(__name__)


# ── Plotly dashboard (kept inline — no need for a separate file) ─────────────
def generate_plotly_dashboard(summary: ExecutiveSummary, output_dir: Path) -> Path | None:
    """Generate interactive HTML dashboard using plotly; returns None if plotly not installed."""
    try:
        import plotly.graph_objects as go  # noqa: F401
        from plotly.subplots import make_subplots
    except ImportError:
        logger.warning("Plotly not installed, skipping interactive dashboard generation")
        return None

    from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

    projects = summary.project_metrics
    project_names = [p.name for p in projects]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Test Coverage",
            "Pipeline Duration",
            "Manuscript Size",
            "Output Distribution",
        ),
    )

    # Test Coverage
    coverages = [p.tests.coverage_percent for p in projects]
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=coverages,
            name="Coverage %",
            marker_color="#2E86AB",
        ),
        row=1,
        col=1,
    )

    # Pipeline Duration
    durations = [p.pipeline.total_duration for p in projects]
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=durations,
            name="Duration (s)",
            marker_color="#F77F00",
        ),
        row=1,
        col=2,
    )

    # Manuscript Size
    words = [p.manuscript.total_words for p in projects]
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=words,
            name="Word Count",
            marker_color="#06A77D",
        ),
        row=2,
        col=1,
    )

    # Output Distribution
    outputs = summary.aggregate_metrics.get("outputs", {})
    output_labels = ["PDFs", "Figures", "Slides", "Web"]
    output_values = [
        outputs.get("total_pdfs", 0),
        outputs.get("total_figures", 0),
        outputs.get("total_slides", 0),
        outputs.get("total_web", 0),
    ]
    filtered = [(lbl, val) for lbl, val in zip(output_labels, output_values) if val > 0]
    if filtered:
        labels, values = zip(*filtered)
        fig.add_trace(
            go.Pie(labels=list(labels), values=list(values), hole=0.3),
            row=2,
            col=2,
        )

    fig.update_layout(
        title_text="Executive Dashboard",
        showlegend=True,
        height=800,
        template="plotly_white",
    )

    organizer = OutputOrganizer()
    html_path = organizer.get_output_path("dashboard.html", output_dir, FileType.REPORT)
    fig.write_html(str(html_path))
    logger.info(f"Generated interactive dashboard: {html_path}")

    return html_path


# ── Master orchestrator ──────────────────────────────────────────────────────
def generate_all_dashboards(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Any]:
    """Generate all dashboard formats including CSV data exports.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of generated file paths. On partial failure the key
        ``"_errors"`` maps to a list of ``(generator_name, error_message)``
        tuples so callers can distinguish partial failure from full success.
    """
    logger.info("Generating all dashboard formats...")

    all_files: dict[str, Any] = {}
    failures: list[str] = []

    def _try(generator_name: str, fn: Any) -> None:
        try:
            result = fn()
            if isinstance(result, dict):
                all_files.update(result)
            elif result is not None:
                all_files[generator_name] = result
        except Exception as e:  # noqa: BLE001 — generator dispatch may raise any exception type
            logger.warning(f"Could not generate {generator_name}: {e}")
            failures.append(f"{generator_name}: {e}")

    # Generate matplotlib dashboards (PNG + PDF)
    matplotlib_files = generate_matplotlib_dashboard(summary, output_dir)
    all_files.update(matplotlib_files)

    # Generate health score visualizations
    _try("health_radar_chart", lambda: generate_health_radar_chart(summary, output_dir))
    _try("health_comparison_chart", lambda: generate_health_comparison_chart(summary, output_dir))

    # Generate individual project dashboards
    _try("project_breakdowns", lambda: generate_project_breakdowns(summary, output_dir))

    # Generate pipeline efficiency visualizations
    _try(
        "pipeline_efficiency_chart", lambda: generate_pipeline_efficiency_chart(summary, output_dir)
    )
    _try(
        "pipeline_bottlenecks_chart",
        lambda: generate_pipeline_bottlenecks_chart(summary, output_dir),
    )

    # Generate output analysis visualizations
    _try(
        "output_distribution_charts",
        lambda: generate_output_distribution_charts(summary, output_dir),
    )
    _try("output_comparison_chart", lambda: generate_output_comparison_chart(summary, output_dir))

    # Generate codebase analysis visualizations
    _try(
        "codebase_complexity_chart", lambda: generate_codebase_complexity_chart(summary, output_dir)
    )
    _try(
        "codebase_comparison_chart", lambda: generate_codebase_comparison_chart(summary, output_dir)
    )

    # Generate plotly dashboard (HTML)
    _try("html", lambda: generate_plotly_dashboard(summary, output_dir))

    # Generate CSV data tables
    def _generate_csvs() -> dict[str, Any]:
        result: dict[str, Any] = {}
        result.update(generate_csv_data_tables(summary, output_dir))
        result["detailed_breakdown_csv"] = generate_detailed_project_breakdown_csv(
            summary, output_dir
        )
        result["comparative_analysis_csv"] = generate_comparative_analysis_csv(summary, output_dir)
        result["recommendations_csv"] = generate_prioritized_recommendations_csv(
            summary, output_dir
        )
        return result

    _try("csv_data_tables", _generate_csvs)

    # Generate manuscript overviews for each project
    _try(
        "manuscript_overviews",
        lambda: generate_all_manuscript_overviews(summary, output_dir, Path(".")),
    )

    if failures:
        all_files["_errors"] = failures
        logger.warning(f"Dashboard generation completed with {len(failures)} partial failure(s)")
    logger.info(f"Generated {len(all_files)} dashboard and data file(s)")
    return all_files
