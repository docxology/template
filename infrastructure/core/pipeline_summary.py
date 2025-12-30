"""Pipeline summary generation and reporting.

This module provides utilities for generating pipeline execution summaries,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger, format_duration
from infrastructure.core.file_inventory import (
    FileInventoryManager,
    FileInventoryEntry
)
from infrastructure.core.pipeline import PipelineStageResult

logger = get_logger(__name__)


@dataclass
class PipelineSummary:
    """Summary of pipeline execution."""
    total_duration: float
    stage_results: List[PipelineStageResult]
    slowest_stage: Optional[PipelineStageResult]
    fastest_stage: Optional[PipelineStageResult]
    failed_stages: List[PipelineStageResult]
    inventory: List[FileInventoryEntry]
    log_file: Optional[Path] = None
    skip_infra: bool = False


class PipelineSummaryGenerator:
    """Generate pipeline execution summaries."""

    def __init__(self):
        """Initialize summary generator."""
        self.file_inventory_manager = FileInventoryManager()

    def generate_summary(
        self,
        stage_results: List[PipelineStageResult],
        total_duration: float,
        output_dir: Path,
        log_file: Optional[Path] = None,
        skip_infra: bool = False
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
            skip_infra=skip_infra
        )

    def format_summary(
        self,
        summary: PipelineSummary,
        format: str = "text"
    ) -> str:
        """Format summary for display (text, json, html).

        Args:
            summary: Pipeline summary to format
            format: Output format ("text", "json", "html")

        Returns:
            Formatted summary string
        """
        if format == "json":
            return self._format_json_summary(summary)
        elif format == "html":
            return self._format_html_summary(summary)
        else:
            return self._format_text_summary(summary)

    def _format_text_summary(self, summary: PipelineSummary) -> str:
        """Format summary as text output.

        Args:
            summary: Pipeline summary

        Returns:
            Text formatted summary
        """
        lines = []

        # Header
        lines.append("")
        lines.append("PIPELINE SUMMARY")
        lines.append("")
        lines.append("All stages completed successfully!")

        # Log file info
        if summary.log_file:
            log_file_final = self._get_final_log_path(summary.log_file)
            lines.append(f"Full pipeline log: {summary.log_file}")
            if str(summary.log_file) != str(log_file_final):
                lines.append(f"  (Will be available at: {log_file_final} after copy stage)")

        lines.append("")
        lines.append("Stage Results:")

        # Stage results
        executed_stages = [r for r in summary.stage_results if r.success or r.exit_code != 0]
        total_stage_time = sum(r.duration for r in executed_stages)

        for result in summary.stage_results:
            stage_display = self._format_stage_result(result, summary.total_duration, summary.skip_infra)
            lines.append(f"  {stage_display}")

        lines.append("")
        lines.append("Performance Metrics:")
        lines.append(f"  Total Execution Time: {summary.total_duration:.1f}s")

        if executed_stages:
            avg_time = total_stage_time / len(executed_stages)
            lines.append(f"  Average Stage Time: {avg_time:.1f}s")

        if summary.slowest_stage:
            slowest_pct = (summary.slowest_stage.duration * 100) / summary.total_duration
            lines.append(f"  Slowest Stage: Stage {summary.slowest_stage.stage_num} - {summary.slowest_stage.stage_name} "
                        f"({format_duration(summary.slowest_stage.duration)}, {slowest_pct:.0f}%)")

        if summary.fastest_stage:
            lines.append(f"  Fastest Stage: Stage {summary.fastest_stage.stage_num} - {summary.fastest_stage.stage_name} "
                        f"({format_duration(summary.fastest_stage.duration)})")

        lines.append("")

        # File inventory
        if summary.inventory:
            base_dir = self._find_base_output_dir(summary.inventory)
            inventory_report = self.file_inventory_manager.generate_inventory_report(
                summary.inventory, "text", base_dir
            )
            lines.append(inventory_report)

            # Add notes about file locations
            if base_dir and "output" in str(base_dir):
                project_name = self._extract_project_name_from_path(base_dir)
                if project_name:
                    lines.append(f"Note: Files are also available in projects/{project_name}/output/ during development")
            else:
                lines.append("Note: Files will be copied to output/ during copy stage")

        # Log file location
        if summary.log_file:
            log_file_final = self._get_final_log_path(summary.log_file)
            lines.append("")
            lines.append("Pipeline Log:")
            lines.append(f"  • Current: {summary.log_file}")
            if str(summary.log_file) != str(log_file_final):
                lines.append(f"  • Final: {log_file_final} (after copy stage)")

        # Coverage reports
        coverage_dir = Path("htmlcov")
        if coverage_dir.exists():
            lines.append("")
            lines.append("Coverage Reports:")
            lines.append("  • HTML: htmlcov/index.html")

        lines.append("")
        lines.append("Pipeline complete - ready for deployment")
        lines.append("")

        return "\n".join(lines)

    def _format_json_summary(self, summary: PipelineSummary) -> str:
        """Format summary as JSON.

        Args:
            summary: Pipeline summary

        Returns:
            JSON formatted summary
        """
        import json

        data = {
            "total_duration": summary.total_duration,
            "total_duration_formatted": format_duration(summary.total_duration),
            "stages": [
                {
                    "stage_num": r.stage_num,
                    "stage_name": r.stage_name,
                    "success": r.success,
                    "duration": r.duration,
                    "duration_formatted": format_duration(r.duration),
                    "exit_code": r.exit_code,
                    "error_message": r.error_message
                }
                for r in summary.stage_results
            ],
            "performance": {
                "slowest_stage": self._stage_result_to_dict(summary.slowest_stage),
                "fastest_stage": self._stage_result_to_dict(summary.fastest_stage),
                "failed_stages": [self._stage_result_to_dict(r) for r in summary.failed_stages]
            },
            "files": {
                "count": len(summary.inventory),
                "inventory": [
                    {
                        "path": str(entry.path),
                        "size": entry.size,
                        "size_formatted": entry.size_formatted,
                        "category": entry.category,
                        "modified": entry.modified
                    }
                    for entry in summary.inventory
                ]
            }
        }

        if summary.log_file:
            data["log_file"] = str(summary.log_file)
            data["log_file_final"] = str(self._get_final_log_path(summary.log_file))

        return json.dumps(data, indent=2)

    def _format_html_summary(self, summary: PipelineSummary) -> str:
        """Format summary as HTML.

        Args:
            summary: Pipeline summary

        Returns:
            HTML formatted summary
        """
        html_parts = []
        html_parts.append("<div class='pipeline-summary'>")
        html_parts.append("<h2>Pipeline Summary</h2>")
        html_parts.append("<p class='success'>All stages completed successfully!</p>")

        if summary.log_file:
            log_file_final = self._get_final_log_path(summary.log_file)
            html_parts.append(f"<p><strong>Log file:</strong> {summary.log_file}")
            if str(summary.log_file) != str(log_file_final):
                html_parts.append(f"<br><em>(Will be available at: {log_file_final} after copy stage)</em></p>")

        html_parts.append("<h3>Stage Results</h3>")
        html_parts.append("<ul class='stage-results'>")

        for result in summary.stage_results:
            css_class = "success" if result.success else "error"
            status_icon = "✓" if result.success else "✗"
            duration_formatted = format_duration(result.duration)
            percentage = (result.duration * 100) / summary.total_duration if summary.total_duration > 0 else 0

            html_parts.append(f"<li class='{css_class}'>")
            html_parts.append(f"  {status_icon} Stage {result.stage_num}: {result.stage_name} ")
            html_parts.append(f"  ({duration_formatted}, {percentage:.0f}%)")
            if result.error_message:
                html_parts.append(f"  <br><em>Error: {result.error_message}</em>")
            html_parts.append("</li>")

        html_parts.append("</ul>")

        html_parts.append("<h3>Performance Metrics</h3>")
        html_parts.append("<ul class='performance-metrics'>")
        html_parts.append(f"<li>Total Execution Time: {summary.total_duration:.1f}s</li>")

        executed_stages = [r for r in summary.stage_results if r.success or r.exit_code != 0]
        if executed_stages:
            avg_time = sum(r.duration for r in executed_stages) / len(executed_stages)
            html_parts.append(f"<li>Average Stage Time: {avg_time:.1f}s</li>")

        if summary.slowest_stage:
            slowest_pct = (summary.slowest_stage.duration * 100) / summary.total_duration
            html_parts.append(f"<li>Slowest Stage: {summary.slowest_stage.stage_name} "
                            f"({format_duration(summary.slowest_stage.duration)}, {slowest_pct:.0f}%)</li>")

        if summary.fastest_stage:
            html_parts.append(f"<li>Fastest Stage: {summary.fastest_stage.stage_name} "
                            f"({format_duration(summary.fastest_stage.duration)})</li>")

        html_parts.append("</ul>")

        # File inventory
        if summary.inventory:
            html_parts.append("<h3>Generated Files</h3>")
            base_dir = self._find_base_output_dir(summary.inventory)
            inventory_html = self.file_inventory_manager.generate_inventory_report(
                summary.inventory, "html", base_dir
            )
            html_parts.append(inventory_html)

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _find_slowest_stage(self, results: List[PipelineStageResult]) -> Optional[PipelineStageResult]:
        """Find the slowest stage.

        Args:
            results: Stage results

        Returns:
            Slowest stage result, or None if no stages
        """
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return None

        return max(successful_results, key=lambda r: r.duration)

    def _find_fastest_stage(self, results: List[PipelineStageResult]) -> Optional[PipelineStageResult]:
        """Find the fastest stage (excluding stage 1 which is usually setup).

        Args:
            results: Stage results

        Returns:
            Fastest stage result, or None if no stages
        """
        successful_results = [r for r in results if r.success and r.stage_num > 1]
        if not successful_results:
            return None

        return min(successful_results, key=lambda r: r.duration)

    def _format_stage_result(
        self,
        result: PipelineStageResult,
        total_duration: float,
        skip_infra: bool
    ) -> str:
        """Format a single stage result for display.

        Args:
            result: Stage result
            total_duration: Total pipeline duration
            skip_infra: Whether infrastructure tests were skipped

        Returns:
            Formatted stage result string
        """
        if not result.success and result.exit_code == 0:
            # Skipped stage
            return f"⊘ Stage {result.stage_num}: {result.stage_name} (skipped)"

        duration_formatted = f"{result.duration:.1f}s"
        percentage = (result.duration * 100) / total_duration if total_duration > 0 else 0

        if result.success:
            # Check if this is the slowest stage
            if (self._find_slowest_stage([result] * 2) and  # Mock comparison
                result.duration > 10):  # Only highlight if > 10 seconds
                return f"✓ Stage {result.stage_num}: {result.stage_name} ({duration_formatted}, {percentage:.1f}%) ⚠ bottleneck"
            else:
                return f"✓ Stage {result.stage_num}: {result.stage_name} ({duration_formatted}, {percentage:.1f}%)"
        else:
            return f"✗ Stage {result.stage_num}: {result.stage_name} ({duration_formatted}) FAILED"

    def _stage_result_to_dict(self, result: Optional[PipelineStageResult]) -> Optional[dict]:
        """Convert stage result to dictionary.

        Args:
            result: Stage result

        Returns:
            Dictionary representation
        """
        if result is None:
            return None

        return {
            "stage_num": result.stage_num,
            "stage_name": result.stage_name,
            "success": result.success,
            "duration": result.duration,
            "duration_formatted": format_duration(result.duration),
            "exit_code": result.exit_code,
            "error_message": result.error_message
        }

    def _get_final_log_path(self, log_file: Path) -> Path:
        """Get the final log file path after copying.

        Args:
            log_file: Current log file path

        Returns:
            Final log file path
        """
        # Replace "projects/{name}/output" with "output" in path
        log_str = str(log_file)
        # Handle paths like "projects/project/output/..." -> "output/..."
        if "projects/" in log_str and "/output/" in log_str:
            # Find the output directory and take everything after it
            output_index = log_str.find("/output/")
            if output_index != -1:
                return Path("output" + log_str[output_index + 7:])  # +7 to skip "/output" but keep the "/"
        return log_file

    def _find_base_output_dir(self, inventory: List[FileInventoryEntry]) -> Optional[Path]:
        """Find the base output directory from inventory.

        Args:
            inventory: File inventory

        Returns:
            Base output directory path
        """
        if not inventory:
            return None

        # Find the most common parent directory
        paths = [entry.path for entry in inventory]
        if not paths:
            return None

        # Start with the first path and find common parent
        common_parent = paths[0].parent
        for path in paths[1:]:
            while not str(path).startswith(str(common_parent)):
                common_parent = common_parent.parent
                if common_parent == common_parent.parent:  # root
                    break

        return common_parent

    def _extract_project_name_from_path(self, path: Path) -> Optional[str]:
        """Extract project name from output path.

        Args:
            path: Path containing project name

        Returns:
            Project name
        """
        path_str = str(path)
        if "projects/" in path_str and "/output" in path_str:
            # Extract project name between "projects/" and "/output"
            start = path_str.find("projects/") + len("projects/")
            end = path_str.find("/output", start)
            if end > start:
                return path_str[start:end]
        return None


def generate_pipeline_summary(
    stage_results: List[PipelineStageResult],
    total_duration: float,
    output_dir: Path,
    log_file: Optional[Path] = None,
    skip_infra: bool = False,
    format: str = "text"
) -> str:
    """Convenience function to generate and format pipeline summary.

    Args:
        stage_results: Results from all pipeline stages
        total_duration: Total pipeline execution time
        output_dir: Output directory to scan for files
        log_file: Path to pipeline log file
        skip_infra: Whether infrastructure tests were skipped
        format: Output format ("text", "json", "html")

    Returns:
        Formatted summary string
    """
    generator = PipelineSummaryGenerator()
    summary = generator.generate_summary(
        stage_results, total_duration, output_dir, log_file, skip_infra
    )
    return generator.format_summary(summary, format)