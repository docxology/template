"""Tests for infrastructure.core.pipeline._performance_monitor — expanded coverage."""

import pytest

from infrastructure.core.exceptions import BuildError
from infrastructure.core.pipeline._performance_monitor import (
    PerformanceMonitor,
    get_system_resources,
    performance_context,
)


class TestPerformanceMonitor:
    def test_start_stop_lifecycle(self):
        monitor = PerformanceMonitor()
        monitor.start()
        metrics = monitor.stop()
        assert metrics.duration >= 0
        assert metrics.operations_count == 0

    def test_stop_without_start_raises(self):
        monitor = PerformanceMonitor()
        with pytest.raises(BuildError, match="not started"):
            monitor.stop()

    def test_record_operations(self):
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.record_operation()
        monitor.record_operation()
        monitor.record_cache_hit()
        monitor.record_cache_miss()
        metrics = monitor.stop()
        assert metrics.operations_count == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1

    def test_update_memory(self):
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.update_memory()
        metrics = monitor.stop()
        assert metrics.resource_usage.peak_memory_mb >= 0

    def test_get_memory_usage(self):
        monitor = PerformanceMonitor()
        mem = monitor._get_memory_usage()
        # Should return a non-negative number (psutil available in this env)
        assert mem >= 0

    def test_get_cpu_percent(self):
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()
        assert cpu >= 0


class TestPerformanceContext:
    def test_basic(self):
        with performance_context("test_op") as monitor:
            assert isinstance(monitor, PerformanceMonitor)
            monitor.record_operation()
        assert monitor.last_metrics is not None
        assert monitor.last_metrics.operations_count == 1

    def test_with_exception(self):
        """Context manager should still stop monitor on exception."""
        with pytest.raises(ValueError, match="test"):
            with performance_context("failing_op") as monitor:
                raise ValueError("test")
        # Monitor should have captured metrics despite the exception
        assert monitor.last_metrics is not None


class TestGetSystemResources:
    def test_returns_dict(self):
        result = get_system_resources()
        # psutil should be available
        assert isinstance(result, dict)
        if result:  # psutil available
            assert "cpu_percent" in result
            assert "memory_total_gb" in result
            assert "memory_available_gb" in result
            assert "disk_total_gb" in result
            assert "process_memory_mb" in result
            assert result["memory_total_gb"] > 0
            assert result["disk_total_gb"] > 0
