"""Tests for infrastructure/core/pipeline/_performance_monitor.py.

Covers: PerformanceMonitor lifecycle, performance_context, get_system_resources.

No mocks used — all tests use real timing and real resource measurements.
"""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import BuildError
from infrastructure.core.pipeline._performance_monitor import (
    PerformanceMonitor,
    performance_context,
    get_system_resources,
)
from infrastructure.core.pipeline._monitor_types import PerformanceMetrics


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_start_and_stop(self):
        """Should start and stop, returning metrics."""
        monitor = PerformanceMonitor()
        monitor.start()
        metrics = monitor.stop()
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.duration >= 0
        assert metrics.operations_count == 0

    def test_stop_without_start_raises(self):
        """Should raise BuildError if stop called before start."""
        monitor = PerformanceMonitor()
        with pytest.raises(BuildError):
            monitor.stop()

    def test_record_operations(self):
        """Should track operation count."""
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.record_operation()
        monitor.record_operation()
        monitor.record_operation()
        metrics = monitor.stop()
        assert metrics.operations_count == 3

    def test_record_cache_hits_and_misses(self):
        """Should track cache hits and misses."""
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.record_cache_hit()
        monitor.record_cache_hit()
        monitor.record_cache_miss()
        metrics = monitor.stop()
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1

    def test_update_memory(self):
        """Should update peak memory."""
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.update_memory()
        metrics = monitor.stop()
        assert metrics.resource_usage.peak_memory_mb >= 0

    def test_memory_usage_returns_float(self):
        """_get_memory_usage should return a float."""
        monitor = PerformanceMonitor()
        mem = monitor._get_memory_usage()
        assert isinstance(mem, float)
        assert mem >= 0

    def test_cpu_percent_returns_float(self):
        """_get_cpu_percent should return a float."""
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()
        assert isinstance(cpu, float)
        assert cpu >= 0


class TestPerformanceContext:
    """Test performance_context context manager."""

    def test_basic_context(self):
        """Should work as context manager."""
        with performance_context("Test") as monitor:
            assert isinstance(monitor, PerformanceMonitor)
        assert monitor.last_metrics is not None
        assert monitor.last_metrics.duration >= 0

    def test_context_with_operations(self):
        """Should track operations within context."""
        with performance_context("Compute") as monitor:
            for _ in range(5):
                monitor.record_operation()
        assert monitor.last_metrics.operations_count == 5

    def test_context_with_exception(self):
        """Should still record metrics on exception."""
        with pytest.raises(ValueError):
            with performance_context("Failing") as monitor:
                raise ValueError("test")
        # last_metrics should still be set by the finally block
        assert monitor.last_metrics is not None


class TestGetSystemResources:
    """Test get_system_resources function."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_system_resources()
        assert isinstance(result, dict)

    def test_has_expected_keys_if_psutil_available(self):
        """If psutil is available, should have resource keys."""
        result = get_system_resources()
        if result:  # psutil is available
            assert "cpu_percent" in result
            assert "memory_total_gb" in result
            assert "process_memory_mb" in result
            assert "disk_total_gb" in result

    def test_resource_values_are_numeric(self):
        """All resource values should be numeric."""
        result = get_system_resources()
        for key, value in result.items():
            assert isinstance(value, (int, float)), f"{key} is not numeric: {type(value)}"

    def test_memory_gb_positive(self):
        """Memory values should be positive."""
        result = get_system_resources()
        if result:
            assert result["memory_total_gb"] > 0
            assert result["memory_available_gb"] > 0

    def test_disk_values_present(self):
        """Disk values should be present and positive."""
        result = get_system_resources()
        if result:
            assert result["disk_total_gb"] > 0
            assert result["disk_free_gb"] >= 0
            assert 0 <= result["disk_percent"] <= 100


class TestPerformanceMonitorMemoryTracking:
    """Test memory tracking paths."""

    def test_update_memory_increases_peak(self):
        """update_memory should track peak memory."""
        monitor = PerformanceMonitor()
        monitor.start()
        # Allocate some memory to potentially increase peak
        data = [0] * 100000
        monitor.update_memory()
        assert monitor.peak_memory >= 0
        del data

    def test_update_memory_preserves_peak_when_lower(self):
        """Peak memory should not decrease."""
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.peak_memory = 999999.0  # Set artificially high
        monitor.update_memory()
        # Peak should stay at the artificially high value
        assert monitor.peak_memory == 999999.0

    def test_memory_usage_with_psutil(self):
        """_get_memory_usage should return positive value when psutil available."""
        from infrastructure.core._optional_deps import psutil as _psutil
        monitor = PerformanceMonitor()
        mem = monitor._get_memory_usage()
        if _psutil is not None:
            assert mem > 0
        else:
            assert mem == 0.0

    def test_cpu_percent_with_psutil(self):
        """_get_cpu_percent should return non-negative value."""
        from infrastructure.core._optional_deps import psutil as _psutil
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()
        if _psutil is not None:
            assert cpu >= 0
        else:
            assert cpu == 0.0
