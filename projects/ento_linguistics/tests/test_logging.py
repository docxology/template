"""Dedicated tests for core/logging.py module.

Covers: get_logger (all log levels, caching, default), log_substep,
log_progress_bar (with and without zero total), log_stage.
"""
from __future__ import annotations

import logging
import os

import pytest

from core.logging import get_logger, log_progress_bar, log_stage, log_substep


class TestGetLogger:
    """Test get_logger function."""

    def test_returns_logger_instance(self):
        """Test that get_logger returns a Logger."""
        logger = get_logger("test_logging_basic")
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        """Test logger has correct name."""
        logger = get_logger("my_custom_name")
        assert logger.name == "my_custom_name"

    def test_debug_level(self, monkeypatch):
        """Test DEBUG level via LOG_LEVEL=0."""
        monkeypatch.setenv("LOG_LEVEL", "0")
        logger = get_logger("test_log_debug_level")
        assert logger.level == logging.DEBUG

    def test_info_level(self, monkeypatch):
        """Test INFO level via LOG_LEVEL=1."""
        monkeypatch.setenv("LOG_LEVEL", "1")
        logger = get_logger("test_log_info_level")
        assert logger.level == logging.INFO

    def test_warning_level(self, monkeypatch):
        """Test WARNING level via LOG_LEVEL=2."""
        monkeypatch.setenv("LOG_LEVEL", "2")
        logger = get_logger("test_log_warning_level")
        assert logger.level == logging.WARNING

    def test_error_level(self, monkeypatch):
        """Test ERROR level via LOG_LEVEL=3."""
        monkeypatch.setenv("LOG_LEVEL", "3")
        logger = get_logger("test_log_error_level")
        assert logger.level == logging.ERROR

    def test_default_level_when_unset(self, monkeypatch):
        """Test default INFO when LOG_LEVEL not set."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        logger = get_logger("test_log_default_level")
        assert logger.level == logging.INFO

    def test_invalid_level_defaults_to_info(self, monkeypatch):
        """Test invalid LOG_LEVEL falls back to INFO."""
        monkeypatch.setenv("LOG_LEVEL", "invalid")
        logger = get_logger("test_log_invalid_level")
        assert logger.level == logging.INFO

    def test_logger_has_handler(self):
        """Test that logger has at least one handler."""
        logger = get_logger("test_log_handler")
        assert len(logger.handlers) >= 1

    def test_logger_caching(self):
        """Test that same name returns same logger instance."""
        logger1 = get_logger("test_log_cache")
        logger2 = get_logger("test_log_cache")
        assert logger1 is logger2

    def test_different_names_different_loggers(self):
        """Test that different names return different loggers."""
        logger1 = get_logger("test_log_name_a")
        logger2 = get_logger("test_log_name_b")
        assert logger1 is not logger2


class TestLogSubstep:
    """Test log_substep function."""

    def test_logs_message(self, caplog):
        """Test that substep message is logged."""
        logger = get_logger("substep_dedicated_test")
        with caplog.at_level(logging.INFO):
            log_substep("Processing data", logger)
        assert "Processing data" in caplog.text

    def test_message_indented(self, caplog):
        """Test that substep message has indentation."""
        logger = get_logger("substep_indent_test")
        with caplog.at_level(logging.INFO):
            log_substep("Indented step", logger)
        assert "  Indented step" in caplog.text

    def test_default_logger(self, caplog):
        """Test substep with default logger (None)."""
        with caplog.at_level(logging.INFO):
            log_substep("Default logger message")
        assert "Default logger message" in caplog.text


class TestLogProgressBar:
    """Test log_progress_bar function."""

    def test_50_percent(self, caplog):
        """Test 50% progress display."""
        logger = get_logger("progress_50_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(5, 10, "Halfway there", logger)
        assert "50%" in caplog.text
        assert "Halfway there" in caplog.text

    def test_100_percent(self, caplog):
        """Test 100% progress display."""
        logger = get_logger("progress_100_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(10, 10, "Complete", logger)
        assert "100%" in caplog.text

    def test_0_percent(self, caplog):
        """Test 0% progress display."""
        logger = get_logger("progress_0_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(0, 10, "Starting", logger)
        assert "0%" in caplog.text

    def test_zero_total(self, caplog):
        """Test with zero total avoids division by zero."""
        logger = get_logger("progress_zero_total_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(0, 0, "Empty task", logger)
        assert "0%" in caplog.text

    def test_default_logger(self, caplog):
        """Test progress bar with default logger (None)."""
        with caplog.at_level(logging.INFO):
            log_progress_bar(3, 10, "Default progress")
        assert "30%" in caplog.text


class TestLogStage:
    """Test log_stage function."""

    def test_stage_format(self, caplog):
        """Test stage output format."""
        logger = get_logger("stage_format_test")
        with caplog.at_level(logging.INFO):
            log_stage(2, 5, "Processing Data", logger)
        assert "Stage 2/5: Processing Data" in caplog.text

    def test_first_stage(self, caplog):
        """Test first stage logging."""
        logger = get_logger("stage_first_test")
        with caplog.at_level(logging.INFO):
            log_stage(1, 10, "Initialize", logger)
        assert "Stage 1/10: Initialize" in caplog.text

    def test_last_stage(self, caplog):
        """Test last stage logging."""
        logger = get_logger("stage_last_test")
        with caplog.at_level(logging.INFO):
            log_stage(8, 8, "Finalize", logger)
        assert "Stage 8/8: Finalize" in caplog.text

    def test_default_logger(self, caplog):
        """Test stage with default logger (None)."""
        with caplog.at_level(logging.INFO):
            log_stage(3, 7, "Default stage")
        assert "Stage 3/7: Default stage" in caplog.text
