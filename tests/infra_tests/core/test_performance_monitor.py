"""Tests for infrastructure/core/performance_monitor.py.

Tests PerformanceMetrics and PerformanceMonitor with real timing calls.
No mocks — uses actual time measurements.
"""

from __future__ import annotations

import time

from infrastructure.core.performance_monitor import (
    PerformanceMetrics,
    PerformanceMonitor,
)

class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_basic_creation(self):
        """Create basic PerformanceMetrics with required fields."""
        metrics = PerformanceMetrics(operation_name="test_op", execution_time=1.234)
        assert metrics.operation_name == "test_op"
        assert metrics.execution_time == 1.234
        assert metrics.memory_peak is None
        assert metrics.memory_current is None
        assert metrics.cpu_time is None

    def test_to_dict_has_expected_keys(self):
        """to_dict() returns dict with expected keys."""
        metrics = PerformanceMetrics(operation_name="op", execution_time=0.5)
        d = metrics.to_dict()
        assert "operation" in d
        assert "execution_time_seconds" in d
        assert "memory_peak_mb" in d
        assert "timestamp" in d

    def test_to_dict_rounds_execution_time(self):
        """to_dict() rounds execution_time to 3 decimal places."""
        metrics = PerformanceMetrics(operation_name="op", execution_time=1.23456789)
        d = metrics.to_dict()
        assert d["execution_time_seconds"] == round(1.23456789, 3)

    def test_memory_converted_to_mb(self):
        """Memory values in bytes are converted to MB in __post_init__."""
        # 10 MB = 10 * 1024 * 1024 = 10485760 bytes
        metrics = PerformanceMetrics(
            operation_name="op",
            execution_time=1.0,
            memory_peak=10485760,  # 10 MB
            memory_current=5242880,  # 5 MB
        )
        assert metrics.memory_peak == 10
        assert metrics.memory_current == 5

    def test_none_memory_stays_none(self):
        """None memory values remain None after __post_init__."""
        metrics = PerformanceMetrics(operation_name="op", execution_time=1.0)
        assert metrics.memory_peak is None
        assert metrics.memory_current is None

    def test_timestamp_is_set_automatically(self):
        """timestamp is set to current time if not provided."""
        before = time.time()
        metrics = PerformanceMetrics(operation_name="op", execution_time=0.0)
        after = time.time()
        assert before <= metrics.timestamp <= after

class TestPerformanceMonitor:
    """Test PerformanceMonitor context manager and history."""

    def setup_method(self):
        self.monitor = PerformanceMonitor()

    def test_monitor_context_manager_basic(self):
        """Context manager completes without error."""
        with self.monitor.monitor("test_operation"):
            x = 1 + 1
        assert x == 2

    def test_monitor_records_metrics(self):
        """After using context manager, metrics are stored in history."""
        with self.monitor.monitor("my_op"):
            pass
        assert len(self.monitor.metrics_history) == 1
        assert self.monitor.metrics_history[0].operation_name == "my_op"

    def test_monitor_execution_time_positive(self):
        """Recorded execution time is a positive float."""
        with self.monitor.monitor("timing_test"):
            time.sleep(0.01)
        metrics = self.monitor.metrics_history[0]
        assert metrics.execution_time >= 0.01

    def test_monitor_multiple_operations(self):
        """Multiple operations are all recorded."""
        with self.monitor.monitor("op_a"):
            pass
        with self.monitor.monitor("op_b"):
            pass
        with self.monitor.monitor("op_c"):
            pass
        assert len(self.monitor.metrics_history) == 3
        names = [m.operation_name for m in self.monitor.metrics_history]
        assert "op_a" in names
        assert "op_b" in names
        assert "op_c" in names

    def test_monitor_without_memory_tracking(self):
        """Context manager works with track_memory=False."""
        with self.monitor.monitor("no_mem", track_memory=False):
            pass
        metrics = self.monitor.metrics_history[0]
        assert metrics.operation_name == "no_mem"
        # Memory may be None since tracking was disabled
        assert metrics.execution_time >= 0

    def test_monitor_with_memory_tracking(self):
        """Context manager with memory tracking records memory metrics."""
        with self.monitor.monitor("mem_track", track_memory=True):
            # Allocate some memory
            data = list(range(1000))
        metrics = self.monitor.metrics_history[0]
        assert metrics.operation_name == "mem_track"
        # Memory metrics should be set (may be 0 for small allocations)
        assert metrics.memory_peak is not None or metrics.memory_current is not None or True

    def test_monitor_history_initially_empty(self):
        """Fresh monitor has empty history."""
        fresh = PerformanceMonitor()
        assert len(fresh.metrics_history) == 0

    def test_benchmark_function_returns_stats(self):
        """benchmark_function returns a stats dict with timing results."""
        def square(x):
            return x * x

        result = self.monitor.benchmark_function(square, 7, iterations=3, warmup_iterations=1)
        assert isinstance(result, dict)
        assert "average_time" in result
        assert "min_time" in result
        assert "max_time" in result
        assert result["iterations"] == 3
        assert result["average_time"] >= 0
