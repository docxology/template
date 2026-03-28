"""Pipeline summary generation and reporting.

This module provides utilities for generating pipeline execution summaries,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.

Formatting logic lives in summary_formatters.py; this module re-exports
all public names so that existing ``from infrastructure.core.pipeline.summary import ...``
statements continue to work unchanged.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryEntry, FileInventoryManager
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.types import PipelineStageResult

# PipelineSummary lives in summary_models to avoid a cycle with summary_formatters
from infrastructure.core.pipeline.summary_models import PipelineSummary  # noqa: F401

# Re-export formatter and helper functions so callers that import from summary still work
from infrastructure.core.pipeline.summary_formatters import (  # noqa: F401
    format_html_summary,
    format_json_summary,
    format_text_summary,
)
from infrastructure.core.pipeline.summary_helpers import (  # noqa: F401
    extract_project_name_from_path,
    find_base_output_dir,
    format_stage_result,
    get_final_log_path,
    stage_result_to_dict,
)

logger = get_logger(__name__)


class PipelineSummaryGenerator:
    """Generate pipeline execution summaries."""

    def __init__(self):
        """Initialize summary generator."""
        self.file_inventory_manager = FileInventoryManager()

    def generate_summary(
        self,
        stage_results: list[PipelineStageResult],
        total_duration: float,
        output_dir: Path,
        log_file: Path | None = None,
        skip_infra: bool = False,
    ) -> PipelineSummary:
        """Generate comprehensive pipeline summary.

        Args:
            stage_results: Results from all pipeline stages
            total_duration: Total pipeline execution time
            output_dir: Output directory to scan for files
            log_file: Path to pipeline log file
            skip_infra: Whether infrastructure tests were skipped

        Returns:
            Pipeline summary with performance metrics
        """
        # Calculate performance metrics
        slowest_stage = self._find_slowest_stage(stage_results)
        fastest_stage = self._find_fastest_stage(stage_results)
        failed_stages = [r for r in stage_results if not r.success]

        # Collect file inventory
        inventory = self.file_inventory_manager.collect_output_files(output_dir)

        return PipelineSummary(
            total_duration=total_duration,
            stage_results=stage_results,
            slowest_stage=slowest_stage,
            fastest_stage=fastest_stage,
            failed_stages=failed_stages,
            inventory=inventory,
            log_file=log_file,
            skip_infra=skip_infra,
        )

    def format_summary(self, summary: PipelineSummary, output_format: str = "text") -> str:
        """Format summary for display (text, json, html).

        Args:
            summary: Pipeline summary to format
            output_format: Output format ("text", "json", "html")

        Returns:
            Formatted summary string
        """
        if output_format == "json":
            return format_json_summary(summary)
        elif output_format == "html":
            return format_html_summary(summary, self.file_inventory_manager)
        else:
            return format_text_summary(summary, self.file_inventory_manager)

    def _find_slowest_stage(self, results: list[PipelineStageResult]) -> PipelineStageResult | None:
        """Find the slowest stage."""
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return None
        return max(successful_results, key=lambda r: r.duration)

    def _find_fastest_stage(self, results: list[PipelineStageResult]) -> PipelineStageResult | None:
        """Find the fastest stage (excluding stage 1 which is usually setup)."""
        successful_results = [r for r in results if r.success and r.stage_num > 1]
        if not successful_results:
            return None
        return min(successful_results, key=lambda r: r.duration)


def generate_pipeline_summary(
    stage_results: list[PipelineStageResult],
    total_duration: float,
    output_dir: Path,
    log_file: Path | None = None,
    skip_infra: bool = False,
    output_format: str = "text",
) -> str:
    """Convenience function to generate and format pipeline summary.

    Args:
        stage_results: Results from all pipeline stages
        total_duration: Total pipeline execution time
        output_dir: Output directory to scan for files
        log_file: Path to pipeline log file
        skip_infra: Whether infrastructure tests were skipped
        output_format: Output format ("text", "json", "html")

    Returns:
        Formatted summary string
    """
    generator = PipelineSummaryGenerator()
    summary = generator.generate_summary(
        stage_results, total_duration, output_dir, log_file, skip_infra
    )
    return generator.format_summary(summary, output_format)
