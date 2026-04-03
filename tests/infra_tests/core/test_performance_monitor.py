"""Tests for infrastructure.core.pipeline._performance_monitor."""

import time

import pytest

from infrastructure.core.exceptions import BuildError
from infrastructure.core.pipeline._performance_monitor import (
    PerformanceMonitor,
    get_system_resources,
    performance_context,
)


class TestPerformanceMonitor:
    """Tests for the PerformanceMonitor class."""

    def test_init_defaults(self):
        m = PerformanceMonitor()
        assert m.start_time is None
        assert m.start_memory is None
        assert m.peak_memory == 0.0
        assert m.operations_count == 0
        assert m.cache_hits == 0
        assert m.cache_misses == 0
        assert m.last_metrics is None

    def test_start_sets_fields(self):
        m = PerformanceMonitor()
        m.start()
        assert m.start_time is not None
        assert isinstance(m.start_time, float)
        assert m.operations_count == 0
        assert m.cache_hits == 0

    def test_stop_without_start_raises(self):
        m = PerformanceMonitor()
        with pytest.raises(BuildError, match="Monitor not started"):
            m.stop()

    def test_start_stop_returns_metrics(self):
        m = PerformanceMonitor()
        m.start()
        time.sleep(0.01)
        metrics = m.stop()
        assert metrics.duration >= 0.0
        assert metrics.resource_usage is not None
        assert metrics.operations_count == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_record_operation(self):
        m = PerformanceMonitor()
        m.start()
        m.record_operation()
        m.record_operation()
        m.record_operation()
        metrics = m.stop()
        assert metrics.operations_count == 3

    def test_record_cache_hit(self):
        m = PerformanceMonitor()
        m.start()
        m.record_cache_hit()
        m.record_cache_hit()
        metrics = m.stop()
        assert metrics.cache_hits == 2

    def test_record_cache_miss(self):
        m = PerformanceMonitor()
        m.start()
        m.record_cache_miss()
        metrics = m.stop()
        assert metrics.cache_misses == 1

    def test_update_memory(self):
        m = PerformanceMonitor()
        m.start()
        m.update_memory()
        # peak_memory should be >= 0
        assert m.peak_memory >= 0.0
        m.stop()

    def test_get_memory_usage(self):
        m = PerformanceMonitor()
        mem = m._get_memory_usage()
        assert isinstance(mem, float)
        assert mem >= 0.0

    def test_get_cpu_percent(self):
        m = PerformanceMonitor()
        cpu = m._get_cpu_percent()
        assert isinstance(cpu, float)
        assert cpu >= 0.0


class TestPerformanceContext:
    """Tests for the performance_context context manager."""

    def test_basic_usage(self):
        with performance_context("test_op") as monitor:
            assert monitor.start_time is not None
            time.sleep(0.01)
        assert monitor.last_metrics is not None
        assert monitor.last_metrics.duration >= 0.0

    def test_records_operations_inside(self):
        with performance_context("test_op") as monitor:
            monitor.record_operation()
            monitor.record_cache_hit()
        assert monitor.last_metrics.operations_count == 1
        assert monitor.last_metrics.cache_hits == 1

    def test_exception_inside_still_records_metrics(self):
        with pytest.raises(ValueError, match="boom"):
            with performance_context("failing_op") as monitor:
                raise ValueError("boom")
        # Metrics should still be captured in finally block
        assert monitor.last_metrics is not None


class TestGetSystemResources:
    """Tests for the get_system_resources function."""

    def test_returns_dict(self):
        result = get_system_resources()
        assert isinstance(result, dict)

    def test_dict_keys_when_psutil_available(self):
        result = get_system_resources()
        # psutil should be available in this env
        if result:
            expected_keys = {
                "cpu_percent",
                "memory_total_gb",
                "memory_available_gb",
                "memory_percent",
                "process_memory_mb",
                "disk_total_gb",
                "disk_free_gb",
                "disk_percent",
            }
            assert expected_keys.issubset(set(result.keys()))
            # Verify types
            for key in expected_keys:
                assert isinstance(result[key], (int, float))
