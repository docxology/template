"""Post-run pipeline reporting helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.executor import StageResult
from infrastructure.reporting.pipeline_summary import generate_pipeline_summary

logger = get_logger(__name__)


def write_pipeline_post_run_reports(
    *,
    results: list[StageResult],
    repo_root: Path,
    project_name: str,
    skip_infra: bool,
) -> None:
    """Generate text summary, JSON/HTML reports, and verify pipeline log."""
    output_dir = repo_root / "projects" / project_name / "output"
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    total_duration = sum(r.duration for r in results)
    text_summary = generate_pipeline_summary(
        stage_results=results,
        total_duration=total_duration,
        output_dir=output_dir,
        skip_infra=skip_infra,
        output_format="text",
    )
    logger.info(text_summary)

    try:
        from infrastructure.reporting import (
            collect_output_statistics,
            generate_pipeline_report,
            save_pipeline_report,
        )
        from infrastructure.reporting.log_analysis import generate_log_summary

        output_stats = collect_output_statistics(repo_root, project_name)
        log_file = output_dir / "logs" / "pipeline.log"
        if log_file.exists():
            try:
                log_summary_file = reports_dir / "log_summary.txt"
                generate_log_summary(log_file, log_summary_file)
                logger.info("Log summary generated")
            except OSError as exc:
                logger.warning("Failed to generate log summary: %s", exc)

        pipeline_report = generate_pipeline_report(
            stage_results=[
                {
                    "name": r.stage_name,
                    "exit_code": r.exit_code,
                    "duration": r.duration,
                    "error_message": r.error_message,
                }
                for r in results
            ],
            total_duration=total_duration,
            repo_root=repo_root,
            output_statistics=output_stats,
            project_name=project_name,
        )
        saved_files = save_pipeline_report(
            pipeline_report,
            reports_dir,
            formats=["json", "html", "markdown"],
        )
        logger.info("Pipeline reports saved to %s", reports_dir)
        for fmt, path in saved_files.items():
            logger.info("  • %s: %s", fmt.upper(), path.name)
    except (ImportError, OSError, KeyError, AttributeError) as exc:
        logger.warning("Failed to generate comprehensive pipeline report: %s", exc, exc_info=True)

    log_file = output_dir / "logs" / "pipeline.log"
    if log_file.exists():
        try:
            size = log_file.stat().st_size
            if size > 0:
                logger.info("Pipeline log file verified: %s (%s bytes)", log_file, f"{size:,}")
            else:
                logger.warning("Pipeline log file is empty: %s", log_file)
        except OSError as exc:
            logger.warning("Failed to verify pipeline log file: %s", exc)
    else:
        logger.warning("Pipeline log file not found: %s", log_file)
