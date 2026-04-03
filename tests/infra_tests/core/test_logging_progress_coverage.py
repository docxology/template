"""Tests for infrastructure/core/logging/progress.py.

Covers: log_progress_bar, Spinner, StreamingProgress, log_progress_streaming,
log_stage_with_eta, log_resource_usage.

No mocks used — all tests use real loggers, real streams, and real timing.
"""

from __future__ import annotations

import io
import logging

import pytest

from infrastructure.core.logging.progress import (
    log_progress_bar,
    Spinner,
    log_with_spinner,
    StreamingProgress,
    log_stage_with_eta,
    log_resource_usage,
)


class TestLogProgressBar:
    """Test log_progress_bar function."""

    def test_normal_progress(self, caplog):
        """Should log progress bar with percentage."""
        logger = logging.getLogger("test_progress")
        with caplog.at_level(logging.INFO, logger="test_progress"):
            log_progress_bar(50, 100, "Building", logger)
        assert "50%" in caplog.text

    def test_zero_total(self, caplog):
        """Should handle zero total gracefully."""
        logger = logging.getLogger("test_progress")
        with caplog.at_level(logging.INFO, logger="test_progress"):
            log_progress_bar(0, 0, "Empty", logger)
        assert "0/0" in caplog.text

    def test_complete_progress(self, caplog):
        """Should show 100% when current equals total."""
        logger = logging.getLogger("test_progress")
        with caplog.at_level(logging.INFO, logger="test_progress"):
            log_progress_bar(10, 10, "Done", logger)
        assert "100%" in caplog.text

    def test_default_logger(self, caplog):
        """Should use default logger when none provided."""
        with caplog.at_level(logging.INFO):
            log_progress_bar(5, 10, "Test")


class TestSpinner:
    """Test Spinner class with non-TTY streams."""

    def test_spinner_non_tty(self):
        """Spinner should work with non-TTY stream (StringIO)."""
        stream = io.StringIO()
        spinner = Spinner("Processing...", stream=stream)
        spinner.start()
        spinner.stop()
        output = stream.getvalue()
        assert "Processing" in output

    def test_spinner_non_tty_with_final_message(self):
        """Spinner stop with final_message on non-TTY."""
        stream = io.StringIO()
        spinner = Spinner("Working...", stream=stream)
        spinner.start()
        spinner.stop(final_message="Done!")
        output = stream.getvalue()
        assert "Done!" in output

    def test_spinner_context_manager(self):
        """Spinner should work as context manager."""
        stream = io.StringIO()
        with Spinner("Loading...", stream=stream) as s:
            assert isinstance(s, Spinner)

    def test_spinner_stop_without_start(self):
        """Spinner stop without start should not crash."""
        stream = io.StringIO()
        spinner = Spinner("Test", stream=stream)
        spinner.stop()  # No thread started

    def test_spinner_stop_with_message_no_thread(self):
        """Spinner stop with final_message but no thread."""
        stream = io.StringIO()
        spinner = Spinner("Test", stream=stream)
        spinner.stop(final_message="Completed")
        assert "Completed" in stream.getvalue()


class TestLogWithSpinner:
    """Test log_with_spinner context manager."""

    def test_successful_block(self, caplog):
        """Should complete successfully and log."""
        logger = logging.getLogger("test_spinner")
        with caplog.at_level(logging.INFO, logger="test_spinner"):
            with log_with_spinner("Test operation", logger):
                pass  # Do nothing

    def test_with_final_message(self):
        """Should display final message on completion."""
        with log_with_spinner("Test", final_message="All done"):
            pass

    def test_exception_propagated(self, caplog):
        """Should re-raise exceptions from the block."""
        logger = logging.getLogger("test_spinner")
        with pytest.raises(ValueError, match="test error"):
            with log_with_spinner("Test operation", logger):
                raise ValueError("test error")


class TestStreamingProgress:
    """Test StreamingProgress class."""

    def test_construction(self):
        """Should construct with basic parameters."""
        stream = io.StringIO()
        progress = StreamingProgress(total=100, message="Test", stream=stream)
        assert progress.total == 100
        assert progress.current == 0

    def test_update_increments(self):
        """Should increment current value."""
        stream = io.StringIO()
        progress = StreamingProgress(total=100, stream=stream, update_interval=0.0)
        progress.update(10)
        assert progress.current == 10
        progress.update(5)
        assert progress.current == 15

    def test_update_capped_at_total(self):
        """Should cap current at total."""
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream, update_interval=0.0)
        progress.update(15)
        assert progress.current == 10

    def test_set_value(self):
        """Should set to specific value."""
        stream = io.StringIO()
        progress = StreamingProgress(total=50, stream=stream)
        progress.set(25)
        assert progress.current == 25

    def test_set_capped_at_total(self):
        """Should cap set value at total."""
        stream = io.StringIO()
        progress = StreamingProgress(total=50, stream=stream)
        progress.set(100)
        assert progress.current == 50

    def test_finish_with_message(self):
        """Should display final message on finish."""
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream)
        progress.finish(final_message="All done!")
        assert "All done!" in stream.getvalue()

    def test_finish_without_message(self):
        """Should handle finish without message."""
        stream = io.StringIO()
        progress = StreamingProgress(total=10, stream=stream)
        progress.finish()


class TestLogStageWithEta:
    """Test log_stage_with_eta function."""

    def test_with_eta(self, caplog):
        """Should log stage with ETA when data is sufficient."""
        logger = logging.getLogger("test_eta")
        with caplog.at_level(logging.INFO, logger="test_eta"):
            log_stage_with_eta("Rendering", 5, 10, 5.0, logger)
        assert "Rendering" in caplog.text

    def test_first_item_no_eta(self, caplog):
        """Should log stage without ETA for first item."""
        logger = logging.getLogger("test_eta")
        with caplog.at_level(logging.INFO, logger="test_eta"):
            log_stage_with_eta("Processing", 0, 10, 0.0, logger)
        assert "Processing" in caplog.text

    def test_default_logger(self, caplog):
        """Should use default logger when none provided."""
        with caplog.at_level(logging.INFO):
            log_stage_with_eta("Test", 1, 5, 1.0)


class TestLogResourceUsage:
    """Test log_resource_usage function."""

    def test_with_cpu_and_memory(self, caplog):
        """Should log CPU and memory usage."""
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(cpu_percent=45.5, memory_mb=512.3, logger=logger)
        assert "45.5%" in caplog.text
        assert "512.3" in caplog.text

    def test_cpu_only(self, caplog):
        """Should log CPU-only usage."""
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(cpu_percent=30.0, logger=logger)
        assert "30.0%" in caplog.text

    def test_memory_only(self, caplog):
        """Should log memory-only usage."""
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(memory_mb=256.0, logger=logger)
        assert "256.0" in caplog.text

    def test_no_metrics(self, caplog):
        """Should handle no metrics gracefully."""
        logger = logging.getLogger("test_resource")
        with caplog.at_level(logging.DEBUG, logger="test_resource"):
            log_resource_usage(logger=logger)

    def test_default_logger(self, caplog):
        """Should use default logger when none provided."""
        with caplog.at_level(logging.DEBUG):
            log_resource_usage(cpu_percent=10.0)
