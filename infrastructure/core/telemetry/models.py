"""Telemetry data models.

Dataclasses representing the structured telemetry report produced at the
end of a pipeline run.  These are serializable to JSON via ``to_dict()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StageTelemetry:
    """Telemetry for a single pipeline stage.

    Attributes:
        stage_name: Human-readable stage label.
        stage_num: 1-based ordinal within the pipeline run.
        duration: Wall-clock seconds.
        exit_code: Process exit code (0 = success).
        success: Whether the stage passed.
        memory_mb: RSS at stage end (MB), 0 if unavailable.
        cpu_percent: CPU usage during the stage, 0 if unavailable.
        io_read_mb: Bytes read during stage (MB), 0 if unavailable.
        io_write_mb: Bytes written during stage (MB), 0 if unavailable.
        diagnostic_errors: Count of ERROR-level diagnostic events.
        diagnostic_warnings: Count of WARNING-level diagnostic events.
        error_message: Error description if the stage failed.
    """

    stage_name: str
    stage_num: int = 0
    duration: float = 0.0
    exit_code: int = 0
    success: bool = True
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0
    diagnostic_errors: int = 0
    diagnostic_warnings: int = 0
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "stage_name": self.stage_name,
            "stage_num": self.stage_num,
            "duration": round(self.duration, 3),
            "exit_code": self.exit_code,
            "success": self.success,
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
            "io_read_mb": round(self.io_read_mb, 2),
            "io_write_mb": round(self.io_write_mb, 2),
            "diagnostic_errors": self.diagnostic_errors,
            "diagnostic_warnings": self.diagnostic_warnings,
            "error_message": self.error_message,
        }


@dataclass
class PerformanceWarning:
    """A single performance anomaly detected during the pipeline run."""

    warning_type: str  # "slow_stage" | "high_memory" | "high_cpu"
    stage_name: str
    message: str
    suggestion: str = ""
    value: float = 0.0
    threshold: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "warning_type": self.warning_type,
            "stage_name": self.stage_name,
            "message": self.message,
            "suggestion": self.suggestion,
            "value": round(self.value, 2),
            "threshold": round(self.threshold, 2),
        }


@dataclass
class PipelineTelemetry:
    """Complete telemetry report for a pipeline run.

    Attributes:
        project_name: Name of the project that was executed.
        total_duration: Wall-clock seconds for the entire pipeline.
        stages: Per-stage telemetry records.
        warnings: Performance warnings detected.
        system_info: System resource snapshot at pipeline start.
        config_used: Serialized TelemetryConfig for reproducibility.
    """

    project_name: str
    total_duration: float = 0.0
    stages: list[StageTelemetry] = field(default_factory=list)
    warnings: list[PerformanceWarning] = field(default_factory=list)
    system_info: dict[str, Any] = field(default_factory=dict)
    config_used: dict[str, Any] = field(default_factory=dict)

    @property
    def total_stages(self) -> int:
        """Number of stages recorded."""
        return len(self.stages)

    @property
    def failed_stages(self) -> list[StageTelemetry]:
        """Stages that did not succeed."""
        return [s for s in self.stages if not s.success]

    @property
    def slowest_stage(self) -> StageTelemetry | None:
        """Stage with the longest duration, or None."""
        successful = [s for s in self.stages if s.success]
        return max(successful, key=lambda s: s.duration) if successful else None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full report to a plain dictionary."""
        return {
            "project_name": self.project_name,
            "total_duration": round(self.total_duration, 3),
            "total_stages": self.total_stages,
            "stages": [s.to_dict() for s in self.stages],
            "warnings": [w.to_dict() for w in self.warnings],
            "system_info": self.system_info,
            "config_used": self.config_used,
        }
