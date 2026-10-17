"""Tests for infrastructure.core.runtime.function_profiler."""

import time
import tracemalloc
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.runtime.function_profiler import (
    CodeProfiler,
    ProfilingMetrics,
    _bytes_to_mb,
    get_code_profiler,
    monitor_performance,
    profile_memory_usage,
)


class TestBytesToMb:
    def test_none_returns_none(self):
        assert _bytes_to_mb(None) is None

    def test_zero(self):
        assert _bytes_to_mb(0) == 0.0

    def test_one_mb(self):
        assert abs(_bytes_to_mb(1024 * 1024) - 1.0) < 1e-6

    def test_fractional(self):
        result = _bytes_to_mb(512 * 1024)
        assert abs(result - 0.5) < 1e-6


class TestProfilingMetrics:
    def test_basic_creation(self):
        m = ProfilingMetrics(operation_name="test", execution_time=1.5)
        assert m.operation_name == "test"
        assert m.execution_time == 1.5
        assert m.memory_peak is None
        assert m.memory_current is None
        assert m.memory_delta is None
        assert m.cpu_time is None
        assert m.function_calls is None

    def test_to_dict(self):
        m = ProfilingMetrics(
            operation_name="op1",
            execution_time=2.0,
            memory_peak=1024 * 1024 * 10,
            memory_current=1024 * 1024 * 5,
            memory_delta=1024 * 1024 * 3,
            cpu_time=1.5,
            function_calls=42,
        )
        d = m.to_dict()
        assert d["operation"] == "op1"
        assert d["execution_time_seconds"] == 2.0
        assert abs(d["memory_peak_mb"] - 10.0) < 1e-6
        assert abs(d["memory_current_mb"] - 5.0) < 1e-6
        assert abs(d["memory_delta_mb"] - 3.0) < 1e-6
        assert d["cpu_time_seconds"] == 1.5
        assert d["function_calls"] == 42
        assert "timestamp" in d

    def test_to_dict_none_memory(self):
        m = ProfilingMetrics(operation_name="op", execution_time=0.1)
        d = m.to_dict()
        assert d["memory_peak_mb"] is None
        assert d["memory_current_mb"] is None
        assert d["memory_delta_mb"] is None


class TestCodeProfiler:
    def test_init_empty_history(self):
        p = CodeProfiler()
        assert p.metrics_history == []

    def test_monitor_context_manager(self):
        p = CodeProfiler()
        with p.monitor("test_op"):
            sum(range(1000))
        assert len(p.metrics_history) == 1
        m = p.metrics_history[0]
        assert m.operation_name == "test_op"
        assert m.execution_time >= 0.0
        assert m.cpu_time is not None

    def test_monitor_with_memory_tracking(self):
        p = CodeProfiler()
        with p.monitor("mem_op", track_memory=True):
            [i for i in range(10000)]
        m = p.metrics_history[0]
        # memory_current and memory_peak should be set
        assert m.memory_current is not None
        assert m.memory_peak is not None

    def test_monitor_without_memory_tracking(self):
        p = CodeProfiler()
        with p.monitor("no_mem", track_memory=False):
            pass
        m = p.metrics_history[0]
        assert m.memory_current is None
        assert m.memory_peak is None

    def test_profile_function(self):
        p = CodeProfiler()

        def add(a, b):
            return a + b

        result = p.profile_function(add, 3, 7)
        assert result == 10

    def test_benchmark_function(self):
        p = CodeProfiler()

        def noop():
            return 42

        result = p.benchmark_function(noop, iterations=3, warmup_iterations=1)
        assert result["function_name"] == "noop"
        assert result["iterations"] == 3
        assert len(result["all_times"]) == 3
        assert result["average_time"] >= 0
        assert result["min_time"] <= result["average_time"]
        assert result["max_time"] >= result["average_time"]
        assert result["std_dev"] >= 0

    def test_get_recent_metrics(self):
        p = CodeProfiler()
        for i in range(15):
            with p.monitor(f"op_{i}"):
                pass
        recent = p.get_recent_metrics(limit=5)
        assert len(recent) == 5
        assert recent[-1].operation_name == "op_14"

    def test_get_recent_metrics_less_than_limit(self):
        p = CodeProfiler()
        with p.monitor("only_op"):
            pass
        recent = p.get_recent_metrics(limit=10)
        assert len(recent) == 1

    def test_clear_metrics_history(self):
        p = CodeProfiler()
        with p.monitor("op"):
            pass
        assert len(p.metrics_history) == 1
        p.clear_metrics_history()
        assert len(p.metrics_history) == 0

    def test_generate_performance_report_empty(self):
        p = CodeProfiler()
        report = p.generate_performance_report()
        assert report == "No performance metrics available."

    def test_generate_performance_report_with_data(self):
        p = CodeProfiler()
        with p.monitor("op1", track_memory=True):
            _ = list(range(100))
        with p.monitor("op2", track_memory=False):
            pass
        report = p.generate_performance_report()
        assert "# Performance Report" in report
        assert "op1" in report
        assert "op2" in report
        assert "Total operations monitored: 2" in report
        assert "Total execution time" in report

    def test_monitor_retains_original_exception_and_external_tracing(self):
        profiler = CodeProfiler()
        error = RuntimeError("actual monitored failure")
        already_tracing = tracemalloc.is_tracing()
        if not already_tracing:
            tracemalloc.start()
        before = time.perf_counter()
        try:
            with pytest.raises(RuntimeError) as raised:
                with profiler.monitor("failed real operation"):
                    time.sleep(0.01)
                    raise error
            elapsed = time.perf_counter() - before
            assert raised.value is error
            assert tracemalloc.is_tracing(), "the caller retains ownership of its tracing session"
            assert len(profiler.metrics_history) == 1
            metric = profiler.metrics_history[0]
            assert 0.01 <= metric.execution_time <= elapsed
            assert metric.memory_peak is not None
        finally:
            if not already_tracing:
                tracemalloc.stop()

    def test_monitor_closes_owned_tracing_after_failure(self):
        # A fresh isolated interpreter owns no caller's existing trace session.
        program = """
import sys
sys.path.insert(0, sys.argv[1])
import tracemalloc
from infrastructure.core.runtime.function_profiler import CodeProfiler
assert not tracemalloc.is_tracing()
profiler = CodeProfiler()
error = ValueError("actual monitored failure")
try:
    with profiler.monitor("owned tracing"):
        assert tracemalloc.is_tracing()
        raise error
except ValueError as observed:
    assert observed is error
else:
    raise AssertionError("the monitored exception was swallowed")
assert not tracemalloc.is_tracing()
assert len(profiler.metrics_history) == 1
"""
        observed = subprocess.run(
            [sys.executable, "-I", "-c", program, str(Path(__file__).resolve().parents[3])],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert observed.returncode == 0, observed.stderr

    @pytest.mark.parametrize("iterations", (0, -1, True, False, 1.5, "3", None))
    def test_invalid_iterations_refuse_before_warmup(self, iterations):
        calls = []
        with pytest.raises(ValueError, match="iterations must be a positive integer"):
            CodeProfiler().benchmark_function(lambda: calls.append("ran"), iterations=iterations)
        assert calls == []

    @pytest.mark.parametrize("warmup", (-1, True, False, 1.5, "2", None))
    def test_invalid_warmup_refuses_before_execution(self, warmup):
        calls = []
        with pytest.raises(ValueError, match="warmup_iterations must be a nonnegative integer"):
            CodeProfiler().benchmark_function(lambda: calls.append("ran"), warmup_iterations=warmup)
        assert calls == []

    def test_benchmark_runs_exact_declared_count_with_zero_warmup(self):
        calls = []
        result = CodeProfiler().benchmark_function(
            lambda value: calls.append(value), 7, iterations=3, warmup_iterations=0
        )
        assert calls == [7, 7, 7]
        assert len(result["all_times"]) == 3

    def test_benchmark_preserves_exception_and_stops_later_iterations(self):
        calls = []
        error = RuntimeError("actual benchmark failure")

        def failing():
            calls.append("ran")
            raise error

        with pytest.raises(RuntimeError) as raised:
            CodeProfiler().benchmark_function(failing, iterations=3, warmup_iterations=0)
        assert raised.value is error
        assert calls == ["ran"]

    @pytest.mark.parametrize("limit", (-1, True, False, 1.5, "2", None))
    def test_invalid_recent_limit_refused(self, limit):
        with pytest.raises(ValueError, match="limit must be a nonnegative integer"):
            CodeProfiler().get_recent_metrics(limit)

    def test_zero_recent_limit_returns_no_metrics_without_clearing_history(self):
        profiler = CodeProfiler()
        with profiler.monitor("retained", track_memory=False):
            sum(range(10))
        assert profiler.get_recent_metrics(0) == []
        assert profiler.get_recent_metrics(1) == profiler.metrics_history

    def test_report_converts_bytes_and_distinguishes_zero_from_unmeasured(self):
        profiler = CodeProfiler()
        profiler.metrics_history.extend(
            [
                ProfilingMetrics("allocated", 0.1, memory_peak=1536 * 1024),
                ProfilingMetrics("zero", 0.2, memory_peak=0),
                ProfilingMetrics("unmeasured", 0.3),
            ]
        )
        report = profiler.generate_performance_report()
        assert "Peak memory usage: 1.50 MB" in report
        assert "| allocated | 0.100 | 1.50 |" in report
        assert "| zero | 0.200 | 0.00 |" in report
        assert "| unmeasured | 0.300 | N/A |" in report
        profiler.metrics_history[:] = [ProfilingMetrics("zero", 0.2, memory_peak=0)]
        assert "Peak memory usage: 0.00 MB" in profiler.generate_performance_report()


class TestGetCodeProfiler:
    def test_returns_same_instance(self):
        # Clear the cache first to make this test independent
        get_code_profiler.cache_clear()
        p1 = get_code_profiler()
        p2 = get_code_profiler()
        assert p1 is p2
        get_code_profiler.cache_clear()


class TestMonitorPerformance:
    def test_decorator(self):
        get_code_profiler.cache_clear()

        @monitor_performance("decorated_op")
        def my_func(x):
            return x * 2

        result = my_func(5)
        assert result == 10
        profiler = get_code_profiler()
        assert any(m.operation_name == "decorated_op" for m in profiler.metrics_history)
        get_code_profiler.cache_clear()


class TestProfileMemoryUsage:
    def test_basic(self):
        get_code_profiler.cache_clear()

        def compute():
            return sum(range(1000))

        result = profile_memory_usage(compute)
        assert result["result"] == sum(range(1000))
        assert "execution_time" in result
        assert "memory_current" in result
        assert "memory_peak" in result
        get_code_profiler.cache_clear()
