"""Tests for infrastructure.core.logging_progress module.

Comprehensive tests for progress tracking functionality including
ETA calculations, progress bars, and spinners.

Test Pattern:
    All logging tests use `caplog` fixture (not `capsys`) because logs go through
    Python's logging framework, not direct stdout/stderr writes. Use `caplog.at_level()`
    to set the appropriate log level for the test.
"""

import pytest
import time
import sys
from io import StringIO
from unittest.mock import Mock, patch

from infrastructure.core.logging_progress import (
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
    log_progress_bar,
    Spinner,
    log_with_spinner,
)


class TestCalculateEta:
    """Test calculate_eta function."""

    def test_calculate_eta_basic(self):
        """Test basic ETA calculation."""
        # 30 seconds for 3 items = 10s/item, 7 remaining = 70s
        eta = calculate_eta(30.0, 3, 10)
        assert eta == pytest.approx(70.0, rel=0.01)

    def test_calculate_eta_zero_completed(self):
        """Test ETA calculation with zero completed items."""
        eta = calculate_eta(30.0, 0, 10)
        assert eta is None

    def test_calculate_eta_zero_total(self):
        """Test ETA calculation with zero total items."""
        eta = calculate_eta(30.0, 3, 0)
        assert eta is None

    def test_calculate_eta_completed_equals_total(self):
        """Test ETA when all items are completed."""
        eta = calculate_eta(30.0, 10, 10)
        assert eta == 0.0

    def test_calculate_eta_completed_exceeds_total(self):
        """Test ETA when completed exceeds total."""
        eta = calculate_eta(30.0, 15, 10)
        assert eta == 0.0

    def test_calculate_eta_fractional_values(self):
        """Test ETA calculation with fractional values."""
        eta = calculate_eta(15.5, 2.5, 10)
        # 15.5s for 2.5 items = 6.2s/item, 7.5 remaining = 46.5s
        assert eta == pytest.approx(46.5, rel=0.01)

    def test_calculate_eta_negative_values(self):
        """Test ETA calculation with negative values."""
        # Should handle gracefully
        eta = calculate_eta(-10.0, 3, 10)
        assert eta is not None  # May return negative or None


class TestCalculateEtaEma:
    """Test calculate_eta_ema function."""

    def test_calculate_eta_ema_basic(self):
        """Test basic EMA ETA calculation."""
        eta = calculate_eta_ema(30.0, 3, 10)
        assert eta is not None
        assert eta > 0

    def test_calculate_eta_ema_with_previous(self):
        """Test EMA ETA with previous estimate."""
        previous_eta = 80.0
        eta = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta)
        assert eta is not None
        # EMA should be between linear estimate and previous
        linear_eta = calculate_eta(30.0, 3, 10)
        assert min(linear_eta, previous_eta) <= eta <= max(linear_eta, previous_eta)

    def test_calculate_eta_ema_zero_completed(self):
        """Test EMA ETA with zero completed items."""
        eta = calculate_eta_ema(30.0, 0, 10)
        assert eta is None

    def test_calculate_eta_ema_completed_equals_total(self):
        """Test EMA ETA when all items are completed."""
        eta = calculate_eta_ema(30.0, 10, 10)
        assert eta == 0.0

    def test_calculate_eta_ema_alpha_parameter(self):
        """Test EMA ETA with different alpha values."""
        previous_eta = 80.0
        eta_low_alpha = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta, alpha=0.1)
        eta_high_alpha = calculate_eta_ema(30.0, 3, 10, previous_eta=previous_eta, alpha=0.9)
        
        # Higher alpha should be closer to linear estimate
        linear_eta = calculate_eta(30.0, 3, 10)
        assert abs(eta_high_alpha - linear_eta) < abs(eta_low_alpha - linear_eta)

    def test_calculate_eta_ema_non_negative(self):
        """Test that EMA ETA is always non-negative."""
        eta = calculate_eta_ema(30.0, 3, 10, previous_eta=-10.0)
        assert eta is not None
        assert eta >= 0.0


class TestCalculateEtaWithConfidence:
    """Test calculate_eta_with_confidence function."""

    def test_calculate_eta_with_confidence_basic(self):
        """Test basic confidence interval calculation."""
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 3, 10)
        
        assert optimistic is not None
        assert realistic is not None
        assert pessimistic is not None
        assert optimistic < realistic < pessimistic

    def test_calculate_eta_with_confidence_with_durations(self):
        """Test confidence intervals with item durations."""
        item_durations = [8.0, 10.0, 12.0]
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(
            30.0, 3, 10, item_durations=item_durations
        )
        
        # 7 remaining items
        # Optimistic: 8.0 * 7 = 56.0
        # Realistic: 10.0 * 7 = 70.0
        # Pessimistic: 12.0 * 7 = 84.0
        assert optimistic == pytest.approx(56.0, rel=0.01)
        assert realistic == pytest.approx(70.0, rel=0.01)
        assert pessimistic == pytest.approx(84.0, rel=0.01)

    def test_calculate_eta_with_confidence_zero_completed(self):
        """Test confidence intervals with zero completed items."""
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 0, 10)
        
        assert optimistic is None
        assert realistic is None
        assert pessimistic is None

    def test_calculate_eta_with_confidence_completed_equals_total(self):
        """Test confidence intervals when all items are completed."""
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(30.0, 10, 10)
        
        assert optimistic == 0.0
        assert realistic == 0.0
        assert pessimistic == 0.0

    def test_calculate_eta_with_confidence_empty_durations(self):
        """Test confidence intervals with empty durations list."""
        optimistic, realistic, pessimistic = calculate_eta_with_confidence(
            30.0, 3, 10, item_durations=[]
        )
        
        # Should fall back to linear calculation with adjustments
        assert optimistic is not None
        assert realistic is not None
        assert pessimistic is not None
        assert optimistic < realistic < pessimistic


class TestLogProgressBar:
    """Test log_progress_bar function."""

    def test_log_progress_bar_basic(self, caplog):
        """Test basic progress bar logging."""
        with caplog.at_level("INFO"):
            log_progress_bar(3, 10, "Processing")
        
        # Check that output was created
        assert "Processing" in caplog.text
        assert "%" in caplog.text or "3/10" in caplog.text

    def test_log_progress_bar_zero_total(self, caplog):
        """Test progress bar with zero total."""
        with caplog.at_level("INFO"):
            log_progress_bar(0, 0, "Processing")
        
        assert "0/0" in caplog.text or "0%" in caplog.text

    def test_log_progress_bar_complete(self, caplog):
        """Test progress bar at 100%."""
        with caplog.at_level("INFO"):
            log_progress_bar(10, 10, "Processing")
        
        assert "100%" in caplog.text or "10/10" in caplog.text

    def test_log_progress_bar_custom_message(self, caplog):
        """Test progress bar with custom message."""
        with caplog.at_level("INFO"):
            log_progress_bar(5, 10, "Custom message")
        
        assert "Custom message" in caplog.text

    def test_log_progress_bar_custom_width(self, caplog):
        """Test progress bar with custom width."""
        with caplog.at_level("INFO"):
            log_progress_bar(5, 10, "Processing", bar_width=20)
        
        # Should still output successfully
        assert "Processing" in caplog.text


class TestSpinner:
    """Test Spinner class."""

    def test_spinner_initialization(self):
        """Test spinner initialization."""
        spinner = Spinner("Test message")
        
        assert spinner.message == "Test message"
        assert spinner.delay == 0.1
        assert spinner.thread is None

    def test_spinner_start_non_tty(self, monkeypatch):
        """Test spinner start on non-TTY stream."""
        stream = StringIO()
        stream.isatty = lambda: False
        
        spinner = Spinner("Test message", stream=stream)
        spinner.start()
        
        # Should write message once for non-TTY
        output = stream.getvalue()
        assert "Test message" in output

    def test_spinner_stop_without_start(self):
        """Test stopping spinner that was never started."""
        spinner = Spinner("Test message")
        
        # Should not raise error
        spinner.stop()

    def test_spinner_context_manager(self):
        """Test spinner as context manager."""
        stream = StringIO()
        stream.isatty = lambda: False
        
        with Spinner("Test message", stream=stream) as spinner:
            assert spinner is not None
        
        # Should have written message
        output = stream.getvalue()
        assert "Test message" in output

    def test_spinner_stop_with_final_message(self):
        """Test stopping spinner with final message."""
        stream = StringIO()
        stream.isatty = lambda: False
        
        spinner = Spinner("Test message", stream=stream)
        spinner.start()
        spinner.stop("Done!")
        
        output = stream.getvalue()
        assert "Done!" in output


class TestLogWithSpinner:
    """Test log_with_spinner context manager."""

    def test_log_with_spinner_basic(self):
        """Test basic spinner context manager."""
        stream = StringIO()
        stream.isatty = lambda: False
        
        with patch('infrastructure.core.logging_progress.Spinner') as mock_spinner:
            mock_spinner_instance = Mock()
            mock_spinner.return_value = mock_spinner_instance
            
            with log_with_spinner("Loading..."):
                pass
            
            # Should have started and stopped spinner
            assert mock_spinner_instance.start.called
            assert mock_spinner_instance.stop.called

    def test_log_with_spinner_final_message(self):
        """Test spinner with final message."""
        stream = StringIO()
        stream.isatty = lambda: False
        
        with patch('infrastructure.core.logging_progress.Spinner') as mock_spinner:
            mock_spinner_instance = Mock()
            mock_spinner.return_value = mock_spinner_instance
            
            with log_with_spinner("Loading...", final_message="Loaded!"):
                pass
            
            # Should have called stop with final message
            mock_spinner_instance.stop.assert_called_with("Loaded!")

    def test_log_with_spinner_with_logger(self, caplog):
        """Test spinner with logger for final message."""
        import logging
        logger = logging.getLogger("test")
        
        stream = StringIO()
        stream.isatty = lambda: False
        
        with patch('infrastructure.core.logging_progress.Spinner') as mock_spinner:
            mock_spinner_instance = Mock()
            mock_spinner.return_value = mock_spinner_instance
            
            with log_with_spinner("Loading...", logger=logger):
                pass
            
            # Should have stopped spinner
            assert mock_spinner_instance.stop.called



