"""Tests for infrastructure.core.pipeline._stage_tracker."""

import pytest

from infrastructure.core.exceptions import BuildError
from infrastructure.core.pipeline._stage_tracker import StagePerformanceTracker


class TestStagePerformanceTracker:
    """Tests for the StagePerformanceTracker class."""

    def test_init_defaults(self):
        t = StagePerformanceTracker()
        assert t.stages == []
        assert t.start_time is None

    def test_init_custom_thresholds(self):
        t = StagePerformanceTracker(
            slow_stage_multiplier=5.0,
            high_memory_mb=2000.0,
            high_cpu_percent=99.0,
        )
        assert t._slow_stage_multiplier == 5.0
        assert t._high_memory_mb == 2000.0
        assert t._high_cpu_percent == 99.0

    def test_start_stage_sets_start_time(self):
        t = StagePerformanceTracker()
        t.start_stage("test")
        assert t.start_time is not None

    def test_end_stage_without_start_raises(self):
        t = StagePerformanceTracker()
        with pytest.raises(BuildError, match="end_stage called without start_stage"):
            t.end_stage("test", 0)

    def test_start_end_stage_returns_metrics(self):
        t = StagePerformanceTracker()
        t.start_stage("build")
        metrics = t.end_stage("build", 0)
        assert metrics["stage_name"] == "build"
        assert metrics["exit_code"] == 0
        assert metrics["duration"] >= 0.0
        assert "memory_mb" in metrics
        assert "cpu_percent" in metrics
        assert "io_read_mb" in metrics
        assert "io_write_mb" in metrics

    def test_end_stage_resets_start_time(self):
        t = StagePerformanceTracker()
        t.start_stage("build")
        t.end_stage("build", 0)
        assert t.start_time is None

    def test_stages_list_accumulates(self):
        t = StagePerformanceTracker()
        t.start_stage("stage1")
        t.end_stage("stage1", 0)
        t.start_stage("stage2")
        t.end_stage("stage2", 1)
        assert len(t.stages) == 2
        assert t.stages[0]["stage_name"] == "stage1"
        assert t.stages[1]["stage_name"] == "stage2"
        assert t.stages[1]["exit_code"] == 1


class TestPerformanceWarnings:
    """Tests for get_performance_warnings."""

    def test_empty_stages_no_warnings(self):
        t = StagePerformanceTracker()
        assert t.get_performance_warnings() == []

    def test_slow_stage_warning(self):
        t = StagePerformanceTracker(slow_stage_multiplier=2.0)
        # Manually populate stages to control timing
        t.stages = [
            {"stage_name": "fast", "duration": 1.0, "memory_mb": 10, "cpu_percent": 10,
             "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
            {"stage_name": "fast2", "duration": 1.0, "memory_mb": 10, "cpu_percent": 10,
             "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
            {"stage_name": "slow", "duration": 10.0, "memory_mb": 10, "cpu_percent": 10,
             "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        warnings = t.get_performance_warnings()
        slow_warnings = [w for w in warnings if w["type"] == "slow_stage"]
        assert len(slow_warnings) == 1
        assert slow_warnings[0]["stage"] == "slow"

    def test_high_memory_warning(self):
        t = StagePerformanceTracker(high_memory_mb=100.0)
        t.stages = [
            {"stage_name": "mem_heavy", "duration": 1.0, "memory_mb": 200.0,
             "cpu_percent": 10, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        warnings = t.get_performance_warnings()
        mem_warnings = [w for w in warnings if w["type"] == "high_memory"]
        assert len(mem_warnings) == 1
        assert mem_warnings[0]["stage"] == "mem_heavy"

    def test_high_cpu_warning(self):
        t = StagePerformanceTracker(high_cpu_percent=50.0)
        t.stages = [
            {"stage_name": "cpu_heavy", "duration": 1.0, "memory_mb": 10,
             "cpu_percent": 80.0, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        warnings = t.get_performance_warnings()
        cpu_warnings = [w for w in warnings if w["type"] == "high_cpu"]
        assert len(cpu_warnings) == 1
        assert cpu_warnings[0]["stage"] == "cpu_heavy"

    def test_no_warnings_when_all_normal(self):
        t = StagePerformanceTracker(
            slow_stage_multiplier=2.0,
            high_memory_mb=1000.0,
            high_cpu_percent=95.0,
        )
        t.stages = [
            {"stage_name": "s1", "duration": 1.0, "memory_mb": 50,
             "cpu_percent": 30, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
            {"stage_name": "s2", "duration": 1.5, "memory_mb": 60,
             "cpu_percent": 40, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        warnings = t.get_performance_warnings()
        assert len(warnings) == 0


class TestGetSummary:
    """Tests for get_summary."""

    def test_empty_stages(self):
        t = StagePerformanceTracker()
        assert t.get_summary() == {}

    def test_summary_with_stages(self):
        t = StagePerformanceTracker()
        t.stages = [
            {"stage_name": "fast", "duration": 1.0, "memory_mb": 50,
             "cpu_percent": 20, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
            {"stage_name": "slow", "duration": 5.0, "memory_mb": 100,
             "cpu_percent": 40, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        summary = t.get_summary()
        assert summary["total_stages"] == 2
        assert summary["total_duration"] == 6.0
        assert summary["average_duration"] == 3.0
        assert summary["slowest_stage"]["stage_name"] == "slow"
        assert summary["fastest_stage"]["stage_name"] == "fast"
        assert summary["total_memory_mb"] == 150
        assert "warnings" in summary

    def test_summary_single_stage(self):
        t = StagePerformanceTracker()
        t.stages = [
            {"stage_name": "only", "duration": 2.0, "memory_mb": 75,
             "cpu_percent": 30, "exit_code": 0, "io_read_mb": 0, "io_write_mb": 0},
        ]
        summary = t.get_summary()
        assert summary["total_stages"] == 1
        assert summary["slowest_stage"]["stage_name"] == "only"
        assert summary["fastest_stage"]["stage_name"] == "only"
