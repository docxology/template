"""Tests for infrastructure.core.logging.progress module.

Comprehensive tests for progress tracking including ETA calculations,
progress bars, spinners, streaming progress, and resource logging.

Test Pattern:
    Logging tests use `caplog` because logs go through Python's logging
    framework. Use `caplog.at_level()` to set the appropriate log level.
"""

from __future__ import annotations

import io
import logging
from io import StringIO

import pytest

from infrastructure.core.logging.progress import (
    Spinner,
    StreamingProgress,
    log_progress_bar,
    log_progress_streaming,
    log_resource_usage,
    log_stage_with_eta,
    log_with_spinner,
)
from infrastructure.core.runtime.eta import (
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
)


class TestCalculateEta:
    """Test calculate_eta function."""

    def test_calculate_eta_basic(self):
        """30 seconds for 3 items = 10s/item, 7 remaining = 70s."""
        eta = calculate_eta(30.0, 3, 10)
        assert eta == pytest.approx(70.0, rel=0.01)

    def test_calculate_eta_zero_completed(self):
        eta = calculate_eta(30.0, 0, 10)
        assert eta is None

    def test_calculate_eta_zero_total(self):
        eta = calculate_eta(30.0, 3, 0)
        assert eta is None

    def test_calculate_eta_completed_equals_total(self):
        eta = calculate_eta(30.0, 10, 10)
        assert eta == 0.0

    def test_calculate_eta_completed_exceeds_total(self):
        eta = calculate_eta(30.0, 15, 10)
        assert eta == 0.0

    def test_calculate_eta_fractional_values(self):
        eta = calculate_eta(15.5, 2.5, 10)
        assert eta == pytest.approx(46.5, rel=0.01)

    def test_calculate_eta_negative_values(self):
        eta = calculate_eta(-10.0, 3, 10)
        assert eta is not None


class TestCalculateEtaEma:
    """Test calculate_eta_ema function."""

    def test_calculate_eta_ema_basic(self):
        eta = calculate_eta_ema(30.0, 3, 10)
        assert eta is not None
        assert eta > 0

    def test_calculate_eta_ema_with_previous(self):
        previous_eta = 80.0
        eta = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta)
        assert eta is not None
        linear_eta = calculate_eta(30.0, 3, 10)
        assert min(linear_eta, previous_eta) <= eta <= max(linear_eta, previous_eta)

    def test_calculate_eta_ema_zero_completed(self):
        eta = calculate_eta_ema(30.0, 0, 10)
        assert eta is None

    def test_calculate_eta_ema_completed_equals_total(self):
        eta = calculate_eta_ema(30.0, 10, 10)
        assert eta == 0.0

    def test_calculate_eta_ema_alpha_parameter(self):
        previous_eta = 80.0
        eta_low_alpha = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta, alpha=0.1)
        eta_high_alpha = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta, alpha=0.9)
        linear_eta = calculate_eta(30.0, 3, 10)
        assert abs(eta_high_alpha - linear_eta) < abs(eta_low_alpha - linear_eta)

    def test_calculate_eta_ema_non_negative(self):
        eta = calculate_eta_ema(30.0, 3, 10, previous_eta=-10.0)
        assert eta is not None
        assert eta >= 0.0


class TestCalculateEtaWithConfidence:
    """Test calculate_eta_with_confidence function."""

    def test_calculate_eta_with_confidence_basic(self):
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 3, 10)
        assert optimistic is not None
        assert realistic is not None
        assert pessimistic is not None
        assert optimistic < realistic < pessimistic

    def test_calculate_eta_with_confidence_with_durations(self):
        item_durations = [8.0, 10.0, 12.0]
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(
            30.0, 3, 10, item_durations=item_durations
        )
        assert optimistic == pytest.approx(56.0, rel=0.01)
        assert realistic == pytest.approx(70.0, rel=0.01)
        assert pessimistic == pytest.approx(84.0, rel=0.01)

    def test_calculate_eta_with_confidence_zero_completed(self):
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 0, 10)
        assert optimistic is None
        assert realistic is None
        assert pessimistic is None

    def test_calculate_eta_with_confidence_completed_equals_total(self):
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 10, 10)
        assert optimistic == 0.0
        assert realistic == 0.0
        assert pessimistic == 0.0

    def test_calculate_eta_with_confidence_empty_durations(self):
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(
            30.0, 3, 10, item_durations=[]
        )
        assert optimistic is not None
        assert realistic is not None
        assert pessimistic is not None
        assert optimistic < realistic < pessimistic


class TestLogProgressBar:
    """Test log_progress_bar function."""

    def test_log_progress_bar_basic(self, caplog):
        with caplog.at_level("INFO"):
            log_progress_bar(3, 10, "Processing")
        assert "Processing" in caplog.text
        assert "%" in caplog.text or "3/10" in caplog.text

    def test_log_progress_bar_zero_total(self, caplog):
        with caplog.at_level("INFO"):
            log_progress_bar(0, 0, "Processing")
        assert "0/0" in caplog.text or "0%" in caplog.text

    def test_log_progress_bar_complete(self, caplog):
        with caplog.at_level("INFO"):
            log_progress_bar(10, 10, "Processing")
        assert "100%" in caplog.text or "10/10" in caplog.text

    def test_log_progress_bar_custom_message(self, caplog):
        with caplog.at_level("INFO"):
            log_progress_bar(5, 10, "Custom message")
        assert "Custom message" in caplog.text

    def test_log_progress_bar_custom_width(self, caplog):
        with caplog.at_level("INFO"):
            log_progress_bar(5, 10, "Processing", bar_width=20)
        assert "Processing" in caplog.text

    def test_log_progress_bar_default_logger(self, caplog):
        with caplog.at_level(logging.INFO):
            log_progress_bar(5, 10, "Test")


class TestSpinner:
    """Test Spinner class."""

    def test_spinner_initialization(self):
        spinner = Spinner("Test message")
        assert spinner.message == "Test message"
        assert spinner.delay == 0.1
        assert spinner.thread is None

    def test_spinner_start_non_tty(self):
        stream = StringIO()
        stream.isatty = lambda: False
        spinner = Spinner("Test message", stream=stream)
        spinner.start()
        assert "Test message" in stream.getvalue()

    def test_spinner_non_tty_start_stop_with_final(self):
        stream = io.StringIO()
        spinner = Spinner("Working...", stream=stream)
        spinner.start()
        spinner.stop(final_message="Done!")
        output = stream.getvalue()
        assert "Working..." in output
        assert "Done!" in output

    def test_spinner_stop_without_start(self):
        spinner = Spinner("Test message")
        spinner.stop()

    def test_spinner_stop_with_final_message_no_thread(self):
        stream = io.StringIO()
        spinner = Spinner("Idle", stream=stream)
        spinner.stop(final_message="Finished")
        assert "Finished" in stream.getvalue()

    def test_spinner_context_manager(self):
        stream = StringIO()
        stream.isatty = lambda: False
        with Spinner("Test message", stream=stream) as spinner:
            assert isinstance(spinner, Spinner)
        assert "Test message" in stream.getvalue()

    def test_spinner_stop_with_final_message(self):
        stream = StringIO()
        stream.isatty = lambda: False
        spinner = Spinner("Test message", stream=stream)
        spinner.start()
        spinner.stop("Done!")
        assert "Done!" in stream.getvalue()


class TestLogWithSpinner:
    """Test log_with_spinner context manager."""

    def test_log_with_spinner_basic(self):
        with log_with_spinner("Loading..."):
            pass

    def test_log_with_spinner_final_message(self):
        with log_with_spinner("Loading...", final_message="Loaded!"):
            pass

    def test_log_with_spinner_with_logger(self, caplog):
        logger = logging.getLogger("test")
        with log_with_spinner("Loading...", logger=logger):
            pass

    def test_log_with_spinner_without_logger_or_final(self):
        with log_with_spinner("Working"):
            pass

    def test_log_with_spinner_exception_propagated(self, caplog):
        logger = logging.getLogger("test_spinner")
        with pytest.raises(ValueError, match="test error"):
            with log_with_spinner("Test operation", logger=logger):
                raise ValueError("test error")


class TestStreamingProgress:
    """Test StreamingProgress class."""

    def test_construction(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=100, message="Test", stream=stream)
        assert progress.total == 100
        assert progress.current == 0

    def test_update_increments(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=100, stream=stream, update_interval=0.0)
        progress.update(10)
        assert progress.current == 10
        progress.update(5)
        assert progress.current == 15

    def test_update_capped_at_total(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream, update_interval=0.0)
        progress.update(15)
        assert progress.current == 10

    def test_set_value(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=50, stream=stream)
        progress.set(25)
        assert progress.current == 25

    def test_set_capped_at_total(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=50, stream=stream)
        progress.set(100)
        assert progress.current == 50

    def test_non_tty_display_skipped(self):
        stream = io.StringIO()
        sp = StreamingProgress(100, "Test", stream=stream)
        sp.update(10)
        sp.set(50)
        assert stream.getvalue() == ""

    def test_finish_with_message(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream)
        progress.finish(final_message="All done!")
        assert "All done!" in stream.getvalue()

    def test_finish_without_message(self):
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream)
        progress.finish()
        assert stream.getvalue() == ""

    def test_throttle(self):
        stream = io.StringIO()
        sp = StreamingProgress(100, "Test", stream=stream, update_interval=10.0)
        sp.update(1)
        sp.update(1)


class TestLogProgressStreaming:
    """Test log_progress_streaming function."""

    def test_non_tty_fallback(self, caplog):
        logger = logging.getLogger("test_streaming")
        with caplog.at_level(logging.INFO, logger="test_streaming"):
            log_progress_streaming(5, 10, "Step", logger=logger)

    def test_zero_total(self, caplog):
        logger = logging.getLogger("test_streaming_zero")
        with caplog.at_level(logging.INFO, logger="test_streaming_zero"):
            log_progress_streaming(0, 0, "Empty", logger=logger)


class TestLogStageWithEta:
    """Test log_stage_with_eta function."""

    def test_with_eta(self, caplog):
        logger = logging.getLogger("test_eta")
        with caplog.at_level(logging.INFO, logger="test_eta"):
            log_stage_with_eta("Rendering", 5, 10, 5.0, logger)
        assert "Rendering" in caplog.text

    def test_first_item_no_eta(self, caplog):
        logger = logging.getLogger("test_eta")
        with caplog.at_level(logging.INFO, logger="test_eta"):
            log_stage_with_eta("Processing", 0, 10, 0.0, logger)
        assert "Processing" in caplog.text

    def test_default_logger(self, caplog):
        with caplog.at_level(logging.INFO):
            log_stage_with_eta("Test", 1, 5, 1.0)


class TestLogResourceUsage:
    """Test log_resource_usage function."""

    def test_with_cpu_and_memory(self, caplog):
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(cpu_percent=45.5, memory_mb=512.3, logger=logger)
        assert "45.5%" in caplog.text
        assert "512.3" in caplog.text

    def test_cpu_only(self, caplog):
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(cpu_percent=30.0, logger=logger)
        assert "30.0%" in caplog.text

    def test_memory_only(self, caplog):
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(memory_mb=256.0, logger=logger)
        assert "256.0" in caplog.text

    def test_no_metrics(self, caplog):
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(logger=logger)

    def test_default_logger(self, caplog):
        with caplog.at_level(logging.DEBUG):
            log_resource_usage(cpu_percent=10.0)


class TestLogProgressBar:
    def test_basic(self):
        log = logging.getLogger("test_progress_bar")
        log_progress_bar(50, 100, "Processing", logger=log)

    def test_zero_total(self):
        log = logging.getLogger("test_progress_bar_zero")
        log_progress_bar(0, 0, "Empty", logger=log)

    def test_complete(self):
        log = logging.getLogger("test_progress_bar_done")
        log_progress_bar(100, 100, "Done", logger=log)

    def test_default_logger(self):
        log_progress_bar(1, 10, "Default")

    def test_custom_bar_width(self):
        log = logging.getLogger("test_bar_width")
        log_progress_bar(5, 10, "Custom width", logger=log, bar_width=20)


class TestSpinner:
    def test_init_defaults(self):
        s = Spinner()
        assert s.message == "Processing..."
        assert s.delay == 0.1
        assert s.thread is None
        assert s.idx == 0

    def test_non_tty_start_stop(self):
        """Non-TTY stream should just print message once."""
        buf = io.StringIO()
        s = Spinner("Working...", stream=buf)
        s.start()
        # StringIO.isatty() returns False, so thread should not start
        assert s.thread is None
        s.stop("Done!")
        output = buf.getvalue()
        assert "Working..." in output
        assert "Done!" in output

    def test_non_tty_stop_with_final_message(self):
        buf = io.StringIO()
        s = Spinner("Working...", stream=buf)
        s.start()
        s.stop("Finished!")
        assert "Finished!" in buf.getvalue()

    def test_non_tty_stop_no_final_message(self):
        buf = io.StringIO()
        s = Spinner("Working...", stream=buf)
        s.start()
        s.stop()  # No final message
        assert "Working..." in buf.getvalue()

    def test_context_manager(self):
        buf = io.StringIO()
        with Spinner("ctx", stream=buf) as s:
            assert isinstance(s, Spinner)


class TestLogWithSpinner:
    def test_basic(self):
        log = logging.getLogger("test_spinner_ctx")
        with log_with_spinner("Loading...", logger=log):
            pass

    def test_with_final_message(self):
        with log_with_spinner("Loading...", final_message="All done"):
            pass

    def test_no_logger(self):
        with log_with_spinner("Loading..."):
            pass

    def test_exception_propagates(self):
        log = logging.getLogger("test_spinner_err")
        with pytest.raises(RuntimeError, match="boom"):
            with log_with_spinner("Failing...", logger=log):
                raise RuntimeError("boom")


class TestStreamingProgress:
    def test_init(self):
        buf = io.StringIO()
        sp = StreamingProgress(100, "Loading", stream=buf)
        assert sp.total == 100
        assert sp.current == 0

    def test_update(self):
        buf = io.StringIO()
        sp = StreamingProgress(10, "Prog", stream=buf, update_interval=0.0)
        sp.update(3)
        assert sp.current == 3

    def test_update_clamps_to_total(self):
        buf = io.StringIO()
        sp = StreamingProgress(5, stream=buf)
        sp.update(100)
        assert sp.current == 5

    def test_set_value(self):
        buf = io.StringIO()
        sp = StreamingProgress(10, stream=buf)
        sp.set(7)
        assert sp.current == 7

    def test_set_clamps(self):
        buf = io.StringIO()
        sp = StreamingProgress(10, stream=buf)
        sp.set(20)
        assert sp.current == 10

    def test_finish_with_message(self):
        buf = io.StringIO()
        sp = StreamingProgress(10, stream=buf)
        sp.finish("All done")
        assert "All done" in buf.getvalue()

    def test_finish_no_message_non_tty(self):
        buf = io.StringIO()
        sp = StreamingProgress(10, stream=buf)
        sp.finish()


class TestLogProgressStreaming:
    def test_non_tty(self):
        log = logging.getLogger("test_streaming")
        log_progress_streaming(5, 10, "Test", logger=log)

    def test_zero_total(self):
        log = logging.getLogger("test_streaming_zero")
        log_progress_streaming(0, 0, "Empty", logger=log)

    def test_default_logger(self):
        log_progress_streaming(1, 10, "Default")


class TestLogStageWithEta:
    def test_with_eta(self):
        log = logging.getLogger("test_eta")
        log_stage_with_eta("Build", 5, 10, 5.0, logger=log)

    def test_no_eta_at_zero(self):
        log = logging.getLogger("test_eta_zero")
        log_stage_with_eta("Build", 0, 10, 0.0, logger=log)

    def test_default_logger(self):
        log_stage_with_eta("Build", 3, 10, 3.0)


class TestLogResourceUsage:
    def test_cpu_only(self):
        log = logging.getLogger("test_resource")
        log_resource_usage(cpu_percent=45.2, logger=log)

    def test_memory_only(self):
        log = logging.getLogger("test_resource")
        log_resource_usage(memory_mb=512.0, logger=log)

    def test_both(self):
        log = logging.getLogger("test_resource")
        log_resource_usage(cpu_percent=30.0, memory_mb=256.0, logger=log)

    def test_neither(self):
        log = logging.getLogger("test_resource")
        log_resource_usage(logger=log)

    def test_default_logger(self):
        log_resource_usage(cpu_percent=10.0)
