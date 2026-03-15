"""Tests for infrastructure/core/stage_monitor.py.

Tests stage performance monitoring utilities using real execution.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.core.stage_monitor import (
    ResourceUsage,
    StageMetricsDict,
)


class TestResourceUsage:
    """Test ResourceUsage dataclass."""

    def test_default_construction(self):
        """Test ResourceUsage can be constructed with defaults."""
        usage = ResourceUsage()
        assert usage.cpu_percent == 0.0
        assert usage.memory_mb == 0.0
        assert usage.peak_memory_mb == 0.0
        assert usage.io_read_mb == 0.0
        assert usage.io_write_mb == 0.0

    def test_custom_values(self):
        """Test ResourceUsage can be constructed with custom values."""
        usage = ResourceUsage(
            cpu_percent=45.0,
            memory_mb=512.0,
            peak_memory_mb=600.0,
            io_read_mb=10.5,
            io_write_mb=2.3,
        )
        assert usage.cpu_percent == 45.0
        assert usage.memory_mb == 512.0
        assert usage.peak_memory_mb == 600.0
        assert usage.io_read_mb == 10.5
        assert usage.io_write_mb == 2.3


class TestStageMetricsDictType:
    """Test StageMetricsDict typed dict structure."""

    def test_can_create_empty(self):
        """Test StageMetricsDict can be created as empty dict."""
        metrics: StageMetricsDict = {}
        assert isinstance(metrics, dict)

    def test_can_create_with_fields(self):
        """Test StageMetricsDict can hold expected fields."""
        metrics: StageMetricsDict = {
            "stage_name": "test_stage",
            "duration": 1.5,
            "exit_code": 0,
            "memory_mb": 256.0,
        }
        assert metrics["stage_name"] == "test_stage"
        assert metrics["duration"] == 1.5
        assert metrics["exit_code"] == 0
