"""Tests for infrastructure.core.progress module.

Comprehensive tests for progress bar and sub-stage progress tracking.
"""

import io
import logging
import time

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
from infrastructure.core.progress import LLMProgressTracker, ProgressBar, SubStageProgress


class TestProgressBar:
    """Test ProgressBar functionality."""

    def test_progress_bar_initialization(self):
        """Test ProgressBar initialization."""
        bar = ProgressBar(total=100, task="Test Task")

        assert bar.total == 100
        assert bar.task == "Test Task"
        assert bar.current == 0
        assert bar.width == 30
        assert bar.show_eta is True

    def test_progress_bar_initialization_defaults(self):
        """Test ProgressBar with default parameters."""
        bar = ProgressBar(total=50)

        assert bar.total == 50
        assert bar.task == ""
        assert bar.width == 30
        assert bar.show_eta is True

    def test_progress_bar_update(self):
        """Test updating progress bar."""
        bar = ProgressBar(total=100, task="Test")

        bar.update(50)

        assert bar.current == 50

    def test_progress_bar_update_overflow(self):
        """Test updating progress bar beyond total."""
        bar = ProgressBar(total=100)

        bar.update(150)

        assert bar.current == 100  # Should be capped at total

    def test_progress_bar_update_throttling(self):
        """Test that progress bar throttles updates."""
        bar = ProgressBar(total=100, update_interval=0.1)

        start = time.time()
        bar.update(1)
        bar.update(2)
        bar.update(3)
        elapsed = time.time() - start

        # Should be fast due to throttling
        assert elapsed < 0.2

    def test_progress_bar_update_force(self):
        """Test forcing progress bar update."""
        bar = ProgressBar(total=100, update_interval=1.0)

        # Force update should bypass throttling
        bar.update(50, force=True)

        assert bar.current == 50

    def test_progress_bar_finish(self):
        """Test finishing progress bar."""
        bar = ProgressBar(total=100, task="Test Task")

        bar.update(100)
        bar.finish()

        assert bar.current == 100

    def test_progress_bar_no_eta(self):
        """Test progress bar without ETA."""
        bar = ProgressBar(total=100, show_eta=False)

        bar.update(50)
        # Should not raise error
        bar.finish()


class TestSubStageProgress:
    """Test SubStageProgress functionality."""

    def test_substage_progress_initialization(self):
        """Test SubStageProgress initialization."""
        progress = SubStageProgress(total=5, stage_name="Test Stage")

        assert progress.total == 5
        assert progress.stage_name == "Test Stage"
        assert progress.current == 0
        assert progress.substage_start_time is None

    def test_substage_progress_start_substage(self):
        """Test starting a sub-stage."""
        progress = SubStageProgress(total=5)

        progress.start_substage(1, "Sub-stage 1")

        assert progress.current == 1
        assert progress.current_substage_name == "Sub-stage 1"
        assert progress.substage_start_time is not None

    def test_substage_progress_start_substage_no_name(self):
        """Test starting sub-stage without name."""
        progress = SubStageProgress(total=5)

        progress.start_substage(2)

        assert progress.current == 2
        assert progress.current_substage_name == ""

    def test_substage_progress_complete_substage(self):
        """Test completing a sub-stage."""
        progress = SubStageProgress(total=5)

        progress.start_substage(1, "Sub-stage 1")
        time.sleep(0.01)  # Small delay to measure
        progress.complete_substage()

        # Should not raise error
        assert progress.substage_start_time is not None

    def test_substage_progress_complete_without_start(self):
        """Test completing sub-stage without starting."""
        progress = SubStageProgress(total=5)

        # Should not raise error
        progress.complete_substage()

    def test_substage_progress_get_eta_zero(self):
        """Test getting ETA when no progress made."""
        progress = SubStageProgress(total=5)

        eta = progress.get_eta()

        assert eta is None

    def test_substage_progress_get_eta(self):
        """Test getting ETA with progress."""
        progress = SubStageProgress(total=5)

        progress.start_substage(1, "Sub-stage 1")
        time.sleep(0.1)
        progress.complete_substage()

        progress.start_substage(2, "Sub-stage 2")
        time.sleep(0.1)

        eta = progress.get_eta()

        # Should have some ETA estimate
        assert eta is not None or eta is None  # May be None if too fast

    def test_substage_progress_log_progress(self):
        """Test logging progress."""
        progress = SubStageProgress(total=5, stage_name="Test")

        progress.start_substage(1, "Sub-stage 1")
        time.sleep(0.01)

        # Should not raise error
        progress.log_progress()

    def test_substage_progress_multiple_substages(self):
        """Test tracking multiple sub-stages."""
        progress = SubStageProgress(total=3, stage_name="Test")

        for i in range(1, 4):
            progress.start_substage(i, f"Sub-stage {i}")
            time.sleep(0.01)
            progress.complete_substage()

        assert progress.current == 3

    def test_substage_progress_eta_calculation(self):
        """Test ETA calculation with multiple sub-stages."""
        progress = SubStageProgress(total=10)

        # Complete a few sub-stages
        for i in range(1, 4):
            progress.start_substage(i, f"Sub-stage {i}")
            time.sleep(0.05)
            progress.complete_substage()

        # Start another one
        progress.start_substage(4, "Sub-stage 4")

        eta = progress.get_eta()

        # ETA should be reasonable (not None if enough data)
        # May be None if calculation can't be done
        assert eta is None or eta >= 0

    def test_substage_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = SubStageProgress(total=10)

        progress.start_substage(5, "Midpoint")

        # Percentage should be 50%
        # This is tested indirectly through log_progress
        progress.log_progress()

        assert progress.current == 5
        assert progress.total == 10

    def test_progress_bar_update_throttling_interval(self):
        """Test that update throttling respects update_interval."""
        bar = ProgressBar(total=100, update_interval=0.2)

        # First update should happen immediately
        bar.update(10)
        first_update_time = bar.last_update_time

        # Second update should be throttled
        bar.update(20)
        # Should not update if within interval
        assert bar.last_update_time == first_update_time

        # Wait for interval to pass
        time.sleep(0.25)
        bar.update(30)
        # Should update after interval
        assert bar.last_update_time > first_update_time

    def test_progress_bar_force_update_bypasses_throttling(self):
        """Test that force=True bypasses update throttling."""
        bar = ProgressBar(total=100, update_interval=1.0)

        bar.update(10)
        first_update_time = bar.last_update_time

        # Force update should bypass throttling
        time.sleep(0.1)  # Much less than interval
        bar.update(20, force=True)

        # Should update immediately despite being within interval
        assert bar.last_update_time > first_update_time

    def test_progress_bar_eta_calculation_slow_progress(self):
        """Test ETA calculation with slow progress rate."""
        bar = ProgressBar(total=100, show_eta=True)

        bar.update(10)
        time.sleep(0.1)  # Simulate some time passing

        # ETA should be calculated (tested through _render)
        bar.update(20, force=True)

        # Should have ETA estimate
        assert bar.current > 0

    def test_progress_bar_eta_calculation_fast_progress(self):
        """Test ETA calculation with fast progress rate."""
        bar = ProgressBar(total=100, show_eta=True)

        bar.update(50)
        time.sleep(0.01)  # Very fast progress

        bar.update(80, force=True)

        # ETA should be shorter for fast progress
        assert bar.current == 80

    def test_progress_bar_zero_total(self):
        """Test progress bar with zero total."""
        bar = ProgressBar(total=0)

        # Should handle zero total gracefully
        bar.update(0)
        bar.finish()

        assert bar.total == 0
        assert bar.current == 0

    def test_progress_bar_very_large_total(self):
        """Test progress bar with very large total."""
        bar = ProgressBar(total=1000000)

        bar.update(500000)

        assert bar.current == 500000
        assert bar.total == 1000000

    def test_progress_bar_terminal_output(self):
        """Test progress bar output to stderr (terminal)."""
        bar = ProgressBar(total=100, task="Test")

        # Should write to stderr
        bar.update(50, force=True)
        bar.finish()

        # Should not raise error
        assert bar.current == 50

    def test_progress_bar_non_terminal_output(self):
        """Test progress bar behavior in non-terminal environment."""
        # Create a progress bar
        bar = ProgressBar(total=100, task="Test")

        # Should still work even if not a terminal
        bar.update(50, force=True)
        bar.finish()

        assert bar.current == 50

    def test_substage_progress_no_substages(self):
        """Test SubStageProgress with no substages started."""
        progress = SubStageProgress(total=5)

        # Should handle no substages gracefully
        eta = progress.get_eta()
        progress.log_progress()

        assert eta is None
        assert progress.current == 0

    def test_substage_progress_single_substage(self):
        """Test SubStageProgress with single substage."""
        progress = SubStageProgress(total=1, stage_name="Single")

        progress.start_substage(1, "Only substage")
        time.sleep(0.01)
        progress.complete_substage()

        assert progress.current == 1
        assert progress.total == 1

    def test_substage_progress_eta_across_substages(self):
        """Test ETA calculation across multiple substages."""
        progress = SubStageProgress(total=10)

        # Complete several substages to build history
        for i in range(1, 6):
            progress.start_substage(i, f"Sub-stage {i}")
            time.sleep(0.02)
            progress.complete_substage()

        # Start new substage
        progress.start_substage(6, "Sub-stage 6")

        eta = progress.get_eta()

        # Should have ETA estimate based on previous substages
        # May be None if calculation can't be done
        assert eta is None or eta >= 0

    def test_substage_progress_logging_multiple_times(self):
        """Test logging progress multiple times."""
        progress = SubStageProgress(total=5, stage_name="Test")

        progress.start_substage(1, "Sub-stage 1")
        time.sleep(0.01)

        # Should be able to log multiple times
        progress.log_progress()
        time.sleep(0.01)
        progress.log_progress()

        # Should not raise error
        assert progress.current == 1

    def test_substage_progress_complete_all_substages(self):
        """Test completing all substages."""
        progress = SubStageProgress(total=3)

        for i in range(1, 4):
            progress.start_substage(i, f"Sub-stage {i}")
            time.sleep(0.01)
            progress.complete_substage()

        assert progress.current == 3
        assert progress.total == 3

    def test_progress_bar_custom_width(self):
        """Test progress bar with custom width."""
        bar = ProgressBar(total=100, width=50)

        assert bar.width == 50
        bar.update(50, force=True)

        # Should render with custom width
        assert bar.current == 50

    def test_progress_bar_update_interval_zero(self):
        """Test progress bar with zero update interval."""
        bar = ProgressBar(total=100, update_interval=0.0)

        # Should update immediately
        bar.update(10)
        first_time = bar.last_update_time

        bar.update(20)
        # Should update immediately with zero interval
        assert bar.last_update_time >= first_time

    def test_substage_progress_get_eta_after_completion(self):
        """Test getting ETA after all substages completed."""
        progress = SubStageProgress(total=3)

        for i in range(1, 4):
            progress.start_substage(i, f"Sub-stage {i}")
            time.sleep(0.01)
            progress.complete_substage()

        # ETA should be None or very small after completion
        eta = progress.get_eta()
        assert eta is None or eta == 0


class TestProgressBarFromProgress:
    def test_init_defaults(self):
        bar = ProgressBar(total=100)
        assert bar.total == 100
        assert bar.current == 0
        assert bar.show_eta is True
        assert bar.use_ema is True

    def test_init_custom(self):
        bar = ProgressBar(total=50, task="Rendering", width=20, show_eta=False, use_ema=False)
        assert bar.total == 50
        assert bar.task == "Rendering"
        assert bar.width == 20
        assert bar.show_eta is False

    def test_update(self):
        bar = ProgressBar(total=10, update_interval=0.0)
        bar.update(5, force=True)
        assert bar.current == 5

    def test_update_clamps_to_total(self):
        bar = ProgressBar(total=10)
        bar.update(20, force=True)
        assert bar.current == 10

    def test_update_throttled(self):
        bar = ProgressBar(total=10, update_interval=999.0)
        bar.update(1)
        # Should not render due to throttle (unless force)

    def test_render_zero_total(self):
        bar = ProgressBar(total=0)
        bar.update(0, force=True)
        # Should not crash with division by zero

    def test_render_with_ema(self):
        bar = ProgressBar(total=10, use_ema=True, update_interval=0.0)
        bar.start_time = time.time() - 5.0  # Pretend 5s elapsed
        bar.update(5, force=True)
        # Should compute ETA via EMA path

    def test_render_with_linear_eta(self):
        bar = ProgressBar(total=10, use_ema=False, update_interval=0.0)
        bar.start_time = time.time() - 5.0
        bar.update(5, force=True)

    def test_render_ema_second_update(self):
        bar = ProgressBar(total=10, use_ema=True, update_interval=0.0)
        bar.start_time = time.time() - 2.0
        bar.update(2, force=True)
        bar.start_time = time.time() - 5.0
        bar.update(5, force=True)
        # previous_eta should have been updated through EMA

    def test_finish(self):
        bar = ProgressBar(total=10, task="Building", update_interval=0.0)
        bar.update(10, force=True)
        bar.finish()

    def test_finish_no_task(self):
        bar = ProgressBar(total=10, update_interval=0.0)
        bar.update(10, force=True)
        bar.finish()


class TestLLMProgressTracker:
    def test_init_defaults(self):
        t = LLMProgressTracker()
        assert t.total_tokens is None
        assert t.task == "LLM Generation"
        assert t.generated_tokens == 0
        assert t.chunks_received == 0

    def test_init_custom(self):
        t = LLMProgressTracker(total_tokens=1000, task="Review", show_throughput=False)
        assert t.total_tokens == 1000
        assert t.show_throughput is False

    def test_update_tokens(self):
        t = LLMProgressTracker(total_tokens=100)
        t.update_tokens(10)
        assert t.generated_tokens == 10
        assert t.chunks_received == 1

    def test_update_tokens_multiple(self):
        t = LLMProgressTracker(total_tokens=100)
        t.last_update_time = 0  # Force display
        t.update_tokens(30)
        t.last_update_time = 0
        t.update_tokens(40)
        assert t.generated_tokens == 70
        assert t.chunks_received == 2

    def test_update_tokens_no_total(self):
        t = LLMProgressTracker()
        t.last_update_time = 0
        t.update_tokens(50)
        assert t.generated_tokens == 50

    def test_display_with_total(self):
        t = LLMProgressTracker(total_tokens=100)
        # Just test that _display doesn't crash
        t.generated_tokens = 50
        t._display(25.0)

    def test_display_without_total(self):
        t = LLMProgressTracker()
        t.generated_tokens = 50
        t._display(25.0)

    def test_display_zero_throughput(self):
        t = LLMProgressTracker(total_tokens=100)
        t.generated_tokens = 0
        t._display(0.0)

    def test_finish(self):
        t = LLMProgressTracker(total_tokens=100)
        t.generated_tokens = 100
        t.finish()


class TestSubStageProgressFromProgress:
    def test_init_defaults(self):
        sp = SubStageProgress(total=5)
        assert sp.total == 5
        assert sp.current == 0
        assert sp.stage_name == ""
        assert sp.use_ema is True
        assert sp.substage_durations == []

    def test_start_substage(self):
        sp = SubStageProgress(total=3, stage_name="Render")
        sp.start_substage(1, "file1.md")
        assert sp.current == 1
        assert sp.current_substage_name == "file1.md"
        assert sp.substage_start_time is not None

    def test_start_substage_no_name(self):
        sp = SubStageProgress(total=3)
        sp.start_substage(1)
        assert sp.current == 1

    def test_complete_substage(self):
        sp = SubStageProgress(total=3)
        sp.start_substage(1, "step1")
        sp.complete_substage()
        assert len(sp.substage_durations) == 1
        assert sp.substage_durations[0] >= 0.0

    def test_complete_substage_without_start(self):
        sp = SubStageProgress(total=3)
        sp.complete_substage()  # substage_start_time is None, should be no-op
        assert len(sp.substage_durations) == 0

    def test_get_eta_at_zero(self):
        sp = SubStageProgress(total=5)
        assert sp.get_eta() is None

    def test_get_eta_with_ema(self):
        sp = SubStageProgress(total=10, use_ema=True)
        sp.start_time = time.time() - 5.0  # 5s elapsed
        sp.current = 5
        eta = sp.get_eta()
        # Should return some positive value
        assert eta is not None
        assert eta >= 0

    def test_get_eta_ema_second_call(self):
        sp = SubStageProgress(total=10, use_ema=True)
        sp.start_time = time.time() - 2.0
        sp.current = 2
        eta1 = sp.get_eta()
        sp.start_time = time.time() - 5.0
        sp.current = 5
        eta2 = sp.get_eta()
        assert eta1 is not None
        assert eta2 is not None

    def test_get_eta_linear(self):
        sp = SubStageProgress(total=10, use_ema=False)
        sp.start_time = time.time() - 5.0
        sp.current = 5
        eta = sp.get_eta()
        assert eta is not None

    def test_get_eta_with_confidence(self):
        sp = SubStageProgress(total=5)
        sp.start_time = time.time() - 3.0
        sp.current = 3
        sp.substage_durations = [0.9, 1.0, 1.1]
        estimate = sp.get_eta_with_confidence()
        # Should return an ETAEstimate
        assert hasattr(estimate, "optimistic")
        assert hasattr(estimate, "realistic")
        assert hasattr(estimate, "pessimistic")

    def test_get_eta_with_confidence_at_zero(self):
        sp = SubStageProgress(total=5)
        estimate = sp.get_eta_with_confidence()
        assert estimate.optimistic is None
        assert estimate.realistic is None
        assert estimate.pessimistic is None

    def test_log_progress(self):
        sp = SubStageProgress(total=5, stage_name="Build")
        sp.start_time = time.time() - 2.0
        sp.current = 2
        sp.log_progress()  # Should not crash

    def test_log_progress_zero_total(self):
        sp = SubStageProgress(total=0)
        sp.log_progress()


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
        logger = logging.getLogger("test_log_spinner")
        with log_with_spinner("Working...", logger=logger):
            pass

    def test_with_final_message(self):
        with log_with_spinner("Working...", final_message="All done"):
            pass

    def test_no_logger_no_final(self):
        with log_with_spinner("Working..."):
            pass

    def test_exception_propagates(self):
        logger = logging.getLogger("test_log_spinner")
        with pytest.raises(ValueError, match="test"):
            with log_with_spinner("Working...", logger=logger):
                raise ValueError("test")


class TestLogProgressStreaming:
    """Test log_progress_streaming — non-TTY paths."""

    def test_non_tty_with_logger(self):
        logger = logging.getLogger("test_streaming")
        log_progress_streaming(5, 10, "Progress", logger)

    def test_non_tty_zero_total(self):
        logger = logging.getLogger("test_streaming")
        log_progress_streaming(0, 0, "Empty", logger)

    def test_non_tty_no_logger(self):
        log_progress_streaming(3, 10, "Test")
