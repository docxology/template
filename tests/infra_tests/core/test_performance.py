"""Tests for infrastructure.core.performance module.

Comprehensive tests for performance monitoring and resource tracking utilities.
"""

import time

import pytest

from infrastructure.core.performance import (PerformanceMetrics,
                                             PerformanceMonitor, ResourceUsage,
                                             StagePerformanceTracker,
                                             get_system_resources,
                                             monitor_performance)

# Check if psutil is available for conditional testing
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class TestResourceUsage:
    """Test ResourceUsage dataclass."""

    def test_resource_usage_creation(self):
        """Test creating a ResourceUsage instance."""
        usage = ResourceUsage(
            cpu_percent=50.5,
            memory_mb=1024.0,
            peak_memory_mb=2048.0,
            io_read_mb=100.0,
            io_write_mb=50.0,
        )

        assert usage.cpu_percent == 50.5
        assert usage.memory_mb == 1024.0
        assert usage.peak_memory_mb == 2048.0
        assert usage.io_read_mb == 100.0
        assert usage.io_write_mb == 50.0

    def test_resource_usage_defaults(self):
        """Test ResourceUsage with default values."""
        usage = ResourceUsage()

        assert usage.cpu_percent == 0.0
        assert usage.memory_mb == 0.0
        assert usage.peak_memory_mb == 0.0
        assert usage.io_read_mb == 0.0
        assert usage.io_write_mb == 0.0

    def test_resource_usage_to_dict(self):
        """Test converting ResourceUsage to dictionary."""
        usage = ResourceUsage(
            cpu_percent=75.0,
            memory_mb=512.0,
            peak_memory_mb=768.0,
            io_read_mb=200.0,
            io_write_mb=100.0,
        )

        data = usage.to_dict()

        assert isinstance(data, dict)
        assert data["cpu_percent"] == 75.0
        assert data["memory_mb"] == 512.0
        assert data["peak_memory_mb"] == 768.0
        assert data["io_read_mb"] == 200.0
        assert data["io_write_mb"] == 100.0


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating a PerformanceMetrics instance."""
        resource_usage = ResourceUsage(cpu_percent=50.0, memory_mb=1024.0)
        metrics = PerformanceMetrics(
            duration=10.5,
            resource_usage=resource_usage,
            operations_count=100,
            cache_hits=80,
            cache_misses=20,
        )

        assert metrics.duration == 10.5
        assert metrics.resource_usage == resource_usage
        assert metrics.operations_count == 100
        assert metrics.cache_hits == 80
        assert metrics.cache_misses == 20

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metrics = PerformanceMetrics(duration=5.0)

        assert metrics.duration == 5.0
        assert isinstance(metrics.resource_usage, ResourceUsage)
        assert metrics.operations_count == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_performance_metrics_to_dict(self):
        """Test converting PerformanceMetrics to dictionary."""
        resource_usage = ResourceUsage(cpu_percent=60.0, memory_mb=512.0)
        metrics = PerformanceMetrics(
            duration=15.0,
            resource_usage=resource_usage,
            operations_count=50,
            cache_hits=40,
            cache_misses=10,
        )

        data = metrics.to_dict()

        assert isinstance(data, dict)
        assert data["duration"] == 15.0
        assert isinstance(data["resource_usage"], dict)
        assert data["operations_count"] == 50
        assert data["cache_hits"] == 40
        assert data["cache_misses"] == 10


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()

        assert monitor.start_time is None
        assert monitor.start_memory is None
        assert monitor.peak_memory == 0.0
        assert monitor.operations_count == 0
        assert monitor.cache_hits == 0
        assert monitor.cache_misses == 0

    def test_performance_monitor_start_stop(self):
        """Test starting and stopping monitor."""
        monitor = PerformanceMonitor()
        monitor.start()

        assert monitor.start_time is not None
        # Memory and CPU values will be real system values (may be 0 if psutil not available)
        assert isinstance(monitor.start_memory, float)
        assert isinstance(monitor.peak_memory, float)

        time.sleep(0.01)  # Small delay to ensure duration > 0

        metrics = monitor.stop()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.duration > 0
        assert isinstance(metrics.resource_usage.memory_mb, float)
        assert isinstance(metrics.resource_usage.cpu_percent, float)

    def test_performance_monitor_stop_without_start(self):
        """Test stopping monitor without starting raises error."""
        monitor = PerformanceMonitor()

        with pytest.raises(RuntimeError, match="not started"):
            monitor.stop()

    def test_performance_monitor_record_operation(self):
        """Test recording operations."""
        monitor = PerformanceMonitor()
        monitor.start()

        monitor.record_operation()
        monitor.record_operation()
        monitor.record_operation()

        assert monitor.operations_count == 3

        metrics = monitor.stop()
        assert metrics.operations_count == 3

    def test_performance_monitor_record_cache(self):
        """Test recording cache hits and misses."""
        monitor = PerformanceMonitor()
        monitor.start()

        monitor.record_cache_hit()
        monitor.record_cache_hit()
        monitor.record_cache_miss()

        assert monitor.cache_hits == 2
        assert monitor.cache_misses == 1

        metrics = monitor.stop()
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1

    def test_performance_monitor_update_memory(self):
        """Test updating peak memory tracking."""
        monitor = PerformanceMonitor()
        monitor.start()

        initial_memory = monitor.peak_memory
        assert isinstance(initial_memory, float)

        monitor.update_memory()
        # Memory should be updated (may be same or different based on real system)
        assert isinstance(monitor.peak_memory, float)
        assert monitor.peak_memory >= initial_memory  # Should not decrease

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_get_memory_usage_with_psutil(self):
        """Test getting memory usage when psutil is available."""
        monitor = PerformanceMonitor()
        memory = monitor._get_memory_usage()

        # Should return a real memory value (not 0.0)
        assert isinstance(memory, float)
        assert memory >= 0.0

    def test_get_memory_usage_without_psutil(self):
        """Test getting memory usage fallback when psutil is not available."""
        if HAS_PSUTIL:
            pytest.skip("psutil is available - cannot test fallback")

        monitor = PerformanceMonitor()
        memory = monitor._get_memory_usage()

        # Should return fallback value when psutil unavailable
        assert memory == 0.0

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_get_cpu_percent_with_psutil(self):
        """Test getting CPU percent when psutil is available."""
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()

        # Should return a real CPU percentage value
        assert isinstance(cpu, float)
        assert 0.0 <= cpu <= 100.0

    def test_get_cpu_percent_without_psutil(self):
        """Test getting CPU percent fallback when psutil is not available."""
        if HAS_PSUTIL:
            pytest.skip("psutil is available - cannot test fallback")

        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()

        # Should return fallback value when psutil unavailable
        assert cpu == 0.0


class TestMonitorPerformance:
    """Test monitor_performance context manager."""

    def test_monitor_performance_context_manager(self):
        """Test using monitor_performance as context manager."""
        with monitor_performance("Test Operation") as monitor:
            assert isinstance(monitor, PerformanceMonitor)
            assert monitor.start_time is not None
            monitor.record_operation()
            time.sleep(0.01)  # Very short sleep to ensure duration > 0

        # Context manager should have stopped the monitor
        # Note: start_time is still set but stop() was called
        assert monitor.start_time is not None

    def test_monitor_performance_with_operations(self):
        """Test monitoring performance with recorded operations."""
        with monitor_performance("Data Processing") as monitor:
            for i in range(5):
                monitor.record_operation()
                if i % 2 == 0:
                    monitor.record_cache_hit()
                else:
                    monitor.record_cache_miss()

        # Operations should be recorded
        assert monitor.operations_count == 5
        assert monitor.cache_hits == 3
        assert monitor.cache_misses == 2


class TestGetSystemResources:
    """Test get_system_resources function."""

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_get_system_resources_with_psutil(self):
        """Test getting system resources when psutil is available."""
        resources = get_system_resources()

        assert isinstance(resources, dict)
        # Should contain real system resource data
        expected_keys = [
            "cpu_percent",
            "memory_total_gb",
            "memory_available_gb",
            "memory_percent",
            "process_memory_mb",
            "disk_total_gb",
            "disk_free_gb",
            "disk_percent",
        ]
        for key in expected_keys:
            assert key in resources
            assert isinstance(resources[key], (int, float))

        # Reasonable bounds checks
        assert 0.0 <= resources["cpu_percent"] <= 100.0
        assert resources["memory_total_gb"] > 0
        assert resources["memory_available_gb"] >= 0
        assert 0.0 <= resources["memory_percent"] <= 100.0
        assert resources["process_memory_mb"] >= 0
        assert resources["disk_total_gb"] > 0
        assert resources["disk_free_gb"] >= 0

    def test_get_system_resources_without_psutil(self):
        """Test getting system resources when psutil is not available."""
        if HAS_PSUTIL:
            pytest.skip("psutil is available - cannot test fallback")

        resources = get_system_resources()

        assert isinstance(resources, dict)
        assert len(resources) == 0  # Should return empty dict when psutil unavailable


class TestStagePerformanceTracker:
    """Test StagePerformanceTracker class."""

    def test_stage_performance_tracker_initialization(self):
        """Test StagePerformanceTracker initialization."""
        tracker = StagePerformanceTracker()

        assert tracker.stages == []
        assert tracker.start_time is None

    def test_start_stage(self):
        """Test starting stage tracking."""
        tracker = StagePerformanceTracker()
        tracker.start_stage("test_stage")

        assert tracker.start_time is not None
        # start_memory will be set based on psutil availability
        assert isinstance(tracker.start_memory, float)

    def test_end_stage(self):
        """Test ending stage tracking."""
        tracker = StagePerformanceTracker()
        tracker.start_stage("test_stage")
        time.sleep(0.01)  # Very short sleep to ensure duration > 0

        metrics = tracker.end_stage("test_stage", exit_code=0)

        assert isinstance(metrics, dict)
        assert metrics["stage_name"] == "test_stage"
        assert metrics["duration"] > 0
        assert metrics["exit_code"] == 0
        assert len(tracker.stages) == 1

        # Check that metrics contain expected keys
        expected_keys = [
            "stage_name",
            "duration",
            "exit_code",
            "memory_mb",
            "peak_memory_mb",
            "cpu_percent",
        ]
        for key in expected_keys:
            assert key in metrics
            if key != "stage_name":
                assert isinstance(metrics[key], (int, float))

    def test_end_stage_without_start(self):
        """Test ending stage without starting returns empty dict."""
        tracker = StagePerformanceTracker()

        metrics = tracker.end_stage("test_stage", exit_code=0)

        assert metrics == {}
        assert len(tracker.stages) == 0

    def test_get_performance_warnings_no_stages(self):
        """Test getting warnings when no stages tracked."""
        tracker = StagePerformanceTracker()

        warnings = tracker.get_performance_warnings()

        assert warnings == []

    def test_get_performance_warnings_slow_stage(self):
        """Test getting warnings for slow stages."""
        tracker = StagePerformanceTracker()

        # Add stages with varying durations
        # Average = (1.0 + 5.0 + 2.0) / 3 = 2.67
        # Slow stage (5.0) is > 2 * 2.67 = 5.34? No, it's 5.0 which is < 5.34
        # Let's make it more clearly slow: 10.0 > 2 * 2.67 = 5.34
        tracker.stages = [
            {
                "stage_name": "fast",
                "duration": 1.0,
                "peak_memory_mb": 100,
                "cpu_percent": 50,
            },
            {
                "stage_name": "slow",
                "duration": 10.0,
                "peak_memory_mb": 100,
                "cpu_percent": 50,
            },
            {
                "stage_name": "medium",
                "duration": 2.0,
                "peak_memory_mb": 100,
                "cpu_percent": 50,
            },
        ]

        warnings = tracker.get_performance_warnings()

        # Should warn about slow stage (10.0 > 2x average of ~4.33 = 8.67)
        assert len(warnings) > 0
        assert any(w["type"] == "slow_stage" for w in warnings)

    def test_get_performance_warnings_high_memory(self):
        """Test getting warnings for high memory usage."""
        tracker = StagePerformanceTracker()

        tracker.stages = [
            {
                "stage_name": "high_mem",
                "duration": 1.0,
                "peak_memory_mb": 2048,
                "cpu_percent": 50,
            },
        ]

        warnings = tracker.get_performance_warnings()

        assert len(warnings) > 0
        assert any(w["type"] == "high_memory" for w in warnings)

    def test_get_performance_warnings_high_cpu(self):
        """Test getting warnings for high CPU usage."""
        tracker = StagePerformanceTracker()

        tracker.stages = [
            {
                "stage_name": "high_cpu",
                "duration": 1.0,
                "peak_memory_mb": 100,
                "cpu_percent": 95,
            },
        ]

        warnings = tracker.get_performance_warnings()

        assert len(warnings) > 0
        assert any(w["type"] == "high_cpu" for w in warnings)

    def test_get_summary(self):
        """Test getting performance summary."""
        tracker = StagePerformanceTracker()

        tracker.stages = [
            {
                "stage_name": "stage1",
                "duration": 1.0,
                "memory_mb": 100,
                "peak_memory_mb": 150,
            },
            {
                "stage_name": "stage2",
                "duration": 2.0,
                "memory_mb": 200,
                "peak_memory_mb": 250,
            },
            {
                "stage_name": "stage3",
                "duration": 3.0,
                "memory_mb": 300,
                "peak_memory_mb": 350,
            },
        ]

        summary = tracker.get_summary()

        assert isinstance(summary, dict)
        assert summary["total_stages"] == 3
        assert summary["total_duration"] == 6.0
        assert summary["average_duration"] == 2.0
        assert summary["slowest_stage"]["stage_name"] == "stage3"
        assert summary["fastest_stage"]["stage_name"] == "stage1"
        assert summary["peak_memory_mb"] == 350

    def test_get_summary_empty(self):
        """Test getting summary when no stages tracked."""
        tracker = StagePerformanceTracker()

        summary = tracker.get_summary()

        assert summary == {}
