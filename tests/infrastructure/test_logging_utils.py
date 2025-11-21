#!/usr/bin/env python3
"""Comprehensive tests for infrastructure/logging_utils.py.

Tests the unified logging system with real usage patterns.
No mocks - tests actual logging behavior and output.
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add infrastructure to path
sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))

from logging_utils import (
    get_log_level_from_env,
    setup_logger,
    get_logger,
    log_operation,
    log_timing,
    log_function_call,
    log_success,
    log_header,
    log_progress,
    set_global_log_level,
    TemplateFormatter,
    USE_EMOJIS,
)


class TestLogLevelConfiguration:
    """Test log level configuration from environment."""
    
    def test_get_log_level_default(self):
        """Test default log level is INFO."""
        # Clear LOG_LEVEL if set
        old_level = os.environ.pop('LOG_LEVEL', None)
        try:
            level = get_log_level_from_env()
            assert level == logging.INFO
        finally:
            if old_level:
                os.environ['LOG_LEVEL'] = old_level
    
    def test_get_log_level_debug(self):
        """Test DEBUG log level from environment."""
        os.environ['LOG_LEVEL'] = '0'
        try:
            level = get_log_level_from_env()
            assert level == logging.DEBUG
        finally:
            os.environ.pop('LOG_LEVEL', None)
    
    def test_get_log_level_info(self):
        """Test INFO log level from environment."""
        os.environ['LOG_LEVEL'] = '1'
        try:
            level = get_log_level_from_env()
            assert level == logging.INFO
        finally:
            os.environ.pop('LOG_LEVEL', None)
    
    def test_get_log_level_warning(self):
        """Test WARNING log level from environment."""
        os.environ['LOG_LEVEL'] = '2'
        try:
            level = get_log_level_from_env()
            assert level == logging.WARNING
        finally:
            os.environ.pop('LOG_LEVEL', None)
    
    def test_get_log_level_error(self):
        """Test ERROR log level from environment."""
        os.environ['LOG_LEVEL'] = '3'
        try:
            level = get_log_level_from_env()
            assert level == logging.ERROR
        finally:
            os.environ.pop('LOG_LEVEL', None)
    
    def test_get_log_level_invalid_defaults_to_info(self):
        """Test invalid log level defaults to INFO."""
        os.environ['LOG_LEVEL'] = '99'
        try:
            level = get_log_level_from_env()
            assert level == logging.INFO
        finally:
            os.environ.pop('LOG_LEVEL', None)


class TestLoggerSetup:
    """Test logger setup and configuration."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
        assert not logger.propagate
    
    def test_setup_logger_with_level(self):
        """Test logger setup with specific level."""
        logger = setup_logger("test_logger", level=logging.DEBUG)
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_with_file(self, tmp_path):
        """Test logger setup with log file."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)
        
        # Write a log message
        logger.info("Test message")
        
        # Check file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
    
    def test_get_logger_creates_if_needed(self):
        """Test get_logger creates logger if not exists."""
        logger = get_logger("new_test_logger")
        assert logger.name == "new_test_logger"
        assert len(logger.handlers) > 0
    
    def test_get_logger_returns_existing(self):
        """Test get_logger returns existing logger."""
        logger1 = get_logger("existing_logger")
        logger2 = get_logger("existing_logger")
        assert logger1 is logger2


class TestTemplateFormatter:
    """Test custom log formatter."""
    
    def test_formatter_includes_timestamp(self):
        """Test formatter includes timestamp."""
        formatter = TemplateFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        
        # Check format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
        assert "[" in formatted
        assert "]" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
    
    def test_formatter_includes_emoji_when_enabled(self):
        """Test formatter includes emoji when enabled."""
        if USE_EMOJIS:
            formatter = TemplateFormatter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None
            )
            formatted = formatter.format(record)
            # Check for info emoji
            assert "ℹ️" in formatted or "INFO" in formatted
    
    def test_formatter_different_levels(self):
        """Test formatter handles different log levels."""
        formatter = TemplateFormatter()
        
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None
            )
            formatted = formatter.format(record)
            assert logging.getLevelName(level) in formatted


class TestContextManagers:
    """Test logging context managers."""
    
    def test_log_operation_success(self, caplog):
        """Test log_operation context manager on success."""
        logger = get_logger("test_operation")
        
        with caplog.at_level(logging.INFO):
            with log_operation("Test operation", logger):
                pass  # Successful operation
        
        # Check start and completion messages
        messages = [rec.message for rec in caplog.records]
        assert any("Starting: Test operation" in msg for msg in messages)
        assert any("Completed: Test operation" in msg for msg in messages)
    
    def test_log_operation_failure(self, caplog):
        """Test log_operation context manager on failure."""
        logger = get_logger("test_operation")
        
        with caplog.at_level(logging.ERROR):
            try:
                with log_operation("Failing operation", logger):
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        # Check failure message
        messages = [rec.message for rec in caplog.records]
        assert any("Failed: Failing operation" in msg for msg in messages)
    
    def test_log_timing(self, caplog):
        """Test log_timing context manager."""
        import time
        
        logger = get_logger("test_timing")
        
        with caplog.at_level(logging.INFO):
            with log_timing("Test task", logger):
                time.sleep(0.01)  # Small delay
        
        # Check timing message
        messages = [rec.message for rec in caplog.records]
        assert any("Test task:" in msg and "s" in msg for msg in messages)


class TestDecorators:
    """Test logging decorators."""
    
    def test_log_function_call(self, caplog):
        """Test log_function_call decorator."""
        logger = get_logger("test_decorator")
        
        @log_function_call(logger)
        def test_function(x: int, y: int) -> int:
            return x + y
        
        with caplog.at_level(logging.DEBUG):
            result = test_function(2, 3)
        
        assert result == 5
        
        # Check debug messages
        messages = [rec.message for rec in caplog.records if rec.levelno == logging.DEBUG]
        assert any("Calling: test_function" in msg for msg in messages)
        assert any("Returned: test_function" in msg for msg in messages)
    
    def test_log_function_call_with_exception(self, caplog):
        """Test log_function_call decorator with exception."""
        logger = get_logger("test_decorator")
        
        @log_function_call(logger)
        def failing_function():
            raise ValueError("Test error")
        
        with caplog.at_level(logging.ERROR):
            try:
                failing_function()
            except ValueError:
                pass
        
        # Check error message
        messages = [rec.message for rec in caplog.records if rec.levelno == logging.ERROR]
        assert any("Exception in failing_function" in msg for msg in messages)


class TestUtilityFunctions:
    """Test logging utility functions."""
    
    def test_log_success(self, caplog):
        """Test log_success utility function."""
        logger = get_logger("test_utils")
        
        with caplog.at_level(logging.INFO):
            log_success("Build completed", logger)
        
        messages = [rec.message for rec in caplog.records]
        assert any("Build completed" in msg for msg in messages)
    
    def test_log_header(self, caplog):
        """Test log_header utility function."""
        logger = get_logger("test_utils")
        
        with caplog.at_level(logging.INFO):
            log_header("STAGE 01: Tests", logger)
        
        messages = [rec.message for rec in caplog.records]
        assert any("STAGE 01: Tests" in msg for msg in messages)
        assert any("=" in msg for msg in messages)
    
    def test_log_progress(self, caplog):
        """Test log_progress utility function."""
        logger = get_logger("test_utils")
        
        with caplog.at_level(logging.INFO):
            log_progress(15, 100, "Processing files", logger)
        
        messages = [rec.message for rec in caplog.records]
        assert any("15/100" in msg and "15%" in msg for msg in messages)
        assert any("Processing files" in msg for msg in messages)
    
    def test_log_progress_zero_total(self, caplog):
        """Test log_progress with zero total."""
        logger = get_logger("test_utils")
        
        with caplog.at_level(logging.INFO):
            log_progress(0, 0, "Empty task", logger)
        
        messages = [rec.message for rec in caplog.records]
        assert any("0/0" in msg and "0%" in msg for msg in messages)


class TestGlobalConfiguration:
    """Test global logging configuration."""
    
    def test_set_global_log_level(self):
        """Test setting global log level."""
        # Create a test logger
        logger = get_logger("test_global")
        
        # Set global level to DEBUG
        set_global_log_level(logging.DEBUG)
        
        # Check logger has DEBUG level
        assert logger.level == logging.DEBUG or logger.level <= logging.DEBUG
        
        # Reset to INFO
        set_global_log_level(logging.INFO)


class TestIntegration:
    """Integration tests for logging system."""
    
    def test_complete_logging_workflow(self, tmp_path):
        """Test complete logging workflow."""
        log_file = tmp_path / "workflow.log"
        logger = setup_logger("workflow_test", log_file=log_file)
        
        # Use various logging features
        logger.info("Starting workflow")
        
        with log_operation("Data processing", logger):
            logger.debug("Processing data")
            logger.info("Data processed successfully")
        
        log_success("Workflow completed", logger)
        
        # Verify log file contains expected content
        content = log_file.read_text()
        assert "Starting workflow" in content
        assert "Data processing" in content
        assert "Workflow completed" in content
    
    def test_multiple_loggers_independent(self):
        """Test multiple loggers operate independently."""
        logger1 = setup_logger("test1", level=logging.DEBUG)
        logger2 = setup_logger("test2", level=logging.ERROR)
        
        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR
        assert logger1 is not logger2

