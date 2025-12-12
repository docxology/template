"""Tests for infrastructure.core.performance module.

Comprehensive tests for performance monitoring and resource tracking utilities.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from builtins import __import__ as original_import

from infrastructure.core.performance import (
    ResourceUsage,
    PerformanceMetrics,
    PerformanceMonitor,
    monitor_performance,
    get_system_resources,
    StagePerformanceTracker,
)


class TestResourceUsage:
    """Test ResourceUsage dataclass."""

    def test_resource_usage_creation(self):
        """Test creating a ResourceUsage instance."""
        usage = ResourceUsage(
            cpu_percent=50.5,
            memory_mb=1024.0,
            peak_memory_mb=2048.0,
            io_read_mb=100.0,
            io_write_mb=50.0
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
            io_write_mb=100.0
        )
        
        data = usage.to_dict()
        
        assert isinstance(data, dict)
        assert data['cpu_percent'] == 75.0
        assert data['memory_mb'] == 512.0
        assert data['peak_memory_mb'] == 768.0
        assert data['io_read_mb'] == 200.0
        assert data['io_write_mb'] == 100.0


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
            cache_misses=20
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
            cache_misses=10
        )
        
        data = metrics.to_dict()
        
        assert isinstance(data, dict)
        assert data['duration'] == 15.0
        assert isinstance(data['resource_usage'], dict)
        assert data['operations_count'] == 50
        assert data['cache_hits'] == 40
        assert data['cache_misses'] == 10


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

    @patch('infrastructure.core.performance.PerformanceMonitor._get_memory_usage')
    @patch('infrastructure.core.performance.PerformanceMonitor._get_cpu_percent')
    def test_performance_monitor_start_stop(self, mock_cpu, mock_memory):
        """Test starting and stopping monitor."""
        mock_memory.return_value = 100.0
        mock_cpu.return_value = 25.0
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        assert monitor.start_time is not None
        assert monitor.start_memory == 100.0
        assert monitor.peak_memory == 100.0
        
        time.sleep(0.1)  # Small delay to ensure duration > 0
        
        metrics = monitor.stop()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.duration > 0
        assert metrics.resource_usage.memory_mb == 100.0
        assert metrics.resource_usage.cpu_percent == 25.0

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

    @patch('infrastructure.core.performance.PerformanceMonitor._get_memory_usage')
    def test_performance_monitor_update_memory(self, mock_memory):
        """Test updating peak memory tracking."""
        mock_memory.side_effect = [100.0, 150.0, 200.0, 180.0]
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        assert monitor.peak_memory == 100.0
        
        monitor.update_memory()
        assert monitor.peak_memory == 150.0
        
        monitor.update_memory()
        assert monitor.peak_memory == 200.0
        
        monitor.update_memory()
        # Should not decrease
        assert monitor.peak_memory == 200.0

    @patch('builtins.__import__')
    def test_get_memory_usage_with_psutil(self, mock_import):
        """Test getting memory usage when psutil is available."""
        # Create mock psutil module
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 512  # 512 MB
        mock_psutil.Process.return_value = mock_process
        
        # Make __import__ return mock_psutil when psutil is imported
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        monitor = PerformanceMonitor()
        memory = monitor._get_memory_usage()
        
        assert memory == 512.0

    @patch('builtins.__import__')
    def test_get_memory_usage_without_psutil(self, mock_import):
        """Test getting memory usage when psutil is not available."""
        # Make __import__ raise ImportError for psutil
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        monitor = PerformanceMonitor()
        memory = monitor._get_memory_usage()
        
        assert memory == 0.0

    @patch('builtins.__import__')
    def test_get_cpu_percent_with_psutil(self, mock_import):
        """Test getting CPU percent when psutil is available."""
        # Create mock psutil module
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.cpu_percent.return_value = 75.5
        mock_psutil.Process.return_value = mock_process
        
        # Make __import__ return mock_psutil when psutil is imported
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()
        
        assert cpu == 75.5

    @patch('builtins.__import__')
    def test_get_cpu_percent_without_psutil(self, mock_import):
        """Test getting CPU percent when psutil is not available."""
        # Make __import__ raise ImportError for psutil
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        monitor = PerformanceMonitor()
        cpu = monitor._get_cpu_percent()
        
        assert cpu == 0.0


class TestMonitorPerformance:
    """Test monitor_performance context manager."""

    @patch('infrastructure.core.performance.PerformanceMonitor._get_memory_usage')
    @patch('infrastructure.core.performance.PerformanceMonitor._get_cpu_percent')
    def test_monitor_performance_context_manager(self, mock_cpu, mock_memory):
        """Test using monitor_performance as context manager."""
        mock_memory.return_value = 100.0
        mock_cpu.return_value = 30.0
        
        with monitor_performance("Test Operation") as monitor:
            assert isinstance(monitor, PerformanceMonitor)
            assert monitor.start_time is not None
            monitor.record_operation()
            time.sleep(0.1)
        
        # Context manager should have stopped the monitor
        assert monitor.start_time is not None  # Still set, but stop() was called

    @patch('infrastructure.core.performance.PerformanceMonitor._get_memory_usage')
    @patch('infrastructure.core.performance.PerformanceMonitor._get_cpu_percent')
    def test_monitor_performance_with_operations(self, mock_cpu, mock_memory):
        """Test monitoring performance with recorded operations."""
        mock_memory.return_value = 200.0
        mock_cpu.return_value = 40.0
        
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

    @patch('builtins.__import__')
    def test_get_system_resources_with_psutil(self, mock_import):
        """Test getting system resources when psutil is available."""
        # Create mock psutil module
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 50.0
        
        # Mock memory
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4 GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # Mock disk
        mock_disk = MagicMock()
        mock_disk.total = 100 * 1024 * 1024 * 1024  # 100 GB
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50 GB
        mock_disk.used = 50 * 1024 * 1024 * 1024
        mock_psutil.disk_usage.return_value = mock_disk
        
        # Mock process
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 512 * 1024 * 1024  # 512 MB
        mock_psutil.Process.return_value = mock_process
        
        # Make __import__ return mock_psutil when psutil is imported
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        resources = get_system_resources()
        
        assert isinstance(resources, dict)
        assert resources['cpu_percent'] == 50.0
        assert resources['memory_total_gb'] == 8.0
        assert resources['memory_available_gb'] == 4.0
        assert resources['memory_percent'] == 50.0
        assert resources['process_memory_mb'] == 512.0
        assert resources['disk_total_gb'] == 100.0
        assert resources['disk_free_gb'] == 50.0

    @patch('builtins.__import__')
    def test_get_system_resources_without_psutil(self, mock_import):
        """Test getting system resources when psutil is not available."""
        # Make __import__ raise ImportError for psutil
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        resources = get_system_resources()
        
        assert isinstance(resources, dict)
        assert len(resources) == 0


class TestStagePerformanceTracker:
    """Test StagePerformanceTracker class."""

    def test_stage_performance_tracker_initialization(self):
        """Test StagePerformanceTracker initialization."""
        tracker = StagePerformanceTracker()
        
        assert tracker.stages == []
        assert tracker.start_time is None

    @patch('builtins.__import__')
    def test_start_stage(self, mock_import):
        """Test starting stage tracking."""
        # Create mock psutil module
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 256 * 1024 * 1024  # 256 MB
        mock_process.io_counters.return_value = MagicMock()
        mock_psutil.Process.return_value = mock_process
        
        # Make __import__ return mock_psutil when psutil is imported
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        tracker = StagePerformanceTracker()
        tracker.start_stage("test_stage")
        
        assert tracker.start_time is not None

    @patch('builtins.__import__')
    def test_start_stage_without_psutil(self, mock_import):
        """Test starting stage when psutil is not available."""
        # Make __import__ raise ImportError for psutil
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        tracker = StagePerformanceTracker()
        tracker.start_stage("test_stage")
        
        assert tracker.start_time is not None
        assert tracker.start_memory == 0.0

    @patch('builtins.__import__')
    def test_end_stage(self, mock_import):
        """Test ending stage tracking."""
        # Create mock psutil module
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 512 * 1024 * 1024  # 512 MB
        mock_process.cpu_percent.return_value = 60.0
        mock_io = MagicMock()
        mock_io.read_bytes = 1000
        mock_io.write_bytes = 500
        mock_process.io_counters.return_value = mock_io
        mock_psutil.Process.return_value = mock_process
        
        # Make __import__ return mock_psutil when psutil is imported
        def import_side_effect(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return original_import(name, *args, **kwargs)
        
        mock_import.side_effect = import_side_effect
        
        tracker = StagePerformanceTracker()
        tracker.start_stage("test_stage")
        time.sleep(0.1)
        
        metrics = tracker.end_stage("test_stage", exit_code=0)
        
        assert isinstance(metrics, dict)
        assert metrics['stage_name'] == "test_stage"
        assert metrics['duration'] > 0
        assert metrics['exit_code'] == 0
        assert len(tracker.stages) == 1

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
            {'stage_name': 'fast', 'duration': 1.0, 'peak_memory_mb': 100, 'cpu_percent': 50},
            {'stage_name': 'slow', 'duration': 10.0, 'peak_memory_mb': 100, 'cpu_percent': 50},
            {'stage_name': 'medium', 'duration': 2.0, 'peak_memory_mb': 100, 'cpu_percent': 50},
        ]
        
        warnings = tracker.get_performance_warnings()
        
        # Should warn about slow stage (10.0 > 2x average of ~4.33 = 8.67)
        assert len(warnings) > 0
        assert any(w['type'] == 'slow_stage' for w in warnings)

    def test_get_performance_warnings_high_memory(self):
        """Test getting warnings for high memory usage."""
        tracker = StagePerformanceTracker()
        
        tracker.stages = [
            {'stage_name': 'high_mem', 'duration': 1.0, 'peak_memory_mb': 2048, 'cpu_percent': 50},
        ]
        
        warnings = tracker.get_performance_warnings()
        
        assert len(warnings) > 0
        assert any(w['type'] == 'high_memory' for w in warnings)

    def test_get_performance_warnings_high_cpu(self):
        """Test getting warnings for high CPU usage."""
        tracker = StagePerformanceTracker()
        
        tracker.stages = [
            {'stage_name': 'high_cpu', 'duration': 1.0, 'peak_memory_mb': 100, 'cpu_percent': 95},
        ]
        
        warnings = tracker.get_performance_warnings()
        
        assert len(warnings) > 0
        assert any(w['type'] == 'high_cpu' for w in warnings)

    def test_get_summary(self):
        """Test getting performance summary."""
        tracker = StagePerformanceTracker()
        
        tracker.stages = [
            {'stage_name': 'stage1', 'duration': 1.0, 'memory_mb': 100, 'peak_memory_mb': 150},
            {'stage_name': 'stage2', 'duration': 2.0, 'memory_mb': 200, 'peak_memory_mb': 250},
            {'stage_name': 'stage3', 'duration': 3.0, 'memory_mb': 300, 'peak_memory_mb': 350},
        ]
        
        summary = tracker.get_summary()
        
        assert isinstance(summary, dict)
        assert summary['total_stages'] == 3
        assert summary['total_duration'] == 6.0
        assert summary['average_duration'] == 2.0
        assert summary['slowest_stage']['stage_name'] == 'stage3'
        assert summary['fastest_stage']['stage_name'] == 'stage1'
        assert summary['peak_memory_mb'] == 350

    def test_get_summary_empty(self):
        """Test getting summary when no stages tracked."""
        tracker = StagePerformanceTracker()
        
        summary = tracker.get_summary()
        
        assert summary == {}

