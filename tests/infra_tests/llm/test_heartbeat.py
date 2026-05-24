"""Tests for infrastructure.llm.utils.heartbeat."""

from __future__ import annotations

import logging
import time

import pytest

from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor


class TestStreamHeartbeatMonitor:
    def test_basic_creation(self):
        monitor = StreamHeartbeatMonitor(operation_name="test_op", timeout_seconds=60.0)
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

    def test_start_and_stop_monitoring(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0, heartbeat_interval=1.0)
        monitor.start_monitoring()
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        monitor.stop_monitoring()
        time.sleep(0.2)
        assert not monitor._monitor_thread.is_alive()

    def test_double_start_is_noop(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0, heartbeat_interval=0.1)
        monitor.start_monitoring()
        thread1 = monitor._monitor_thread
        monitor.start_monitoring()
        assert monitor._monitor_thread is thread1
        monitor.stop_monitoring()

    def test_stop_without_start(self):
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0)
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
        monitor = StreamHeartbeatMonitor("test", timeout_seconds=10.0)
        monitor.start_monitoring()
        monitor.update_token_received(3)
        first_time = monitor.first_token_time
        monitor.update_token_received(7)
        assert monitor.token_count == 10
        assert monitor.first_token_time == first_time
        monitor.stop_monitoring()

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
        with StreamHeartbeatMonitor("ctx_test", timeout_seconds=10.0, heartbeat_interval=0.1) as monitor:
            assert monitor._monitor_thread is not None
            assert monitor._monitor_thread.is_alive()
            monitor.update_token_received(5)
        time.sleep(0.2)
        assert not monitor._monitor_thread.is_alive()
        assert monitor.token_count == 5

    @pytest.mark.parametrize(
        ("setup_tokens", "setup_estimated_total"),
        [
            (False, False),
            (True, False),
            (True, True),
        ],
    )
    def test_log_progress_update(self, setup_tokens, setup_estimated_total):
        monitor = StreamHeartbeatMonitor("prog", timeout_seconds=60.0)
        if setup_tokens:
            monitor.start_time = time.time() - 10.0
            monitor.first_token_time = monitor.start_time + 1.0
            monitor.token_count = 100
        if setup_estimated_total:
            monitor.estimated_total_tokens = 500
        monitor._log_progress_update(10.0 if setup_tokens else 5.0)
