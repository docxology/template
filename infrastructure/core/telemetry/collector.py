"""Unified Telemetry Collector for the infrastructure pipeline.

Bridges ``StagePerformanceTracker`` (resource metrics) and
``DiagnosticReporter`` (validation events) into a single collector
that produces a unified ``PipelineTelemetry`` report at end of run.

Usage in ``PipelineExecutor``::

    collector = TelemetryCollector(config, project_name, output_dir)
    collector.capture_system_info()

    for stage in stages:
        collector.start_stage(stage.name, stage_num)
        result = run_stage(stage)
        collector.end_stage(stage.name, stage_num, result)

    collector.finalize()
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from infrastructure.core._optional_deps import psutil
from infrastructure.core.logging.diagnostic import (
    DiagnosticReporter,
    DiagnosticSeverity,
)
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.telemetry.config import TelemetryConfig
from infrastructure.core.telemetry.models import (
    PerformanceWarning,
    PipelineTelemetry,
    StageTelemetry,
)

logger = get_logger(__name__)


class TelemetryCollector:
    """Unified telemetry collector for pipeline execution.

    Combines resource tracking (CPU, memory, I/O) with diagnostic event
    aggregation into a single ``PipelineTelemetry`` report.

    When ``config.enabled`` is False, all methods become no-ops.
    """

    def __init__(
        self,
        config: TelemetryConfig,
        project_name: str,
        output_dir: Path | None = None,
        diagnostic_reporter: DiagnosticReporter | None = None,
    ):
        """Initialize the telemetry collector.

        Args:
            config: Telemetry configuration.
            project_name: Name of the project being executed.
            output_dir: Directory for persisting telemetry reports.
            diagnostic_reporter: Optional existing reporter to aggregate from.
        """
        self.config = config
        self.project_name = project_name
        self.output_dir = output_dir
        self.diagnostic_reporter = diagnostic_reporter

        self._report = PipelineTelemetry(
            project_name=project_name,
            config_used=config.to_dict(),
        )

        # Per-stage tracking state
        self._current_stage: str | None = None
        self._stage_start_time: float = 0.0
        self._stage_start_memory: float = 0.0
        self._stage_start_io: Any | None = None
        self._stage_diagnostic_snapshot: int = 0

    # ------------------------------------------------------------------
    # System info
    # ------------------------------------------------------------------

    def capture_system_info(self) -> dict[str, Any]:
        """Capture a snapshot of system resources at pipeline start.

        Returns:
            Dictionary of system resource information.
        """
        if not self.config.enabled or not self.config.track_resources:
            return {}

        info: dict[str, Any] = {}
        if psutil is not None:
            try:
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                info = {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_total_gb": round(mem.total / 1024**3, 2),
                    "memory_available_gb": round(mem.available / 1024**3, 2),
                    "memory_percent": mem.percent,
                    "disk_total_gb": round(disk.total / 1024**3, 2),
                    "disk_free_gb": round(disk.free / 1024**3, 2),
                }
            except (OSError, AttributeError) as e:
                logger.debug(f"Failed to capture system info: {e}")

        self._report.system_info = info
        return info

    # ------------------------------------------------------------------
    # Stage lifecycle
    # ------------------------------------------------------------------

    def start_stage(self, stage_name: str, stage_num: int = 0) -> None:
        """Begin tracking a pipeline stage.

        Args:
            stage_name: Human-readable stage label.
            stage_num: 1-based ordinal.

        Note: start_stage intentionally accepts fewer arguments than end_stage.
        At start time only the stage identity is known; outcome fields (success,
        exit_code, error_message) only exist at end time and belong in end_stage.
        """
        if not self.config.enabled:
            return

        self._current_stage = stage_name
        self._stage_start_time = time.time()
        self._stage_start_memory = 0.0
        self._stage_start_io = None

        if self.config.track_resources and psutil is not None:
            try:
                proc = psutil.Process(os.getpid())
                self._stage_start_memory = proc.memory_info().rss / 1024 / 1024
                self._stage_start_io = proc.io_counters()
            except (AttributeError, OSError) as e:
                logger.debug(f"Resource tracking unavailable: {e}")

        # Snapshot diagnostic event count so we can compute delta
        if self.config.track_diagnostics and self.diagnostic_reporter:
            self._stage_diagnostic_snapshot = len(self.diagnostic_reporter.events)

        logger.debug(f"Telemetry: started stage '{stage_name}' (#{stage_num})")

    def end_stage(
        self,
        stage_name: str,
        stage_num: int = 0,
        success: bool = True,
        exit_code: int = 0,
        error_message: str = "",
    ) -> StageTelemetry:
        """End tracking for the current stage and record telemetry.

        Args:
            stage_name: Stage label (must match start_stage call).
            stage_num: 1-based ordinal.
            success: Whether the stage succeeded.
            exit_code: Process exit code.
            error_message: Error description if failed.

        Returns:
            The ``StageTelemetry`` record for this stage.
        """
        duration = time.time() - self._stage_start_time if self._stage_start_time else 0.0

        stage = StageTelemetry(
            stage_name=stage_name,
            stage_num=stage_num,
            duration=duration,
            exit_code=exit_code,
            success=success,
            error_message=error_message,
        )

        if not self.config.enabled:
            return stage

        # Resource metrics
        if self.config.track_resources and psutil is not None:
            try:
                proc = psutil.Process(os.getpid())
                stage.memory_mb = proc.memory_info().rss / 1024 / 1024
                stage.cpu_percent = proc.cpu_percent(interval=0.1)

                if self._stage_start_io is not None:
                    current_io = proc.io_counters()
                    stage.io_read_mb = (
                        current_io.read_bytes - self._stage_start_io.read_bytes
                    ) / 1024 / 1024
                    stage.io_write_mb = (
                        current_io.write_bytes - self._stage_start_io.write_bytes
                    ) / 1024 / 1024
            except (AttributeError, OSError) as e:
                logger.debug(f"Resource metrics unavailable for '{stage_name}': {e}")

        # Diagnostic event delta
        if self.config.track_diagnostics and self.diagnostic_reporter:
            new_events = self.diagnostic_reporter.events[self._stage_diagnostic_snapshot:]
            stage.diagnostic_errors = sum(
                1 for e in new_events if e.severity == DiagnosticSeverity.ERROR
            )
            stage.diagnostic_warnings = sum(
                1 for e in new_events if e.severity == DiagnosticSeverity.WARNING
            )

        self._report.stages.append(stage)
        self._current_stage = None
        logger.debug(
            f"Telemetry: ended stage '{stage_name}' "
            f"(duration={duration:.2f}s, success={success})"
        )
        return stage

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self, total_duration: float | None = None) -> PipelineTelemetry:
        """Finalize the telemetry report, detect warnings, and persist.

        Args:
            total_duration: Override total duration (otherwise sum of stages).

        Returns:
            The completed ``PipelineTelemetry`` report.
        """
        if not self.config.enabled:
            return self._report

        # Total duration
        if total_duration is not None:
            self._report.total_duration = total_duration
        else:
            self._report.total_duration = sum(s.duration for s in self._report.stages)

        # Detect performance warnings
        self._report.warnings = self._detect_warnings()

        # Persist report
        if self.config.persist_report and self.output_dir:
            self._persist_report()

        logger.info(
            f"Telemetry finalized: {self._report.total_stages} stages, "
            f"{len(self._report.warnings)} warnings, "
            f"{self._report.total_duration:.1f}s total"
        )
        return self._report

    # ------------------------------------------------------------------
    # Warning detection
    # ------------------------------------------------------------------

    def _detect_warnings(self) -> list[PerformanceWarning]:
        """Analyze collected stage data for performance anomalies."""
        warnings: list[PerformanceWarning] = []
        stages = self._report.stages
        if not stages:
            return warnings

        durations = [s.duration for s in stages if s.success]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        for stage in stages:
            # Slow stage
            if (
                avg_duration > 0
                and stage.duration > avg_duration * self.config.slow_stage_multiplier
            ):
                warnings.append(
                    PerformanceWarning(
                        warning_type="slow_stage",
                        stage_name=stage.stage_name,
                        message=(
                            f"Stage '{stage.stage_name}' took {stage.duration:.1f}s "
                            f"({self.config.slow_stage_multiplier}× the average {avg_duration:.1f}s)"
                        ),
                        suggestion="Consider optimizing this stage or running it in parallel",
                        value=stage.duration,
                        threshold=avg_duration * self.config.slow_stage_multiplier,
                    )
                )

            # High memory
            if stage.memory_mb > self.config.high_memory_mb:
                warnings.append(
                    PerformanceWarning(
                        warning_type="high_memory",
                        stage_name=stage.stage_name,
                        message=(
                            f"Stage '{stage.stage_name}' used {stage.memory_mb:.0f} MB RSS "
                            f"(threshold: {self.config.high_memory_mb:.0f} MB)"
                        ),
                        suggestion="Consider memory optimization or streaming",
                        value=stage.memory_mb,
                        threshold=self.config.high_memory_mb,
                    )
                )

            # High CPU
            if stage.cpu_percent > self.config.high_cpu_percent:
                warnings.append(
                    PerformanceWarning(
                        warning_type="high_cpu",
                        stage_name=stage.stage_name,
                        message=(
                            f"Stage '{stage.stage_name}' used {stage.cpu_percent:.1f}% CPU "
                            f"(threshold: {self.config.high_cpu_percent:.0f}%)"
                        ),
                        suggestion="Consider parallelization or CPU optimization",
                        value=stage.cpu_percent,
                        threshold=self.config.high_cpu_percent,
                    )
                )

        return warnings

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_report(self) -> None:
        """Write the telemetry report to the output directory."""
        if not self.output_dir:
            return

        report_dir = self.output_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "telemetry.json"

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(self._report.to_dict(), f, indent=2)
            logger.debug(f"Telemetry report written to {report_file}")
        except OSError as e:
            logger.warning(f"Failed to write telemetry report: {e}")

        # Text format
        if "text" in self.config.output_formats:
            text_file = report_dir / "telemetry.txt"
            try:
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(self._format_text_report())
                logger.debug(f"Telemetry text report written to {text_file}")
            except OSError as e:
                logger.warning(f"Failed to write telemetry text report: {e}")

    def _format_text_report(self) -> str:
        """Format the telemetry report as human-readable text."""
        lines: list[str] = []
        r = self._report

        lines.append("=" * 72)
        lines.append(f" TELEMETRY REPORT: {r.project_name}")
        lines.append("=" * 72)
        lines.append("")
        lines.append(f"Total Duration : {r.total_duration:.1f}s")
        lines.append(f"Total Stages   : {r.total_stages}")
        lines.append(f"Failed Stages  : {len(r.failed_stages)}")
        lines.append("")

        # Stage table
        lines.append(f"{'Stage':<35} {'Time':>8} {'Mem MB':>8} {'CPU%':>6} {'Status':>8}")
        lines.append("-" * 72)
        for s in r.stages:
            status = "✓ OK" if s.success else "✗ FAIL"
            lines.append(
                f"{s.stage_name:<35} {s.duration:>7.1f}s {s.memory_mb:>7.0f} "
                f"{s.cpu_percent:>5.1f} {status:>8}"
            )

        # Warnings
        if r.warnings:
            lines.append("")
            lines.append(f"Performance Warnings ({len(r.warnings)}):")
            lines.append("-" * 72)
            for w in r.warnings:
                lines.append(f"  ⚠ [{w.warning_type}] {w.message}")
                if w.suggestion:
                    lines.append(f"    → {w.suggestion}")

        lines.append("")
        lines.append("=" * 72)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def report(self) -> PipelineTelemetry:
        """Access the current (possibly incomplete) telemetry report."""
        return self._report
