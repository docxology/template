"""StagePerformanceTracker for tracking metrics across pipeline stages.

Provides the StagePerformanceTracker class that collects per-stage timing,
memory, CPU, and I/O metrics and generates warnings and summaries.
"""

from __future__ import annotations

import os
import time
from typing import Any

from infrastructure.core._optional_deps import psutil
from infrastructure.core.exceptions import BuildError
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline._monitor_types import (
    HIGH_CPU_PERCENT,
    HIGH_MEMORY_MB,
    SLOW_STAGE_MULTIPLIER,
    PerformanceWarningDict,
    StageMetricsDict,
)

logger = get_logger(__name__)


class StagePerformanceTracker:
    """Track performance metrics for pipeline stages."""

    def __init__(
        self,
        slow_stage_multiplier: float = SLOW_STAGE_MULTIPLIER,
        high_memory_mb: float = HIGH_MEMORY_MB,
        high_cpu_percent: float = HIGH_CPU_PERCENT,
    ):
        self.stages: list[StageMetricsDict] = []
        self.start_time: float | None = None
        self.start_memory: float = 0.0
        self.start_io: Any | None = None
        self._slow_stage_multiplier = slow_stage_multiplier
        self._high_memory_mb = high_memory_mb
        self._high_cpu_percent = high_cpu_percent

    def start_stage(self, stage_name: str) -> None:
        """Start tracking a stage."""
        self.start_time = time.time()
        if psutil is None:
            self.start_memory = 0.0
            self.start_io = None
            return
        try:
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024
            self.start_io = process.io_counters()
        except AttributeError:
            self.start_memory = 0.0
            self.start_io = None

    def end_stage(self, stage_name: str, exit_code: int) -> StageMetricsDict:
        """End tracking a stage and return metrics."""
        if self.start_time is None:
            raise BuildError(f"end_stage called without start_stage for {stage_name}")

        duration = time.time() - self.start_time

        memory_mb = 0.0
        cpu_percent = 0.0
        io_read_mb = 0.0
        io_write_mb = 0.0

        if psutil is not None:
            try:
                process = psutil.Process(os.getpid())
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_mb = current_memory
                cpu_percent = process.cpu_percent(interval=0.1)
                if self.start_io:
                    current_io = process.io_counters()
                    io_read_mb = (current_io.read_bytes - self.start_io.read_bytes) / 1024 / 1024
                    io_write_mb = (current_io.write_bytes - self.start_io.write_bytes) / 1024 / 1024
            except AttributeError as e:
                logger.debug(f"psutil attribute not available on this platform: {e}")

        metrics: StageMetricsDict = {
            "stage_name": stage_name,
            "duration": duration,
            "exit_code": exit_code,
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "io_read_mb": io_read_mb,
            "io_write_mb": io_write_mb,
        }

        self.stages.append(metrics)
        self.start_time = None

        return metrics

    def get_performance_warnings(self) -> list[PerformanceWarningDict]:
        """Return performance warnings for stages."""
        warnings: list[PerformanceWarningDict] = []

        if not self.stages:
            return warnings

        durations = [s["duration"] for s in self.stages]
        avg_duration = sum(durations) / len(durations)

        for stage in self.stages:
            if stage["duration"] > avg_duration * self._slow_stage_multiplier and avg_duration > 0:
                warnings.append(
                    {
                        "type": "slow_stage",
                        "stage": stage["stage_name"],
                        "duration": stage["duration"],
                        "average": avg_duration,
                        "message": f"Stage {stage['stage_name']} took {format_duration(stage['duration'])} ({self._slow_stage_multiplier}x average)",  # noqa: E501
                        "suggestion": "Consider optimizing this stage or running it in parallel",
                    }
                )
            if stage.get("memory_mb", 0) > self._high_memory_mb:
                warnings.append(
                    {
                        "type": "high_memory",
                        "stage": stage["stage_name"],
                        "memory_mb": stage["memory_mb"],
                        "message": f"Stage {stage['stage_name']} used {stage['memory_mb']:.0f} MB memory",  # noqa: E501
                        "suggestion": "Consider memory optimization or increasing available memory",
                    }
                )
            if stage.get("cpu_percent", 0) > self._high_cpu_percent:
                warnings.append(
                    {
                        "type": "high_cpu",
                        "stage": stage["stage_name"],
                        "cpu_percent": stage["cpu_percent"],
                        "message": f"Stage {stage['stage_name']} used {stage['cpu_percent']:.1f}% CPU",  # noqa: E501
                        "suggestion": "Consider parallelization or CPU optimization",
                    }
                )

        return warnings

    def get_summary(self) -> dict[str, Any]:
        """Return performance summary."""
        if not self.stages:
            return {}

        durations = [s["duration"] for s in self.stages]
        total_duration = sum(durations)

        return {
            "total_stages": len(self.stages),
            "total_duration": total_duration,
            "average_duration": total_duration / len(self.stages),
            "slowest_stage": max(self.stages, key=lambda s: s["duration"]),
            "fastest_stage": min(self.stages, key=lambda s: s["duration"]),
            "total_memory_mb": sum(s.get("memory_mb", 0) for s in self.stages),
            "peak_memory_mb": max((s.get("end_memory_mb", 0) for s in self.stages), default=0),
            "warnings": self.get_performance_warnings(),
        }
