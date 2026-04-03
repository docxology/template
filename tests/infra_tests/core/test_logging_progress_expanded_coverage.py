"""Tests for infrastructure.core.logging.progress — expanded coverage."""

import io
import logging

from infrastructure.core.logging.progress import (
    log_progress_bar,
    Spinner,
    log_with_spinner,
    StreamingProgress,
    log_progress_streaming,
    log_stage_with_eta,
    log_resource_usage,
)


class TestLogProgressBar:
    def test_basic_progress(self):
        logger = logging.getLogger("test_progress_bar")
        log_progress_bar(50, 100, "Test", logger=logger)

    def test_zero_total(self):
        logger = logging.getLogger("test_progress_bar_zero")
        log_progress_bar(0, 0, "Zero", logger=logger)

    def test_full_progress(self):
        logger = logging.getLogger("test_progress_bar_full")
        log_progress_bar(100, 100, "Full", logger=logger, bar_width=20)

    def test_default_logger(self):
        log_progress_bar(10, 50, "Default")


class TestSpinner:
    def test_non_tty_start_stop(self):
        """Non-TTY stream: start writes message, stop writes final."""
        stream = io.StringIO()
        spinner = Spinner("Working...", stream=stream)
        spinner.start()
        spinner.stop(final_message="Done!")
        output = stream.getvalue()
        assert "Working..." in output
        assert "Done!" in output

    def test_non_tty_stop_no_thread(self):
        """Stop without start on non-TTY: no crash, writes final message."""
        stream = io.StringIO()
        spinner = Spinner("Idle", stream=stream)
        spinner.stop(final_message="Finished")
        output = stream.getvalue()
        assert "Finished" in output

    def test_non_tty_stop_no_message(self):
        """Stop without start and no final message."""
        stream = io.StringIO()
        spinner = Spinner("Idle", stream=stream)
        spinner.stop()
        # Should not crash

    def test_context_manager(self):
        stream = io.StringIO()
        with Spinner("Processing", stream=stream) as s:
            assert isinstance(s, Spinner)


class TestLogWithSpinner:
    def test_basic(self):
        logger = logging.getLogger("test_spinner_ctx")
        with log_with_spinner("Working", logger=logger, final_message="All done"):
            pass

    def test_without_final_message_with_logger(self):
        logger = logging.getLogger("test_spinner_ctx2")
        with log_with_spinner("Working", logger=logger):
            pass

    def test_without_logger_or_final(self):
        with log_with_spinner("Working"):
            pass

    def test_exception_propagation(self):
        logger = logging.getLogger("test_spinner_exc")
        try:
            with log_with_spinner("Failing", logger=logger):
                raise RuntimeError("test error")
        except RuntimeError:
            pass  # Expected


class TestStreamingProgress:
    def test_non_tty_display_skipped(self):
        stream = io.StringIO()
        sp = StreamingProgress(100, "Test", stream=stream)
        sp.update(10)
        sp.set(50)
        # Non-TTY: _display does nothing
        assert stream.getvalue() == ""

    def test_finish_with_message(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Test", stream=stream)
        sp.finish(final_message="Complete!")
        assert "Complete!" in stream.getvalue()

    def test_finish_non_tty_no_message(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Test", stream=stream)
        sp.finish()
        # Non-TTY with no final_message: nothing written
        assert stream.getvalue() == ""

    def test_throttle(self):
        stream = io.StringIO()
        sp = StreamingProgress(100, "Test", stream=stream, update_interval=10.0)
        sp.update(1)
        sp.update(1)  # Should be throttled
        # Non-TTY so nothing displayed regardless


class TestLogProgressStreaming:
    def test_non_tty_fallback(self):
        """Non-TTY: falls back to plain log line."""
        logger = logging.getLogger("test_streaming")
        log_progress_streaming(5, 10, "Step", logger=logger)

    def test_zero_total(self):
        logger = logging.getLogger("test_streaming_zero")
        log_progress_streaming(0, 0, "Empty", logger=logger)


class TestLogStageWithEta:
    def test_with_eta(self):
        logger = logging.getLogger("test_eta")
        log_stage_with_eta("Build", 5, 10, 10.0, logger=logger)

    def test_no_eta(self):
        logger = logging.getLogger("test_no_eta")
        log_stage_with_eta("Build", 0, 10, 0.0, logger=logger)

    def test_default_logger(self):
        log_stage_with_eta("Stage", 3, 10, 5.0)


class TestLogResourceUsage:
    def test_cpu_and_memory(self):
        logger = logging.getLogger("test_resource")
        log_resource_usage(cpu_percent=45.2, memory_mb=512.0, logger=logger)

    def test_cpu_only(self):
        logger = logging.getLogger("test_cpu")
        log_resource_usage(cpu_percent=30.0, logger=logger)

    def test_memory_only(self):
        logger = logging.getLogger("test_mem")
        log_resource_usage(memory_mb=256.5, logger=logger)

    def test_no_metrics(self):
        logger = logging.getLogger("test_empty_resource")
        log_resource_usage(logger=logger)

    def test_default_logger(self):
        log_resource_usage(cpu_percent=10.0)
