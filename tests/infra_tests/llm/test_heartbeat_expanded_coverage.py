"""Tests for infrastructure.llm.utils.heartbeat — expanded coverage."""

import time
import logging

from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor


class TestStreamHeartbeatMonitorInit:
    def test_default_init(self):
        monitor = StreamHeartbeatMonitor("test_op", timeout_seconds=60.0)
        assert monitor.operation_name == "test_op"
        assert monitor.timeout_seconds == 60.0
        assert monitor.heartbeat_interval == 15.0
        assert monitor.stall_threshold == 60.0
        assert monitor.early_warning_threshold == 30.0
        assert monitor.token_count == 0
        assert monitor.first_token_time is None
        assert monitor.last_token_time is None

    def test_custom_init(self):
        custom_logger = logging.getLogger("custom")
        monitor = StreamHeartbeatMonitor(
            "custom_op",
            timeout_seconds=120.0,
            heartbeat_interval=5.0,
            stall_threshold=30.0,
            early_warning_threshold=10.0,
            logger=custom_logger,
        )
        assert monitor.heartbeat_interval == 5.0
        assert monitor.stall_threshold == 30.0
        assert monitor.early_warning_threshold == 10.0
        assert monitor.logger is custom_logger


class TestStreamHeartbeatMonitorLifecycle:
    def test_start_stop(self):
        monitor = StreamHeartbeatMonitor("lifecycle", timeout_seconds=10.0, heartbeat_interval=0.1)
        monitor.start_monitoring()
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        monitor.stop_monitoring()
        assert not monitor._monitor_thread.is_alive()

    def test_double_start(self):
        """Starting twice should not create a second thread."""
        monitor = StreamHeartbeatMonitor("double", timeout_seconds=10.0, heartbeat_interval=0.1)
        monitor.start_monitoring()
        thread1 = monitor._monitor_thread
        monitor.start_monitoring()
        assert monitor._monitor_thread is thread1
        monitor.stop_monitoring()

    def test_stop_without_start(self):
        """Stopping without starting should not crash."""
        monitor = StreamHeartbeatMonitor("nostop", timeout_seconds=10.0)
        monitor.stop_monitoring()


class TestStreamHeartbeatMonitorTokenTracking:
    def test_update_token(self):
        monitor = StreamHeartbeatMonitor("tokens", timeout_seconds=10.0)
        monitor.start_monitoring()
        monitor.update_token_received(5)
        assert monitor.token_count == 5
        assert monitor.first_token_time is not None
        assert monitor.last_token_time is not None
        monitor.stop_monitoring()

    def test_multiple_token_updates(self):
        monitor = StreamHeartbeatMonitor("multi", timeout_seconds=10.0)
        monitor.start_monitoring()
        monitor.update_token_received(3)
        first_time = monitor.first_token_time
        monitor.update_token_received(7)
        assert monitor.token_count == 10
        assert monitor.first_token_time == first_time  # first_token_time shouldn't change
        monitor.stop_monitoring()

    def test_set_estimated_total(self):
        monitor = StreamHeartbeatMonitor("estimate", timeout_seconds=10.0)
        monitor.set_estimated_total(1000)
        assert monitor.estimated_total_tokens == 1000


class TestStreamHeartbeatMonitorContextManager:
    def test_context_manager(self):
        with StreamHeartbeatMonitor("ctx", timeout_seconds=10.0, heartbeat_interval=0.1) as monitor:
            assert isinstance(monitor, StreamHeartbeatMonitor)
            monitor.update_token_received(1)
        # After exit, thread should be stopped
        assert not monitor._monitor_thread.is_alive()


class TestStreamHeartbeatMonitorProgressLog:
    def test_progress_update_no_tokens(self):
        """Log progress when no tokens received yet."""
        monitor = StreamHeartbeatMonitor("noprog", timeout_seconds=10.0)
        monitor._log_progress_update(5.0)

    def test_progress_update_with_tokens(self):
        """Log progress with tokens and rate calculation."""
        monitor = StreamHeartbeatMonitor("prog", timeout_seconds=60.0)
        monitor.start_time = time.time() - 10.0
        monitor.first_token_time = monitor.start_time + 1.0
        monitor.token_count = 100
        monitor._log_progress_update(10.0)

    def test_progress_update_with_estimated_total(self):
        """Log progress with estimated total for ETA calculation."""
        monitor = StreamHeartbeatMonitor("eta", timeout_seconds=60.0)
        monitor.start_time = time.time() - 10.0
        monitor.first_token_time = monitor.start_time + 1.0
        monitor.token_count = 100
        monitor.estimated_total_tokens = 500
        monitor._log_progress_update(10.0)
