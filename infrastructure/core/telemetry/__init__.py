"""Unified telemetry subpackage for the infrastructure pipeline.

Bridges performance monitoring (CPU, memory, I/O) with diagnostic
event collection into a single ``TelemetryCollector`` that produces
structured ``PipelineTelemetry`` reports.

Quick start::

    from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

    config = TelemetryConfig(enabled=True, track_resources=True)
    collector = TelemetryCollector(config, "my_project", output_dir)
    collector.capture_system_info()

    collector.start_stage("Analysis", stage_num=1)
    # ... run stage ...
    collector.end_stage("Analysis", stage_num=1, success=True)

    report = collector.finalize(total_duration=42.0)
"""

from __future__ import annotations

from infrastructure.core.telemetry.collector import TelemetryCollector
from infrastructure.core.telemetry.config import TelemetryConfig
from infrastructure.core.telemetry.models import (
    PerformanceWarning,
    PipelineTelemetry,
    StageTelemetry,
)

__all__ = [
    "PerformanceWarning",
    "PipelineTelemetry",
    "StageTelemetry",
    "TelemetryCollector",
    "TelemetryConfig",
]
