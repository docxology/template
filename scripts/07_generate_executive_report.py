#!/usr/bin/env python3
"""Executive report generation orchestrator script.

This thin orchestrator coordinates the executive reporting stage:
1. Discovers all projects in the repository
2. Collects comprehensive metrics using infrastructure.reporting.executive_reporter
3. Generates comparative analysis across projects
4. Creates visual dashboards (PNG/PDF/HTML)
5. Saves reports to output/executive_summary/

Stage 10 of the pipeline orchestration (optional, multi-project only).

Architecture:
    This is a generic entry point orchestrator (Layer 1 - Infrastructure).
    It coordinates executive reporting without implementing business logic.
    Follows thin orchestrator pattern - all logic in infrastructure modules.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep
)
from infrastructure.project.discovery import discover_projects
from infrastructure.reporting.executive_reporter import (
    generate_executive_summary,
    save_executive_summary
)
from infrastructure.reporting.dashboard_generator import generate_all_dashboards

# Set up logger for this module
logger = get_logger(__name__)


def verify_project_completion(repo_root: Path, project_name: str) -> bool:
    """Verify that a project has completed the pipeline successfully.

    Args:
        repo_root: Repository root path
        project_name: Name of the project

    Returns:
        True if project completed successfully, False otherwise
    """
    project_root = repo_root / "projects" / project_name
    output_dir = repo_root / "output" / project_name

    # Check for output directory (primary requirement)
    if not output_dir.exists():
        logger.warning(f"Project '{project_name}' missing output directory")
        return False

    # Check for pipeline report (optional - executive report can work without it)
    pipeline_report = project_root / "output" / "reports" / "pipeline_report.json"
    if not pipeline_report.exists():
        logger.debug(f"Project '{project_name}' missing pipeline report - executive report will use alternative data sources")
    else:
        logger.debug(f"Project '{project_name}' has pipeline report")

    # Check for test results (optional - warn if missing but continue)
    test_results = project_root / "output" / "reports" / "test_results.json"
    if not test_results.exists():
        logger.debug(f"Project '{project_name}' missing test results - executive report will use limited data")
    else:
        logger.debug(f"Project '{project_name}' has test results")

    # Check for manuscript PDF (indicates PDF generation completed)
    manuscript_pdf = output_dir / "pdf" / f"{project_name}_combined.pdf"
    if not manuscript_pdf.exists():
        logger.warning(f"Project '{project_name}' missing combined PDF - may indicate incomplete pipeline")
        return False

    logger.debug(f"Project '{project_name}' verification passed")
    return True


def main() -> int:
    """Execute executive reporting orchestration.
    
    Returns:
        Exit code (0=success, 1=failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate executive report")
    parser.add_argument(
        '--project',
        help='Project name (ignored - this stage runs for all projects)'
    )
    args = parser.parse_args()
    
    log_header("STAGE 10: Executive Reporting", logger)
    
    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("Executive reporting stage start", logger)
    
    try:
        repo_root = Path(__file__).parent.parent
        
        # Discover all projects
        log_substep("Discovering projects...", logger)
        projects = discover_projects(repo_root)
        
        if not projects:
            logger.error("No projects found in repository")
            return 1
        
        if len(projects) == 1:
            logger.info("Only one project found - skipping executive reporting")
            logger.info("  Executive reporting is designed for multi-project comparisons")
            return 0
        
        logger.info(f"Found {len(projects)} projects:")
        for project in projects:
            logger.info(f"  • {project.name}")
        
        # Verify each project has completed successfully
        log_substep("Verifying project completion...", logger)
        completed_projects = []
        incomplete_projects = []
        
        for project in projects:
            if verify_project_completion(repo_root, project.name):
                completed_projects.append(project.name)
                logger.info(f"  ✓ {project.name}")
            else:
                incomplete_projects.append(project.name)
                logger.warning(f"  ✗ {project.name} (incomplete)")
        
        if not completed_projects:
            logger.error("No projects have completed the pipeline successfully")
            logger.error("  Run pipeline for at least one project before generating executive report")
            return 1
        
        if incomplete_projects:
            logger.warning(f"Skipping {len(incomplete_projects)} incomplete project(s)")
            for project_name in incomplete_projects:
                logger.warning(f"  - {project_name}")
        
        # Generate executive summary
        log_substep(f"Generating executive summary for {len(completed_projects)} project(s)...", logger)
        summary = generate_executive_summary(repo_root, completed_projects)
        
        # Save reports
        output_dir = repo_root / "output" / "executive_summary"
        log_substep("Saving reports...", logger)
        saved_reports = save_executive_summary(summary, output_dir)
        
        for format_name, file_path in saved_reports.items():
            logger.info(f"  {format_name.upper()}: {file_path.name}")
        
        # Generate dashboards
        log_substep("Generating visual dashboards...", logger)
        dashboard_files = generate_all_dashboards(summary, output_dir)
        
        for format_name, file_path in dashboard_files.items():
            logger.info(f"  {format_name.upper()}: {file_path.name}")
        
        # Log high-level summary
        logger.info("\n" + "="*60)
        logger.info("EXECUTIVE SUMMARY")
        logger.info("="*60)
        logger.info(f"\nTotal Projects: {summary.total_projects}")
        logger.info(f"Total Tests: {summary.aggregate_metrics['tests']['total_tests']} "
                   f"({summary.aggregate_metrics['tests']['total_passed']} passed)")
        logger.info(f"Average Coverage: {summary.aggregate_metrics['tests']['average_coverage']:.1f}%")
        logger.info(f"Total Pipeline Time: {summary.aggregate_metrics['pipeline']['total_duration']:.0f}s")
        logger.info(f"\nManuscript: {summary.aggregate_metrics['manuscript']['total_words']:,} words, "
                   f"{summary.aggregate_metrics['manuscript']['total_sections']} sections")
        logger.info(f"Outputs: {summary.aggregate_metrics['outputs']['total_pdfs']} PDFs, "
                   f"{summary.aggregate_metrics['outputs']['total_figures']} figures")
        
        # Log recommendations
        if summary.recommendations:
            logger.info("\nRecommendations:")
            for rec in summary.recommendations:
                logger.info(f"  {rec}")
        
        logger.info("")
        
        # Log output location
        log_success(f"\n✅ Executive reporting complete!", logger)
        logger.info(f"Reports saved to: {output_dir}")
        logger.info(f"  • Consolidated report: consolidated_report.{{json,html,md}}")
        logger.info(f"  • Visual dashboard: dashboard.{{png,pdf,html}}")
        
        # Log resource usage at end
        log_resource_usage("Executive reporting stage end", logger)
        
        return 0
        
    except Exception as e:
        logger.error(f"Executive reporting failed: {e}", exc_info=True)
        log_resource_usage("Executive reporting stage end (error)", logger)
        return 1


if __name__ == "__main__":
    exit(main())
