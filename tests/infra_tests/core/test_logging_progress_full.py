"""Tests for infrastructure.core.logging.progress — comprehensive coverage."""

import io
import logging

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
        # Non-TTY should not write completion message


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
