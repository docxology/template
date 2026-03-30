"""Data model for pipeline execution summaries.

Separated from summary.py so that summary_formatters.py can import
PipelineSummary without creating an import cycle through summary.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryEntry
from infrastructure.core.pipeline.types import PipelineStageResult


@dataclass
class PipelineSummary:
    """Summary of pipeline execution."""

    total_duration: float
    stage_results: list[PipelineStageResult]
    slowest_stage: PipelineStageResult | None
    fastest_stage: PipelineStageResult | None
    failed_stages: list[PipelineStageResult]
    inventory: list[FileInventoryEntry]
    log_file: Path | None = None
    skip_infra: bool = False

    @property
    def executed_stages(self) -> list[PipelineStageResult]:
        """Stages that were actually run (excludes skipped stages)."""
        return [r for r in self.stage_results if not r.is_skipped]
