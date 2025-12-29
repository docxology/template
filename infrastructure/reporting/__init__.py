"""Pipeline reporting module for generating consolidated reports.

This module provides utilities for generating comprehensive reports from
pipeline execution, including test results, validation results, performance
metrics, and error summaries.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

from infrastructure.reporting.pipeline_reporter import (
    generate_pipeline_report,
    generate_test_report,
    generate_validation_report,
    generate_performance_report,
    generate_error_summary,
    save_pipeline_report,
)
from infrastructure.reporting.test_reporter import (
    parse_pytest_output,
    generate_test_report as generate_test_report_from_results,
    save_test_report,
)
from infrastructure.reporting.error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from infrastructure.reporting.output_reporter import (
    generate_output_summary,
    collect_output_statistics,
)
from infrastructure.reporting.executive_reporter import (
    generate_executive_summary,
    save_executive_summary,
    collect_project_metrics,
    ProjectMetrics,
    ExecutiveSummary,
)
from infrastructure.reporting.dashboard_generator import (
    generate_all_dashboards,
    generate_matplotlib_dashboard,
    generate_plotly_dashboard,
)

def generate_multi_project_report(repo_root: Path, project_names: List[str], output_dir: Path) -> Dict[str, Path]:
    """Orchestrate complete multi-project reporting workflow.

    This is a convenience function that runs the full executive reporting pipeline:
    1. Generate executive summary with metrics collection
    2. Save summary reports (JSON, HTML, Markdown)
    3. Generate visual dashboards (PNG, PDF, HTML)
    4. Export CSV data tables

    Args:
        repo_root: Repository root path
        project_names: List of project names to include in report
        output_dir: Directory to save all reports and dashboards

    Returns:
        Dictionary mapping file types to saved file paths

    Example:
        >>> from pathlib import Path
        >>> from infrastructure.reporting import generate_multi_project_report
        >>>
        >>> files = generate_multi_project_report(
        ...     Path("."), ["project1", "project2"], Path("output/executive_summary")
        ... )
        >>> print(f"Generated {len(files)} files")
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Starting multi-project reporting for {len(project_names)} projects...")

    all_files = {}

    try:
        # Step 1: Generate executive summary
        logger.info("Generating executive summary...")
        summary = generate_executive_summary(repo_root, project_names)

        # Step 2: Save summary reports
        logger.info("Saving summary reports...")
        summary_files = save_executive_summary(summary, output_dir)
        all_files.update(summary_files)

        # Step 3: Generate dashboards
        logger.info("Generating visual dashboards...")
        dashboard_files = generate_all_dashboards(summary, output_dir)
        all_files.update(dashboard_files)

        logger.info(f"Multi-project reporting complete. Generated {len(all_files)} files:")
        for file_type, path in all_files.items():
            logger.info(f"  {file_type.upper()}: {path.name}")

        return all_files

    except Exception as e:
        logger.error(f"Multi-project reporting failed: {e}")
        raise


__all__ = [
    'generate_pipeline_report',
    'generate_test_report',
    'generate_validation_report',
    'generate_performance_report',
    'generate_error_summary',
    'save_pipeline_report',
    'parse_pytest_output',
    'generate_test_report_from_results',
    'save_test_report',
    'ErrorAggregator',
    'ErrorEntry',
    'get_error_aggregator',
    'reset_error_aggregator',
    'generate_output_summary',
    'collect_output_statistics',
    'generate_executive_summary',
    'save_executive_summary',
    'collect_project_metrics',
    'ProjectMetrics',
    'ExecutiveSummary',
    'generate_all_dashboards',
    'generate_matplotlib_dashboard',
    'generate_plotly_dashboard',
    'generate_multi_project_report',
]

