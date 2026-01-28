"""Tests for custom exceptions and utilities."""

import logging
import os
from pathlib import Path

import pytest
from src.utils.exceptions import ValidationError
from src.utils.logging import (get_logger, log_progress_bar, log_stage,
                               log_substep)
from src.utils.markdown_integration import ImageManager, MarkdownIntegration


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        error = ValidationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}
        assert error.suggestions == []

    def test_validation_error_with_context(self):
        """Test ValidationError with context."""
        context = {"field": "value", "count": 5}
        error = ValidationError("Test error", context=context)
        assert error.context == context
        assert error.message == "Test error"

    def test_validation_error_with_suggestions(self):
        """Test ValidationError with suggestions."""
        suggestions = ["Try this", "Or try that"]
        error = ValidationError("Test error", suggestions=suggestions)
        assert error.suggestions == suggestions
        assert error.message == "Test error"

    def test_validation_error_with_all_params(self):
        """Test ValidationError with all parameters."""
        context = {"field": "value"}
        suggestions = ["Fix it"]
        error = ValidationError("Test error", context=context, suggestions=suggestions)
        assert error.message == "Test error"
        assert error.context == context
        assert error.suggestions == suggestions

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from Exception."""
        error = ValidationError("Test")
        assert isinstance(error, Exception)


class TestLogging:
    """Test logging utilities."""

    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_with_level(self, monkeypatch):
        """Test logger with different log levels."""
        # Test DEBUG level
        monkeypatch.setenv("LOG_LEVEL", "0")
        logger = get_logger("test_debug")
        assert logger.level == logging.DEBUG

        # Test INFO level (default)
        monkeypatch.setenv("LOG_LEVEL", "1")
        logger = get_logger("test_info")
        assert logger.level == logging.INFO

        # Test WARNING level
        monkeypatch.setenv("LOG_LEVEL", "2")
        logger = get_logger("test_warning")
        assert logger.level == logging.WARNING

        # Test ERROR level
        monkeypatch.setenv("LOG_LEVEL", "3")
        logger = get_logger("test_error")
        assert logger.level == logging.ERROR

    def test_get_logger_default_level(self):
        """Test logger with default level when env var not set."""
        # Remove LOG_LEVEL if it exists
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]

        logger = get_logger("test_default")
        assert logger.level == logging.INFO

    def test_get_logger_reuse(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = get_logger("reuse_test")
        logger2 = get_logger("reuse_test")
        assert logger1 is logger2

    def test_log_substep(self, caplog):
        """Test log_substep function."""
        logger = get_logger("substep_test")
        with caplog.at_level(logging.INFO):
            log_substep("Test message", logger)

        assert "Test message" in caplog.text
        assert "substep_test" in caplog.text

    def test_log_progress_bar(self, caplog):
        """Test log_progress_bar function."""
        logger = get_logger("progress_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(5, 10, "Test task", logger)

        assert "50%" in caplog.text
        assert "Test task" in caplog.text

    def test_log_progress_bar_zero_total(self, caplog):
        """Test log_progress_bar with zero total."""
        logger = get_logger("progress_zero_test")
        with caplog.at_level(logging.INFO):
            log_progress_bar(0, 0, "Zero task", logger)

        assert "0%" in caplog.text

    def test_log_stage(self, caplog):
        """Test log_stage function."""
        logger = get_logger("stage_test")
        with caplog.at_level(logging.INFO):
            log_stage(2, 5, "Processing", logger)

        assert "Stage 2/5: Processing" in caplog.text


class TestMarkdownIntegration:
    """Test markdown integration utilities."""

    def test_markdown_integration_init(self, tmp_path):
        """Test MarkdownIntegration initialization."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        integration = MarkdownIntegration(manuscript_dir)
        assert integration.manuscript_dir == manuscript_dir

    def test_detect_sections(self, tmp_path):
        """Test section detection (returns empty list as stub)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        integration = MarkdownIntegration(manuscript_dir)

        test_file = manuscript_dir / "test.md"
        test_file.write_text("# Test\n\nSome content")

        sections = integration.detect_sections(test_file)
        assert sections == []  # Stub implementation returns empty list

    def test_insert_figure_in_section(self, tmp_path):
        """Test figure insertion (returns False as stub)."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        integration = MarkdownIntegration(manuscript_dir)

        test_file = manuscript_dir / "test.md"
        test_file.write_text("# Test\n\nSome content")

        result = integration.insert_figure_in_section(
            test_file, "fig:test", "introduction"
        )
        assert result is False  # Stub implementation returns False


class TestImageManager:
    """Test image manager utilities."""

    def test_image_manager_init(self):
        """Test ImageManager initialization."""
        manager = ImageManager()
        assert manager.images == {}

    def test_register_image_basic(self):
        """Test basic image registration."""
        manager = ImageManager()
        manager.register_image("test.png", "Test caption")

        assert "test.png" in manager.images
        assert manager.images["test.png"]["caption"] == "Test caption"
        assert manager.images["test.png"]["alt_text"] is None

    def test_register_image_with_alt_text(self):
        """Test image registration with alt text."""
        manager = ImageManager()
        manager.register_image("test.png", "Test caption", "Alt text")

        assert manager.images["test.png"]["alt_text"] == "Alt text"

    def test_get_image_info_existing(self):
        """Test getting info for existing image."""
        manager = ImageManager()
        manager.register_image("test.png", "Test caption")

        info = manager.get_image_info("test.png")
        assert info is not None
        assert info["caption"] == "Test caption"

    def test_get_image_info_nonexistent(self):
        """Test getting info for nonexistent image."""
        manager = ImageManager()

        info = manager.get_image_info("nonexistent.png")
        assert info is None
