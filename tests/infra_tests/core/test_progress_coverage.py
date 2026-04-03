"""Tests for infrastructure.core.logging.progress — comprehensive coverage."""

import io
import logging

from infrastructure.core.logging.progress import (
    log_progress_bar,
    log_stage_with_eta,
    log_resource_usage,
    Spinner,
    StreamingProgress,
)


class TestLogProgressBar:
    def test_basic(self):
        logger = logging.getLogger("test_progress")
        # Should not raise
        log_progress_bar(5, 10, "Building", logger)

    def test_zero_total(self):
        logger = logging.getLogger("test_progress")
        log_progress_bar(0, 0, "Empty", logger)

    def test_complete(self):
        logger = logging.getLogger("test_progress")
        log_progress_bar(10, 10, "Done", logger)

    def test_no_logger(self):
        # Uses default logger
        log_progress_bar(3, 10, "Default")


class TestSpinner:
    def test_non_tty_stream(self):
        stream = io.StringIO()
        spinner = Spinner("Processing...", stream=stream)
        spinner.start()
        # Non-TTY: writes message once
        spinner.stop("Done")
        output = stream.getvalue()
        assert "Processing" in output

    def test_stop_without_start(self):
        stream = io.StringIO()
        spinner = Spinner("Test", stream=stream)
        # stop() without start() should not crash
        spinner.stop("Finished")
        assert "Finished" in stream.getvalue()

    def test_context_manager(self):
        stream = io.StringIO()
        with Spinner("Working...", stream=stream) as s:
            assert isinstance(s, Spinner)

    def test_stop_no_final_message(self):
        stream = io.StringIO()
        spinner = Spinner("Test", stream=stream)
        spinner.start()
        spinner.stop()  # No final message


class TestStreamingProgress:
    def test_update_non_tty(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Loading", stream=stream)
        sp.update(5)
        # Non-TTY: _display is no-op
        sp.finish()

    def test_set_value(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Loading", stream=stream)
        sp.set(7)
        assert sp.current == 7

    def test_set_capped(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Loading", stream=stream)
        sp.set(20)
        assert sp.current == 10  # Capped at total

    def test_update_capped(self):
        stream = io.StringIO()
        sp = StreamingProgress(5, "Work", stream=stream)
        sp.update(10)
        assert sp.current == 5

    def test_finish_with_message(self):
        stream = io.StringIO()
        sp = StreamingProgress(10, "Work", stream=stream)
        sp.finish("All done!")
        assert "All done!" in stream.getvalue()


class TestLogStageWithEta:
    def test_with_eta(self):
        logger = logging.getLogger("test_eta")
        # current > 0 and elapsed > 0 produces ETA
        log_stage_with_eta("Build", 5, 10, 10.0, logger)

    def test_no_eta(self):
        logger = logging.getLogger("test_eta")
        # current = 0, no ETA possible
        log_stage_with_eta("Build", 0, 10, 0.0, logger)

    def test_no_logger(self):
        log_stage_with_eta("Stage", 3, 10, 5.0)


class TestLogResourceUsage:
    def test_cpu_only(self):
        logger = logging.getLogger("test_resource")
        log_resource_usage(cpu_percent=50.0, logger=logger)

    def test_memory_only(self):
        logger = logging.getLogger("test_resource")
        log_resource_usage(memory_mb=1024.0, logger=logger)

    def test_both(self):
        logger = logging.getLogger("test_resource")
        log_resource_usage(cpu_percent=30.0, memory_mb=512.0, logger=logger)

    def test_none(self):
        logger = logging.getLogger("test_resource")
        log_resource_usage(logger=logger)

    def test_no_logger(self):
        log_resource_usage(cpu_percent=10.0)


class TestLogWithSpinner:
    """Test log_with_spinner context manager — non-TTY paths."""

    def test_basic_usage(self):
        from infrastructure.core.logging.progress import log_with_spinner
        logger = logging.getLogger("test_log_spinner")
        with log_with_spinner("Working...", logger=logger):
            pass

    def test_with_final_message(self):
        from infrastructure.core.logging.progress import log_with_spinner
        with log_with_spinner("Working...", final_message="All done"):
            pass

    def test_no_logger_no_final(self):
        from infrastructure.core.logging.progress import log_with_spinner
        with log_with_spinner("Working..."):
            pass

    def test_exception_propagates(self):
        from infrastructure.core.logging.progress import log_with_spinner
        import pytest
        logger = logging.getLogger("test_log_spinner")
        with pytest.raises(ValueError, match="test"):
            with log_with_spinner("Working...", logger=logger):
                raise ValueError("test")


class TestLogProgressStreaming:
    """Test log_progress_streaming — non-TTY paths."""

    def test_non_tty_with_logger(self):
        from infrastructure.core.logging.progress import log_progress_streaming
        logger = logging.getLogger("test_streaming")
        log_progress_streaming(5, 10, "Progress", logger)

    def test_non_tty_zero_total(self):
        from infrastructure.core.logging.progress import log_progress_streaming
        logger = logging.getLogger("test_streaming")
        log_progress_streaming(0, 0, "Empty", logger)

    def test_non_tty_no_logger(self):
        from infrastructure.core.logging.progress import log_progress_streaming
        log_progress_streaming(3, 10, "Test")
