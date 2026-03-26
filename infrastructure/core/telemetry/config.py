"""Telemetry configuration dataclasses.

Defines ``TelemetryConfig`` — the single configuration surface for the
unified telemetry subsystem.  Values can be set programmatically or loaded
from the optional ``telemetry:`` block in ``pipeline.yaml``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TelemetryConfig:
    """Configuration for pipeline telemetry collection.

    Attributes:
        enabled: Master switch — when False the collector becomes a no-op.
        track_resources: Collect CPU, memory, and I/O via psutil.
        track_diagnostics: Aggregate DiagnosticReporter events.
        output_formats: Formats for the persisted report (json, text).
        persist_report: Write telemetry.json at end of pipeline.
        slow_stage_multiplier: Warn when a stage exceeds N× the average.
        high_memory_mb: Warn when RSS exceeds this threshold (MB).
        high_cpu_percent: Warn when CPU usage exceeds this percentage.
    """

    enabled: bool = True
    track_resources: bool = True
    track_diagnostics: bool = True
    output_formats: list[str] = field(default_factory=lambda: ["json", "text"])
    persist_report: bool = True
    slow_stage_multiplier: float = 2.0
    high_memory_mb: float = 1024.0
    high_cpu_percent: float = 90.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryConfig:
        """Create config from a dictionary (e.g. parsed YAML block).

        Unknown keys are silently ignored so that forward-compatible YAML
        fields don't break older code.
        """
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "enabled": self.enabled,
            "track_resources": self.track_resources,
            "track_diagnostics": self.track_diagnostics,
            "output_formats": list(self.output_formats),
            "persist_report": self.persist_report,
            "slow_stage_multiplier": self.slow_stage_multiplier,
            "high_memory_mb": self.high_memory_mb,
            "high_cpu_percent": self.high_cpu_percent,
        }
