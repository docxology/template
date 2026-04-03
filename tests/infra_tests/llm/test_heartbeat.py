"""Tests for infrastructure.llm.utils.heartbeat module.

Tests StreamHeartbeatMonitor including start/stop, token tracking,
and context manager protocol.
"""

from __future__ import annotations

import time


from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor


class TestStreamHeartbeatMonitor:
    """Tests for StreamHeartbeatMonitor."""

    def test_basic_creation(self):
        monitor = StreamHeartbeatMonitor(
            operation_name="test_op",
            timeout_seconds=60.0,
        )
        assert monitor.operation_name == "test_op"
        assert monitor.timeout_seconds == 60.0
        assert monitor.token_count == 0

    def test_start_and_stop_monitoring(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0, heartbeat_interval=1.0)
        monitor.start_monitoring()
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        monitor.stop_monitoring()
        # Thread should stop within timeout
        time.sleep(0.2)
        assert not monitor._monitor_thread.is_alive()

    def test_double_start_is_noop(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0)
        monitor.start_monitoring()
        thread1 = monitor._monitor_thread
        monitor.start_monitoring()  # Should not create new thread
        assert monitor._monitor_thread is thread1
        monitor.stop_monitoring()

    def test_update_token_received(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=60.0)
        assert monitor.token_count == 0
        assert monitor.first_token_time is None

        monitor.update_token_received(5)
        assert monitor.token_count == 5
        assert monitor.first_token_time is not None
        assert monitor.last_token_time is not None

    def test_multiple_token_updates(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=60.0)
        monitor.update_token_received(3)
        monitor.update_token_received(7)
        assert monitor.token_count == 10

    def test_first_token_time_set_once(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=60.0)
        monitor.update_token_received(1)
        first_time = monitor.first_token_time
        time.sleep(0.01)
        monitor.update_token_received(1)
        assert monitor.first_token_time == first_time

    def test_set_estimated_total(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=60.0)
        assert monitor.estimated_total_tokens is None
        monitor.set_estimated_total(1000)
        assert monitor.estimated_total_tokens == 1000

    def test_context_manager(self):
        with StreamHeartbeatMonitor(
            "ctx_test", timeout_seconds=10.0, heartbeat_interval=1.0
        ) as monitor:
            assert monitor._monitor_thread is not None
            assert monitor._monitor_thread.is_alive()
            monitor.update_token_received(5)
        # After exiting context, thread should be stopped
        time.sleep(0.2)
        assert not monitor._monitor_thread.is_alive()
        assert monitor.token_count == 5

    def test_stop_without_start(self):
        """Stopping before starting should not raise."""
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0)
        monitor.stop_monitoring()  # Should not raise

    def test_custom_logger(self):
        """Should accept custom logger."""
        import logging
        custom_logger = logging.getLogger("test.custom")
        monitor = StreamHeartbeatMonitor(
            "test", timeout_seconds=60.0, logger=custom_logger
        )
        assert monitor.logger is custom_logger

    def test_custom_thresholds(self):
        monitor = StreamHeartbeatMonitor(
            "test",
            timeout_seconds=120.0,
            heartbeat_interval=5.0,
            stall_threshold=30.0,
            early_warning_threshold=10.0,
        )
        assert monitor.heartbeat_interval == 5.0
        assert monitor.stall_threshold == 30.0
        assert monitor.early_warning_threshold == 10.0
