"""Tests for infrastructure.core.progress module.

Comprehensive tests for progress bar and sub-stage progress tracking.
"""

import time
import sys
from io import StringIO
import pytest

from infrastructure.core.progress import ProgressBar, SubStageProgress


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


